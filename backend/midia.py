"""Valida conteúdo de anexos e guarda nomes privados, definidos pelo servidor."""

from io import BytesIO
from pathlib import Path
import re
import struct
from uuid import uuid4
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_ARQUIVO = 20 * 1024 * 1024
MAX_PIXELS = 20_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class MidiaInvalida(Exception):
    def __init__(self, mensagem, status_code=400):
        super().__init__(mensagem)
        self.status_code = status_code


def _foto_limpa(conteudo):
    """A extensão e o MIME enviados pelo cliente não comprovam o formato real."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(conteudo)) as foto:
                formato = foto.format
                if formato not in ("JPEG", "PNG"):
                    raise MidiaInvalida("Envie uma foto JPEG ou PNG.", 415)
                if foto.width * foto.height > MAX_PIXELS:
                    raise MidiaInvalida("A foto deve ter no máximo 20 milhões de pixels.", 413)
                if getattr(foto, "is_animated", False):
                    raise MidiaInvalida("Envie uma foto estática JPEG ou PNG.", 415)
                foto.verify()
            with Image.open(BytesIO(conteudo)) as foto:
                foto.load()
                with ImageOps.exif_transpose(foto) as orientada:
                    modo = "RGB" if formato == "JPEG" else "RGBA"
                    with orientada.convert(modo) as convertida:
                        # Uma imagem nova elimina EXIF, GPS e os demais metadados.
                        with Image.new(modo, convertida.size) as limpa:
                            limpa.paste(convertida)
                            saida = BytesIO()
                            limpa.save(saida, format=formato, **({"quality": 85} if formato == "JPEG" else {}))
                            resultado = saida.getvalue()
        if len(resultado) > MAX_ARQUIVO:
            raise MidiaInvalida("A foto processada excede o limite de 20 MiB.", 413)
        return resultado, ("jpg", "image/jpeg") if formato == "JPEG" else ("png", "image/png")
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as erro:
        raise MidiaInvalida("A foto deve ter no máximo 20 milhões de pixels.", 413) from erro
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as erro:
        raise MidiaInvalida("O conteúdo da foto está inválido ou incompleto.") from erro


def _caixas(conteudo, inicio, fim, orcamento):
    """Lê os tamanhos de boxes ISO BMFF sem sair dos limites do arquivo/pai."""
    posicao = inicio
    while posicao < fim:
        orcamento[0] += 1
        if fim - posicao < 8 or orcamento[0] > 10_000:
            raise MidiaInvalida("A estrutura do vídeo MP4 está inválida.")
        tamanho, tipo = struct.unpack_from(">I4s", conteudo, posicao)
        cabecalho = 8
        if tamanho == 1:
            if fim - posicao < 16:
                raise MidiaInvalida("O cabeçalho do vídeo MP4 está incompleto.")
            tamanho = struct.unpack_from(">Q", conteudo, posicao + 8)[0]
            cabecalho = 16
        elif tamanho == 0:
            tamanho = fim - posicao
        if tamanho < cabecalho or tamanho > fim - posicao:
            raise MidiaInvalida("O tamanho de um bloco do vídeo MP4 está inválido.")
        yield tipo, posicao + cabecalho, posicao + tamanho
        posicao += tamanho


def _validar_mp4(conteudo):
    orcamento = [0]
    caixas = list(_caixas(conteudo, 0, len(conteudo), orcamento))
    tipos = [tipo for tipo, _, _ in caixas]
    if tipos.count(b"ftyp") != 1 or tipos.count(b"moov") != 1 or b"mdat" not in tipos:
        raise MidiaInvalida("Envie uma foto JPEG/PNG ou um vídeo MP4 válido.", 415)
    inicio, fim = next((inicio, fim) for tipo, inicio, fim in caixas if tipo == b"ftyp")
    if fim - inicio < 8 or (fim - inicio) % 4:
        raise MidiaInvalida("A identificação do vídeo MP4 está inválida.")
    marcas = {conteudo[inicio:inicio + 4]}
    marcas.update(conteudo[pos:pos + 4] for pos in range(inicio + 8, fim, 4))
    permitidas = {
        b"isom", b"iso2", b"iso3", b"iso4", b"iso5", b"iso6", b"iso7", b"iso8", b"iso9",
        b"mp41", b"mp42", b"avc1", b"hvc1", b"hev1", b"M4V ", b"M4VH", b"M4VP", b"dash",
    }
    if not marcas.intersection(permitidas):
        raise MidiaInvalida("O arquivo não identifica um vídeo MP4 compatível.", 415)
    if not any(tipo == b"mdat" and fim > inicio for tipo, inicio, fim in caixas):
        raise MidiaInvalida("O vídeo MP4 não contém dados de mídia.")

    inicio, fim = next((inicio, fim) for tipo, inicio, fim in caixas if tipo == b"moov")
    filhos = list(_caixas(conteudo, inicio, fim, orcamento))
    cabecalhos = [(ini, fim) for tipo, ini, fim in filhos if tipo == b"mvhd"]
    if len(cabecalhos) != 1:
        raise MidiaInvalida("O vídeo MP4 não contém um cabeçalho de filme válido.")
    ini, fim = cabecalhos[0]
    versao = conteudo[ini] if fim > ini else -1
    if versao not in (0, 1) or fim - ini < (100 if versao == 0 else 112):
        raise MidiaInvalida("O cabeçalho de filme MP4 está incompleto.")
    tem_video = False
    for tipo, inicio, fim in filhos:
        if tipo != b"trak":
            continue
        trilha = list(_caixas(conteudo, inicio, fim, orcamento))
        for tipo, inicio, fim in trilha:
            if tipo != b"mdia":
                continue
            for tipo, inicio, fim in _caixas(conteudo, inicio, fim, orcamento):
                if tipo == b"hdlr":
                    if fim - inicio < 24:
                        raise MidiaInvalida("O cabeçalho de mídia MP4 está incompleto.")
                    tem_video = tem_video or conteudo[inicio + 8:inicio + 12] == b"vide"
    if not tem_video:
        raise MidiaInvalida("O MP4 deve conter uma trilha de vídeo.")
    # Verificação estrutural; não substitui decodificação ou análise antivírus.


def preparar_arquivo(arquivo, upload_folder):
    """Valida um FileStorage e retorna metadados após salvar com nome UUID."""
    if arquivo is None:
        raise MidiaInvalida("Selecione uma foto ou um vídeo.")
    conteudo = arquivo.stream.read(MAX_ARQUIVO + 1)
    if not conteudo:
        raise MidiaInvalida("O arquivo está vazio.")
    if len(conteudo) > MAX_ARQUIVO:
        raise MidiaInvalida("O arquivo deve ter no máximo 20 MiB.", 413)
    if conteudo.startswith((b"\xff\xd8", b"\x89PNG\r\n\x1a\n")):
        conteudo, (extensao, mime) = _foto_limpa(conteudo)
        tipo = "imagem"
    else:
        # Texto, SVG e arquivos de outros formatos não entram pelo MIME declarado.
        if len(conteudo) < 8 or conteudo[4:8] not in (b"ftyp", b"free", b"skip", b"wide"):
            raise MidiaInvalida("Envie uma foto JPEG/PNG ou um vídeo MP4.", 415)
        _validar_mp4(conteudo)
        extensao, mime, tipo = "mp4", "video/mp4", "video"

    pasta = Path(upload_folder).resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    identificador = uuid4().hex
    nome = f"{identificador}.{extensao}"
    temporario = pasta / f"{identificador}.tmp"
    destino = pasta / nome
    try:
        with temporario.open("xb") as saida:
            saida.write(conteudo)
        temporario.replace(destino)
    finally:
        temporario.unlink(missing_ok=True)
    return {"nome_arquivo": nome, "tipo": tipo, "mime_type": mime, "tamanho": len(conteudo)}


def apagar_arquivo(upload_folder, nome_arquivo):
    """Somente nomes gerados pela API podem ser removidos; nunca aceita caminhos."""
    if not isinstance(nome_arquivo, str) or not re.fullmatch(r"[a-f0-9]{32}\.(?:jpg|png|mp4)", nome_arquivo):
        raise ValueError("Nome de anexo inválido.")
    pasta = Path(upload_folder).resolve()
    destino = pasta / nome_arquivo
    if destino.resolve().parent != pasta:
        raise ValueError("O anexo deve permanecer na pasta de uploads.")
    destino.unlink(missing_ok=True)
