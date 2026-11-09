"""
Testes funcionais dos Cenários A a G descritos no documento de refinamento de UX/UI.
"""
import pytest
from pathlib import Path
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.workflow import WorkflowService
from src.simulation import SimulationEngine
from src.validators import validar_cpf, validar_beneficiarios
from src.synthetic_data import gerar_cpf_valido, gerar_cpf_invalido
from src.sla import calcular_metricas_sla
from src.models import StatusSolicitacao, EtapaProcesso, EstadoSLA
import random


@pytest.fixture
def service(tmp_path: Path):
    db_file = tmp_path / "functional_scenarios.db"
    init_db(db_file)
    repo = SolicitacaoRepository(db_file)
    wf = WorkflowService(repo)
    return repo, wf


def test_cenario_a_solicitacao_valida(service):
    """Cenário A: Preencher dados válidos, registrar, gerar protocolo, verificar persistência e status."""
    repo, wf = service
    rng = random.Random(101)

    cliente = {"nome": "Lucas Ferreira", "cpf": gerar_cpf_valido(rng), "email": "lucas@exemplo.com"}
    beneficiarios = [{"nome": "Carla Ferreira", "cpf": gerar_cpf_valido(rng), "parentesco": "Cônjuge", "percentual": 100.0}]
    documentos = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "identificacao.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "formulario.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
    ]

    solic_id, protocolo, val = wf.criar_solicitacao("APP", cliente, beneficiarios, documentos, auto_validar=True)
    assert val.valido is True
    assert solic_id is not None
    assert protocolo.startswith("BEN-")

    solic = repo.get_solicitacao(solic_id)
    assert solic["status"] == StatusSolicitacao.PRONTA_PARA_CADASTRO.value
    assert solic["etapa"] == EtapaProcesso.CADASTRO.value
    assert len(solic["beneficiarios"]) == 1
    assert len(solic["eventos"]) >= 3


def test_cenario_b_cpf_invalido(service):
    """Cenário B: Inserir CPF inválido, confirmar bloqueio preventivo, corrigir e aceitar."""
    repo, wf = service
    rng = random.Random(102)

    cpf_ruim = "111.111.111-11"
    v1, m1 = validar_cpf(cpf_ruim)
    assert v1 is False
    assert "repetidos" in m1

    # Tenta submeter com CPF inválido
    cliente_ruim = {"nome": "Teste Bloqueio", "cpf": cpf_ruim, "email": "t@teste.com"}
    beneficiarios = [{"nome": "Filho", "cpf": gerar_cpf_valido(rng), "parentesco": "Filho(a)", "percentual": 100.0}]
    docs = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "id.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "form.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
    ]

    s_id, _, val_ruim = wf.criar_solicitacao("WEB", cliente_ruim, beneficiarios, docs)
    assert s_id is None
    assert val_ruim.valido is False
    assert any("repetidos" in e for e in val_ruim.erros)

    # Corrige o CPF
    cpf_bom = gerar_cpf_valido(rng)
    cliente_bom = {"nome": "Teste Bloqueio", "cpf": cpf_bom, "email": "t@teste.com"}
    s_id_ok, prot, val_bom = wf.criar_solicitacao("WEB", cliente_bom, beneficiarios, docs)
    assert s_id_ok is not None
    assert val_bom.valido is True


def test_cenario_c_percentuais_invalidos(service):
    """Cenário C: Percentuais diferentes de 100% são bloqueados preventivamente."""
    rng = random.Random(103)
    bens_errados = [
        {"nome": "Ben 1", "cpf": gerar_cpf_valido(rng), "percentual": 60.0},
        {"nome": "Ben 2", "cpf": gerar_cpf_valido(rng), "percentual": 60.0} # Total = 120%
    ]
    res = validar_beneficiarios(bens_errados)
    assert res.valido is False
    assert any("120.00%" in e for e in res.erros)

    # Corrige para 100%
    bens_certos = [
        {"nome": "Ben 1", "cpf": gerar_cpf_valido(rng), "percentual": 50.0},
        {"nome": "Ben 2", "cpf": gerar_cpf_valido(rng), "percentual": 50.0}
    ]
    res_ok = validar_beneficiarios(bens_certos)
    assert res_ok.valido is True


