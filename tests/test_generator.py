"""
Testes unitários para o gerador de dados sintéticos (Marco M1 / Critérios AC-11 e AC-12).
"""
import json
from src.synthetic_data import generate_synthetic_intents, gerar_cpf_valido
from src.config import DEFAULT_SEED
import random


def validar_cpf_digitos(cpf: str) -> bool:
    """Função auxiliar de teste para validar matematicamente os dois dígitos verificadores do CPF."""
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(nums) != 11 or len(set(nums)) == 1:
        return False
    # Primeiro dígito
    soma1 = sum(nums[i] * (10 - i) for i in range(9))
    r1 = (soma1 * 10) % 11
    d1 = 0 if r1 == 10 else r1
    if nums[9] != d1:
        return False
    # Segundo dígito
    soma2 = sum(nums[i] * (11 - i) for i in range(10))
    r2 = (soma2 * 10) % 11
    d2 = 0 if r2 == 10 else r2
    return nums[10] == d2


def test_gerador_distribuicao_exata():
    """AC-11: Exatamente 550 E-mail, 300 Agência, 150 App e 250 inadequações documentais."""
    intents = generate_synthetic_intents(seed=DEFAULT_SEED, total=1000)
    assert len(intents) == 1000

    canais = {}
    inadequados = 0
    clientes_lentos = 0
    subclasses = {}

    for item in intents:
        canais[item.canal] = canais.get(item.canal, 0) + 1
        flags = json.loads(item.flags_json)
        if flags.get("inadequado_inicial"):
            inadequados += 1
            sub = flags.get("subclasse_inadequacao")
            subclasses[sub] = subclasses.get(sub, 0) + 1
            if flags.get("dias_resposta_cliente", 0) > 5:
                clientes_lentos += 1

    # Verificação factual dos canais
    assert canais.get("EMAIL") == 550
    assert canais.get("AGENCIA") == 300
    assert canais.get("APP") == 150

    # Verificação factual das inadequações
    assert inadequados == 250
    assert len(intents) - inadequados == 750

    # Verificação dos clientes lentos (>5 dias de resposta)
    assert clientes_lentos == 100

    # Subclasses hipotéticas somam 250
    assert sum(subclasses.values()) == 250


def test_reprodutibilidade_seed():
    """AC-12: Mesma seed produz resultados determinísticos e idênticos."""
    intents1 = generate_synthetic_intents(seed=20261108, total=100)
    intents2 = generate_synthetic_intents(seed=20261108, total=100)

    for i1, i2 in zip(intents1, intents2):
        assert i1.id == i2.id
        assert i1.canal == i2.canal
        assert i1.cliente_dados_json == i2.cliente_dados_json
        assert i1.beneficiarios_json == i2.beneficiarios_json
        assert i1.flags_json == i2.flags_json


def test_cpfs_sinteticos_sao_validos():
    """Garante que CPFs gerados para clientes e beneficiários respeitam o algoritmo matemático."""
    rng = random.Random(42)
    for _ in range(50):
        cpf = gerar_cpf_valido(rng)
        assert validar_cpf_digitos(cpf) is True

