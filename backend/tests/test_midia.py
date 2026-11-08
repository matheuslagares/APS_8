"""Valida anexos diretamente, com arquivos temporários e conteúdo fictício."""

from io import BytesIO
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from PIL.TiffImagePlugin import IFDRational
from werkzeug.datastructures import FileStorage

import midia
from midia import MidiaInvalida, apagar_arquivo, preparar_arquivo


# Vídeo sintético de dois quadros azuis. Os testes não executam FFmpeg.
VIDEO = Path(__file__).resolve().parent / "fixtures" / "curto.mp4"


def foto_em_memoria(formato="PNG", tamanho=(4, 4), cor=(12, 34, 56, 123), exif=None):
    saida = BytesIO()
    with Image.new("RGBA" if formato == "PNG" else "RGB", tamanho, cor) as foto:
        foto.save(saida, format=formato, **({"exif": exif} if exif is not None else {}))
    return saida.getvalue()


def caixa(tipo, conteudo=b""):
    return struct.pack(">I4s", len(conteudo) + 8, tipo) + conteudo


class MidiaTest(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name) / "uploads"

    def enviar(self, conteudo, nome="arquivo.jpg", mime="application/octet-stream"):
        arquivo = FileStorage(stream=BytesIO(conteudo), filename=nome, content_type=mime)
        try:
            return preparar_arquivo(arquivo, self.pasta)
        finally:
            arquivo.close()

    def conferir_rejeicao(self, conteudo, codigo, nome="arquivo.jpg"):
        antes = set(self.pasta.iterdir()) if self.pasta.exists() else set()
        with self.assertRaises(MidiaInvalida) as erro:
            self.enviar(conteudo, nome)
        self.assertEqual(erro.exception.status_code, codigo)
        depois = set(self.pasta.iterdir()) if self.pasta.exists() else set()
        self.assertEqual(depois, antes, "Rejeitar um anexo não deve criar arquivos.")

    def test_jpeg_corrige_orientacao_e_remove_exif_inclusive_gps(self):
        exif = Image.Exif()
        exif[274] = 6  # Rotação de 90 graus informada pela câmera.
        exif[270] = "Descrição fictícia que não deve ser publicada"
        exif[34853] = {
            1: "N", 2: (IFDRational(23), IFDRational(30), IFDRational(0)),
            3: "E", 4: (IFDRational(45), IFDRational(15), IFDRational(0)),
        }
        conteudo = foto_em_memoria("JPEG", tamanho=(5, 9), cor="red", exif=exif)
        with Image.open(BytesIO(conteudo)) as original:
            self.assertIn(34853, original.getexif())
        resultado = self.enviar(conteudo)
        self.assertEqual(resultado["tipo"], "imagem")
        self.assertEqual(resultado["mime_type"], "image/jpeg")
        with Image.open(self.pasta / resultado["nome_arquivo"]) as limpa:
            self.assertEqual(limpa.size, (9, 5))
            self.assertEqual(dict(limpa.getexif()), {})

    def test_png_preserva_transparencia_e_detecta_conteudo(self):
        resultado = self.enviar(foto_em_memoria(), nome="../../falso.svg", mime="text/html")
        self.assertEqual(resultado["tipo"], "imagem")
        self.assertEqual(resultado["mime_type"], "image/png")
        self.assertRegex(resultado["nome_arquivo"], r"^[a-f0-9]{32}\.png$")
        caminho = self.pasta / resultado["nome_arquivo"]
        self.assertEqual(resultado["tamanho"], caminho.stat().st_size)
        with Image.open(caminho) as foto:
            self.assertEqual(foto.mode, "RGBA")
            self.assertEqual(foto.getpixel((0, 0)), (12, 34, 56, 123))

    def test_nomes_uuid_nao_reutilizam_nome_enviado(self):
        primeira = self.enviar(foto_em_memoria(), nome="minha-foto.jpg")
        segunda = self.enviar(foto_em_memoria(), nome="minha-foto.jpg")
        self.assertNotEqual(primeira["nome_arquivo"], segunda["nome_arquivo"])
        self.assertEqual(len(list(self.pasta.iterdir())), 2)
        self.assertFalse(any(caminho.suffix == ".tmp" for caminho in self.pasta.iterdir()))

    def test_jpeg_falso_e_jpeg_truncado_sao_rejeitados(self):
        self.conferir_rejeicao(b"\xff\xd8isto-nao-e-uma-foto", 400)
        self.conferir_rejeicao(foto_em_memoria("JPEG", cor="blue")[:30], 400)

    def test_svg_e_html_nao_sao_imagens_aceitas(self):
        self.conferir_rejeicao(b'<svg xmlns="http://www.w3.org/2000/svg"/>', 415)
        self.conferir_rejeicao(b"<html>arquivo falso</html>", 415)

    def test_vazio_ou_ausente_sao_rejeitados(self):
        self.conferir_rejeicao(b"", 400)
        with self.assertRaises(MidiaInvalida) as erro:
            preparar_arquivo(None, self.pasta)
        self.assertEqual(erro.exception.status_code, 400)
        self.assertFalse(self.pasta.exists())

    def test_arquivo_maior_que_vinte_mib_e_rejeitado(self):
        self.conferir_rejeicao(b"a" * (20 * 1024 * 1024 + 1), 413)

    def test_limite_de_pixels_rejeita_bomba_de_descompressao(self):
        # A foto é criada antes do limite reduzido para testar com pouca memória.
        conteudo = foto_em_memoria(tamanho=(11, 10))
        with patch.object(midia, "MAX_PIXELS", 100), patch.object(Image, "MAX_IMAGE_PIXELS", 100):
            self.conferir_rejeicao(conteudo, 413)

    def test_video_mp4_real_e_aceito_sem_confiar_na_extensao(self):
        conteudo = VIDEO.read_bytes()
        resultado = self.enviar(conteudo, nome="foto.jpg", mime="image/jpeg")
        self.assertEqual(resultado["tipo"], "video")
        self.assertEqual(resultado["mime_type"], "video/mp4")
        self.assertRegex(resultado["nome_arquivo"], r"^[a-f0-9]{32}\.mp4$")
        self.assertEqual(resultado["tamanho"], len(conteudo))
        self.assertEqual((self.pasta / resultado["nome_arquivo"]).read_bytes(), conteudo)

    def test_video_mp4_truncado_e_tamanhos_invalidos_sao_rejeitados(self):
        self.conferir_rejeicao(VIDEO.read_bytes()[:-4], 400, nome="video.mp4")
        self.conferir_rejeicao(struct.pack(">I4s", 4, b"ftyp") + b"isom", 400)
        self.conferir_rejeicao(struct.pack(">I4sQ", 1, b"ftyp", 1000) + b"isom", 400)
        self.conferir_rejeicao(struct.pack(">I4s", 1, b"ftyp") + b"isom", 400)

    def test_tres_caixas_vazias_nao_representam_video_mp4(self):
        conteudo = caixa(b"ftyp", b"isom" + b"\0" * 4) + caixa(b"moov") + caixa(b"mdat")
        self.conferir_rejeicao(conteudo, 400)

    def test_mp4_sem_trilha_de_video_e_rejeitado(self):
        conteudo = VIDEO.read_bytes()
        inicio_handler = conteudo.index(b"hdlr") + 12
        self.assertEqual(conteudo[inicio_handler:inicio_handler + 4], b"vide")
        somente_audio = conteudo[:inicio_handler] + b"soun" + conteudo[inicio_handler + 4:]
        self.conferir_rejeicao(somente_audio, 400)

    def test_mp4_sem_trilhas_e_rejeitado(self):
        conteudo = (
            caixa(b"ftyp", b"isom" + b"\0" * 4)
            + caixa(b"moov", caixa(b"mvhd", b"\0" * 100))
            + caixa(b"mdat", b"dado ficticio")
        )
        self.conferir_rejeicao(conteudo, 400)

    def test_falha_ao_mover_arquivo_limpa_temporario(self):
        with patch.object(Path, "replace", side_effect=OSError("falha simulada")):
            with self.assertRaisesRegex(OSError, "falha simulada"):
                self.enviar(foto_em_memoria())
        self.assertEqual(list(self.pasta.iterdir()), [])

    def test_remocao_segura_e_idempotente(self):
        resultado = self.enviar(foto_em_memoria())
        nome = resultado["nome_arquivo"]
        apagar_arquivo(self.pasta, nome)
        apagar_arquivo(self.pasta, nome)
        self.assertEqual(list(self.pasta.iterdir()), [])
        for inseguro in ("../fora.jpg", "/tmp/fora.jpg", "subpasta/foto.jpg", "foto.jpg", None):
            with self.subTest(nome=inseguro):
                with self.assertRaises(ValueError):
                    apagar_arquivo(self.pasta, inseguro)

    def test_remocao_rejeita_link_para_fora_da_pasta(self):
        self.pasta.mkdir()
        externo = Path(self.temporario.name) / "externo.jpg"
        externo.write_bytes(b"arquivo ficticio a preservar")
        nome = "a" * 32 + ".jpg"
        try:
            (self.pasta / nome).symlink_to(externo)
        except OSError as erro:
            self.skipTest(f"Sistema sem permissão para criar links simbólicos: {erro}")
        with self.assertRaises(ValueError):
            apagar_arquivo(self.pasta, nome)
        self.assertEqual(externo.read_bytes(), b"arquivo ficticio a preservar")


if __name__ == "__main__":
    unittest.main()
