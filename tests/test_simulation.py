"""
Testes automatizados para o motor de simulação e geração de relatórios (AC-11 a AC-16).
"""
import pytest
from pathlib import Path
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.simulation import SimulationEngine
from src.metrics import gerar_relatorio_markdown, gerar_tabela_slide10


@pytest.fixture
def sim_engine(tmp_path: Path):
    db_file = tmp_path / "sim_test.db"
    init_db(db_file)
    repo = SolicitacaoRepository(db_file)
    return SimulationEngine(repo)


def test_execucao_lote_completo_1000(sim_engine, tmp_path):
    """Executa lote completo de 1.000 casos e afere métricas computacionais e contadores."""
    metricas = sim_engine.executar_lote(seed=20261108, run_id="TEST-RUN-01", tempo_medio_humano_minutos=5.0)

    assert metricas["total_intencoes"] == 1000
    assert metricas["duracao_computacional_segundos"] > 0
    assert metricas["run_id"] == "TEST-RUN-01"

    cont = metricas["contadores"]
    assert cont["total"] == 1000
    # 750 sem inadequação inicial vão direto para cadastro
    assert cont["direto_para_cadastro"] == 750
    # 60 casos de baixa legibilidade geram exceção humana
    assert cont["excecao_humana"] == 60
    # 190 casos de documentos faltantes/inválidos geram pendência
    assert cont["pendencia_complemento"] == 190

    # Verifica persistência no banco
    run_records = sim_engine.repo.list_solicitacoes(run_id="TEST-RUN-01", limit=1500)
    assert len(run_records) == 1000

    # Verifica geração de relatório e tabela
    rep_path = tmp_path / "relatorio_teste.md"
    relatorio = gerar_relatorio_markdown(metricas, rep_path)
    assert "Fatos Documentados do Case" in relatorio
    assert "313,33 horas" in relatorio
    assert rep_path.exists()

    tabela = gerar_tabela_slide10(metricas)
    assert "AS-IS" in tabela
    assert "18.800 min" in tabela


def test_reprodutibilidade_logica_cenario_padrao(sim_engine):
    """
    Teste L e 2.5 — Reprodutibilidade estrita da semente 20261108:
    Mesmos parâmetros produzem os mesmos registros sintéticos, classificações e contadores.
    """
    # Execução 1
    m1 = sim_engine.executar_lote(seed=20261108, run_id="RUN-REPROD-1")
    # Execução 2
    m2 = sim_engine.executar_lote(seed=20261108, run_id="RUN-REPROD-2")

    # Contadores lógicos devem ser 100% idênticos
    assert m1["contadores"]["direto_para_cadastro"] == m2["contadores"]["direto_para_cadastro"] == 750
    assert m1["contadores"]["pendencia_complemento"] == m2["contadores"]["pendencia_complemento"] == 190
    assert m1["contadores"]["excecao_humana"] == m2["contadores"]["excecao_humana"] == 60
    assert m1["contadores"]["erros_preventivos_evitados"] == m2["contadores"]["erros_preventivos_evitados"] == 77

    # Esforço modelado residual idêntico
    comp1 = m1["comparativo"]["to_be_estimado"]
    comp2 = m2["comparativo"]["to_be_estimado"]
    assert comp1["horas_esforco_humano_estimadas"] == comp2["horas_esforco_humano_estimadas"] == 40.25
    assert comp1["reducao_esforco_humano_pct"] == comp2["reducao_esforco_humano_pct"] == 87.2

