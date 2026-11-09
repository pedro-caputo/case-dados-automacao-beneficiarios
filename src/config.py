"""
Configurações, constantes e parâmetros factuais do case.
"""
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
DOCS_DIR = BASE_DIR / "docs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Banco de dados
DB_PATH = DATA_DIR / "beneficiarios.db"

# Parâmetros factuais do case (AS-IS) - Imutáveis conforme especificação
AS_IS_VOLUME_MENSAL = 1000
AS_IS_CRESCIMENTO_PREVISTO_AA = 0.10
AS_IS_EQUIPE_ANALISTAS = 3

AS_IS_DISTRIBUICAO_CANAIS = {
    "EMAIL": 550,    # 55%
    "AGENCIA": 300,  # 30%
    "APP": 150       # 15%
}

AS_IS_INADEQUACOES_DOCS = 250       # 25% chegam incompletas ou ilegíveis
AS_IS_DOCS_ADEQUADOS = 750          # 75%
AS_IS_COMPLEMENTOS_MAIS_5_DIAS = 100 # 40% de 250 = 100 clientes

AS_IS_MINUTOS_TRIAGEM = 4000         # 1000 * 4 min (66h40)
AS_IS_MINUTOS_CONFERENCIA = 6000     # 1000 * 6 min (100h)
AS_IS_MINUTOS_COMPLEMENTO = 2500     # 250 * 10 min (41h40)
AS_IS_MINUTOS_CADASTRO = 4500        # 900 * 5 min (75h)
AS_IS_MINUTOS_RESPOSTA = 1800        # 900 * 2 min (30h)
AS_IS_TOTAL_MINUTOS = 18800          # 313h20min = 313.33h
AS_IS_TOTAL_HORAS = 313.3333333333333

AS_IS_SLA_DIAS = 5
AS_IS_SLA_NO_PRAZO = 0.62
AS_IS_SLA_FORA_PRAZO = 0.38
AS_IS_RECLAMACOES_MENSAL = 60
AS_IS_ERRO_DIGITACAO_PCT = 0.08      # 8% em CPF/percentual na operação manual

# Parâmetros de Simulação e TO-BE
DEFAULT_SEED = 20261108
DEFAULT_SLA_DIAS = 5
MAX_RETRY_COMUNICACOES = 3

# Paleta corporativa refinada (Conforme Diretrizes de Design do Protótipo)
THEME_COLORS = {
    "primary": "#0C2340",      # Azul-marinho executivo
    "secondary": "#2F73D8",    # Azul de destaque
    "accent": "#F28C28",       # Laranja de ação
    "background": "#F6F8FB",   # Off-white corporativo
    "muted": "#64748B",        # Cinza técnico
    "text": "#0F172A",         # Texto escuro de alto contraste
    "surface": "#FFFFFF",      # Superfície de cartões
    "success": "#15803D",      # Verde escuro legível
    "warning": "#B45309",      # Âmbar escuro legível
    "danger": "#B91C1C"        # Vermelho escuro legível
}

# Nomes amigáveis para estados operacionais (Linguagem Humana no Frontend)
STATUS_ROTULOS = {
    "RECEBIDA": "Recebida",
    "EM_VALIDACAO": "Em validação automática",
    "AGUARDANDO_CLIENTE": "Aguardando cliente",
    "PRONTA_PARA_CADASTRO": "Pronta para cadastro",
    "EM_CADASTRO": "Em cadastro",
    "CONCLUIDA": "Concluída",
    "EXCECAO": "Em análise do analista (Exceção)",
    "REJEITADA": "Rejeitada"
}

ETAPA_ROTULOS = {
    "TRIAGEM": "Triagem",
    "CONFERENCIA": "Conferência",
    "COMPLEMENTO": "Complemento",
    "CADASTRO": "Cadastro",
    "RESPOSTA": "Resposta",
    "FINALIZADO": "Finalizado"
}
