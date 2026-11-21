# API do Alerta de Alagamentos
# feito por: Saad, Matheus, Guilherme, Gustavo e Henrique
# pra rodar: python app.py  (o banco e criado sozinho)

import io
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta

from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, ImageOps
from werkzeug.security import check_password_hash, generate_password_hash

from banco import PASTA, conectar, criar_tabelas

app = Flask(__name__)

PASTA_UPLOADS = os.path.join(PASTA, "uploads")
LIMITE_ARQUIVO = 20 * 1024 * 1024  # 20 MB
app.config["MAX_CONTENT_LENGTH"] = 24 * 1024 * 1024  # um pouco a mais por causa dos outros campos do form

# cria as tabelas qdo o servidor sobe
criar_tabelas()


# ---------------------------------------------------------
# funcoes de ajuda (Saad)
# ---------------------------------------------------------

def erro(mensagem, codigo):
    # todo erro da api volta nesse formato: {"erro": "..."}
    return jsonify(erro=mensagem), codigo


def agora():
    return datetime.now().isoformat(timespec="seconds")


def usuario_logado():
    # pega o token do header "Authorization: Bearer xxxxx"
    # se nao tiver ou estiver expirado retorna None
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        return None
    token = cabecalho[7:]  # tira o "Bearer " da frente

    conexao = conectar()
    usuario = conexao.execute(
        """SELECT usuarios.id, usuarios.nome, usuarios.email FROM sessoes
           JOIN usuarios ON usuarios.id = sessoes.usuario_id
           WHERE sessoes.token = ? AND sessoes.expira_em > ?""",
        (token, agora()),
    ).fetchone()
    conexao.close()

    if usuario is None:
        return None
    return dict(usuario)


def criar_sessao(conexao, usuario_id):
    # token aleatorio, vale por 7 dias
    token = secrets.token_urlsafe(32)
    expira = (datetime.now() + timedelta(days=7)).isoformat(timespec="seconds")
    conexao.execute(
        "INSERT INTO sessoes (usuario_id, token, expira_em) VALUES (?, ?, ?)",
        (usuario_id, token, expira),
    )
    return token


def texto(dados, campo):
    # pega um campo de texto ja sem espaco nas pontas
    valor = dados.get(campo)
    if not isinstance(valor, str):
        return ""
    return valor.strip()


# libera o app web (expo web roda em outra porta) - CORS
# TODO revisar com o Saad se precisa restringir isso
@app.after_request
def liberar_cors(resposta):
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
    return resposta


@app.errorhandler(413)
def arquivo_grande(e):
    return erro("A requisição ultrapassa o limite de 24 MiB.", 413)


@app.errorhandler(404)
def nao_achou(e):
    return erro("Recurso não encontrado.", 404)


@app.errorhandler(500)
def erro_interno(e):
    return erro("Erro interno do servidor.", 500)


@app.get("/saude")
def saude():
    # so pra testar se o servidor ta de pe
    return jsonify(status="ok")


# ---------------------------------------------------------
# login e cadastro de usuario - parte do Matheus
# ---------------------------------------------------------

@app.post("/auth/cadastro")
def cadastrar_usuario():
    dados = request.get_json(silent=True) or {}
    nome = texto(dados, "nome")
    email = texto(dados, "email").lower()
    senha = dados.get("senha") or ""

    # validacoes basicas
    if nome == "" or len(nome) > 100:
        return erro("O nome deve ter entre 1 e 100 caracteres.", 400)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return erro("Informe um e-mail válido.", 400)
    if len(senha) < 8 or len(senha) > 128:
        return erro("A senha deve ter entre 8 e 128 caracteres.", 400)

    conexao = conectar()
    # ve se o email ja existe antes de inserir
    ja_existe = conexao.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if ja_existe:
        conexao.close()
        return erro("Este e-mail já está cadastrado.", 409)

    # nunca salvar a senha pura!! so o hash
    cursor = conexao.execute(
        "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
        (nome, email, generate_password_hash(senha)),
    )
    usuario = {"id": cursor.lastrowid, "nome": nome, "email": email}
    token = criar_sessao(conexao, usuario["id"])
    conexao.commit()
    conexao.close()

    return jsonify(usuario=usuario, token=token), 201


@app.post("/auth/login")
def login():
    dados = request.get_json(silent=True) or {}
    email = texto(dados, "email").lower()
    senha = dados.get("senha") or ""

    conexao = conectar()
    usuario = conexao.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

    # msm msg pra email errado e senha errada, assim ngm descobre quais emails existem
    if usuario is None or not check_password_hash(usuario["senha_hash"], senha):
        conexao.close()
        return erro("E-mail ou senha incorretos.", 401)

    token = criar_sessao(conexao, usuario["id"])
    conexao.commit()
    conexao.close()

    publico = {"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"]}
    return jsonify(usuario=publico, token=token)


