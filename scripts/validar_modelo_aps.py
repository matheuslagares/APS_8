"""Confere a reserva de páginas do modelo, sem avaliar autoria ou texto acadêmico."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import zipfile
from pypdf import PdfReader

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / 'documentacao' / 'modelo_aps'
config = json.loads((PASTA / 'ORCAMENTO_PAGINAS.json').read_text())
marcadores = dict((m, g) for g, m in config['marcadores'])
reader = PdfReader(PASTA / 'MODELO_PREENCHIVEL_APS.pdf')
paginas = {}
sequencia = []
for numero, pagina in enumerate(reader.pages, 1):
    encontrados = re.findall(r'APS_[A-Z]+_\d{2}', pagina.extract_text())
    assert len(encontrados) == 1, f'Quebra ou transbordamento inesperado na página {numero}: {encontrados}'
    marcador = encontrados[0]
    assert marcador in marcadores and marcador not in sequencia
    sequencia.append(marcador)
    grupo = marcadores[marcador]
    paginas.setdefault(grupo, []).append(numero)
assert sequencia == [m for _, m in config['marcadores']], 'Ordem de seções incorreta.'
checagens = []
for secao, (minimo, maximo) in config['limites'].items():
    quantidade = len(paginas[secao])
    assert (minimo is None or quantidade >= minimo) and quantidade <= maximo
    checagens.append({'secao': secao, 'paginas_reservadas': quantidade, 'intervalo_modelo': paginas[secao], 'minimo_rubrica': minimo, 'maximo_rubrica': maximo})
codigo = PdfReader(PASTA / 'RELATORIO_TECNICO_CODIGO_SELECIONADO.pdf')
assert len(codigo.pages) == 6
with zipfile.ZipFile(PASTA / 'FONTE_REFERENCIA_PARA_PREPARAR_NO_WINRAR.zip') as arquivo:
    assert arquivo.testzip() is None
    for nome in arquivo.namelist():
        assert not nome.endswith(('.db', '/.env')) and '/uploads/' not in nome and '/node_modules/' not in nome
relatorio = {
    'verificado_em_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'natureza': 'Verificação da paginação reservada e integridade de um modelo preenchível, não do trabalho acadêmico final.',
    'paginas_pdf_modelo': len(reader.pages), 'paginas_pdf_codigo_selecionado': len(codigo.pages),
    'checagens': checagens,
    'limites_da_conclusao': [
        'Espaços e perguntas não substituem a redação nem comprovam o mínimo de conteúdo.',
        'Depois da edição, conferir novamente páginas, índice e formatação institucional.',
        'Código é seleção de 135 linhas, não o fonte completo de 2.096 linhas de produção.',
        'O ZIP não foi criado com WinRAR e não é o pacote .doc pedido para upload.',
        'Autoria/uso de IA dependem da orientação do professor; este modelo não atesta aceitação.',
        'Ficha oficial, horas reais e assinaturas manuscritas continuam a cargo de cada aluno.',
    ],
}
(PASTA / 'VALIDACAO_PAGINAS.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n')
arquivos = sorted(p for p in PASTA.rglob('*') if p.is_file() and p.name != 'SHA256_ARTEFATOS.txt')
(PASTA / 'SHA256_ARTEFATOS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(PASTA)) + '\n' for p in arquivos))
print(json.dumps({'paginas_modelo': len(reader.pages), 'paginas_codigo': len(codigo.pages), 'reservas': {c['secao']: c['paginas_reservadas'] for c in checagens}}, ensure_ascii=False))
