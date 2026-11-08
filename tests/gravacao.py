"""Gravação opcional de uma página Chromium com CDP e FFmpeg do sistema."""

import base64
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from playwright.sync_api import Page


class Gravacao:
    """Começa ao construir; chame fechar() antes de fechar a página/navegador."""

    def __init__(self, pagina: Page, caminho, fps=10):
        executavel = shutil.which("ffmpeg")
        if not executavel:
            raise RuntimeError("Gravação opcional requer FFmpeg instalado no sistema.")
        if not isinstance(fps, int) or fps < 1:
            raise ValueError("A taxa da gravação deve ser um inteiro positivo.")
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._fps, self._quadros = fps, 0
        self._frame = self._origem = self._inicio_real = self._sessao = self._processo = None
        self._erro, self._fechada = None, False
        self._ultimo_tempo = 0
        self._ultima_chegada = time.monotonic()
        self._log = tempfile.TemporaryFile()
        try:
            self._processo = subprocess.Popen(
                [executavel, "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "mjpeg", "-framerate", str(fps), "-i", "pipe:0", "-an",
                 "-c:v", "libvpx-vp9", "-deadline", "realtime", "-cpu-used", "8",
                 "-pix_fmt", "yuv420p", str(self.caminho)],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self._log,
            )
            self._sessao = pagina.context.new_cdp_session(pagina)
            self._sessao.on("Page.screencastFrame", self._receber_frame)
            tamanho = pagina.viewport_size or pagina.evaluate(
                "({width: innerWidth, height: innerHeight})"
            )
            self._sessao.send("Page.startScreencast", {
                "format": "jpeg", "quality": 70, "everyNthFrame": 1,
                "maxWidth": tamanho["width"], "maxHeight": tamanho["height"],
            })
        except Exception as erro:
            try:
                self.fechar()
            except Exception:
                pass
            raise RuntimeError(f"Não foi possível iniciar a gravação: {erro}") from erro

    def _escrever(self):
        self._processo.stdin.write(self._frame)
        self._quadros += 1

    def _completar_ate(self, tempo):
        # CDP envia quadros quando a tela muda. Repetições preservam as pausas.
        quantidade = int(max(0, tempo) * self._fps)
        while self._frame is not None and self._quadros < quantidade:
            self._escrever()
        return quantidade

    def _receber_frame(self, evento):
        try:
            if self._fechada or self._erro:
                return
            agora = time.monotonic()
            timestamp = evento.get("metadata", {}).get("timestamp")
            if self._inicio_real is None:
                self._inicio_real = agora
            if timestamp is not None and self._origem is None:
                self._origem = timestamp - (agora - self._inicio_real)
            tempo = timestamp - self._origem if timestamp is not None else agora - self._inicio_real
            tempo = max(self._ultimo_tempo, tempo)
            indice = self._completar_ate(tempo)
            self._frame = base64.b64decode(evento["data"])
            if self._quadros <= indice:
                self._escrever()
            self._ultimo_tempo, self._ultima_chegada = tempo, agora
        except Exception as erro:
            self._erro = str(erro)
        finally:
            # Cada evento precisa de ACK, mesmo se a codificação tiver falhado.
            try:
                self._sessao.send("Page.screencastFrameAck", {"sessionId": evento["sessionId"]})
            except Exception as erro:
                if not self._fechada:
                    self._erro = str(erro)

    def fechar(self):
        """Finaliza a tela estática, encerra recursos e devolve o Path do WebM."""
        if self._fechada:
            if self._erro:
                raise RuntimeError(f"Gravação não gerada corretamente: {self._erro}.")
            return self.caminho
        self._fechada = True
        if self._sessao is not None:
            try:
                self._sessao.send("Page.stopScreencast")
            except Exception:
                pass  # A página pode já ter fechado; o processo ainda será limpo.
            finally:
                try:
                    self._sessao.detach()
                except Exception:
                    pass
        try:
            if not self._erro:
                self._completar_ate(self._ultimo_tempo + time.monotonic() - self._ultima_chegada)
        except Exception as erro:
            self._erro = str(erro)
        finally:
            if self._processo is not None:
                try:
                    self._processo.stdin.close()
                except OSError:
                    pass
                try:
                    self._processo.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    self._processo.kill()
                    self._processo.wait(timeout=5)
                    self._erro = "FFmpeg excedeu o tempo para finalizar."
            self._log.seek(0)
            detalhes = self._log.read().decode("utf-8", errors="replace").strip()
            self._log.close()
        if (self._erro or self._processo is None or self._processo.returncode != 0
                or not self._quadros or not self.caminho.exists() or self.caminho.stat().st_size == 0):
            self._erro = self._erro or detalhes or "nenhum quadro recebido"
            raise RuntimeError(f"Gravação não gerada corretamente: {self._erro}.")
        return self.caminho
