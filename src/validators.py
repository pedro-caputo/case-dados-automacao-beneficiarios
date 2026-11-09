"""
Motor de regras de negócio e validações preventivas e sistêmicas.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    valido: bool
    erros: List[str]
    alertas: List[str]

    @property
    def sucesso(self) -> bool:
        return self.valido and len(self.erros) == 0


def limpar_cpf(cpf: str) -> str:
    """Remove pontuação e espaços do CPF."""
    return re.sub(r"\D", "", cpf or "")


def format_cpf(cpf: str) -> str:
    """
    Aplica máscara profissional de CPF (000.000.000-00) progressivamente.
    Aceita colagem de texto com ou sem pontuação.
    """
    nums = limpar_cpf(cpf)[:11]
    if len(nums) <= 3:
        return nums
    elif len(nums) <= 6:
        return f"{nums[:3]}.{nums[3:]}"
    elif len(nums) <= 9:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:]}"
    else:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"


def format_phone(phone: str) -> str:
    """
    Aplica máscara profissional de telefone celular ou fixo progressivamente:
    - Celular (11 dígitos): (00) 00000-0000
    - Fixo (10 dígitos): (00) 0000-0000
    Aceita colagem de números com ou sem pontuação.
    """
    nums = re.sub(r"\D", "", phone or "")[:11]
    if not nums:
        return ""
    if len(nums) <= 2:
        return f"({nums}"
    elif len(nums) <= 6:
        return f"({nums[:2]}) {nums[2:]}"
    elif len(nums) <= 10:
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    else:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"


def validar_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Valida a estrutura do endereço de e-mail, rejeitando formatos evidentemente inválidos.
    """
    email_limpo = (email or "").strip()
    if not email_limpo:
        return False, "E-mail de contato é obrigatório."
    
    padrao = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(padrao, email_limpo):
        return False, f"Formato de e-mail inválido ('{email_limpo}'). Exemplo válido: usuario@dominio.com.br"
    
    return True, None


def validar_cpf(cpf: str) -> Tuple[bool, Optional[str]]:
    """
    Valida CPF segundo o algoritmo oficial da Receita Federal (dígitos verificadores).
    Retorna (valido, motivo_erro).
    """
    numeros = limpar_cpf(cpf)

    if not numeros:
        return False, "CPF é obrigatório."

    if len(numeros) != 11:
        return False, f"CPF deve conter exatamente 11 dígitos numéricos (informado: {len(numeros)})."

    # Rejeita CPFs com todos os dígitos repetidos (ex.: 111.111.111-11)
    if len(set(numeros)) == 1:
        return False, "CPF com dígitos repetidos é inválido."

    # Cálculo do 1º dígito verificador
    soma1 = sum(int(numeros[i]) * (10 - i) for i in range(9))
    resto1 = (soma1 * 10) % 11
    d10 = 0 if resto1 == 10 else resto1

    if int(numeros[9]) != d10:
        return False, "Primeiro dígito verificador do CPF inválido."

    # Cálculo do 2º dígito verificador
    soma2 = sum(int(numeros[i]) * (11 - i) for i in range(10))
    resto2 = (soma2 * 10) % 11
    d11 = 0 if resto2 == 10 else resto2

    if int(numeros[10]) != d11:
        return False, "Segundo dígito verificador do CPF inválido."

    return True, None


def validar_beneficiarios(
    beneficiarios: List[Dict[str, Any]],
    exigir_total_100: bool = True,
    tolerancia_decimal: float = 0.01
) -> ValidationResult:
    """
    Valida a lista de beneficiários da solicitação:
    - Ao menos um beneficiário.
    - Nomes obrigatórios.
    - CPFs válidos.
    - Ausência de CPFs duplicados entre beneficiários.
    - Percentuais maiores que zero.
    - Soma exatamente igual a 100% (quando exigido pela política).
    """
    erros: List[str] = []
    alertas: List[str] = []

    if not beneficiarios:
        erros.append("Ao menos um beneficiário deve ser informado.")
        return ValidationResult(valido=False, erros=erros, alertas=alertas)

    soma_percentuais = 0.0
    cpfs_vistos = set()

    for idx, b in enumerate(beneficiarios, start=1):
        nome = (b.get("nome") or b.get("nome_ficticio") or "").strip()
        cpf = b.get("cpf") or b.get("cpf_ficticio") or ""
        percentual = b.get("percentual", 0.0)

        if not nome:
            erros.append(f"Beneficiário #{idx}: nome é obrigatório.")

        valido_cpf, motivo_cpf = validar_cpf(cpf)
        if not valido_cpf:
            erros.append(f"Beneficiário #{idx} ({nome or 'Sem nome'}): {motivo_cpf}")
        else:
            cpf_limpo = limpar_cpf(cpf)
            if cpf_limpo in cpfs_vistos:
                erros.append(f"Beneficiário #{idx}: CPF duplicado ({cpf}). Cada beneficiário deve ter CPF único.")
            cpfs_vistos.add(cpf_limpo)

        try:
            pct_float = float(percentual)
            if pct_float <= 0.0:
                erros.append(f"Beneficiário #{idx}: percentual deve ser maior que 0% (informado: {pct_float}%).")
            elif pct_float > 100.0:
                erros.append(f"Beneficiário #{idx}: percentual individual não pode exceder 100% (informado: {pct_float}%).")
            soma_percentuais += pct_float
        except (ValueError, TypeError):
            erros.append(f"Beneficiário #{idx}: percentual inválido '{percentual}'.")

    if exigir_total_100:
        diferenca = abs(soma_percentuais - 100.0)
        if diferenca > tolerancia_decimal:
            erros.append(
                f"A soma dos percentuais dos beneficiários deve ser exatamente 100.00%. "
                f"Soma atual: {soma_percentuais:.2f}% (diferença de {soma_percentuais - 100.0:+.2f}%)."
            )

    return ValidationResult(valido=(len(erros) == 0), erros=erros, alertas=alertas)


