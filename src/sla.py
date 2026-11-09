"""
Motor de cálculo e controle de SLA com suporte a pausas de complemento e lead time.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from src.models import EstadoSLA


def calcular_metricas_sla(
    solic: Dict[str, Any],
    agora_iso: Optional[str] = None,
    usar_dias_uteis: bool = False
) -> Dict[str, Any]:
    """
    Calcula tempo líquido consumido, tempo restante, estado de violação de SLA e lead time bruto.
    - O relógio de SLA é pausado enquanto aguarda complemento do cliente.
    - Pausas só são descontadas quando devidamente registradas.
    - Não altera prazos retroativamente sem evento registrado.
    """
    dt_agora = datetime.fromisoformat(agora_iso) if agora_iso else datetime.now()

    sla_inicio_str = solic.get("sla_inicio") or solic.get("data_criacao")
    if not sla_inicio_str:
        return {
            "segundos_decorridos_liquidos": 0.0,
            "segundos_restantes": 0.0,
            "horas_restantes": 0.0,
            "dias_restantes": 0.0,
            "expirado": False,
            "percentual_consumido": 0.0,
            "lead_time_bruto_horas": 0.0,
            "estado": EstadoSLA.CORRENDO.value
        }

    dt_inicio = datetime.fromisoformat(sla_inicio_str)

    # Data de fim: se já concluída usa data_conclusao, senão agora
    dt_fim = dt_agora
    if solic.get("data_conclusao"):
        dt_fim = datetime.fromisoformat(solic["data_conclusao"])

    # Lead time bruto
    lead_time_bruto_segundos = max(0.0, (dt_fim - dt_inicio).total_seconds())

    # Pausa acumulada já finalizada
    pausa_acumulada = float(solic.get("sla_pausa_acumulada_segundos", 0.0))

    # Se está atualmente pausado, soma o intervalo da pausa corrente
    sla_estado = solic.get("sla_estado", EstadoSLA.CORRENDO.value)
    pausado_em_str = solic.get("sla_pausado_em")
    if sla_estado == EstadoSLA.PAUSADO.value and pausado_em_str:
        dt_pausa_ini = datetime.fromisoformat(pausado_em_str)
        if dt_fim > dt_pausa_ini:
            pausa_acumulada += (dt_fim - dt_pausa_ini).total_seconds()

    # Tempo líquido consumido do SLA
    segundos_liquidos = max(0.0, lead_time_bruto_segundos - pausa_acumulada)

    # Prazo total do SLA em segundos
    sla_dias = int(solic.get("sla_dias", 5))
    segundos_limite = float(sla_dias * 24 * 3600)

    segundos_restantes = segundos_limite - segundos_liquidos
    expirado = segundos_restantes < 0
    percentual_consumido = min(100.0, max(0.0, (segundos_liquidos / segundos_limite) * 100)) if segundos_limite > 0 else 100.0

    status_str = (solic.get("status") or "").upper()
    concluido = bool(status_str in ["CONCLUIDA", "REJEITADA"] or solic.get("data_conclusao"))
    lead_time_liquido_horas = round(segundos_liquidos / 3600, 2)

    return {
        "segundos_decorridos_liquidos": segundos_liquidos,
        "segundos_restantes": 0.0 if concluido else segundos_restantes,
        "horas_restantes": 0.0 if concluido else round(segundos_restantes / 3600, 2),
        "dias_restantes": 0.0 if concluido else round(segundos_restantes / (24 * 3600), 2),
        "expirado": expirado,
        "concluido": concluido,
        "concluido_no_prazo": (not expirado) if concluido else None,
        "percentual_consumido": round(percentual_consumido, 1),
        "lead_time_bruto_horas": round(lead_time_bruto_segundos / 3600, 2),
        "lead_time_liquido_horas": lead_time_liquido_horas,
        "pausa_acumulada_horas": round(pausa_acumulada / 3600, 2),
        "estado": "ENCERRADO" if concluido else sla_estado
    }

