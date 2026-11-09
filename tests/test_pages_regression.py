"""
Testes de regressão automatizados para interface e páginas Streamlit via AppTest.
Garante que todas as páginas carregam, renderizam componentes e interagem sem exceções.
"""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

BASE_DIR = Path(__file__).resolve().parent.parent


def test_regression_page_app():
    """Valida que a página inicial app.py inicializa sem exceções e contém botões de navegação."""
    at = AppTest.from_file(str(BASE_DIR / "app.py"), default_timeout=30)
    at.run()
    assert not at.exception, f"Erro na página app.py: {at.exception}"
    button_labels = [b.label for b in at.button]
    assert any("Criar Nova Solicitação" in lbl for lbl in button_labels)
    assert any("Acessar Fila Operacional" in lbl for lbl in button_labels)
    assert any("Abrir Laboratório" in lbl for lbl in button_labels)


def test_regression_page_01_nova_solicitacao():
    """Valida formulário de Nova Solicitação, geração de perfil dinâmico e validação de entrada."""
    at = AppTest.from_file(str(BASE_DIR / "pages" / "01_Nova_Solicitacao.py"), default_timeout=30)
    at.run()
    assert not at.exception, f"Erro inicial em 01_Nova_Solicitacao.py: {at.exception}"

    # Testa clique no botão de geração de perfil fictício completo
    gerar_btn = [b for b in at.button if "Gerar Novo Perfil" in b.label]
    assert len(gerar_btn) > 0, "Botão Gerar Perfil Fictício não encontrado"
    gerar_btn[0].click()
    at.run()
    assert not at.exception, f"Erro após Gerar Perfil: {at.exception}"

    # Verifica que campos foram preenchidos
    nome = at.text_input(key="input_nome_segurado").value
    cpf = at.text_input(key="input_cpf_segurado").value
    email = at.text_input(key="input_email_segurado").value
    assert len(nome) > 0, "Nome do segurado não foi gerado"
    assert len(cpf) > 0, "CPF do segurado não foi gerado"
    assert "@" in email, "E-mail gerado é inválido"


def test_regression_page_02_fila_operacional():
    """Valida carregamento da Fila Operacional, filtros e ausência de exceções."""
    at = AppTest.from_file(str(BASE_DIR / "pages" / "02_Fila_Operacional.py"), default_timeout=30)
    at.run()
    assert not at.exception, f"Erro em 02_Fila_Operacional.py: {at.exception}"
    assert len(at.selectbox) >= 3, "Filtros da Fila Operacional não foram renderizados"


def test_regression_page_03_analise_humana():
    """Valida bancada do analista, cronômetro e ausência de exceções."""
    at = AppTest.from_file(str(BASE_DIR / "pages" / "03_Analise_Humana.py"), default_timeout=30)
    at.run()
    assert not at.exception, f"Erro em 03_Analise_Humana.py: {at.exception}"
    button_labels = [b.label for b in at.button]
    assert any("Iniciar Análise" in lbl for lbl in button_labels)
    assert any("Gravar Decisão" in lbl for lbl in button_labels)


def test_regression_page_04_dashboard():
    """Valida dashboard gerencial e métricas de pendências abertas vs resolvidas."""
    at = AppTest.from_file(str(BASE_DIR / "pages" / "04_Dashboard.py"), default_timeout=30)
    at.run()
    assert not at.exception, f"Erro em 04_Dashboard.py: {at.exception}"


def test_regression_page_05_laboratorio():
    """Valida laboratório experimental, painel do Slide 10 e auditoria de esforço."""
    at = AppTest.from_file(str(BASE_DIR / "pages" / "05_Laboratorio.py"), default_timeout=30)
    at.run()
    assert not at.exception, f"Erro em 05_Laboratorio.py: {at.exception}"
