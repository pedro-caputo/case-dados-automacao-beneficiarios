"""
Testes automatizados para regras de negócio e validações (AC-01, AC-02, AC-03).
"""
import pytest
from src.validators import (
    validar_cpf, validar_beneficiarios, validar_documentos,
    validar_solicitacao_completa, limpar_cpf, format_cpf,
    format_phone, validar_email
)
from src.synthetic_data import gerar_cpf_valido, gerar_perfil_ficticio_completo
import random


def test_ac01_cpf_invalido_bloqueado():
    """AC-01: CPF sintaticamente inválido é bloqueado com mensagem clara e explicativa."""
    # 1. Dígito repetido
    val, motivo = validar_cpf("111.111.111-11")
    assert val is False
    assert "repetidos" in motivo

    # 2. Tamanho incorreto
    val, motivo = validar_cpf("123.456")
    assert val is False
    assert "11 dígitos" in motivo

    # 3. Dígito verificador errado
    val, motivo = validar_cpf("123.456.789-00")
    assert val is False
    assert "dígito verificador" in motivo.lower()

    # 4. CPF válido gerado matematicamente
    rng = random.Random(123)
    cpf_valido = gerar_cpf_valido(rng)
    val, motivo = validar_cpf(cpf_valido)
    assert val is True
    assert motivo is None


def test_ac02_beneficiarios_soma_percentuais_e_duplicidade():
    """AC-02: Bloqueia soma diferente de 100% e duplicidade de CPF."""
    rng = random.Random(456)
    cpf1 = gerar_cpf_valido(rng)
    cpf2 = gerar_cpf_valido(rng)

    # Caso 1: Soma = 120%
    bens_120 = [
        {"nome": "Filho 1", "cpf": cpf1, "percentual": 70.0},
        {"nome": "Filho 2", "cpf": cpf2, "percentual": 50.0}
    ]
    res = validar_beneficiarios(bens_120, exigir_total_100=True)
    assert res.valido is False
    assert any("exatamente 100.00%" in e for e in res.erros)
    assert any("120.00%" in e for e in res.erros)

    # Caso 2: Soma = 80%
    bens_80 = [
        {"nome": "Filho 1", "cpf": cpf1, "percentual": 80.0}
    ]
    res80 = validar_beneficiarios(bens_80, exigir_total_100=True)
    assert res80.valido is False
    assert any("80.00%" in e for e in res80.erros)

    # Caso 3: CPF duplicado
    bens_dup = [
        {"nome": "Filho 1", "cpf": cpf1, "percentual": 50.0},
        {"nome": "Filho 2", "cpf": cpf1, "percentual": 50.0}
    ]
    res_dup = validar_beneficiarios(bens_dup, exigir_total_100=True)
    assert res_dup.valido is False
    assert any("CPF duplicado" in e for e in res_dup.erros)

    # Caso 4: Válido 100%
    bens_ok = [
        {"nome": "Filho 1", "cpf": cpf1, "percentual": 60.0},
        {"nome": "Filho 2", "cpf": cpf2, "percentual": 40.0}
    ]
    res_ok = validar_beneficiarios(bens_ok, exigir_total_100=True)
    assert res_ok.valido is True
    assert len(res_ok.erros) == 0


def test_ac03_anexos_obrigatorios_e_formato():
    """AC-03: Anexo obrigatório ausente ou formato inválido é bloqueado."""
    # Ausência de formulário
    docs_sem_form = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "rg.pdf", "presente": True, "formato": "pdf"}
    ]
    res = validar_documentos(docs_sem_form)
    assert res.valido is False
    assert any("Formulário de alteração" in e for e in res.erros)

    # Formato inválido (.exe)
    docs_exe = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "rg.pdf", "presente": True, "formato": "pdf"},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "virus.exe", "presente": True, "formato": "exe"}
    ]
    res_exe = validar_documentos(docs_exe)
    assert res_exe.valido is False
    assert any("formato 'exe' não suportado" in e for e in res_exe.erros)

    # Todos válidos
    docs_ok = [
        {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "rg.pdf", "presente": True, "formato": "pdf"},
        {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "formulario.pdf", "presente": True, "formato": "pdf"}
    ]
    res_ok = validar_documentos(docs_ok)
    assert res_ok.valido is True


def test_teste_c_formatacao_manual_cpf_e_telefone():
    """Teste C — Formatação manual de CPF e telefone aceita números brutos ou com máscara sem perda."""
    # 1. CPF bruto sem máscara
    cpf_formatado = format_cpf("12345678901")
    assert cpf_formatado == "123.456.789-01"

    # 2. CPF já com máscara
    assert format_cpf("123.456.789-01") == "123.456.789-01"

    # 3. Digitação progressiva de CPF
    assert format_cpf("123") == "123"
    assert format_cpf("123456") == "123.456"

    # 4. Telefone celular (11 dígitos)
    cel = format_phone("11987654321")
    assert cel == "(11) 98765-4321"

    # 5. Telefone fixo (10 dígitos)
    fixo = format_phone("1134567890")
    assert fixo == "(11) 3456-7890"


def test_teste_d_validacao_email():
    """Teste D — Validação de e-mail rejeita formatos estruturalmente inválidos."""
    # Válidos
    val, mot = validar_email("cliente@exemplo.com.br")
    assert val is True
    assert mot is None

    val2, _ = validar_email("mariana.alencar@seguradora.com")
    assert val2 is True

    # Inválidos
    val_sem_arroba, mot1 = validar_email("cliente.exemplo.com")
    assert val_sem_arroba is False
    assert "inválido" in mot1.lower()

    val_sem_dominio, mot2 = validar_email("cliente@")
    assert val_sem_dominio is False

    val_vazio, mot3 = validar_email("")
    assert val_vazio is False
    assert "obrigatório" in mot3.lower()


def test_gerador_perfil_ficticio_consistencia():
    """Valida gerador de perfis fictícios ricos: dados consistentes e 100% de soma."""
    perfil = gerar_perfil_ficticio_completo(seed=999)
    titular = perfil["titular"]
    bens = perfil["beneficiarios"]

    # Titular válido
    val_cpf, _ = validar_cpf(titular["cpf"])
    assert val_cpf is True
    val_em, _ = validar_email(titular["email"])
    assert val_em is True
    assert len(titular["telefone"]) >= 14

    # Beneficiários somando 100%
    assert len(bens) >= 1
    soma_pct = sum(b["percentual"] for b in bens)
    assert abs(soma_pct - 100.0) < 0.01

    # Todos CPFs válidos
    for b in bens:
        b_val, _ = validar_cpf(b["cpf"])
        assert b_val is True


