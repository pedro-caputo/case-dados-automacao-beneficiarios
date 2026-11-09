"""
Camada de repositório para persistência, consultas e transações SQLite.
"""
import sqlite3
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from src.database import get_connection
from src.models import (
    Solicitacao, Cliente, Beneficiario, Documento,
    Pendencia, TarefaHumana, Evento, Comunicacao,
    SimulationRun, RawIntent, StatusSolicitacao,
    EtapaProcesso, Prioridade, EstadoSLA, TipoEvento,
    TipoDocumento, TipoPendencia, EstadoComunicacao
)


class SolicitacaoRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def save_raw_intents(self, intents: List[RawIntent]) -> int:
        """Salva lote de intenções brutas imutáveis."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM raw_intents WHERE seed = ?", (intents[0].seed if intents else 0,))
        
        data = [
            (i.id, i.canal, i.cliente_dados_json, i.beneficiarios_json, i.docs_json, i.flags_json, i.seed)
            for i in intents
        ]
        cursor.executemany("""
            INSERT INTO raw_intents (id, canal, cliente_dados_json, beneficiarios_json, docs_json, flags_json, seed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        count = cursor.rowcount
        conn.close()
        return len(intents)

    def get_raw_intents(self, seed: Optional[int] = None) -> List[RawIntent]:
        """Recupera intenções sintéticas brutas."""
        conn = self._get_conn()
        cursor = conn.cursor()
        if seed is not None:
            cursor.execute("SELECT * FROM raw_intents WHERE seed = ? ORDER BY id", (seed,))
        else:
            cursor.execute("SELECT * FROM raw_intents ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [
            RawIntent(
                id=r["id"],
                canal=r["canal"],
                cliente_dados_json=r["cliente_dados_json"],
                beneficiarios_json=r["beneficiarios_json"],
                docs_json=r["docs_json"],
                flags_json=r["flags_json"],
                seed=r["seed"]
            )
            for r in rows
        ]

    def count_raw_intents(self, seed: Optional[int] = None) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        if seed is not None:
            cursor.execute("SELECT COUNT(*) FROM raw_intents WHERE seed = ?", (seed,))
        else:
            cursor.execute("SELECT COUNT(*) FROM raw_intents")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def create_solicitacao(
        self,
        solicitacao: Solicitacao,
        cliente: Cliente,
        beneficiarios: List[Beneficiario],
        documentos: List[Documento],
        ator: str = "SISTEMA"
    ) -> int:
        """Cria transacionalmente a solicitação, cliente, beneficiários, documentos e evento inicial."""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            now_iso = datetime.now().isoformat()
            data_criacao = solicitacao.data_criacao or now_iso
            sla_inicio = solicitacao.sla_inicio or now_iso

            universo = getattr(solicitacao, 'universo', None)
            if not universo:
                universo = 'EXPERIMENTAL' if solicitacao.run_id else 'INTERATIVO'

            cursor.execute("""
                INSERT INTO solicitacoes (
                    protocolo, external_intent_id, run_id, universo, canal, data_criacao,
                    status, etapa, prioridade, responsavel, sla_dias,
                    sla_inicio, sla_pausado_em, sla_pausa_acumulada_segundos,
                    sla_estado, data_conclusao, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                solicitacao.protocolo,
                solicitacao.external_intent_id,
                solicitacao.run_id,
                universo,
                solicitacao.canal.value if hasattr(solicitacao.canal, 'value') else str(solicitacao.canal),
                data_criacao,
                solicitacao.status.value if hasattr(solicitacao.status, 'value') else str(solicitacao.status),
                solicitacao.etapa.value if hasattr(solicitacao.etapa, 'value') else str(solicitacao.etapa),
                solicitacao.prioridade.value if hasattr(solicitacao.prioridade, 'value') else str(solicitacao.prioridade),
                solicitacao.responsavel,
                solicitacao.sla_dias,
                sla_inicio,
                solicitacao.sla_pausado_em,
                solicitacao.sla_pausa_acumulada_segundos,
                solicitacao.sla_estado.value if hasattr(solicitacao.sla_estado, 'value') else str(solicitacao.sla_estado),
                solicitacao.data_conclusao,
                now_iso,
                now_iso
            ))
            solic_id = cursor.lastrowid
            solicitacao.id = solic_id

            # Cliente
            cursor.execute("""
                INSERT INTO clientes (solicitacao_id, nome_ficticio, cpf_ficticio, email_ficticio, telefone_ficticio)
                VALUES (?, ?, ?, ?, ?)
            """, (solic_id, cliente.nome_ficticio, cliente.cpf_ficticio, cliente.email_ficticio, cliente.telefone_ficticio))

            # Beneficiários
            for b in beneficiarios:
                cursor.execute("""
                    INSERT INTO beneficiarios (solicitacao_id, nome_ficticio, cpf_ficticio, parentesco, percentual)
                    VALUES (?, ?, ?, ?, ?)
                """, (solic_id, b.nome_ficticio, b.cpf_ficticio, b.parentesco, b.percentual))

            # Documentos
            for d in documentos:
                meta_json = json.dumps(d.metadados or {})
                tipo_str = d.tipo.value if hasattr(d.tipo, 'value') else str(d.tipo)
                cursor.execute("""
                    INSERT INTO documentos (solicitacao_id, tipo, nome_arquivo, presente, formato, valido_sintatico, legibilidade_simulada, metadados_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (solic_id, tipo_str, d.nome_arquivo, 1 if d.presente else 0, d.formato, 1 if d.valido_sintatico else 0, 1 if d.legibilidade_simulada else 0, meta_json))

            # Evento inicial
            cursor.execute("""
                INSERT INTO eventos (solicitacao_id, tipo_evento, timestamp, origem_ator, estado_anterior, estado_novo, detalhes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                solic_id,
                TipoEvento.CRIACAO.value,
                data_criacao,
                ator,
                None,
                solicitacao.status.value if hasattr(solicitacao.status, 'value') else str(solicitacao.status),
                json.dumps({"protocolo": solicitacao.protocolo, "canal": str(solicitacao.canal)})
            ))

            # Evento de SLA iniciado
            cursor.execute("""
                INSERT INTO eventos (solicitacao_id, tipo_evento, timestamp, origem_ator, estado_anterior, estado_novo, detalhes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                solic_id,
                TipoEvento.SLA_INICIADO.value,
                sla_inicio,
                "SISTEMA",
                None,
                EstadoSLA.CORRENDO.value,
                json.dumps({"sla_dias": solicitacao.sla_dias})
            ))

            conn.commit()
            return solic_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_solicitacao(self, solic_id: int) -> Optional[Dict[str, Any]]:
        """Recupera solicitação completa com clientes, beneficiários, documentos, pendências, tarefas, eventos e comunicações."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM solicitacoes WHERE id = ?", (solic_id,))
        solic_row = cursor.fetchone()
        if not solic_row:
            conn.close()
            return None

        solic = dict(solic_row)

        # Cliente
        cursor.execute("SELECT * FROM clientes WHERE solicitacao_id = ?", (solic_id,))
        solic["cliente"] = dict(cursor.fetchone() or {})

        # Beneficiários
        cursor.execute("SELECT * FROM beneficiarios WHERE solicitacao_id = ?", (solic_id,))
        solic["beneficiarios"] = [dict(r) for r in cursor.fetchall()]

        # Documentos
        cursor.execute("SELECT * FROM documentos WHERE solicitacao_id = ?", (solic_id,))
        solic["documentos"] = [dict(r) for r in cursor.fetchall()]

        # Pendências
        cursor.execute("SELECT * FROM pendencias WHERE solicitacao_id = ? ORDER BY aberta_em DESC", (solic_id,))
        solic["pendencias"] = [dict(r) for r in cursor.fetchall()]

        # Tarefas
        cursor.execute("SELECT * FROM tarefas WHERE solicitacao_id = ? ORDER BY id DESC", (solic_id,))
        solic["tarefas"] = [dict(r) for r in cursor.fetchall()]

        # Eventos
        cursor.execute("SELECT * FROM eventos WHERE solicitacao_id = ? ORDER BY timestamp ASC, id ASC", (solic_id,))
        solic["eventos"] = [dict(r) for r in cursor.fetchall()]

        # Comunicações
        cursor.execute("SELECT * FROM comunicacoes WHERE solicitacao_id = ? ORDER BY criado_em ASC", (solic_id,))
        solic["comunicacoes"] = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return solic

    def get_solicitacao_by_protocolo(self, protocolo: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM solicitacoes WHERE protocolo = ?", (protocolo,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self.get_solicitacao(row["id"])
        return None

    def list_solicitacoes(
        self,
        status: Optional[str] = None,
        etapa: Optional[str] = None,
        canal: Optional[str] = None,
        universo: Optional[str] = None,
        run_id: Optional[str] = None,
        search_protocol: Optional[str] = None,
        apenas_ativas: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista solicitações com filtros para a fila operacional e isolamento de universo."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT s.*, c.nome_ficticio as cliente_nome, c.cpf_ficticio as cliente_cpf,
                   (SELECT COUNT(*) FROM pendencias p WHERE p.solicitacao_id = s.id AND p.fechada_em IS NULL) as pendencias_abertas
            FROM solicitacoes s
            LEFT JOIN clientes c ON c.solicitacao_id = s.id
            WHERE 1=1
        """
        params = []

        if universo == "INTERATIVO":
            query += " AND (s.universo = 'INTERATIVO' OR s.run_id IS NULL OR s.run_id = '')"
        elif universo == "EXPERIMENTAL":
            if run_id:
                query += " AND s.run_id = ?"
                params.append(run_id)
            else:
                query += " AND (s.universo = 'EXPERIMENTAL' OR (s.run_id IS NOT NULL AND s.run_id != ''))"
        elif run_id:
            query += " AND s.run_id = ?"
            params.append(run_id)

        if status:
            query += " AND s.status = ?"
            params.append(status)
        elif apenas_ativas:
            query += " AND s.status NOT IN ('CONCLUIDA', 'REJEITADA')"

        if etapa:
            query += " AND s.etapa = ?"
            params.append(etapa)
        if canal:
            query += " AND s.canal = ?"
            params.append(canal)
        if search_protocol:
            query += " AND (s.protocolo LIKE ? OR c.nome_ficticio LIKE ?)"
            termo = f"%{search_protocol}%"
            params.extend([termo, termo])

        query += " ORDER BY CASE s.prioridade WHEN 'URGENTE' THEN 1 WHEN 'ALTA' THEN 2 WHEN 'MEDIA' THEN 3 ELSE 4 END, s.data_criacao ASC"
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_status(
        self,
        solic_id: int,
        novo_status: StatusSolicitacao,
        nova_etapa: EtapaProcesso,
        ator: str = "SISTEMA",
        responsavel: Optional[str] = None,
        justificativa: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Atualiza status e etapa da solicitação garantindo registro de evento de auditoria."""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT status, etapa, responsavel FROM solicitacoes WHERE id = ?", (solic_id,))
            current = cursor.fetchone()
            if not current:
                raise ValueError(f"Solicitação {solic_id} não encontrada.")

            estado_ant = current["status"]
            etapa_ant = current["etapa"]
            resp = responsavel if responsavel is not None else current["responsavel"]
            now_iso = datetime.now().isoformat()

            status_str = novo_status.value if hasattr(novo_status, 'value') else str(novo_status)
            etapa_str = nova_etapa.value if hasattr(nova_etapa, 'value') else str(nova_etapa)

            conclusao = now_iso if status_str in ["CONCLUIDA", "REJEITADA"] else None

            cursor.execute("""
                UPDATE solicitacoes
                SET status = ?, etapa = ?, responsavel = ?, data_conclusao = COALESCE(?, data_conclusao), updated_at = ?
                WHERE id = ?
            """, (status_str, etapa_str, resp, conclusao, now_iso, solic_id))

            # Evento correspondente
            payload = detalhes or {}
            if justificativa:
                payload["justificativa"] = justificativa
            payload["etapa_anterior"] = etapa_ant
            payload["etapa_nova"] = etapa_str

            cursor.execute("""
                INSERT INTO eventos (solicitacao_id, tipo_evento, timestamp, origem_ator, estado_anterior, estado_novo, detalhes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                solic_id,
                f"TRANSICAO_{status_str}",
                now_iso,
                ator,
                estado_ant,
                status_str,
                json.dumps(payload)
            ))

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_evento(self, evento: Evento) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO eventos (solicitacao_id, tipo_evento, timestamp, origem_ator, estado_anterior, estado_novo, detalhes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            evento.solicitacao_id,
            evento.tipo_evento.value if hasattr(evento.tipo_evento, 'value') else str(evento.tipo_evento),
            evento.timestamp,
            evento.origem_ator,
            evento.estado_anterior,
            evento.estado_novo,
            evento.detalhes_json
        ))
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        return event_id

    def add_pendencia(self, pendencia: Pendencia, ator: str = "SISTEMA") -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            tipo_str = pendencia.tipo.value if hasattr(pendencia.tipo, 'value') else str(pendencia.tipo)
            cursor.execute("""
                INSERT INTO pendencias (solicitacao_id, tipo, descricao, aberta_em, fechada_em, resolucao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pendencia.solicitacao_id, tipo_str, pendencia.descricao, pendencia.aberta_em, pendencia.fechada_em, pendencia.resolucao))
            pend_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO eventos (solicitacao_id, tipo_evento, timestamp, origem_ator, estado_anterior, estado_novo, detalhes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pendencia.solicitacao_id,
                TipoEvento.PENDENCIA_ABERTA.value,
                pendencia.aberta_em,
                ator,
                None,
                tipo_str,
                json.dumps({"pendencia_id": pend_id, "descricao": pendencia.descricao})
            ))
            conn.commit()
            return pend_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def close_pendencia(self, pendencia_id: int, resolucao: str, ator: str = "SISTEMA") -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT solicitacao_id, tipo FROM pendencias WHERE id = ?", (pendencia_id,))
            p = cursor.fetchone()
            if not p:
                return
            solic_id = p["solicitacao_id"]
            now_iso = datetime.now().isoformat()

            cursor.execute("""
                UPDATE pendencias
                SET fechada_em = ?, resolucao = ?
                WHERE id = ?
            """, (now_iso, resolucao, pendencia_id))

            cursor.execute("""
                INSERT INTO eventos (solicitacao_id, tipo_evento, timestamp, origem_ator, estado_anterior, estado_novo, detalhes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                solic_id,
                TipoEvento.PENDENCIA_FECHADA.value,
                now_iso,
                ator,
                p["tipo"],
                "RESOLVIDA",
                json.dumps({"pendencia_id": pendencia_id, "resolucao": resolucao})
            ))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def add_tarefa(self, tarefa: TarefaHumana) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tarefas (solicitacao_id, tipo, atribuida_a, estado, iniciada_em, encerrada_em, duracao_ativa_segundos, decisao, justificativa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tarefa.solicitacao_id, tarefa.tipo, tarefa.atribuida_a, tarefa.estado,
            tarefa.iniciada_em, tarefa.encerrada_em, tarefa.duracao_ativa_segundos,
            tarefa.decisao, tarefa.justificativa
        ))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return task_id

    def update_tarefa(
        self,
        tarefa_id: int,
        estado: str,
        duracao_ativa_segundos: float,
        decisao: Optional[str] = None,
        justificativa: Optional[str] = None
    ) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute("""
            UPDATE tarefas
            SET estado = ?, encerrada_em = ?, duracao_ativa_segundos = duracao_ativa_segundos + ?, decisao = ?, justificativa = ?
            WHERE id = ?
        """, (estado, now_iso, duracao_ativa_segundos, decisao, justificativa, tarefa_id))
        conn.commit()
        conn.close()

    def add_comunicacao(self, com: Comunicacao) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        estado_str = com.estado.value if hasattr(com.estado, 'value') else str(com.estado)
        cursor.execute("""
            INSERT INTO comunicacoes (solicitacao_id, template, destinatario, canal, estado, tentativa, motivo_falha, criado_em, enviado_simulado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            com.solicitacao_id, com.template, com.destinatario, com.canal,
            estado_str, com.tentativa, com.motivo_falha, com.criado_em, com.enviado_simulado_em
        ))
        conn.commit()
        com_id = cursor.lastrowid
        conn.close()
        return com_id

    def update_comunicacao(
        self,
        com_id: int,
        estado: EstadoComunicacao,
        tentativa: int,
        motivo_falha: Optional[str] = None,
        enviado_em: Optional[str] = None
    ) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        estado_str = estado.value if hasattr(estado, 'value') else str(estado)
        cursor.execute("""
            UPDATE comunicacoes
            SET estado = ?, tentativa = ?, motivo_falha = ?, enviado_simulado_em = ?
            WHERE id = ?
        """, (estado_str, tentativa, motivo_falha, enviado_em, com_id))
        conn.commit()
        conn.close()

    def update_sla_pause(self, solic_id: int, pausar: bool, timestamp_iso: Optional[str] = None) -> None:
        """Pausa ou retoma a contagem de SLA registrando eventos."""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT sla_estado, sla_pausado_em, sla_pausa_acumulada_segundos FROM solicitacoes WHERE id = ?", (solic_id,))
            row = cursor.fetchone()
            if not row:
                return

            now_iso = timestamp_iso or datetime.now().isoformat()
            now_dt = datetime.fromisoformat(now_iso)

            if pausar and row["sla_estado"] != EstadoSLA.PAUSADO.value:
                cursor.execute("""
                    UPDATE solicitacoes
                    SET sla_estado = ?, sla_pausado_em = ?, updated_at = ?
                    WHERE id = ?
                """, (EstadoSLA.PAUSADO.value, now_iso, now_iso, solic_id))

                cursor.execute("""
                    INSERT INTO eventos (solicitacao_id, tipo_evento, timestamp, origem_ator, estado_anterior, estado_novo, detalhes_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (solic_id, TipoEvento.SLA_PAUSADO.value, now_iso, "SISTEMA", EstadoSLA.CORRENDO.value, EstadoSLA.PAUSADO.value, "{}"))

            elif not pausar and row["sla_estado"] == EstadoSLA.PAUSADO.value:
                pausa_ini_dt = datetime.fromisoformat(row["sla_pausado_em"])
                segundos_pausa = max(0.0, (now_dt - pausa_ini_dt).total_seconds())
                nova_pausa_acum = row["sla_pausa_acumulada_segundos"] + segundos_pausa

                cursor.execute("""
                    UPDATE solicitacoes
                    SET sla_estado = ?, sla_pausado_em = NULL, sla_pausa_acumulada_segundos = ?, updated_at = ?
                    WHERE id = ?
                """, (EstadoSLA.CORRENDO.value, nova_pausa_acum, now_iso, solic_id))

                cursor.execute("""
                    INSERT INTO eventos (solicitacao_id, tipo_evento, timestamp, origem_ator, estado_anterior, estado_novo, detalhes_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    solic_id,
                    TipoEvento.SLA_RETOMADO.value,
                    now_iso,
                    "SISTEMA",
                    EstadoSLA.PAUSADO.value,
                    EstadoSLA.CORRENDO.value,
                    json.dumps({"segundos_pausados": segundos_pausa, "total_acumulado": nova_pausa_acum})
                ))

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_simulation_run(self, run: SimulationRun) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO simulation_runs (id, seed, total_intents, parametros_json, iniciado_em, concluido_em, metricas_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (run.id, run.seed, run.total_intents, run.parametros_json, run.iniciado_em, run.concluido_em, run.metricas_json))
        conn.commit()
        conn.close()

    def get_dashboard_metrics(self, universo: Optional[str] = None, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Agrega dados do banco de dados para os dashboards e KPIs respeitando o universo e run_id."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Determina cláusula de filtro rigorosa
        if universo == "INTERATIVO" or (universo is None and run_id is None):
            where_solic = "WHERE (s.universo = 'INTERATIVO' OR s.run_id IS NULL OR s.run_id = '')"
            where_sub = "WHERE (universo = 'INTERATIVO' OR run_id IS NULL OR run_id = '')"
            params = ()
        elif universo == "EXPERIMENTAL" or run_id is not None:
            if run_id:
                where_solic = "WHERE s.run_id = ?"
                where_sub = "WHERE run_id = ?"
                params = (run_id,)
            else:
                where_solic = "WHERE (s.universo = 'EXPERIMENTAL' OR (s.run_id IS NOT NULL AND s.run_id != ''))"
                where_sub = "WHERE (universo = 'EXPERIMENTAL' OR (run_id IS NOT NULL AND run_id != ''))"
                params = ()
        else:  # "TODOS"
            where_solic = "WHERE 1=1"
            where_sub = "WHERE 1=1"
            params = ()

        # Total por status
        cursor.execute(f"SELECT status, COUNT(*) as qtd FROM solicitacoes {where_sub} GROUP BY status", params)
        status_counts = {r["status"]: r["qtd"] for r in cursor.fetchall()}

        # Total por etapa
        cursor.execute(f"SELECT etapa, COUNT(*) as qtd FROM solicitacoes {where_sub} GROUP BY etapa", params)
        etapa_counts = {r["etapa"]: r["qtd"] for r in cursor.fetchall()}

        # Total por canal
        cursor.execute(f"SELECT canal, COUNT(*) as qtd FROM solicitacoes {where_sub} GROUP BY canal", params)
        canal_counts = {r["canal"]: r["qtd"] for r in cursor.fetchall()}

        # Total por prioridade
        cursor.execute(f"SELECT prioridade, COUNT(*) as qtd FROM solicitacoes {where_sub} GROUP BY prioridade", params)
        prioridade_counts = {r["prioridade"]: r["qtd"] for r in cursor.fetchall()}

        # Total geral
        cursor.execute(f"SELECT COUNT(*) as total FROM solicitacoes {where_sub}", params)
        total_solicitacoes = cursor.fetchone()["total"]

        # Esforço humano observado
        cursor.execute(f"""
            SELECT COUNT(t.id) as total_tarefas,
                   COALESCE(SUM(t.duracao_ativa_segundos), 0) as tempo_ativo_total_segundos,
                   COALESCE(AVG(t.duracao_ativa_segundos), 0) as tempo_ativo_medio_segundos
            FROM tarefas t
            JOIN solicitacoes s ON s.id = t.solicitacao_id
            {where_solic}
        """, params)
        tarefas_metricas = dict(cursor.fetchone() or {})

        # Pendências Abertas por tipo (ainda não resolvidas)
        cursor.execute(f"""
            SELECT p.tipo, COUNT(p.id) as qtd
            FROM pendencias p
            JOIN solicitacoes s ON s.id = p.solicitacao_id
            {where_solic} AND p.fechada_em IS NULL
            GROUP BY p.tipo
        """, params)
        pendencias_abertas_tipo = {r["tipo"]: r["qtd"] for r in cursor.fetchall()}

        # Ocorrências documentais históricas resolvidas
        cursor.execute(f"""
            SELECT p.tipo, COUNT(p.id) as qtd
            FROM pendencias p
            JOIN solicitacoes s ON s.id = p.solicitacao_id
            {where_solic} AND p.fechada_em IS NOT NULL
            GROUP BY p.tipo
        """, params)
        pendencias_resolvidas_tipo = {r["tipo"]: r["qtd"] for r in cursor.fetchall()}

        # Total geral por tipo (histórico cumulativo)
        cursor.execute(f"""
            SELECT p.tipo, COUNT(p.id) as qtd
            FROM pendencias p
            JOIN solicitacoes s ON s.id = p.solicitacao_id
            {where_solic}
            GROUP BY p.tipo
        """, params)
        pendencias_tipo = {r["tipo"]: r["qtd"] for r in cursor.fetchall()}

        conn.close()

        return {
            "total_solicitacoes": total_solicitacoes,
            "status_counts": status_counts,
            "etapa_counts": etapa_counts,
            "canal_counts": canal_counts,
            "prioridade_counts": prioridade_counts,
            "tarefas_metricas": tarefas_metricas,
            "pendencias_tipo": pendencias_tipo,
            "pendencias_abertas_tipo": pendencias_abertas_tipo,
            "pendencias_resolvidas_tipo": pendencias_resolvidas_tipo,
            "total_pendencias_abertas": sum(pendencias_abertas_tipo.values()),
            "total_pendencias_resolvidas": sum(pendencias_resolvidas_tipo.values())
        }

    def list_simulation_runs(self) -> List[Dict[str, Any]]:
        """Lista todas as execuções de simulação salvas com contagem de solicitações vinculadas."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*,
                   (SELECT COUNT(*) FROM solicitacoes s WHERE s.run_id = r.id) as total_solicitacoes
            FROM simulation_runs r
            ORDER BY r.iniciado_em DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_simulation_run(self, run_id: str) -> bool:
        """Exclui transacionalmente uma execução experimental e todas as suas solicitações filhas."""
        if not run_id or not str(run_id).strip() or run_id == "__INTERATIVO__":
            return False
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            # Garante que não afeta solicitações interativas
            cursor.execute("SELECT id FROM simulation_runs WHERE id = ?", (run_id,))
            run_row = cursor.fetchone()
            if not run_row:
                conn.close()
                return False

            cursor.execute("DELETE FROM solicitacoes WHERE run_id = ? AND (universo = 'EXPERIMENTAL' OR universo IS NULL)", (run_id,))
            cursor.execute("DELETE FROM simulation_runs WHERE id = ?", (run_id,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

