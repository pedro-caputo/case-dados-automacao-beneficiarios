"""
Gerenciamento de banco de dados SQLite, esquema relacional e conexões.
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional
from src.config import DB_PATH


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Retorna uma conexão ativa com o banco SQLite com chaves estrangeiras ativadas."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Inicializa todas as tabelas e índices necessários para o sistema."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    -- Tabela de intenções brutas sintéticas imutáveis
    CREATE TABLE IF NOT EXISTS raw_intents (
        id TEXT PRIMARY KEY,
        canal TEXT NOT NULL,
        cliente_dados_json TEXT NOT NULL,
        beneficiarios_json TEXT NOT NULL,
        docs_json TEXT NOT NULL,
        flags_json TEXT NOT NULL,
        seed INTEGER NOT NULL
    );

    -- Tabela de execuções de simulação
    CREATE TABLE IF NOT EXISTS simulation_runs (
        id TEXT PRIMARY KEY,
        seed INTEGER NOT NULL,
        total_intents INTEGER NOT NULL,
        parametros_json TEXT NOT NULL,
        iniciado_em TEXT NOT NULL,
        concluido_em TEXT,
        metricas_json TEXT
    );

    -- Tabela principal de solicitações
    CREATE TABLE IF NOT EXISTS solicitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        protocolo TEXT UNIQUE NOT NULL,
        external_intent_id TEXT,
        run_id TEXT,
        universo TEXT NOT NULL DEFAULT 'INTERATIVO',
        canal TEXT NOT NULL,
        data_criacao TEXT NOT NULL,
        status TEXT NOT NULL,
        etapa TEXT NOT NULL,
        prioridade TEXT NOT NULL,
        responsavel TEXT,
        sla_dias INTEGER NOT NULL DEFAULT 5,
        sla_inicio TEXT,
        sla_pausado_em TEXT,
        sla_pausa_acumulada_segundos REAL NOT NULL DEFAULT 0.0,
        sla_estado TEXT NOT NULL DEFAULT 'CORRENDO',
        data_conclusao TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES simulation_runs(id) ON DELETE CASCADE
    );

    -- Tabela de clientes fictícios
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitacao_id INTEGER NOT NULL,
        nome_ficticio TEXT NOT NULL,
        cpf_ficticio TEXT NOT NULL,
        email_ficticio TEXT,
        telefone_ficticio TEXT,
        FOREIGN KEY (solicitacao_id) REFERENCES solicitacoes(id) ON DELETE CASCADE
    );

    -- Tabela de beneficiários
    CREATE TABLE IF NOT EXISTS beneficiarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitacao_id INTEGER NOT NULL,
        nome_ficticio TEXT NOT NULL,
        cpf_ficticio TEXT NOT NULL,
        parentesco TEXT NOT NULL,
        percentual REAL NOT NULL,
        FOREIGN KEY (solicitacao_id) REFERENCES solicitacoes(id) ON DELETE CASCADE
    );

    -- Tabela de documentos simulados
    CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitacao_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        nome_arquivo TEXT NOT NULL,
        presente INTEGER NOT NULL DEFAULT 1,
        formato TEXT NOT NULL,
        valido_sintatico INTEGER NOT NULL DEFAULT 1,
        legibilidade_simulada INTEGER NOT NULL DEFAULT 1,
        metadados_json TEXT,
        FOREIGN KEY (solicitacao_id) REFERENCES solicitacoes(id) ON DELETE CASCADE
    );

    -- Tabela de pendências operacionais
    CREATE TABLE IF NOT EXISTS pendencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitacao_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        aberta_em TEXT NOT NULL,
        fechada_em TEXT,
        resolucao TEXT,
        FOREIGN KEY (solicitacao_id) REFERENCES solicitacoes(id) ON DELETE CASCADE
    );

    -- Tabela de tarefas operacionais e participação humana
    CREATE TABLE IF NOT EXISTS tarefas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitacao_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        atribuida_a TEXT NOT NULL,
        estado TEXT NOT NULL,
        iniciada_em TEXT,
        encerrada_em TEXT,
        duracao_ativa_segundos REAL NOT NULL DEFAULT 0.0,
        decisao TEXT,
        justificativa TEXT,
        FOREIGN KEY (solicitacao_id) REFERENCES solicitacoes(id) ON DELETE CASCADE
    );

    -- Tabela de eventos para rastreabilidade auditável
    CREATE TABLE IF NOT EXISTS eventos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitacao_id INTEGER NOT NULL,
        tipo_evento TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        origem_ator TEXT NOT NULL,
        estado_anterior TEXT,
        estado_novo TEXT,
        detalhes_json TEXT,
        FOREIGN KEY (solicitacao_id) REFERENCES solicitacoes(id) ON DELETE CASCADE
    );

    -- Tabela de comunicações simuladas
    CREATE TABLE IF NOT EXISTS comunicacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        solicitacao_id INTEGER NOT NULL,
        template TEXT NOT NULL,
        destinatario TEXT NOT NULL,
        canal TEXT NOT NULL,
        estado TEXT NOT NULL,
        tentativa INTEGER NOT NULL DEFAULT 1,
        motivo_falha TEXT,
        criado_em TEXT NOT NULL,
        enviado_simulado_em TEXT,
        FOREIGN KEY (solicitacao_id) REFERENCES solicitacoes(id) ON DELETE CASCADE
    );

    -- Índices estratégicos para performance
    CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status);
    CREATE INDEX IF NOT EXISTS idx_solicitacoes_etapa ON solicitacoes(etapa);
    CREATE INDEX IF NOT EXISTS idx_solicitacoes_protocolo ON solicitacoes(protocolo);
    CREATE INDEX IF NOT EXISTS idx_solicitacoes_run_id ON solicitacoes(run_id);
    CREATE INDEX IF NOT EXISTS idx_solicitacoes_universo ON solicitacoes(universo);
    CREATE INDEX IF NOT EXISTS idx_eventos_solicitacao ON eventos(solicitacao_id);
    CREATE INDEX IF NOT EXISTS idx_beneficiarios_solicitacao ON beneficiarios(solicitacao_id);
    CREATE INDEX IF NOT EXISTS idx_documentos_solicitacao ON documentos(solicitacao_id);
    CREATE INDEX IF NOT EXISTS idx_pendencias_solicitacao ON pendencias(solicitacao_id);
    CREATE INDEX IF NOT EXISTS idx_tarefas_solicitacao ON tarefas(solicitacao_id);
    CREATE INDEX IF NOT EXISTS idx_comunicacoes_solicitacao ON comunicacoes(solicitacao_id);
    """)

    # Migração segura e idempotente para garantir coluna universo em bancos legados
    cursor.execute("PRAGMA table_info(solicitacoes)")
    cols = [r[1] for r in cursor.fetchall()]
    if "universo" not in cols:
        cursor.execute("ALTER TABLE solicitacoes ADD COLUMN universo TEXT NOT NULL DEFAULT 'INTERATIVO'")
        cursor.execute("UPDATE solicitacoes SET universo = 'EXPERIMENTAL' WHERE run_id IS NOT NULL AND run_id != ''")
        cursor.execute("UPDATE solicitacoes SET universo = 'INTERATIVO' WHERE run_id IS NULL OR run_id = ''")

    conn.commit()
    conn.close()


def reset_operational_data(db_path: Optional[Path] = None) -> None:
    """Limpa dados operacionais interativos, preservando execuções experimentais e intenções sintéticas."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM solicitacoes WHERE universo = 'INTERATIVO' OR run_id IS NULL OR run_id = ''")
    conn.commit()
    conn.close()

