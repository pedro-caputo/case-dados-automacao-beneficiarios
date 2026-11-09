"""
Gerador determinístico de intenções sintéticas reproduzíveis para o case.
Respeita estritamente a distribuição factual de 1.000 casos do AS-IS.
"""
import random
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple
from faker import Faker
from src.config import (
    DEFAULT_SEED, AS_IS_DISTRIBUICAO_CANAIS,
    AS_IS_INADEQUACOES_DOCS, AS_IS_DOCS_ADEQUADOS,
    AS_IS_COMPLEMENTOS_MAIS_5_DIAS, DATA_DIR
)
from src.models import RawIntent, TipoPendencia, TipoDocumento, Canal


def gerar_cpf_valido(rng: random.Random) -> str:
    """Gera um CPF sintético matematicamente válido com dígitos verificadores corretos."""
    while True:
        nove_digitos = [rng.randint(0, 9) for _ in range(9)]
        # Evita sequências de todos os dígitos iguais
        if len(set(nove_digitos)) == 1:
            continue
        break

    # Primeiro dígito verificador
    soma1 = sum(d * (10 - i) for i, d in enumerate(nove_digitos))
    resto1 = (soma1 * 10) % 11
    d10 = 0 if resto1 == 10 else resto1

    # Segundo dígito verificador
    dez_digitos = nove_digitos + [d10]
    soma2 = sum(d * (11 - i) for i, d in enumerate(dez_digitos))
    resto2 = (soma2 * 10) % 11
    d11 = 0 if resto2 == 10 else resto2

    onze_digitos = dez_digitos + [d11]
    cpf_str = "".join(str(d) for d in onze_digitos)
    return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"


def gerar_cpf_invalido(rng: random.Random) -> str:
    """Gera um CPF com dígito verificador comprovadamente incorreto."""
    cpf_val = gerar_cpf_valido(rng)
    # Altera o último dígito
    ult = int(cpf_val[-1])
    novo_ult = (ult + rng.randint(1, 9)) % 10
    return cpf_val[:-1] + str(novo_ult)


def gerar_perfil_ficticio_completo(seed: Any = None) -> Dict[str, Any]:
    """
    Gera um perfil sintético completo, rico e realista para demonstrações:
    - Titular com nome brasileiro autêntico, CPF válido formatado, e-mail coerente e telefone celular formatado.
    - 1 a 3 beneficiários com parentesco e sobrenomes coerentes.
    - Percentuais válidos somando exatamente 100,00%.
    """
    if seed is not None:
        rng = random.Random(seed)
        Faker.seed(seed)
    else:
        rng = random.Random()
    fake = Faker("pt_BR")

    nome_titular = fake.name()
    partes_nome = nome_titular.split()
    sobrenome_familia = partes_nome[-1] if len(partes_nome) > 1 else "Silva"
    primeiro_nome = partes_nome[0]

    provedores = ["gmail.com", "outlook.com", "yahoo.com.br", "exemplo.com.br", "empresa.com.br"]
    nome_email = f"{primeiro_nome.lower()}.{sobrenome_familia.lower()}"
    nome_email = "".join(c for c in nome_email if c.isalnum() or c == ".")
    email_titular = f"{nome_email}@{rng.choice(provedores)}"

    ddd = rng.choice([11, 19, 21, 31, 41, 51, 61, 71, 81, 85])
    num_cel = rng.randint(910000000, 999999999)
    cel_str = str(num_cel)
    telefone_titular = f"({ddd}) {cel_str[:5]}-{cel_str[5:]}"
    cpf_titular = gerar_cpf_valido(rng)

    padroes_beneficiarios = [
        [
            {"relacao": "Cônjuge", "pct": 100.0}
        ],
        [
            {"relacao": "Cônjuge", "pct": 50.0},
            {"relacao": "Filho(a)", "pct": 50.0}
        ],
        [
            {"relacao": "Filho(a)", "pct": 70.0},
            {"relacao": "Filho(a)", "pct": 30.0}
        ],
        [
            {"relacao": "Cônjuge", "pct": 50.0},
            {"relacao": "Filho(a)", "pct": 25.0},
            {"relacao": "Filho(a)", "pct": 25.0}
        ]
    ]

    escolha_padrao = rng.choice(padroes_beneficiarios)
    beneficiarios = []
    for b_item in escolha_padrao:
        nome_ben = f"{fake.first_name()} {sobrenome_familia}"
        cpf_ben = gerar_cpf_valido(rng)
        beneficiarios.append({
            "nome": nome_ben,
            "cpf": cpf_ben,
            "parentesco": b_item["relacao"],
            "percentual": float(b_item["pct"])
        })

    return {
        "titular": {
            "nome": nome_titular,
            "cpf": cpf_titular,
            "email": email_titular,
            "telefone": telefone_titular
        },
        "beneficiarios": beneficiarios
    }