def test_cenario_d_documentacao_incompleta_e_pausa_sla(service):
    """Cenário D: Anexo ausente gera pendência, notificação, pausa de SLA e retomada ao receber complemento."""
    repo, wf = service
    rng = random.Random(104)

    cliente = {"nome": "Patrícia Costa", "cpf": gerar_cpf_valido(rng), "email": "patricia@exemplo.com"}
    beneficiarios = [{"nome": "Marcos Costa", "cpf": gerar_cpf_valido(rng), "parentesco": "Cônjuge", "percentual": 100.0}]
    
    # Criamos direto na camada de negócio simulando canal com anexo ausente
    from src.models import Solicitacao, Cliente, Beneficiario, Documento, Canal, Prioridade
    solic = Solicitacao(protocolo="BEN-TESTE-CEN-D", canal=Canal.EMAIL, status=StatusSolicitacao.RECEBIDA, etapa=EtapaProcesso.TRIAGEM, prioridade=Prioridade.MEDIA)
    cli = Cliente(nome_ficticio="Patrícia Costa", cpf_ficticio=cliente["cpf"], email_ficticio=cliente["email"])
    bens = [Beneficiario(nome_ficticio="Marcos Costa", cpf_ficticio=beneficiarios[0]["cpf"], parentesco="Cônjuge", percentual=100.0)]
    docs = [
        Documento(tipo="DOCUMENTO_IDENTIFICACAO", nome_arquivo="id.pdf", presente=True, formato="pdf"),
        Documento(tipo="FORMULARIO_ALTERACAO", nome_arquivo="", presente=False, formato="pdf")
    ]
    s_id = repo.create_solicitacao(solic, cli, bens, docs)

    # Executa validação sistêmica
    diag = wf.executar_validacao_sistemica(s_id)
    assert diag["status"] == StatusSolicitacao.AGUARDANDO_CLIENTE.value

    # Confirma status e pausa de SLA
    solic_p = repo.get_solicitacao(s_id)
    assert solic_p["status"] == StatusSolicitacao.AGUARDANDO_CLIENTE.value
    assert solic_p["sla_estado"] == EstadoSLA.PAUSADO.value
    assert len(solic_p["pendencias"]) == 1

    # Registra complemento
    novos_docs = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "id.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "form_assinado.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
    ]
    wf.registrar_complemento_cliente(s_id, novos_docs, resolucao="Formulário entregue.")
    
    solic_pos = repo.get_solicitacao(s_id)
    assert solic_pos["status"] == StatusSolicitacao.PRONTA_PARA_CADASTRO.value
    assert solic_pos["sla_estado"] == EstadoSLA.CORRENDO.value


def test_cenario_e_intervencao_humana_e_decisao(service):
    """Cenário E: Exceção documental vai para análise humana, analista registra decisão e justifica."""
    repo, wf = service
    rng = random.Random(105)

    cliente = {"nome": "Roberto Dias", "cpf": gerar_cpf_valido(rng), "email": "roberto@exemplo.com"}
    beneficiarios = [{"nome": "Julia Dias", "cpf": gerar_cpf_valido(rng), "parentesco": "Filho(a)", "percentual": 100.0}]
    # Documento com baixa legibilidade simulada
    docs = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "id_borrado.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "form.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": False}
    ]

    s_id, _, _ = wf.criar_solicitacao("APP", cliente, beneficiarios, docs, auto_validar=True)
    solic = repo.get_solicitacao(s_id)
    assert solic["status"] == StatusSolicitacao.EXCECAO.value

    # Analista atua sobre a exceção e aprova
    wf.iniciar_cadastro(s_id, ator="ANALISTA")
    solic_cad = repo.get_solicitacao(s_id)
    assert solic_cad["status"] == StatusSolicitacao.EM_CADASTRO.value


def test_cenario_f_conclusao_segura(service):
    """Cenário F: Bloqueio de conclusão arbitrária e finalização segura com confirmação cadastral."""
    repo, wf = service
    rng = random.Random(106)

    cliente = {"nome": "Sílvia Prado", "cpf": gerar_cpf_valido(rng), "email": "silvia@exemplo.com"}
    beneficiarios = [{"nome": "Fábio Prado", "cpf": gerar_cpf_valido(rng), "parentesco": "Cônjuge", "percentual": 100.0}]
    docs = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "id.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "form.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
    ]

    s_id, _, _ = wf.criar_solicitacao("APP", cliente, beneficiarios, docs, auto_validar=True)
    # Tentar concluir sem iniciar cadastro deve falhar!
    with pytest.raises(ValueError):
        wf.efetivar_cadastro_e_concluir(s_id, ator="ANALISTA")

    # Inicia cadastro e depois conclui
    wf.iniciar_cadastro(s_id, ator="ANALISTA")
    ok = wf.efetivar_cadastro_e_concluir(s_id, ator="ANALISTA", observacao="Averbado na apólice com sucesso.")
    assert ok is True

    solic_fim = repo.get_solicitacao(s_id)
    assert solic_fim["status"] == StatusSolicitacao.CONCLUIDA.value
    assert solic_fim["etapa"] == EtapaProcesso.FINALIZADO.value
    assert solic_fim["data_conclusao"] is not None


def test_cenario_g_experimento_reprodutibilidade(service):
    """Cenário G: Executar lote de 1.000, validar categorias, métricas e reprodutibilidade de seed."""
    repo, wf = service
    engine = SimulationEngine(repo)

    m1 = engine.executar_lote(seed=20261108, run_id="TEST-CEN-G1")
    assert m1["total_intencoes"] == 1000
    assert m1["contadores"]["direto_para_cadastro"] == 750
    assert m1["contadores"]["pendencia_complemento"] == 190
    assert m1["contadores"]["excecao_humana"] == 60

    # Reexecução com mesma semente produz os mesmos números
    m2 = engine.executar_lote(seed=20261108, run_id="TEST-CEN-G2")
    assert m2["contadores"] == m1["contadores"]

