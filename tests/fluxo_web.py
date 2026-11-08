"""Teste integrado V2: login, GPS simulado, mapa e anexos com API real.

Inicie o Expo web em 8081 com EXPO_PUBLIC_API_URL=http://127.0.0.1:5000.
O teste cria seu próprio SQLite e diretório de uploads temporários na porta 5000.
Dois navegadores isolados não substituem aparelhos físicos nem o GPS real.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from playwright.sync_api import expect, sync_playwright


RAIZ = Path(__file__).resolve().parents[1]
PYTHON_API = RAIZ / "backend" / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
URL_WEB = "http://127.0.0.1:8081"
URL_API = "http://127.0.0.1:5000"
RESULTADOS = RAIZ / "test-results"
FIXTURES = RAIZ / "tests" / "fixtures"
GPS_SIMULADO = {"latitude": -23.550520, "longitude": -46.633308}


def requisitar_api(caminho, token=None, metodo="GET", dados=None):
    """Consulta real; credenciais do banco temporário nunca entram no relatório."""
    cabecalhos = {"Accept": "application/json"}
    if token:
        cabecalhos["Authorization"] = f"Bearer {token}"
    corpo = None
    if dados is not None:
        corpo = json.dumps(dados).encode("utf-8")
        cabecalhos["Content-Type"] = "application/json"
    pedido = Request(f"{URL_API}{caminho}", data=corpo, headers=cabecalhos, method=metodo)
    try:
        resposta = urlopen(pedido, timeout=5)
    except HTTPError as erro:
        resposta = erro
    with resposta:
        corpo = resposta.read()
        conteudo = json.loads(corpo) if "application/json" in resposta.headers.get("Content-Type", "") else corpo
        return resposta.status, conteudo


def consultar(caminho, token=None):
    status, dados = requisitar_api(caminho, token)
    assert status == 200, f"Consulta {caminho} retornou HTTP {status}."
    return dados


def conferir_porta_livre():
    # Não encerra o servidor de outra pessoa nem grava no banco de demonstração.
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", 5000)) == 0:
            raise RuntimeError("Pare sua API na porta 5000 antes do teste isolado.")


def iniciar_api(banco, uploads, log):
    codigo = (
        "from app import create_app; from database import inicializar_banco; "
        f"banco={str(banco)!r}; inicializar_banco(banco); "
        f"create_app({{'DATABASE': banco, 'UPLOAD_FOLDER': {str(uploads)!r}}})"
        ".run(host='127.0.0.1', port=5000, debug=False)"
    )
    processo = subprocess.Popen(
        [str(PYTHON_API), "-c", codigo], cwd=RAIZ / "backend", stdout=log, stderr=log,
    )
    try:
        for _ in range(100):
            if processo.poll() is not None:
                raise RuntimeError("A API de teste não iniciou; consulte test-results/api.log.")
            try:
                if consultar("/saude") == {"status": "ok"}:
                    return processo
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("Tempo esgotado ao iniciar a API de teste.")
    except BaseException:
        parar_api(processo)
        raise


def parar_api(processo):
    if processo and processo.poll() is None:
        processo.terminate()
        try:
            processo.wait(timeout=5)
        except subprocess.TimeoutExpired:
            processo.kill()
            processo.wait(timeout=5)


def pausar_gravacao(tela, gravar):
    # Somente a gravação recebe uma pausa de leitura; assertions aguardam condições.
    if gravar:
        tela.wait_for_timeout(1000)


def capturar(tela, nome, gravar):
    tela.screenshot(path=str(RESULTADOS / nome), full_page=True)
    pausar_gravacao(tela, gravar)


def identificar_codigo():
    arquivos = [RAIZ / "mobile" / "App.js", Path(__file__).resolve(), RAIZ / "tests" / "gravacao.py"]
    arquivos += list((RAIZ / "mobile" / "src").rglob("*.js"))
    arquivos += list((RAIZ / "backend").glob("*.py"))
    arquivos += [RAIZ / "backend" / "schema.sql", RAIZ / "backend" / "requirements.txt", RAIZ / "mobile" / "package-lock.json", RAIZ / "mobile" / "app.json"]
    arquivos += [FIXTURES / "foto-teste.png", FIXTURES / "video-teste.mp4"]
    return {
        str(arquivo.relative_to(RAIZ)): hashlib.sha256(arquivo.read_bytes()).hexdigest()
        for arquivo in sorted(arquivos)
    }


def criar_conta(tela, conta):
    tela.get_by_role("button", name="Quero criar uma conta", exact=True).click()
    tela.get_by_label("Nome", exact=True).fill(conta["nome"])
    tela.get_by_label("E-mail", exact=True).fill(conta["email"])
    tela.get_by_label("Senha", exact=True).fill(conta["senha"])
    with tela.expect_response(lambda r: r.url == f"{URL_API}/auth/cadastro" and r.request.method == "POST") as recebido:
        tela.get_by_role("button", name="Criar conta", exact=True).click()
    resposta = recebido.value
    assert resposta.status == 201, "O cadastro de conta deve retornar 201."
    dados = resposta.json()
    expect(tela.get_by_role("button", name="Nova ocorrência", exact=True)).to_be_visible()
    return dados["token"], dados["usuario"]


def entrar_conta(tela, conta):
    tela.get_by_label("E-mail", exact=True).fill(conta["email"])
    tela.get_by_label("Senha", exact=True).fill(conta["senha"])
    with tela.expect_response(lambda r: r.url == f"{URL_API}/auth/login" and r.request.method == "POST") as recebido:
        tela.get_by_role("button", name="Entrar", exact=True).click()
    assert recebido.value.status == 200, "O login válido deve retornar 200."
    expect(tela.get_by_role("button", name="Nova ocorrência", exact=True)).to_be_visible()
    return recebido.value.json()["token"]


def preencher_relato(tela, bairro, descricao):
    tela.get_by_label("Bairro", exact=True).fill(bairro)
    tela.get_by_label("Endereço", exact=True).fill("Rua fictícia de demonstração, próximo ao número 100")
    tela.get_by_label("Descrição", exact=True).fill(descricao)
    tela.get_by_role("radio", name="Média", exact=True).click()


def selecionar_arquivo(tela, arquivo):
    with tela.expect_file_chooser() as escolhido:
        tela.get_by_role("button", name="Anexar foto ou vídeo", exact=True).click()
    escolhido.value.set_files(str(arquivo))
    expect(tela.get_by_text(f"Arquivo selecionado: {arquivo.name}", exact=True)).to_be_visible()


def abrir_detalhes(tela, identificador):
    tela.get_by_role("button", name=re.compile(rf"^Abrir relato {identificador},")).click()
    expect(tela.get_by_text("Informações do relato", exact=False)).to_be_visible()


def verificar_imagem(tela):
    expect(tela.get_by_label("Imagem anexada pelo autor do relato", exact=True)).to_be_visible()
    tela.wait_for_function("Array.from(document.images).some(img => img.src.startsWith('blob:') && img.complete && img.naturalWidth > 0)")


def encerrar_gravacao(gravacoes, gravacao):
    if gravacao is not None:
        gravacao.fechar()
        gravacoes.remove(gravacao)


def executar(gravar=False):
    inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
    RESULTADOS.mkdir(exist_ok=True)
    # Uma execução com erro não pode conservar o relatório anterior como sucesso.
    (RESULTADOS / "resultado.json").unlink(missing_ok=True)
    if gravar:
        for nome in ("cliente-a.webm", "cliente-b.webm"):
            (RESULTADOS / nome).unlink(missing_ok=True)
    conferir_porta_livre()
    if not PYTHON_API.exists():
        raise RuntimeError("Crie backend/.venv e instale backend/requirements.txt primeiro.")
    with urlopen(URL_WEB, timeout=5) as resposta:
        assert resposta.status == 200, "Inicie o Expo web na porta 8081."
    casos, gravacoes = [], []
    processo, gravacao_a, gravacao_b = None, None, None
    # Contas fictícias só existem neste banco temporário; senhas não são publicadas.
    conta_a = {"nome": "Participante A — ensaio", "email": "participante-a@ensaio.test", "senha": secrets.token_urlsafe(18)}
    conta_b = {"nome": "Participante B — ensaio", "email": "participante-b@ensaio.test", "senha": secrets.token_urlsafe(18)}
    erros_js = []
    with tempfile.TemporaryDirectory() as pasta, (RESULTADOS / "api.log").open("w", encoding="utf-8") as log:
        banco, uploads = Path(pasta) / "teste.db", Path(pasta) / "uploads"
        try:
            processo = iniciar_api(banco, uploads, log)
            with sync_playwright() as p:
                opcoes = {"headless": True}
                if os.environ.get("CHROMIUM_PATH"):
                    opcoes["executable_path"] = os.environ["CHROMIUM_PATH"]
                browser = p.chromium.launch(**opcoes)
                configuracao = {"is_mobile": True, "has_touch": True, "locale": "pt-BR", "timezone_id": "America/Sao_Paulo"}
                primeiro = browser.new_context(viewport={"width": 390, "height": 844}, geolocation=GPS_SIMULADO, permissions=["geolocation"], **configuracao)
                # O mapa é exercitado sem depender de um serviço externo no teste.
                # Os pontos e fallback são reais; os tiles ficam deliberadamente indisponíveis.
                primeiro.route("https://tile.openstreetmap.org/**", lambda rota: rota.abort())
                tela = primeiro.new_page()
                tela.on("pageerror", lambda erro: erros_js.append(str(erro)))
                tela.goto(URL_WEB)
                expect(tela.get_by_role("button", name="Entrar", exact=True)).to_be_visible(timeout=60000)
                assert requisitar_api("/ocorrencias")[0] == 401
                capturar(tela, "00-login.png", False)
                casos.append("Acesso sem sessão exige login e API recusa consulta anônima")

                tela.get_by_label("E-mail", exact=True).fill("inexistente@ensaio.test")
                tela.get_by_label("Senha", exact=True).fill(secrets.token_urlsafe(18))
                with tela.expect_response(lambda r: r.url == f"{URL_API}/auth/login") as recusado:
                    tela.get_by_role("button", name="Entrar", exact=True).click()
                assert recusado.value.status == 401
                expect(tela.get_by_text("E-mail ou senha incorretos.", exact=True)).to_be_visible()
                casos.append("Login inválido apresenta mensagem sem conceder acesso")

                token_a, usuario_a = criar_conta(tela, conta_a)
                expect(tela.get_by_text("Nenhuma ocorrência cadastrada.", exact=True)).to_be_visible()
                assert consultar("/ocorrencias", token_a) == []
                casos.append("Cadastro de conta A inicia sessão e consulta lista vazia")
                if gravar:
                    # As gravações começam depois do acesso: não capturam credenciais.
                    from gravacao import Gravacao
                    gravacao_a = Gravacao(tela, RESULTADOS / "cliente-a.webm")
                    gravacoes.append(gravacao_a)
                capturar(tela, "00-lista-vazia.png", gravar)

                tela.get_by_role("button", name="Nova ocorrência", exact=True).click()
                tela.get_by_role("button", name="Salvar", exact=True).click()
                expect(tela.get_by_text("Preencha bairro, endereço e descrição.", exact=True)).to_be_visible()
                assert consultar("/ocorrencias", token_a) == []
                preencher_relato(tela, "Centro — foto", "Relato fictício com foto: água acumulada em parte da rua")
                tela.get_by_role("button", name="Usar minha localização", exact=True).click()
                expect(tela.get_by_text("Latitude:", exact=False)).to_contain_text("-23.550520")
                selecionar_arquivo(tela, FIXTURES / "foto-teste.png")
                capturar(tela, "01-cadastro.png", gravar)
                casos.append("Formulário valida obrigatórios e recebe GPS simulado e foto PNG")

                def falhar_envio(rota):
                    rota.abort() if rota.request.method == "POST" else rota.continue_()
                tela.route("**/ocorrencias", falhar_envio)
                tela.get_by_role("button", name="Salvar", exact=True).click()
                expect(tela.get_by_text("Não foi possível acessar a API.", exact=False)).to_be_visible()
                expect(tela.get_by_label("Bairro", exact=True)).to_have_value("Centro — foto")
                expect(tela.get_by_text("Arquivo selecionado: foto-teste.png", exact=True)).to_be_visible()
                expect(tela.get_by_text("Latitude:", exact=False)).to_contain_text("-23.550520")
                assert consultar("/ocorrencias", token_a) == []
                capturar(tela, "01b-falha-envio.png", gravar)
                tela.unroute("**/ocorrencias", falhar_envio)
                casos.append("Falha de rede preserva texto, coordenadas e anexo sem criar registro")

                pendentes = []
                def segurar_cadastro(rota):
                    pendentes.append(rota) if rota.request.method == "POST" else rota.continue_()
                tela.route("**/ocorrencias", segurar_cadastro)
                tela.get_by_role("button", name="Salvar", exact=True).click()
                salvando = tela.get_by_role("button", name="Salvando…", exact=True)
                expect(salvando).to_be_disabled()
                salvando.evaluate("el => { el.click(); el.click(); }")
                assert len(pendentes) == 1, "Toques repetidos não podem gerar mais de um envio."
                pendentes[0].continue_()
                expect(tela.get_by_text("Centro — foto", exact=True)).to_be_visible()
                tela.unroute("**/ocorrencias", segurar_cadastro)
                registros = consultar("/ocorrencias", token_a)
                assert len(registros) == 1
                foto = registros[0]
                id_foto = foto["id"]
                assert foto["autor_id"] == usuario_a["id"] and foto["pode_alterar"] is True
                assert abs(foto["latitude"] - GPS_SIMULADO["latitude"]) < 0.000001
                assert abs(foto["longitude"] - GPS_SIMULADO["longitude"]) < 0.000001
                assert len(foto["anexos"]) == 1 and foto["anexos"][0]["tipo"] == "imagem"
                caminho_foto = foto["anexos"][0]["url"]
                assert requisitar_api(caminho_foto)[0] == 401
                assert consultar(caminho_foto, token_a).startswith(b"\x89PNG")
                casos.append("Multipart cria um único relato com autoria, GPS e imagem privada")

                tela.get_by_role("tab", name="Mapa", exact=True).click()
                expect(tela.get_by_label("Mapa dos relatos com localização", exact=True)).to_be_visible()
                expect(tela.locator(".leaflet-interactive")).to_have_count(1)
                expect(tela.get_by_text("Não foi possível carregar o mapa base.", exact=False)).to_be_visible()
                expect(tela.get_by_role("button", name=f"Abrir relato {id_foto} no mapa, Centro — foto", exact=True)).to_be_visible()
                capturar(tela, "02-mapa.png", gravar)
                tela.get_by_role("tab", name="Lista", exact=True).click()
                casos.append("Mapa renderiza ponto salvo e oferece lista quando tiles são bloqueados no teste")

                segundo = browser.new_context(viewport={"width": 412, "height": 915}, **configuracao)
                segundo.route("https://tile.openstreetmap.org/**", lambda rota: rota.abort())
                outra = segundo.new_page()
                outra.on("pageerror", lambda erro: erros_js.append(str(erro)))
                outra.goto(URL_WEB)
                expect(outra.get_by_role("button", name="Entrar", exact=True)).to_be_visible(timeout=60000)
                token_b, usuario_b = criar_conta(outra, conta_b)
                assert usuario_b["id"] != usuario_a["id"]
                if gravar:
                    gravacao_b = Gravacao(outra, RESULTADOS / "cliente-b.webm")
                    gravacoes.append(gravacao_b)
                abrir_detalhes(outra, id_foto)
                verificar_imagem(outra)
                expect(outra.get_by_role("button", name="Marcar como resolvido", exact=True)).to_have_count(0)
                expect(outra.get_by_text("Somente o autor deste relato pode alterar a situação.", exact=False)).to_be_visible()
                assert requisitar_api(f"/ocorrencias/{id_foto}/situacao", token_b, "PATCH", {"situacao": "resolvido"})[0] == 403
                capturar(outra, "02-detalhes.png", gravar)
                casos.append("Conta B consulta imagem autenticada e é impedida de resolver relato de A")

                abrir_detalhes(tela, id_foto)
                verificar_imagem(tela)
                tela.get_by_role("button", name="Marcar como resolvido", exact=True).click()
                expect(tela.get_by_text("Resolvido", exact=True)).to_be_visible()
                assert consultar(f"/ocorrencias/{id_foto}", token_a)["situacao"] == "resolvido"
                capturar(tela, "02b-resolvido.png", gravar)
                outra.get_by_role("button", name="Voltar", exact=True).click()
                outra.get_by_role("button", name="Atualizar", exact=True).click()
                expect(outra.get_by_text("Resolvido", exact=True)).to_be_visible()
                capturar(outra, "03-lista.png", gravar)
                casos.append("Somente A resolve seu relato e B recebe a alteração após atualizar")
                encerrar_gravacao(gravacoes, gravacao_b)

                tela.get_by_role("button", name="Voltar", exact=True).click()
                tela.get_by_role("button", name="Nova ocorrência", exact=True).click()
                preencher_relato(tela, "Centro — vídeo", "Vídeo fictício e sintético usado apenas no teste acadêmico")
                selecionar_arquivo(tela, FIXTURES / "video-teste.mp4")
                tela.get_by_role("button", name="Salvar", exact=True).click()
                expect(tela.get_by_text("Centro — vídeo", exact=True)).to_be_visible()
                video_relato = consultar("/ocorrencias", token_a)[0]
                assert video_relato["anexos"][0]["tipo"] == "video"
                assert video_relato["latitude"] is None and video_relato["longitude"] is None
                abrir_detalhes(tela, video_relato["id"])
                expect(tela.get_by_text("Vídeo do relato", exact=True)).to_be_visible()
                video = tela.locator("video")
                expect(video).to_have_count(1)
                tela.wait_for_function("document.querySelector('video')?.readyState >= 1")
                video.evaluate("async v => { v.muted = true; await v.play(); }")
                tela.wait_for_function("document.querySelector('video')?.currentTime > 0")
                assert video.evaluate("v => v.videoWidth") == 160
                video.evaluate("v => v.pause()")
                capturar(tela, "03b-video.png", gravar)
                caminho_video = video_relato["anexos"][0]["url"]
                assert requisitar_api(caminho_video)[0] == 401
                casos.append("Vídeo MP4 real é enviado, protegido e reproduzido sem exigir GPS")
                encerrar_gravacao(gravacoes, gravacao_a)

                # Os testes de autenticação não são gravados e não salvam respostas de login.
                tela.get_by_role("button", name="Sair", exact=True).click()
                expect(tela.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
                assert requisitar_api("/auth/me", token_a)[0] == 401
                capturar(tela, "06-logout.png", False)
                token_a = entrar_conta(tela, conta_a)
                assert consultar("/auth/me", token_a)["usuario"]["id"] == usuario_a["id"]
                casos.append("Sair revoga o token e novo login recupera a conta do autor")

                outra.reload()
                expect(outra.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
                token_b = entrar_conta(outra, conta_b)
                expect(outra.get_by_text("Centro — foto", exact=True)).to_be_visible()
                casos.append("Recarregar a versão web exige novo login sem credencial em armazenamento local")

                parar_api(processo)
                processo = None
                tela.get_by_role("button", name="Atualizar", exact=True).click()
                expect(tela.get_by_text("Não foi possível acessar a API.", exact=False)).to_be_visible()
                expect(tela.get_by_role("button", name="Sair", exact=True)).to_be_visible()
                capturar(tela, "04-api-desligada.png", False)
                casos.append("API desligada mostra erro e mantém a sessão para nova tentativa")
                processo = iniciar_api(banco, uploads, log)
                tela.get_by_role("button", name="Tentar novamente", exact=True).click()
                expect(tela.get_by_text("Centro — foto", exact=True)).to_be_visible()
                assert len(consultar("/ocorrencias", token_a)) == 2
                assert consultar(f"/ocorrencias/{id_foto}", token_b)["situacao"] == "resolvido"
                assert consultar(caminho_foto, token_b).startswith(b"\x89PNG")
                assert consultar(caminho_video, token_a)[4:8] == b"ftyp"
                capturar(tela, "05-recuperacao.png", False)
                casos.append("Reiniciar API preserva contas, sessões, situação, GPS e os dois arquivos")

                assert requisitar_api("/auth/logout", token_a, "POST")[0] == 200
                tela.get_by_role("button", name="Atualizar", exact=True).click()
                expect(tela.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
                expect(tela.get_by_text("Sua sessão expirou. Entre novamente.", exact=True)).to_be_visible()
                casos.append("Sessão revogada no servidor retorna à tela de acesso ao receber HTTP 401")
                assert not erros_js, f"Erros de JavaScript: {erros_js}"
                primeiro.close()
                segundo.close()
                browser.close()
        finally:
            for gravacao in gravacoes:
                try:
                    gravacao.fechar()
                except Exception as erro:
                    log.write(f"Falha ao finalizar vídeo de apoio: {erro}\n")
            parar_api(processo)

    relatorio = {
        "versao": 2, "resultado": "passou", "inicio_utc": inicio,
        "fim_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "casos": casos, "erros_javascript": len(erros_js),
        "videos": ["cliente-a.webm", "cliente-b.webm"] if gravar else [],
        "sha256_codigo": identificar_codigo(),
        "limitacoes": [
            "Dados e contas fictícios em dois contextos isolados de Chromium; não são celulares físicos.",
            "Coordenadas fornecidas pelo simulador de geolocalização do navegador, sem teste de GPS real.",
            "Tiles OpenStreetMap deliberadamente bloqueados: valida pontos e fallback, não o mapa base online.",
            "SecureStore e mapas nativos do Expo Go exigem validação no aparelho.",
        ],
    }
    (RESULTADOS / "resultado.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gravar", action="store_true", help="Grava dois vídeos de apoio sem capturar credenciais.")
    executar(gravar=parser.parse_args().gravar)
