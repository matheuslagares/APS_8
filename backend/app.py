"""API de ocorrências. Execute init_db.py antes de iniciar o servidor."""

import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from database import DEFAULT_DATABASE, conectar


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(DEFAULT_DATABASE),
        CORS_ORIGINS=("http://localhost:8081", "http://127.0.0.1:8081"),
    )
    if test_config is not None:
        app.config.update(test_config)

    @app.after_request
    def permitir_expo_web(resposta):
        # O navegador só recebe permissão para as origens locais configuradas.
        origem = request.headers.get("Origin")
        if origem and origem in app.config["CORS_ORIGINS"]:
            resposta.headers["Access-Control-Allow-Origin"] = origem
            resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
            resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
            resposta.vary.add("Origin")
        return resposta

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        mensagens = {
            400: "JSON inválido.",
            404: "Recurso não encontrado.",
            405: "Método não permitido.",
            415: "Envie o corpo como application/json.",
        }
        return jsonify(erro=mensagens.get(erro.code, erro.description)), erro.code

    @app.errorhandler(sqlite3.Error)
    def erro_banco(erro):
        app.logger.exception("Falha ao acessar o banco de dados")
        return jsonify(erro="Não foi possível acessar o banco de dados."), 500

    @app.errorhandler(Exception)
    def erro_inesperado(erro):
        app.logger.exception("Falha inesperada na API")
        return jsonify(erro="Erro interno do servidor."), 500

    def ler_json():
        # get_json também distingue conteúdo não JSON (415) de JSON malformado (400).
        dados = request.get_json()
        if not isinstance(dados, dict):
            return None, (jsonify(erro="O JSON deve ser um objeto."), 400)
        return dados, None

    @app.get("/saude")
    def saude():
        # Este teste funciona mesmo antes de o banco ser criado.
        return jsonify(status="ok"), 200

    @app.get("/ocorrencias")
    def listar_ocorrencias():
        with conectar(app.config["DATABASE"]) as conexao:
            registros = conexao.execute(
                "SELECT * FROM ocorrencias ORDER BY id DESC"
            ).fetchall()
        return jsonify([dict(registro) for registro in registros]), 200

    @app.post("/ocorrencias")
    def criar_ocorrencia():
        dados, erro = ler_json()
        if erro:
            return erro

        valores = {}
        for campo, limite, nome, obrigatorio in (
            ("bairro", 100, "O bairro", "obrigatório"),
            ("endereco", 200, "O endereço", "obrigatório"),
            ("descricao", 1000, "A descrição", "obrigatória"),
        ):
            valor = dados.get(campo)
            if valor is None:
                return jsonify(erro=f"{nome} é {obrigatorio}."), 400
            if not isinstance(valor, str):
                return jsonify(erro=f"{nome} deve ser um texto."), 400
            if not valor.strip():
                return jsonify(erro=f"{nome} é {obrigatorio}."), 400
            if len(valor.strip()) > limite:
                return jsonify(erro=f"{nome} deve ter no máximo {limite} caracteres."), 400
            valores[campo] = valor.strip()

        gravidade = dados.get("gravidade")
        if gravidade is None:
            return jsonify(erro="A gravidade é obrigatória."), 400
        if not isinstance(gravidade, str):
            return jsonify(erro="A gravidade deve ser um texto."), 400
        gravidade = gravidade.strip()
        if gravidade not in ("baixa", "media", "alta"):
            return jsonify(erro="A gravidade deve ser baixa, media ou alta."), 400

        # O cliente não escolhe o identificador, a data ou a situação inicial.
        criado_em = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with conectar(app.config["DATABASE"]) as conexao:
            cursor = conexao.execute(
                """INSERT INTO ocorrencias
                   (bairro, endereco, descricao, gravidade, situacao, criado_em)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (valores["bairro"], valores["endereco"], valores["descricao"],
                 gravidade, "ativo", criado_em),
            )
            registro = conexao.execute(
                "SELECT * FROM ocorrencias WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return jsonify(dict(registro)), 201

    @app.get("/ocorrencias/<int:id>")
    def obter_ocorrencia(id):
        with conectar(app.config["DATABASE"]) as conexao:
            registro = conexao.execute(
                "SELECT * FROM ocorrencias WHERE id = ?", (id,)
            ).fetchone()
        if registro is None:
            return jsonify(erro="Ocorrência não encontrada."), 404
        return jsonify(dict(registro)), 200

    @app.patch("/ocorrencias/<int:id>/situacao")
    def atualizar_situacao(id):
        dados, erro = ler_json()
        if erro:
            return erro
        situacao = dados.get("situacao")
        if situacao is None:
            return jsonify(erro="A situação é obrigatória."), 400
        if not isinstance(situacao, str):
            return jsonify(erro="A situação deve ser um texto."), 400
        situacao = situacao.strip()
        if situacao not in ("ativo", "resolvido"):
            return jsonify(erro="A situação deve ser ativo ou resolvido."), 400
        with conectar(app.config["DATABASE"]) as conexao:
            cursor = conexao.execute(
                "UPDATE ocorrencias SET situacao = ? WHERE id = ?", (situacao, id)
            )
            if cursor.rowcount == 0:
                return jsonify(erro="Ocorrência não encontrada."), 404
            registro = conexao.execute(
                "SELECT * FROM ocorrencias WHERE id = ?", (id,)
            ).fetchone()
        return jsonify(dict(registro)), 200

    return app


if __name__ == "__main__":
    # Para um celular na mesma rede, o servidor precisa escutar todas as interfaces.
    create_app().run(host="0.0.0.0", port=5000, debug=False)
