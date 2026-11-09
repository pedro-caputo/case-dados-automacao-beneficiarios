"""
Script utilitário para inicializar o banco de dados principal e popular dados sintéticos demonstrativos.
Permite reproduzir 100% do ambiente a partir de um clone limpo do GitHub.
"""
from pathlib import Path
from datetime import datetime, timedelta
from src.config import DB_PATH, DEFAULT_SEED, DATA_DIR
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.synthetic_data import generate_synthetic_intents, export_intents_to_csv
from src.simulation import SimulationEngine
from src.models import (
    Solicitacao, Cliente, Beneficiario, Documento,
    Canal, StatusSolicitacao, EtapaProcesso, Prioridade, EstadoSLA
)
from src.workflow import gerar_protocolo_unico


def seed_interactive_demo_cases(repo: SolicitacaoRepository):
    """Cria os 3 casos interativos de referência para demonstração da esteira operacional."""
    interativos = repo.list_solicitacoes(universo="INTERATIVO")
    if interativos:
        print(f"[i] Já existem {len(interativos)} solicitações interativas no banco.")
        return

    print("[*] Criando casos de referência da Operação Interativa...")

    # Caso 1: Concluída STP
    p1 = gerar_protocolo_unico()
    now_iso = datetime.now().isoformat()
    s1 = Solicitacao(
        protocolo=p1,
        universo="INTERATIVO",
        canal=Canal.APP,
        status=StatusSolicitacao.CONCLUIDA,
        etapa=EtapaProcesso.FINALIZADO,
        prioridade=Prioridade.MEDIA,
        responsavel="SISTEMA_STP",
        sla_estado=EstadoSLA.CORRENDO,
        data_conclusao=now_iso
    )
    c1 = Cliente(nome_ficticio="Carlos Eduardo Moreira", cpf_ficticio="123.456.789-00", email_ficticio="carlos.moreira@exemplo.com", telefone_ficticio="(11) 98765-4321")
    b1 = [Beneficiario(nome_ficticio="Mariana Moreira", cpf_ficticio="234.567.890-11", parentesco="Filho(a)", percentual=100.0)]
    d1 = [Documento(tipo="DOCUMENTO_IDENTIFICACAO", nome_arquivo="cnh_carlos.pdf", presente=True, valido_sintatico=True, legibilidade_simulada=True)]
    repo.create_solicitacao(s1, c1, b1, d1, ator="DEMO")

    # Caso 2: Concluída após Análise Humana
    p2 = gerar_protocolo_unico()
    s2 = Solicitacao(
        protocolo=p2,
        universo="INTERATIVO",
        canal=Canal.AGENCIA,
        status=StatusSolicitacao.CONCLUIDA,
        etapa=EtapaProcesso.FINALIZADO,
        prioridade=Prioridade.ALTA,
        responsavel="Analista Operacional",
        sla_estado=EstadoSLA.CORRENDO,
        data_conclusao=now_iso
    )
    c2 = Cliente(nome_ficticio="Beatriz Antunes de Souza", cpf_ficticio="345.678.901-22", email_ficticio="beatriz.antunes@exemplo.com", telefone_ficticio="(21) 97654-3210")
    b2 = [
        Beneficiario(nome_ficticio="Lucas Antunes", cpf_ficticio="456.789.012-33", parentesco="Cônjuge", percentual=60.0),
        Beneficiario(nome_ficticio="Juliana Antunes", cpf_ficticio="567.890.123-44", parentesco="Filho(a)", percentual=40.0)
    ]
    d2 = [
        Documento(tipo="DOCUMENTO_IDENTIFICACAO", nome_arquivo="rg_beatriz.pdf", presente=True, valido_sintatico=True, legibilidade_simulada=True),
        Documento(tipo="COMPROVANTE_VINCULO", nome_arquivo="certidao_casamento.pdf", presente=True, valido_sintatico=True, legibilidade_simulada=True)
    ]
    repo.create_solicitacao(s2, c2, b2, d2, ator="DEMO")

    # Caso 3: Em Exceção no Backlog (Aguardando Análise do Analista)
    p3 = gerar_protocolo_unico()
    s3 = Solicitacao(
        protocolo=p3,
        universo="INTERATIVO",
        canal=Canal.EMAIL,
        status=StatusSolicitacao.EXCECAO,
        etapa=EtapaProcesso.CONFERENCIA,
        prioridade=Prioridade.ALTA,
        responsavel="Fila de Exceções",
        sla_estado=EstadoSLA.CORRENDO
    )
    c3 = Cliente(nome_ficticio="Roberto Alves Guimarães", cpf_ficticio="678.901.234-55", email_ficticio="roberto.guimaraes@exemplo.com", telefone_ficticio="(31) 96543-2109")
    b3 = [Beneficiario(nome_ficticio="Fernanda Guimarães", cpf_ficticio="789.012.345-66", parentesco="Irmão/Irmã", percentual=100.0)]
    d3 = [Documento(tipo="DOCUMENTO_IDENTIFICACAO", nome_arquivo="documento_ilegivel.pdf", presente=True, valido_sintatico=True, legibilidade_simulada=False)]
    repo.create_solicitacao(s3, c3, b3, d3, ator="DEMO")
    print(f"[+] 3 casos interativos de referência criados ({p1}, {p2}, {p3}).")


def run_seed():
    print(f"[*] Inicializando banco de dados em: {DB_PATH}")
    init_db(DB_PATH)

    repo = SolicitacaoRepository(DB_PATH)
    total_existente = repo.count_raw_intents(DEFAULT_SEED)

    if total_existente == 1000:
        print(f"[+] 1.000 intenções brutas para a seed {DEFAULT_SEED} já existem no banco.")
    else:
        print(f"[*] Gerando 1.000 intenções sintéticas com seed={DEFAULT_SEED}...")
        intents = generate_synthetic_intents(seed=DEFAULT_SEED, total=1000)
        repo.save_raw_intents(intents)
        csv_path = DATA_DIR / "raw_intents_1000.csv"
        export_intents_to_csv(intents, csv_path)
        print(f"[+] 1.000 intenções gravadas no SQLite e exportadas para: {csv_path}")

    # Inicializa casos interativos de demonstração
    seed_interactive_demo_cases(repo)

    # Inicializa simulação experimental padrão se não existir
    runs = repo.list_simulation_runs()
    if not runs:
        print("[*] Executando lote experimental de referência (EXP-20261108)...")
        engine = SimulationEngine(repo)
        engine.executar_lote(seed=DEFAULT_SEED, run_id="EXP-20261108")
        print("[+] Lote experimental de 1.000 casos executado com sucesso.")


if __name__ == "__main__":
    run_seed()
