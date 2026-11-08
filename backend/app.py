"""API autenticada de relatos. Execute init_db.py antes de iniciar o servidor."""

import math
import re
import sqlite3

from flask import Flask, g, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from autenticacao import agora_utc, criar_sessao, hash_token
from database import BASE_DIR, DEFAULT_DATABASE, conectar
from midia import MidiaInvalida, apagar_arquivo, preparar_arquivo


# Evita uma resposta mais rápida para e-mails que não existem.
HASH_INEXISTENTE = generate_password_hash("senha-aleatoria-inexistente", method="scrypt")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(DEFAULT_DATABASE),
        UPLOAD_FOLDER=str(BASE_DIR / "uploads"),
        MAX_CONTENT_LENGTH=24 * 1024 * 1024,
        CORS_ORIGINS=("http://localhost:8081", "http://127.0.0.1:8081"),
    )
    if test_config is not None:
        app.config.update(test_config)

    def falha(mensagem, codigo):
        resposta = jsonify(erro=mensagem)
        if codigo == 401:
            resposta.headers["WWW-Authenticate"] = "Bearer"
        return resposta, codigo

    @app.before_request
    def verificar_sessao():
        # O preflight CORS não leva o token. Os dados e anexos continuam privados.
        if request.method == "OPTIONS":
            return None
        privado = (
            request.path == "/ocorrencias" or request.path.startswith("/ocorrencias/")
            or request.path.startswith("/anexos/")
            or request.path in ("/auth/me", "/auth/logout")
        )
        if not privado:
            return None
        partes = request.headers.get("Authorization", "").split()
        if len(partes) != 2 or partes[0].lower() != "bearer":
            return falha("Entre na sua conta para continuar.", 401)
        with conectar(app.config["DATABASE"]) as conexao:
            usuario = conexao.execute(
                """SELECT u.id, u.nome, u.email FROM sessoes s
                   JOIN usuarios u ON u.id = s.usuario_id
                   WHERE s.token_hash = ? AND s.expira_em > ?""",
                (hash_token(partes[1]), agora_utc()),
            ).fetchone()
        if usuario is None:
            return falha("Sessão inválida ou expirada. Entre novamente.", 401)
        g.usuario = dict(usuario)
        g.token_hash = hash_token(partes[1])

    @app.after_request
    def finalizar_resposta(resposta):
        origem = request.headers.get("Origin")
        if origem and origem in app.config["CORS_ORIGINS"]:
            resposta.headers["Access-Control-Allow-Origin"] = origem
            resposta.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
            resposta.vary.add("Origin")
        if request.path != "/saude":
            resposta.headers["Cache-Control"] = "no-store"
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        return resposta

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        mensagens = {
            400: "JSON ou formulário inválido.", 404: "Recurso não encontrado.",
            405: "Método não permitido.", 413: "A requisição ultrapassa o limite de 24 MiB.",
            415: "Envie JSON ou, no cadastro com arquivo, multipart/form-data.",
        }
        return falha(mensagens.get(erro.code, erro.description), erro.code)

    @app.errorhandler(MidiaInvalida)
    def erro_midia(erro):
        return falha(str(erro), erro.status_code)

    @app.errorhandler(sqlite3.Error)
    def erro_banco(erro):
        app.logger.exception("Falha ao acessar o banco de dados")
        return falha("Não foi possível acessar o banco de dados.", 500)

    @app.errorhandler(Exception)
    def erro_inesperado(erro):
        app.logger.exception("Falha inesperada na API")
        return falha("Erro interno do servidor.", 500)

    def ler_json():
        dados = request.get_json()
        if not isinstance(dados, dict):
            return None, falha("O JSON deve ser um objeto.", 400)
        return dados, None

    def validar_email_senha(dados):
        email, senha = dados.get("email"), dados.get("senha")
        if (not isinstance(email, str) or len(email.strip()) > 254
                or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip())):
            return None, None, falha("Informe um e-mail válido.", 400)
        if not isinstance(senha, str) or not 8 <= len(senha) <= 128 or not senha.strip():
            return None, None, falha("A senha deve ter entre 8 e 128 caracteres.", 400)
        return email.strip().lower(), senha, None

    def resposta_sessao(usuario, token, expira_em):
        return jsonify(usuario=dict(usuario), token=token, expira_em=expira_em)

    @app.get("/saude")
    def saude():
        return jsonify(status="ok"), 200

    @app.post("/auth/cadastro")
    def cadastrar_usuario():
        dados, erro = ler_json()
        if erro:
            return erro
        nome = dados.get("nome")
        if not isinstance(nome, str) or not 1 <= len(nome.strip()) <= 100:
            return falha("O nome deve ter entre 1 e 100 caracteres.", 400)
        email, senha, erro = validar_email_senha(dados)
        if erro:
            return erro
        senha_hash = generate_password_hash(senha, method="scrypt")
        try:
            with conectar(app.config["DATABASE"]) as conexao:
                cursor = conexao.execute(
                    "INSERT INTO usuarios(nome, email, senha_hash) VALUES (?, ?, ?)",
                    (nome.strip(), email, senha_hash),
                )
                usuario = {"id": cursor.lastrowid, "nome": nome.strip(), "email": email}
                token, expira_em = criar_sessao(conexao, usuario["id"])
        except sqlite3.IntegrityError:
            with conectar(app.config["DATABASE"]) as conexao:
                existente = conexao.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
            if existente is not None:
                return falha("Este e-mail já está cadastrado.", 409)
            raise
        return resposta_sessao(usuario, token, expira_em), 201

    @app.post("/auth/login")
    def entrar():
        dados, erro = ler_json()
        if erro:
            return erro
        email, senha, erro = validar_email_senha(dados)
        if erro:
            return erro
        with conectar(app.config["DATABASE"]) as conexao:
            usuario = conexao.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
            valido = check_password_hash(usuario["senha_hash"] if usuario else HASH_INEXISTENTE, senha)
            if not usuario or not valido:
                return falha("E-mail ou senha incorretos.", 401)
            token, expira_em = criar_sessao(conexao, usuario["id"])
        publico = {chave: usuario[chave] for chave in ("id", "nome", "email")}
        return resposta_sessao(publico, token, expira_em), 200

    @app.get("/auth/me")
    def minha_conta():
        return jsonify(usuario=g.usuario), 200

    @app.post("/auth/logout")
    def sair():
        with conectar(app.config["DATABASE"]) as conexao:
            conexao.execute("DELETE FROM sessoes WHERE token_hash = ?", (g.token_hash,))
        return jsonify(mensagem="Sessão encerrada."), 200

    def pode_alterar(registro):
        # Registros antigos, sem autor, não são atribuídos ao primeiro cadastrado.
        return registro["autor_id"] is not None and registro["autor_id"] == g.usuario["id"]

    def serializar_ocorrencia(conexao, registro):
        resultado = dict(registro)
        resultado["pode_alterar"] = pode_alterar(registro)
        anexos = conexao.execute(
            "SELECT id, tipo, mime_type, tamanho FROM anexos WHERE ocorrencia_id = ? ORDER BY id",
            (registro["id"],),
        ).fetchall()
        resultado["anexos"] = [{**dict(anexo), "url": f"/anexos/{anexo['id']}"} for anexo in anexos]
        return resultado

    @app.get("/ocorrencias")
    def listar_ocorrencias():
        with conectar(app.config["DATABASE"]) as conexao:
            registros = conexao.execute("SELECT * FROM ocorrencias ORDER BY id DESC").fetchall()
            resultado = [serializar_ocorrencia(conexao, registro) for registro in registros]
        return jsonify(resultado), 200

    def validar_relato(dados, multipart):
        valores = {}
        for campo, limite, nome, obrigatorio in (
            ("bairro", 100, "O bairro", "obrigatório"),
            ("endereco", 200, "O endereço", "obrigatório"),
            ("descricao", 1000, "A descrição", "obrigatória"),
        ):
            valor = dados.get(campo)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                return None, falha(f"{nome} é {obrigatorio}.", 400)
            if not isinstance(valor, str):
                return None, falha(f"{nome} deve ser um texto.", 400)
            if len(valor.strip()) > limite:
                return None, falha(f"{nome} deve ter no máximo {limite} caracteres.", 400)
            valores[campo] = valor.strip()
        gravidade = dados.get("gravidade")
        if not isinstance(gravidade, str) or gravidade.strip() not in ("baixa", "media", "alta"):
            return None, falha("A gravidade deve ser baixa, media ou alta.", 400)
        valores["gravidade"] = gravidade.strip()
        latitude, longitude = dados.get("latitude"), dados.get("longitude")
        if latitude is None and longitude is None:
            valores.update(latitude=None, longitude=None)
            return valores, None
        for campo, valor, limite in (("latitude", latitude, 90), ("longitude", longitude, 180)):
            if isinstance(valor, bool) or (not multipart and not isinstance(valor, (int, float))):
                return None, falha("Informe latitude e longitude numéricas juntas.", 400)
            try:
                numero = float(valor)
            except (TypeError, ValueError, OverflowError):
                return None, falha("Informe latitude e longitude numéricas juntas.", 400)
            if not math.isfinite(numero) or not -limite <= numero <= limite:
                return None, falha(f"A {campo} deve estar entre {-limite} e {limite}.", 400)
            valores[campo] = numero
        return valores, None

    @app.post("/ocorrencias")
    def criar_ocorrencia():
        multipart = request.mimetype == "multipart/form-data"
        arquivo = None
        if multipart:
            dados = request.form.to_dict()
            if any(nome != "arquivo" for nome in request.files) or len(request.files.getlist("arquivo")) > 1:
                return falha("Envie no máximo um arquivo no campo arquivo.", 400)
            arquivo = request.files.get("arquivo")
        else:
            dados, erro = ler_json()
            if erro:
                return erro
        valores, erro = validar_relato(dados, multipart)
        if erro:
            return erro
        anexo = preparar_arquivo(arquivo, app.config["UPLOAD_FOLDER"]) if arquivo is not None else None
        try:
            # Falha no INSERT, no anexo ou no commit desfaz o banco e remove o arquivo.
            with conectar(app.config["DATABASE"]) as conexao:
                cursor = conexao.execute(
                    """INSERT INTO ocorrencias
                       (bairro, endereco, descricao, gravidade, situacao, criado_em, autor_id, latitude, longitude)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (valores["bairro"], valores["endereco"], valores["descricao"], valores["gravidade"],
                     "ativo", agora_utc(), g.usuario["id"], valores["latitude"], valores["longitude"]),
                )
                identificador = cursor.lastrowid
                if anexo:
                    conexao.execute(
                        """INSERT INTO anexos(ocorrencia_id, nome_arquivo, tipo, mime_type, tamanho)
                           VALUES (?, ?, ?, ?, ?)""",
                        (identificador, anexo["nome_arquivo"], anexo["tipo"], anexo["mime_type"], anexo["tamanho"]),
                    )
                registro = conexao.execute("SELECT * FROM ocorrencias WHERE id = ?", (identificador,)).fetchone()
                resultado = serializar_ocorrencia(conexao, registro)
        except Exception:
            if anexo:
                apagar_arquivo(app.config["UPLOAD_FOLDER"], anexo["nome_arquivo"])
            raise
        return jsonify(resultado), 201

    @app.get("/ocorrencias/<int:id>")
    def obter_ocorrencia(id):
        with conectar(app.config["DATABASE"]) as conexao:
            registro = conexao.execute("SELECT * FROM ocorrencias WHERE id = ?", (id,)).fetchone()
            if registro is None:
                return falha("Ocorrência não encontrada.", 404)
            resultado = serializar_ocorrencia(conexao, registro)
        return jsonify(resultado), 200

    @app.patch("/ocorrencias/<int:id>/situacao")
    def atualizar_situacao(id):
        dados, erro = ler_json()
        if erro:
            return erro
        situacao = dados.get("situacao")
        if not isinstance(situacao, str) or situacao.strip() not in ("ativo", "resolvido"):
            return falha("A situação deve ser ativo ou resolvido.", 400)
        with conectar(app.config["DATABASE"]) as conexao:
            registro = conexao.execute("SELECT * FROM ocorrencias WHERE id = ?", (id,)).fetchone()
            if registro is None:
                return falha("Ocorrência não encontrada.", 404)
            if not pode_alterar(registro):
                return falha("Somente quem cadastrou pode alterar esta ocorrência.", 403)
            conexao.execute("UPDATE ocorrencias SET situacao = ? WHERE id = ?", (situacao.strip(), id))
            registro = conexao.execute("SELECT * FROM ocorrencias WHERE id = ?", (id,)).fetchone()
            resultado = serializar_ocorrencia(conexao, registro)
        return jsonify(resultado), 200

    @app.get("/anexos/<int:id>")
    def obter_anexo(id):
        with conectar(app.config["DATABASE"]) as conexao:
            anexo = conexao.execute("SELECT * FROM anexos WHERE id = ?", (id,)).fetchone()
        if anexo is None:
            return falha("Anexo não encontrado.", 404)
        return send_from_directory(app.config["UPLOAD_FOLDER"], anexo["nome_arquivo"], mimetype=anexo["mime_type"])

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000, debug=False)