def generate_synthetic_intents(seed: int = DEFAULT_SEED, total: int = 1000) -> List[RawIntent]:
    """
    Gera exatamente 1.000 intenções de solicitação determinísticas baseadas nos fatos do case:
    - 550 E-mail, 300 Agência, 150 App
    - 250 com inadequação documental inicial
    - 750 sem inadequação documental
    - 100 clientes que demoram > 5 dias para responder complemento (entre as 250 inadequações)
    """
    rng = random.Random(seed)
    fake = Faker('pt_BR')
    Faker.seed(seed)

    # 1. Definir canais com exatidão
    canais_lista = (
        [Canal.EMAIL.value] * AS_IS_DISTRIBUICAO_CANAIS["EMAIL"] +
        [Canal.AGENCIA.value] * AS_IS_DISTRIBUICAO_CANAIS["AGENCIA"] +
        [Canal.APP.value] * AS_IS_DISTRIBUICAO_CANAIS["APP"]
    )
    rng.shuffle(canais_lista)

    # 2. Definir inadequações documentais (250 inadequadas vs 750 adequadas)
    # Subclasses hipotéticas distribuídas:
    # 75 DOCUMENTO_AUSENTE, 45 FORMATO_INVALIDO, 60 DOCUMENTO_ILEGIVEL, 70 DADOS_DIVERGENTES = 250
    subclasses_inadequadas = (
        [TipoPendencia.DOCUMENTO_AUSENTE.value] * 75 +
        [TipoPendencia.FORMATO_INVALIDO.value] * 45 +
        [TipoPendencia.DOCUMENTO_ILEGIVEL.value] * 60 +
        [TipoPendencia.DADOS_DIVERGENTES.value] * 70
    )
    rng.shuffle(subclasses_inadequadas)

    # 100 das 250 com resposta lenta (>5 dias), 150 normais (<= 5 dias)
    tempos_resposta = [rng.randint(6, 15) for _ in range(AS_IS_COMPLEMENTOS_MAIS_5_DIAS)] + \
                     [rng.randint(1, 4) for _ in range(AS_IS_INADEQUACOES_DOCS - AS_IS_COMPLEMENTOS_MAIS_5_DIAS)]
    rng.shuffle(tempos_resposta)

    inadequacoes_detalhadas = []
    for tipo, dias in zip(subclasses_inadequadas, tempos_resposta):
        inadequacoes_detalhadas.append({
            "inadequado": True,
            "subclasse": tipo,
            "dias_resposta_cliente": dias
        })

    # 750 adequadas
    adequacoes_detalhadas = [{
        "inadequado": False,
        "subclasse": None,
        "dias_resposta_cliente": 0
    } for _ in range(AS_IS_DOCS_ADEQUADOS)]

    lista_inadequacoes = inadequacoes_detalhadas + adequacoes_detalhadas
    rng.shuffle(lista_inadequacoes)

    # Parentescos para beneficiários
    parentescos = ["Cônjuge", "Filho(a)", "Pai/Mãe", "Irmão(ã)", "Outro"]

    intents: List[RawIntent] = []

    for i in range(total):
        intent_id = f"INT-{seed}-{i+1:04d}"
        canal = canais_lista[i]
        inad = lista_inadequacoes[i]

        # Dados do cliente
        nome_cliente = fake.name()
        cpf_cliente = gerar_cpf_valido(rng)
        email_cliente = f"cliente.{i+1:04d}@exemplo.com.br"
        tel_cliente = f"(11) 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"

        cliente_dados = {
            "nome": nome_cliente,
            "cpf": cpf_cliente,
            "email": email_cliente,
            "telefone": tel_cliente
        }

        # Beneficiários (1 a 3)
        num_beneficiarios = rng.choice([1, 2, 2, 3])
        beneficiarios = []
        if num_beneficiarios == 1:
            beneficiarios.append({
                "nome": fake.name(),
                "cpf": gerar_cpf_valido(rng),
                "parentesco": rng.choice(parentescos),
                "percentual": 100.0
            })
        elif num_beneficiarios == 2:
            p1 = rng.choice([50.0, 60.0, 70.0, 80.0])
            p2 = round(100.0 - p1, 2)
            beneficiarios.append({
                "nome": fake.name(),
                "cpf": gerar_cpf_valido(rng),
                "parentesco": rng.choice(parentescos),
                "percentual": p1
            })
            beneficiarios.append({
                "nome": fake.name(),
                "cpf": gerar_cpf_valido(rng),
                "parentesco": rng.choice(parentescos),
                "percentual": p2
            })
        else:
            beneficiarios.append({
                "nome": fake.name(),
                "cpf": gerar_cpf_valido(rng),
                "parentesco": rng.choice(parentescos),
                "percentual": 50.0
            })
            beneficiarios.append({
                "nome": fake.name(),
                "cpf": gerar_cpf_valido(rng),
                "parentesco": rng.choice(parentescos),
                "percentual": 30.0
            })
            beneficiarios.append({
                "nome": fake.name(),
                "cpf": gerar_cpf_valido(rng),
                "parentesco": rng.choice(parentescos),
                "percentual": 20.0
            })

        # Documentos base
        docs = [
            {
                "tipo": TipoDocumento.DOCUMENTO_IDENTIFICACAO.value,
                "nome_arquivo": f"doc_identificacao_{i+1:04d}.pdf",
                "presente": True,
                "formato": "pdf",
                "valido_sintatico": True,
                "legibilidade_simulada": True
            },
            {
                "tipo": TipoDocumento.FORMULARIO_ALTERACAO.value,
                "nome_arquivo": f"formulario_alteracao_{i+1:04d}.pdf",
                "presente": True,
                "formato": "pdf",
                "valido_sintatico": True,
                "legibilidade_simulada": True
            }
        ]

        # Se inadequado, injeta o problema específico conforme a subclasse hipotética
        if inad["inadequado"]:
            sub = inad["subclasse"]
            if sub == TipoPendencia.DOCUMENTO_AUSENTE.value:
                # Ausência de formulário assinado
                docs[1]["presente"] = False
                docs[1]["nome_arquivo"] = ""
            elif sub == TipoPendencia.FORMATO_INVALIDO.value:
                # Formato inadequado (ex: .exe, .zip ou corrompido)
                docs[0]["formato"] = "exe"
                docs[0]["nome_arquivo"] = f"documento_{i+1:04d}.exe"
                docs[0]["valido_sintatico"] = False
            elif sub == TipoPendencia.DOCUMENTO_ILEGIVEL.value:
                # Baixa legibilidade simulada
                docs[0]["legibilidade_simulada"] = False
            elif sub == TipoPendencia.DADOS_DIVERGENTES.value:
                # Divergência cadastral (ex: CPF do formulário difere do segurado)
                docs[1]["valido_sintatico"] = False

        flags = {
            "inadequado_inicial": inad["inadequado"],
            "subclasse_inadequacao": inad["subclasse"],
            "dias_resposta_cliente": inad["dias_resposta_cliente"],
            "as_is_erro_digitacao_potencial": rng.random() < 0.08  # 8% probabilidade de erro no AS-IS manual
        }

        intent = RawIntent(
            id=intent_id,
            canal=canal,
            cliente_dados_json=json.dumps(cliente_dados, ensure_ascii=False),
            beneficiarios_json=json.dumps(beneficiarios, ensure_ascii=False),
            docs_json=json.dumps(docs, ensure_ascii=False),
            flags_json=json.dumps(flags, ensure_ascii=False),
            seed=seed
        )
        intents.append(intent)

    return intents


def export_intents_to_csv(intents: List[RawIntent], csv_path: Path) -> None:
    """Exporta intenções sintéticas para arquivo CSV."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "canal", "cliente_nome", "cliente_cpf",
            "qtd_beneficiarios", "inadequado_inicial",
            "subclasse_inadequacao", "dias_resposta_cliente", "seed"
        ])
        for item in intents:
            cliente = json.loads(item.cliente_dados_json)
            beneficiarios = json.loads(item.beneficiarios_json)
            flags = json.loads(item.flags_json)
            writer.writerow([
                item.id,
                item.canal,
                cliente.get("nome"),
                cliente.get("cpf"),
                len(beneficiarios),
                flags.get("inadequado_inicial"),
                flags.get("subclasse_inadequacao"),
                flags.get("dias_resposta_cliente"),
                item.seed
            ])

