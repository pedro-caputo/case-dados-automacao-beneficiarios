"""
Testes automatizados para workflow, transições, pendências e efetivação de cadastro (AC-04 a AC-10).
"""
import pytest
from pathlib import Path
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.workflow import WorkflowService
from src.synthetic_data import gerar_cpf_valido
from src.models import StatusSolicitacao, EtapaProcesso, EstadoSLA, EstadoComunicacao
import random


@pytest.fixture
def workflow(tmp_path: Path):
    db_file = tmp_path / "test_wf.db"
    init_db(db_file)
    repo = SolicitacaoRepository(db_file)
    return WorkflowService(repo)


def test_ac04_formulario_correto_cria_protocolo_e_evento(workflow):
    """AC-04: Formulário correto gera protocolo único, status RECEBIDA/PRONTA_PARA_CADASTRO e histórico persistido."""
    rng = random.Random(777)
    cpf_cliente = gerar_cpf_valido(rng)
    cpf_ben = gerar_cpf_valido(rng)

    cliente = {"nome": "Maria Silva", "cpf": cpf_cliente, "email": "maria@teste.com"}
    beneficiarios = [{"nome": "Lucas Silva", "cpf": cpf_ben, "parentesco": "Filho(a)", "percentual": 100.0}]
    docs = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "rg.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "form.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
    ]

    solic_id, protocolo, res = workflow.criar_solicitacao(
        canal="APP",
        cliente_dados=cliente,
        beneficiarios_dados=beneficiarios,
        documentos_dados=docs,
        auto_validar=True
    )

    assert solic_id is not None
    assert protocolo.startswith("BEN-")
    assert res.valido is True

    solic = workflow.repo.get_solicitacao(solic_id)
    assert solic["status"] == StatusSolicitacao.PRONTA_PARA_CADASTRO.value
    assert len(solic["eventos"]) >= 3  # CRIACAO, SLA_INICIADO, TRANSICAO_EM_VALIDACAO, TRANSICAO_PRONTA_PARA_CADASTRO
    assert len(solic["comunicacoes"]) >= 1
    assert solic["comunicacoes"][0]["template"] == "CONFIRMACAO_RECEBIMENTO"


def test_ac05_ac06_inconsistencia_gera_pendencia_e_pausa_sla(workflow):
    """AC-05 e AC-06: Inconsistência documental abre pendência, vai para AGUARDANDO_CLIENTE e pausa SLA."""
    rng = random.Random(888)
    cpf_cliente = gerar_cpf_valido(rng)
    cpf_ben = gerar_cpf_valido(rng)

    cliente = {"nome": "João Santos", "cpf": cpf_cliente, "email": "joao@teste.com"}
    beneficiarios = [{"nome": "Pedro Santos", "cpf": cpf_ben, "parentesco": "Filho(a)", "percentual": 100.0}]
    
    # Documento ausente intencional na validação sistêmica
    docs_com_falha = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "rg.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "", "presente": False, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
    ]

    # Cria sem autovalidar preventivamente para simular entrada de canal legado (como e-mail)
    solic_id = workflow.repo.create_solicitacao(
        solicitacao=workflow.repo._get_conn() and None, # Mock helper
        cliente=None, beneficiarios=[], documentos=[]
    ) if False else None

    # Usamos o método do repositório diretamente para simular e-mail legado com anexo faltante
    from src.models import Solicitacao, Cliente, Beneficiario, Documento, Canal, Prioridade
    solic = Solicitacao(protocolo="BEN-TESTE-PEND", canal=Canal.EMAIL, status=StatusSolicitacao.RECEBIDA, etapa=EtapaProcesso.TRIAGEM, prioridade=Prioridade.MEDIA)
    cli = Cliente(nome_ficticio="João Santos", cpf_ficticio=cpf_cliente, email_ficticio="joao@teste.com")
    bens = [Beneficiario(nome_ficticio="Pedro Santos", cpf_ficticio=cpf_ben, parentesco="Filho(a)", percentual=100.0)]
    documentos = [
        Documento(tipo="DOCUMENTO_IDENTIFICACAO", nome_arquivo="rg.pdf", presente=True, formato="pdf"),
        Documento(tipo="FORMULARIO_ALTERACAO", nome_arquivo="", presente=False, formato="pdf")
    ]
    s_id = workflow.repo.create_solicitacao(solic, cli, bens, documentos)

    # Executa conferência sistêmica
    resultado = workflow.executar_validacao_sistemica(s_id, ator="SISTEMA")
    assert resultado["status"] == StatusSolicitacao.AGUARDANDO_CLIENTE.value

    recup = workflow.repo.get_solicitacao(s_id)
    assert recup["status"] == StatusSolicitacao.AGUARDANDO_CLIENTE.value
    assert recup["sla_estado"] == EstadoSLA.PAUSADO.value
    assert len(recup["pendencias"]) == 1
    assert "Documento obrigatório ausente" in recup["pendencias"][0]["descricao"]

    # AC-08: Complemento recebido fecha pendência, retoma SLA e revalida
    novos_docs = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "rg.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "formulario_assinado.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
    ]
    sucesso_comp = workflow.registrar_complemento_cliente(s_id, novos_docs, resolucao="Anexado formulário correto.")
    assert sucesso_comp is True

    apos_comp = workflow.repo.get_solicitacao(s_id)
    assert apos_comp["status"] == StatusSolicitacao.PRONTA_PARA_CADASTRO.value
    assert apos_comp["sla_estado"] == EstadoSLA.CORRENDO.value
    assert apos_comp["pendencias"][0]["fechada_em"] is not None


def test_ac10_bloqueio_conclusao_sem_efetivacao_cadastro(workflow):
    """AC-10: Impede marcar conclusão sem confirmação de cadastro no estado EM_CADASTRO."""
    rng = random.Random(999)
    cpf_cliente = gerar_cpf_valido(rng)
    cpf_ben = gerar_cpf_valido(rng)

    cliente = {"nome": "Ana Lima", "cpf": cpf_cliente, "email": "ana@teste.com"}
    beneficiarios = [{"nome": "Paulo Lima", "cpf": cpf_ben, "parentesco": "Cônjuge", "percentual": 100.0}]
    docs = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "rg.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "form.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
    ]

    solic_id, _, _ = workflow.criar_solicitacao("APP", cliente, beneficiarios, docs, auto_validar=True)
    solic = workflow.repo.get_solicitacao(solic_id)
    assert solic["status"] == StatusSolicitacao.PRONTA_PARA_CADASTRO.value

    # Tenta concluir diretamente estando em PRONTA_PARA_CADASTRO -> Deve lançar erro!
    with pytest.raises(ValueError) as excinfo:
        workflow.efetivar_cadastro_e_concluir(solic_id, ator="ANALISTA")
    assert "sem efetivação prévia" in str(excinfo.value)

    # Fluxo correto: Inicia cadastro (EM_CADASTRO) e então conclui com sucesso
    workflow.iniciar_cadastro(solic_id, ator="ANALISTA")
    solic_cad = workflow.repo.get_solicitacao(solic_id)
    assert solic_cad["status"] == StatusSolicitacao.EM_CADASTRO.value

    sucesso_conc = workflow.efetivar_cadastro_e_concluir(solic_id, ator="ANALISTA", observacao="Confirmado no sistema central.")
    assert sucesso_conc is True

    solic_final = workflow.repo.get_solicitacao(solic_id)
    assert solic_final["status"] == StatusSolicitacao.CONCLUIDA.value
    assert solic_final["etapa"] == EtapaProcesso.FINALIZADO.value
    assert solic_final["data_conclusao"] is not None

