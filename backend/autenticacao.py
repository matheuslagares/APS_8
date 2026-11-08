"""Senhas com salt e sessões: somente o hash do token fica no SQLite."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone


def agora_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def criar_sessao(conexao, usuario_id):
    token = secrets.token_urlsafe(32)
    expira_em = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="seconds")
    conexao.execute(
        "INSERT INTO sessoes(usuario_id, token_hash, expira_em) VALUES (?, ?, ?)",
        (usuario_id, hash_token(token), expira_em),
    )
    return token, expira_em