@app.get("/auth/me")
def minha_conta():
    usuario = usuario_logado()
    if usuario is None:
        return erro("Entre na sua conta para continuar.", 401)
    return jsonify(usuario=usuario)


@app.post("/auth/logout")
def logout():
    usuario = usuario_logado()
    if usuario is None:
        return erro("Entre na sua conta para continuar.", 401)
    # apaga o token, ai ele para de funcionar
    token = request.headers["Authorization"][7:]
    conexao = conectar()
    conexao.execute("DELETE FROM sessoes WHERE token = ?", (token,))
    conexao.commit()
    conexao.close()
    return jsonify(mensagem="Sessão encerrada.")


# ---------------------------------------------------------
# ocorrencias - Guilherme
# ---------------------------------------------------------

def montar_ocorrencia(conexao, linha, usuario):
    # transforma a linha do banco em dicionario e junta os anexos
    ocorrencia = dict(linha)
    # so quem criou pode mudar a situacao
    ocorrencia["pode_alterar"] = linha["autor_id"] == usuario["id"]

    anexos = conexao.execute(
        "SELECT id, tipo, mime_type, tamanho FROM anexos WHERE ocorrencia_id = ?",
        (linha["id"],),
    ).fetchall()
    ocorrencia["anexos"] = []
    for anexo in anexos:
        item = dict(anexo)
        item["url"] = "/anexos/" + str(anexo["id"])
        ocorrencia["anexos"].append(item)
    return ocorrencia


@app.get("/ocorrencias")
def listar_ocorrencias():
    usuario = usuario_logado()
    if usuario is None:
        return erro("Entre na sua conta para continuar.", 401)

    conexao = conectar()
    linhas = conexao.execute("SELECT * FROM ocorrencias ORDER BY id DESC").fetchall()
    lista = []
    for linha in linhas:
        lista.append(montar_ocorrencia(conexao, linha, usuario))
    conexao.close()
    return jsonify(lista)


@app.get("/ocorrencias/<int:id>")
def ver_ocorrencia(id):
    usuario = usuario_logado()
    if usuario is None:
        return erro("Entre na sua conta para continuar.", 401)

    conexao = conectar()
    linha = conexao.execute("SELECT * FROM ocorrencias WHERE id = ?", (id,)).fetchone()
    if linha is None:
        conexao.close()
        return erro("Ocorrência não encontrada.", 404)
    resultado = montar_ocorrencia(conexao, linha, usuario)
    conexao.close()
    return jsonify(resultado)


def salvar_arquivo(arquivo):
    # parte do Henrique - salva a foto/video na pasta uploads
    # retorna (dados_do_anexo, mensagem_de_erro)
    conteudo = arquivo.read()
    if len(conteudo) == 0:
        return None, "O arquivo está vazio."
    if len(conteudo) > LIMITE_ARQUIVO:
        return None, "O arquivo deve ter no máximo 20 MiB."

    # descobre o tipo pelos primeiros bytes do arquivo (nao da pra confiar na extensao q o usuario manda)
    if conteudo.startswith(b"\xff\xd8"):
        extensao, mime, tipo = "jpg", "image/jpeg", "imagem"
    elif conteudo.startswith(b"\x89PNG"):
        extensao, mime, tipo = "png", "image/png", "imagem"
    elif conteudo[4:8] == b"ftyp":
        extensao, mime, tipo = "mp4", "video/mp4", "video"
    else:
        return None, "Envie uma foto JPEG/PNG ou um vídeo MP4."

    # se for foto, abre e salva de novo -> isso tira os dados do EXIF (tipo o GPS da foto)
    if tipo == "imagem":
        try:
            foto = Image.open(io.BytesIO(conteudo))
            formato = foto.format
            foto = ImageOps.exif_transpose(foto)  # deixa a foto na posicao certa
            if formato == "JPEG":
                foto = foto.convert("RGB")
            saida = io.BytesIO()
            foto.save(saida, format=formato)
            conteudo = saida.getvalue()
        except Exception:
            return None, "O conteúdo da foto está inválido ou incompleto."

    # nome aleatorio pra nao dar conflito entre arquivos
    os.makedirs(PASTA_UPLOADS, exist_ok=True)
    nome = uuid.uuid4().hex + "." + extensao
    with open(os.path.join(PASTA_UPLOADS, nome), "wb") as saida:
        saida.write(conteudo)

    return {"nome_arquivo": nome, "tipo": tipo, "mime_type": mime, "tamanho": len(conteudo)}, None


