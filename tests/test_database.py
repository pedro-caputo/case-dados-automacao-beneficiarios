"""
Testes unitários de persistência, modelo relacional e integridade (Marco M1).
"""
import pytest
from pathlib import Path
from src.database import init_db, get_connection
from src.repositories import SolicitacaoRepository
from src.synthetic_data import generate_synthetic_intents
from src.models import (
    Solicitacao, Cliente, Beneficiario, Documento,
    StatusSolicitacao, EtapaProcesso, Prioridade, Canal,
    TipoDocumento
)


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_beneficiarios.db"
    init_db(db_file)
    return db_file


def test_init_db_and_foreign_keys(test_db):
    """Verifica se tabelas foram criadas e chaves estrangeiras estão ativas."""
    conn = get_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    fk_enabled = cursor.fetchone()[0]
    assert fk_enabled == 1

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {r[0] for r in cursor.fetchall()}
    expected = {
        "raw_intents", "simulation_runs", "solicitacoes",
        "clientes", "beneficiarios", "documentos",
        "pendencias", "tarefas", "eventos", "comunicacoes"
    }
    assert expected.issubset(tables)
    conn.close()


def test_salvar_e_recuperar_raw_intents(test_db):
    """Verifica salvamento e contagem de raw intents no SQLite."""
    repo = SolicitacaoRepository(test_db)
    intents = generate_synthetic_intents(seed=20261108, total=100)
    saved = repo.save_raw_intents(intents)
    assert saved == 100

    count = repo.count_raw_intents(seed=20261108)
    assert count == 100

    recovered = repo.get_raw_intents(seed=20261108)
    assert len(recovered) == 100
    assert recovered[0].id == intents[0].id


def test_transacao_completa_solicitacao(test_db):
    """AC-04: Registro transacional com cliente, beneficiários, documentos e evento inicial."""
    repo = SolicitacaoRepository(test_db)

    solic = Solicitacao(
        protocolo="PROT-20261108-0001",
        canal=Canal.EMAIL,
        status=StatusSolicitacao.RECEBIDA,
        etapa=EtapaProcesso.TRIAGEM,
        prioridade=Prioridade.MEDIA,
        sla_dias=5
    )

    cliente = Cliente(
        nome_ficticio="Ana Souza",
        cpf_ficticio="123.456.789-00",
        email_ficticio="ana@exemplo.com.br"
    )

    beneficiarios = [
        Beneficiario(nome_ficticio="Carlos Souza", cpf_ficticio="987.654.321-99", parentesco="Filho(a)", percentual=60.0),
        Beneficiario(nome_ficticio="Beatriz Souza", cpf_ficticio="555.444.333-22", parentesco="Cônjuge", percentual=40.0)
    ]

    docs = [
        Documento(tipo=TipoDocumento.DOCUMENTO_IDENTIFICACAO, nome_arquivo="rg.pdf", presente=True),
        Documento(tipo=TipoDocumento.FORMULARIO_ALTERACAO, nome_arquivo="formulario.pdf", presente=True)
    ]

    solic_id = repo.create_solicitacao(solic, cliente, beneficiarios, docs, ator="TEST_USER")
    assert solic_id > 0

    # Recupera e valida
    recuperada = repo.get_solicitacao(solic_id)
    assert recuperada is not None
    assert recuperada["protocolo"] == "PROT-20261108-0001"
    assert recuperada["cliente"]["nome_ficticio"] == "Ana Souza"
    assert len(recuperada["beneficiarios"]) == 2
    assert len(recuperada["documentos"]) == 2
    assert len(recuperada["eventos"]) == 2  # CRIACAO e SLA_INICIADO
    assert recuperada["eventos"][0]["tipo_evento"] == "CRIACAO"
    assert recuperada["eventos"][0]["origem_ator"] == "TEST_USER"

