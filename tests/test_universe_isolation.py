"""
Testes automatizados para isolamento de universos de dados (Operação Interativa vs Simulação Experimental).
Garante que métricas, filas, bancada do analista e exclusões não sofram vazamento entre contextos.
"""
import pytest
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.models import (
    Solicitacao, Cliente, Beneficiario, Documento,
    Canal, StatusSolicitacao, EtapaProcesso, Prioridade, SimulationRun
)
from src.simulation import SimulationEngine
from src.config import DB_PATH


def test_isolamento_solicitacao_interativa_vs_experimental():
    """Valida que solicitações criadas interativamente têm universo INTERATIVO e run_id nulo."""
    repo = SolicitacaoRepository(DB_PATH)

    import uuid
    proto_teste = f"BEN-TESTE-{uuid.uuid4().hex[:6].upper()}"

    # 1. Cria solicitação interativa
    solic_interativa = Solicitacao(
        protocolo=proto_teste,
        run_id=None,
        canal=Canal.APP,
        status=StatusSolicitacao.EXCECAO,
        etapa=EtapaProcesso.CONFERENCIA,
        prioridade=Prioridade.ALTA
    )
    cli = Cliente(nome_ficticio="Segurado Interativo Teste", cpf_ficticio="111.444.777-35")
    bens = [Beneficiario(nome_ficticio="Beneficiário 1", cpf_ficticio="222.555.888-40", parentesco="Cônjuge", percentual=100.0)]
    docs = [Documento(tipo="DOCUMENTO_IDENTIFICACAO", nome_arquivo="rg.pdf", legibilidade_simulada=False)]

    solic_id = repo.create_solicitacao(solic_interativa, cli, bens, docs, ator="TESTE")
    assert solic_id > 0

    solic_gravada = repo.get_solicitacao(solic_id)
    assert solic_gravada["universo"] == "INTERATIVO"
    assert solic_gravada["run_id"] is None

    # 2. Testa list_solicitacoes com filtro de universo
    interativos = repo.list_solicitacoes(universo="INTERATIVO", limit=1000)
    assert any(s["id"] == solic_id for s in interativos)
    assert all(s.get("universo") == "INTERATIVO" or s.get("run_id") is None for s in interativos)

    experimentais = repo.list_solicitacoes(universo="EXPERIMENTAL", limit=1000)
    assert not any(s["id"] == solic_id for s in experimentais)
    assert all(s.get("universo") == "EXPERIMENTAL" or s.get("run_id") is not None for s in experimentais)

    # Limpa registro temporário de teste
    conn = repo._get_conn()
    conn.execute("DELETE FROM solicitacoes WHERE id = ?", (solic_id,))
    conn.commit()


def test_dashboard_metrics_isolamento_rigoroso():
    """Valida que get_dashboard_metrics para INTERATIVO não contabiliza casos do lote experimental."""
    repo = SolicitacaoRepository(DB_PATH)

    metrics_interativo = repo.get_dashboard_metrics(universo="INTERATIVO")
    metrics_experimental = repo.get_dashboard_metrics(universo="EXPERIMENTAL", run_id="EXP-20261108")

    # Volume interativo é uma coorte pequena de teste (<= 20 registros)
    assert metrics_interativo["total_solicitacoes"] < 100, "Métricas interativas estão misturadas com o lote experimental!"

    # Volume experimental com semente padrão é exatamente 1.000
    assert metrics_experimental["total_solicitacoes"] == 1000, "Métricas experimentais devem totalizar 1.000 casos!"


def test_roteamento_fila_para_bancada_com_isolamento():
    """Valida que a consulta da Bancada do Analista incorpora o caso interativo sem misturar com experimental."""
    repo = SolicitacaoRepository(DB_PATH)

    # Localiza uma exceção interativa
    excecoes_interativas = repo.list_solicitacoes(status="EXCECAO", universo="INTERATIVO", limit=10)
    assert len(excecoes_interativas) > 0, "Deve haver pelo menos uma exceção interativa para teste"

    alvo = excecoes_interativas[0]
    alvo_id = alvo["id"]

    # Simula busca de casos elegíveis na Bancada para o universo INTERATIVO
    casos_excecao = repo.list_solicitacoes(status="EXCECAO", universo="INTERATIVO", limit=50)
    casos_cadastro = repo.list_solicitacoes(status="EM_CADASTRO", universo="INTERATIVO", limit=50)
    casos_analise = casos_excecao + casos_cadastro

    # Garante que o caso alvo está presente
    ids_analise = [c["id"] for c in casos_analise]
    assert alvo_id in ids_analise, f"Caso #{alvo_id} não foi encontrado na lista de análise da Bancada Interativa"


def test_gerenciamento_e_exclusao_transacional_de_simulacao():
    """Valida criação e exclusão segura de lote experimental descartável sem afetar interativos."""
    repo = SolicitacaoRepository(DB_PATH)
    engine = SimulationEngine(repo)

    # 1. Conta interativos antes
    count_interativos_antes = len(repo.list_solicitacoes(universo="INTERATIVO", limit=1000))

    # 2. Executa uma simulação descartável
    test_run_id = "EXP-TESTE-DESCARTE-99"
    engine.executar_lote(seed=99999, run_id=test_run_id)

    # Verifica que o lote foi registrado
    runs = repo.list_simulation_runs()
    assert any(r["id"] == test_run_id for r in runs)

    solics_criadas = repo.list_solicitacoes(universo="EXPERIMENTAL", run_id=test_run_id, limit=2000)
    assert len(solics_criadas) == 1000

    # 3. Exclui o lote experimental
    removido = repo.delete_simulation_run(test_run_id)
    assert removido is True

    # 4. Confirma que o lote foi excluído
    solics_pos = repo.list_solicitacoes(universo="EXPERIMENTAL", run_id=test_run_id, limit=2000)
    assert len(solics_pos) == 0

    runs_pos = repo.list_simulation_runs()
    assert not any(r["id"] == test_run_id for r in runs_pos)

    # 5. Confirma que os registros interativos permaneceram 100% intactos
    count_interativos_depois = len(repo.list_solicitacoes(universo="INTERATIVO", limit=1000))
    assert count_interativos_depois == count_interativos_antes, "Exclusão experimental afetou indevidamente os registros interativos!"
