"""Teste integrado opcional: Expo web + API real + SQLite temporário.

Execute o Expo web na porta 8081 antes deste arquivo (ver documentacao/TESTES.md).
Dois contextos de navegador representam clientes independentes, não celulares reais.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


RAIZ = Path(__file__).resolve().parents[1]
PYTHON_API = RAIZ / "backend" / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
URL_WEB = "http://127.0.0.1:8081"
URL_API = "http://127.0.0.1:5000"
RESULTADOS = RAIZ / "test-results"


def consultar(caminho):
    with urlopen(f"{URL_API}{caminho}", timeout=3) as resposta:
        return json.load(resposta)


def conferir_porta_livre():
    # Nunca encerra o servidor de outra pessoa nem grava no banco de demonstração.
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", 5000)) == 0:
            raise RuntimeError("Pare sua API na porta 5000 antes do teste isolado.")


def iniciar_api(banco, log):
    codigo = (
        "from app import create_app; from database import inicializar_banco; "
        f"banco={str(banco)!r}; inicializar_banco(banco); "
        "create_app({'DATABASE': banco}).run(host='127.0.0.1', port=5000, debug=False)"
    )
    processo = subprocess.Popen(
        [str(PYTHON_API), "-c", codigo], cwd=RAIZ / "backend", stdout=log, stderr=log,
    )
    try:
        for _ in range(50):
            if processo.poll() is not None:
                raise RuntimeError("A API de teste não iniciou; consulte test-results/api.log.")
            try:
                if consultar("/saude") == {"status": "ok"}:
                    return processo
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("Tempo esgotado ao iniciar a API de teste.")
    except BaseException:
        # Também encerra o subprocesso se o startup falhar ou for interrompido.
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
    # A pausa serve apenas à leitura do vídeo; os testes usam condições de espera.
    if gravar:
        tela.wait_for_timeout(1200)


def identificar_codigo():
    """Os hashes identificam o código testado, mesmo antes de criar um commit."""
    arquivos = [RAIZ / "mobile" / "App.js", Path(__file__).resolve(), RAIZ / "tests" / "gravacao.py"]
    arquivos += list((RAIZ / "mobile" / "src").rglob("*.js"))
    arquivos += list((RAIZ / "backend").glob("*.py"))
    arquivos += [RAIZ / "backend" / "schema.sql", RAIZ / "mobile" / "package-lock.json"]
    return {
        str(arquivo.relative_to(RAIZ)): hashlib.sha256(arquivo.read_bytes()).hexdigest()
        for arquivo in sorted(arquivos)
    }


def executar(gravar=False):
    inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
    RESULTADOS.mkdir(exist_ok=True)
    # Um erro nesta execução não pode deixar um relatório anterior de sucesso.
    (RESULTADOS / "resultado.json").unlink(missing_ok=True)
    if gravar:
        for nome in ("cliente-a.webm", "cliente-b.webm"):
            (RESULTADOS / nome).unlink(missing_ok=True)
    conferir_porta_livre()
    if not PYTHON_API.exists():
        raise RuntimeError("Crie backend/.venv e instale backend/requirements.txt primeiro.")
    # A URL do app deve usar o fallback web local, sem um .env apontando para outra API.
    with urlopen(URL_WEB, timeout=5) as resposta:
        assert resposta.status == 200, "Inicie o Expo web na porta 8081."
    casos = []
    processo = None
    gravacoes = []
    with tempfile.TemporaryDirectory() as pasta, (RESULTADOS / "api.log").open("w", encoding="utf-8") as log:
        banco = Path(pasta) / "teste.db"
        try:
            processo = iniciar_api(banco, log)
            with sync_playwright() as p:
                opcoes = {"headless": True}
                if os.environ.get("CHROMIUM_PATH"):
                    opcoes["executable_path"] = os.environ["CHROMIUM_PATH"]
                browser = p.chromium.launch(**opcoes)
                # Cookies/armazenamento isolados simulam duas instalações diferentes.
                # O ensaio usa o idioma e o fuso da demonstração brasileira.
                primeiro = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="pt-BR", timezone_id="America/Sao_Paulo")
                tela = primeiro.new_page()
                if gravar:
                    # O FFmpeg do sistema grava os quadros Chromium sem baixar binários.
                    from gravacao import Gravacao
                    gravacoes.append(Gravacao(tela, RESULTADOS / "cliente-a.webm"))
                erros_js = []
                tela.on("pageerror", lambda erro: erros_js.append(str(erro)))
                tela.goto(URL_WEB)
                expect(tela.get_by_text("Nenhuma ocorrência cadastrada.", exact=True)).to_be_visible(timeout=60000)
                assert consultar("/ocorrencias") == []
                casos.append("Lista vazia com API real")
                tela.screenshot(path=str(RESULTADOS / "00-lista-vazia.png"), full_page=True)
                pausar_gravacao(tela, gravar)

                tela.get_by_role("button", name="Nova ocorrência", exact=True).click()
                tela.get_by_role("button", name="Salvar", exact=True).click()
                assert consultar("/ocorrencias") == [], "Formulário vazio não deve cadastrar."
                tela.get_by_label("Bairro", exact=True).fill("Centro")
                tela.get_by_label("Endereço", exact=True).fill("Rua de exemplo, próximo ao número 100")
                tela.get_by_label("Descrição", exact=True).fill("Água acumulada bloqueando parte da rua")
                tela.get_by_role("radio", name="Média", exact=True).click()
                tela.screenshot(path=str(RESULTADOS / "01-cadastro.png"), full_page=True)
                casos.append("Validação do formulário e preenchimento")
                pausar_gravacao(tela, gravar)

                def falhar_envio(rota):
                    if rota.request.method == "POST":
                        rota.abort()
                    else:
                        rota.continue_()
                tela.route("**/ocorrencias", falhar_envio)
                tela.get_by_role("button", name="Salvar", exact=True).click()
                expect(tela.get_by_text("Não foi possível acessar a API.", exact=False)).to_be_visible()
                expect(tela.get_by_label("Bairro", exact=True)).to_have_value("Centro")
                expect(tela.get_by_label("Descrição", exact=True)).to_have_value("Água acumulada bloqueando parte da rua")
                assert consultar("/ocorrencias") == []
                tela.screenshot(path=str(RESULTADOS / "01b-falha-envio.png"), full_page=True)
                pausar_gravacao(tela, gravar)
                tela.unroute("**/ocorrencias", falhar_envio)
                casos.append("Falha de rede simulada preserva campos e permite nova tentativa")

                # Segura a resposta para verificar que o botão bloqueia cliques repetidos.
                pendentes = []
                def segurar_cadastro(rota):
                    if rota.request.method == "POST":
                        pendentes.append(rota)
                    else:
                        rota.continue_()
                tela.route("**/ocorrencias", segurar_cadastro)
                salvar = tela.get_by_role("button", name="Salvar", exact=True)
                salvar.click()
                expect(tela.get_by_role("button", name="Salvando…", exact=True)).to_be_disabled()
                tela.get_by_role("button", name="Salvando…", exact=True).evaluate("el => { el.click(); el.click(); }")
                assert len(pendentes) == 1, "Deve haver apenas um POST pendente."
                pendentes[0].continue_()
                expect(tela.get_by_text("Centro", exact=True)).to_be_visible()
                tela.unroute("**/ocorrencias", segurar_cadastro)
                registros = consultar("/ocorrencias")
                assert len(registros) == 1
                identificador = registros[0]["id"]
                casos.append("Cadastro persistido e bloqueio de envio duplicado")
                pausar_gravacao(tela, gravar)

                segundo = browser.new_context(viewport={"width": 412, "height": 915}, is_mobile=True, has_touch=True, locale="pt-BR", timezone_id="America/Sao_Paulo")
                outra = segundo.new_page()
                if gravar:
                    gravacoes.append(Gravacao(outra, RESULTADOS / "cliente-b.webm"))
                outra.on("pageerror", lambda erro: erros_js.append(str(erro)))
                outra.goto(URL_WEB)
                expect(outra.get_by_text("Centro", exact=True)).to_be_visible(timeout=60000)
                pausar_gravacao(outra, gravar)
                outra.get_by_text("Centro", exact=True).click()
                expect(outra.get_by_text("Água acumulada bloqueando parte da rua", exact=True)).to_be_visible()
                outra.screenshot(path=str(RESULTADOS / "02-detalhes.png"), full_page=True)
                pausar_gravacao(outra, gravar)
                outra.get_by_role("button", name="Marcar como resolvido", exact=True).click()
                expect(outra.get_by_text("Resolvido", exact=True)).to_be_visible()
                assert consultar(f"/ocorrencias/{identificador}")["situacao"] == "resolvido"
                outra.screenshot(path=str(RESULTADOS / "02b-resolvido.png"), full_page=True)
                pausar_gravacao(outra, gravar)
                outra.get_by_role("button", name="Voltar", exact=True).click()
                tela.get_by_role("button", name="Atualizar", exact=True).click()
                expect(tela.get_by_text("Resolvido", exact=True)).to_be_visible()
                tela.screenshot(path=str(RESULTADOS / "03-lista.png"), full_page=True)
                casos.append("Segundo cliente consulta e resolve; primeiro atualiza manualmente")
                pausar_gravacao(tela, gravar)

                parar_api(processo)
                processo = None
                tela.get_by_role("button", name="Atualizar", exact=True).click()
                expect(tela.get_by_text("Não foi possível acessar a API.", exact=False)).to_be_visible()
                casos.append("API desligada apresenta mensagem e opção de tentar novamente")
                tela.screenshot(path=str(RESULTADOS / "04-api-desligada.png"), full_page=True)
                pausar_gravacao(tela, gravar)
                processo = iniciar_api(banco, log)
                tela.get_by_role("button", name="Tentar novamente", exact=True).click()
                expect(tela.get_by_text("Resolvido", exact=True)).to_be_visible()
                assert consultar(f"/ocorrencias/{identificador}")["situacao"] == "resolvido"
                casos.append("API reiniciada preserva dados e interface recupera consulta")
                tela.screenshot(path=str(RESULTADOS / "05-recuperacao.png"), full_page=True)
                pausar_gravacao(tela, gravar)
                assert not erros_js, f"Erros de JavaScript: {erros_js}"
                # Finaliza a captura antes de fechar as páginas que fornecem quadros.
                for gravacao in gravacoes:
                    gravacao.fechar()
                gravacoes.clear()
                primeiro.close()
                segundo.close()
                browser.close()
        finally:
            # Também recolhe os processos de vídeo se alguma verificação falhar.
            for gravacao in gravacoes:
                try:
                    gravacao.fechar()
                except Exception as erro:
                    log.write(f"Falha ao finalizar vídeo de apoio: {erro}\n")
            parar_api(processo)

    relatorio = {
        "resultado": "passou", "inicio_utc": inicio,
        "fim_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "casos": casos, "erros_javascript": len(erros_js),
        "videos": ["cliente-a.webm", "cliente-b.webm"] if gravar else [],
        "sha256_codigo": identificar_codigo(),
        "limite": "Dados fictícios em navegadores isolados; não substitui dois celulares físicos.",
    }
    (RESULTADOS / "resultado.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gravar", action="store_true", help="Grava dois vídeos de apoio em test-results/.")
    executar(gravar=parser.parse_args().gravar)
