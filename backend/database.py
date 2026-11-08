"""Acesso ao SQLite sem manter conexões abertas entre requisições."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = BASE_DIR / "alagamentos.db"


@contextmanager
def conectar(database):
    """Cada operação recebe sua conexão e confirma ou desfaz a transação."""
    conexao = sqlite3.connect(str(database), timeout=10)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def inicializar_banco(database):
    """CREATE TABLE IF NOT EXISTS permite repetir a inicialização sem apagar dados."""
    caminho = Path(database)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    schema = (BASE_DIR / "schema.sql").read_text(encoding="utf-8")
    with conectar(caminho) as conexao:
        conexao.executescript(schema)
        # Bancos da primeira versão recebem colunas sem apagar ou atribuir autoria.
        colunas = {coluna["name"] for coluna in conexao.execute("PRAGMA table_info(ocorrencias)")}
        for nome, definicao in (
            ("autor_id", "INTEGER REFERENCES usuarios(id)"),
            ("latitude", "REAL CHECK(latitude BETWEEN -90 AND 90)"),
            ("longitude", "REAL CHECK(longitude BETWEEN -180 AND 180)"),
        ):
            if nome not in colunas:
                conexao.execute(f"ALTER TABLE ocorrencias ADD COLUMN {nome} {definicao}")