@app.post("/ocorrencias")
def criar_ocorrencia():
    usuario = usuario_logado()
    if usuario is None:
        return erro("Entre na sua conta para continuar.", 401)

    # o app manda JSON qdo nao tem anexo e form-data qdo tem
    if request.is_json:
        dados = request.get_json()
    else:
        dados = request.form
    arquivo = request.files.get("arquivo")

    bairro = texto(dados, "bairro")
    endereco = texto(dados, "endereco")
    descricao = texto(dados, "descricao")
    gravidade = texto(dados, "gravidade")

    # validacao dos campos obrigatorios
    if bairro == "" or len(bairro) > 100:
        return erro("O bairro é obrigatório (máximo 100 caracteres).", 400)
    if endereco == "" or len(endereco) > 200:
        return erro("O endereço é obrigatório (máximo 200 caracteres).", 400)
    if descricao == "" or len(descricao) > 1000:
        return erro("A descrição é obrigatória (máximo 1000 caracteres).", 400)
    if gravidade not in ("baixa", "media", "alta"):
        return erro("A gravidade deve ser baixa, media ou alta.", 400)

    # latitude/longitude sao opcionais, mas se vier uma tem q vir a outra
    latitude = dados.get("latitude")
    longitude = dados.get("longitude")
    if latitude is not None or longitude is not None:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return erro("Informe latitude e longitude numéricas juntas.", 400)
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return erro("Latitude ou longitude fora do intervalo.", 400)

    anexo = None
    if arquivo:
        anexo, mensagem = salvar_arquivo(arquivo)
        if mensagem:
            return erro(mensagem, 400)

    conexao = conectar()
    cursor = conexao.execute(
        """INSERT INTO ocorrencias
           (bairro, endereco, descricao, gravidade, situacao, criado_em, autor_id, latitude, longitude)
           VALUES (?, ?, ?, ?, 'ativo', ?, ?, ?, ?)""",
        (bairro, endereco, descricao, gravidade, agora(), usuario["id"], latitude, longitude),
    )
    novo_id = cursor.lastrowid

    if anexo:
        conexao.execute(
            "INSERT INTO anexos (ocorrencia_id, nome_arquivo, tipo, mime_type, tamanho) VALUES (?, ?, ?, ?, ?)",
            (novo_id, anexo["nome_arquivo"], anexo["tipo"], anexo["mime_type"], anexo["tamanho"]),
        )
    conexao.commit()

    linha = conexao.execute("SELECT * FROM ocorrencias WHERE id = ?", (novo_id,)).fetchone()
    resultado = montar_ocorrencia(conexao, linha, usuario)
    conexao.close()
    return jsonify(resultado), 201


@app.patch("/ocorrencias/<int:id>/situacao")
def mudar_situacao(id):
    usuario = usuario_logado()
    if usuario is None:
        return erro("Entre na sua conta para continuar.", 401)

    dados = request.get_json(silent=True) or {}
    situacao = texto(dados, "situacao")
    if situacao not in ("ativo", "resolvido"):
        return erro("A situação deve ser ativo ou resolvido.", 400)

    conexao = conectar()
    linha = conexao.execute("SELECT * FROM ocorrencias WHERE id = ?", (id,)).fetchone()
    if linha is None:
        conexao.close()
        return erro("Ocorrência não encontrada.", 404)
    if linha["autor_id"] != usuario["id"]:
        conexao.close()
        return erro("Somente quem cadastrou pode alterar esta ocorrência.", 403)

    conexao.execute("UPDATE ocorrencias SET situacao = ? WHERE id = ?", (situacao, id))
    conexao.commit()
    linha = conexao.execute("SELECT * FROM ocorrencias WHERE id = ?", (id,)).fetchone()
    resultado = montar_ocorrencia(conexao, linha, usuario)
    conexao.close()
    return jsonify(resultado)


@app.get("/anexos/<int:id>")
def ver_anexo(id):
    if usuario_logado() is None:
        return erro("Entre na sua conta para continuar.", 401)

    conexao = conectar()
    anexo = conexao.execute("SELECT * FROM anexos WHERE id = ?", (id,)).fetchone()
    conexao.close()
    if anexo is None:
        return erro("Anexo não encontrado.", 404)
    return send_from_directory(PASTA_UPLOADS, anexo["nome_arquivo"], mimetype=anexo["mime_type"])


if __name__ == "__main__":
    # host 0.0.0.0 pra o celular conseguir acessar pela rede wi-fi
    app.run(host="0.0.0.0", port=5000)