def validar_documentos(
    documentos: List[Dict[str, Any]],
    exigir_identificacao: bool = True,
    exigir_formulario: bool = True
) -> ValidationResult:
    """
    Valida presença e formato dos anexos:
    - Presença dos documentos obrigatórios.
    - Extensão permitida (pdf, jpg, jpeg, png).
    - Validação sintática e legibilidade simulada.
    """
    erros: List[str] = []
    alertas: List[str] = []
    formatos_permitidos = {"pdf", "jpg", "jpeg", "png"}

    tipos_presentes = set()

    for doc in documentos:
        tipo = doc.get("tipo")
        presente = doc.get("presente", True)
        formato = (doc.get("formato") or "").lower().replace(".", "")
        valido_sintatico = doc.get("valido_sintatico", True)
        legibilidade = doc.get("legibilidade_simulada", True)
        nome = doc.get("nome_arquivo", "")

        if presente and nome:
            tipos_presentes.add(tipo)
            if formato not in formatos_permitidos:
                erros.append(f"Documento '{nome}': formato '{formato}' não suportado. Permitidos: PDF, JPG, PNG.")
            if not valido_sintatico:
                erros.append(f"Documento '{nome}': arquivo inválido ou divergente sintaticamente.")
            if not legibilidade:
                alertas.append(f"Documento '{nome}': baixa legibilidade detectada na conferência.")

    if exigir_identificacao and "DOCUMENTO_IDENTIFICACAO" not in tipos_presentes:
        erros.append("Documento de identificação do segurado é obrigatório.")

    if exigir_formulario and "FORMULARIO_ALTERACAO" not in tipos_presentes:
        erros.append("Formulário de alteração de beneficiários é obrigatório.")

    return ValidationResult(valido=(len(erros) == 0), erros=erros, alertas=alertas)


def validar_solicitacao_completa(
    cliente: Dict[str, Any],
    beneficiarios: List[Dict[str, Any]],
    documentos: List[Dict[str, Any]],
    exigir_total_100: bool = True
) -> ValidationResult:
    """Validação holística unificada aplicada preventivamente na entrada e na camada de negócio."""
    erros: List[str] = []
    alertas: List[str] = []

    # 1. Cliente
    nome_cliente = (cliente.get("nome") or cliente.get("nome_ficticio") or "").strip()
    if not nome_cliente:
        erros.append("Nome do segurado é obrigatório.")

    cpf_cliente = cliente.get("cpf") or cliente.get("cpf_ficticio") or ""
    cpf_val, motivo_cpf = validar_cpf(cpf_cliente)
    if not cpf_val:
        erros.append(f"Segurado: {motivo_cpf}")

    # E-mail
    email_cliente = cliente.get("email") or cliente.get("email_ficticio")
    if email_cliente:
        email_val, motivo_email = validar_email(email_cliente)
        if not email_val:
            erros.append(f"Segurado: {motivo_email}")

    # 2. Beneficiários
    res_ben = validar_beneficiarios(beneficiarios, exigir_total_100=exigir_total_100)
    erros.extend(res_ben.erros)
    alertas.extend(res_ben.alertas)

    # 3. Documentos
    res_doc = validar_documentos(documentos)
    erros.extend(res_doc.erros)
    alertas.extend(res_doc.alertas)

    return ValidationResult(valido=(len(erros) == 0), erros=erros, alertas=alertas)

