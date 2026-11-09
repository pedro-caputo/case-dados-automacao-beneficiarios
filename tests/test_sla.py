"""
Testes automatizados para contagem, pausas e lead time de SLA (AC-14).
"""
import pytest
from datetime import datetime, timedelta
from src.sla import calcular_metricas_sla
from src.models import EstadoSLA


def test_ac14_sla_pausa_e_desconto_correto():
    """AC-14: Contador de SLA desconta somente intervalos elegíveis com evento de pausa."""
    dt_inicio = datetime(2026, 11, 1, 9, 0, 0)
    # 5 dias de prazo total = 120 horas
    solic = {
        "sla_inicio": dt_inicio.isoformat(),
        "sla_dias": 5,
        "sla_pausa_acumulada_segundos": 0.0,
        "sla_estado": EstadoSLA.CORRENDO.value,
        "sla_pausado_em": None,
        "data_conclusao": None
    }

    # Passaram-se 2 dias (48 horas) de relógio correndo
    dt_agora_1 = dt_inicio + timedelta(days=2)
    m1 = calcular_metricas_sla(solic, agora_iso=dt_agora_1.isoformat())
    assert m1["horas_restantes"] == 72.0  # 120 - 48 = 72 horas restantes
    assert m1["expirado"] is False

    # Cliente entra em pendência no dia 2 e fica pausado por 4 dias
    dt_pausa = dt_agora_1
    solic["sla_estado"] = EstadoSLA.PAUSADO.value
    solic["sla_pausado_em"] = dt_pausa.isoformat()

    # Checagem durante a pausa no dia 4 (2 dias após a pausa)
    dt_durante_pausa = dt_pausa + timedelta(days=2)
    m_pausa = calcular_metricas_sla(solic, agora_iso=dt_durante_pausa.isoformat())
    # O tempo restante continua sendo 72 horas porque o relógio está pausado!
    assert m_pausa["horas_restantes"] == 72.0
    assert m_pausa["pausa_acumulada_horas"] == 48.0
    assert m_pausa["lead_time_bruto_horas"] == 96.0  # 4 dias corridos de calendário

    # Cliente responde no dia 6 (4 dias de pausa acumulada) e retoma o relógio
    dt_retomada = dt_pausa + timedelta(days=4)
    solic["sla_pausa_acumulada_segundos"] = 4 * 24 * 3600  # 4 dias acumulados
    solic["sla_estado"] = EstadoSLA.CORRENDO.value
    solic["sla_pausado_em"] = None

    # Checagem no dia 7 (1 dia após retorno)
    dt_agora_2 = dt_retomada + timedelta(days=1)
    m2 = calcular_metricas_sla(solic, agora_iso=dt_agora_2.isoformat())
    # Tempo líquido consumido: 2 dias antes da pausa + 1 dia agora = 3 dias (72 horas)
    # Restante: 5 dias - 3 dias = 2 dias (48 horas)
    assert m2["horas_restantes"] == 48.0
    assert m2["expirado"] is False
    assert m2["lead_time_bruto_horas"] == 168.0  # 7 dias corridos de calendário
    assert m2["pausa_acumulada_horas"] == 96.0   # 4 dias de pausa descontados

