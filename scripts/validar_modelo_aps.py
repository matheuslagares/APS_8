"""Verifica formatação e páginas do modelo ABNT; não certifica conteúdo/autoria."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re
import zipfile
from docx import Document
from docx.oxml.ns import qn
from pypdf import PdfReader
import fitz

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / 'documentacao/modelo_aps'
config = json.loads((PASTA / 'ORCAMENTO_PAGINAS.json').read_text())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--atualizar-mapa', action='store_true', help='Lê os PDFs e prepara páginas reais para a próxima geração do sumário.')
args = parser.parse_args()


def normalizar(s):
    return re.sub(r'\s+', '', s).casefold()


def localizar(reader, paginas):
    indice, mapa = 0, {}
    for item in paginas:
        achou = None
        for n in range(indice, len(reader.pages)):
            linhas = [s.strip() for s in reader.pages[n].extract_text().splitlines() if s.strip()]
            if linhas and linhas[0].isdigit(): linhas = linhas[1:]
            inicio = normalizar(' '.join(linhas[:3]))
            if inicio.startswith(normalizar(item['titulo'])):
                achou = n + 1; break
        assert achou is not None, f"Título não encontrado: {item['titulo']}"
        mapa[item['id']] = {'pagina_fisica': achou, 'pagina_exibida': achou - 1, 'titulo': item['titulo']}
        indice = achou
    return mapa


principal_path = PASTA / 'MODELO_PREENCHIVEL_APS.pdf'
codigo_path = PASTA / 'RELATORIO_TECNICO_CODIGO_SELECIONADO.pdf'
reader = PdfReader(principal_path); codigo = PdfReader(codigo_path)
mapa = localizar(reader, config['paginas'])
if args.atualizar_mapa:
    (PASTA / 'MAPA_PAGINAS_ABNT.json').write_text(json.dumps(mapa, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'mapa_atualizado': True, 'paginas_pdf': len(reader.pages), 'primeira_textual': mapa['OBJETIVO_01']}, ensure_ascii=False))
    raise SystemExit(0)

# Documento Word: geometria, estilos e seções efetivamente gravados no OOXML.
doc = Document(PASTA / 'MODELO_PREENCHIVEL_APS.docx')
assert len(doc.sections) == 3
for sec in doc.sections:
    for medido, cm in [(sec.page_width,21),(sec.page_height,29.7),(sec.top_margin,3),(sec.left_margin,3),(sec.right_margin,2),(sec.bottom_margin,2)]:
        assert abs(medido.cm-cm)<0.02, (medido.cm,cm)
normal=doc.styles['Normal']
assert normal.font.name=='Arial' and normal.font.size.pt==12
assert abs(normal.paragraph_format.line_spacing-1.5)<0.01
assert abs(normal.paragraph_format.first_line_indent.cm-1.25)<0.01
assert str(normal.paragraph_format.alignment).startswith('JUSTIFY')
for nome in ['Heading 1','Heading 2']:
    s=doc.styles[nome];assert s.font.name=='Arial' and s.font.size.pt==12 and s.font.bold
    assert str(s.font.color.rgb)=='000000'
for nome in ['Legenda ABNT','Fonte ABNT','Nota ABNT','Codigo ABNT','Citacao longa ABNT']:
    s=doc.styles[nome];assert s.font.size.pt==10 and s.paragraph_format.line_spacing==1
assert abs(doc.styles['Citacao longa ABNT'].paragraph_format.left_indent.cm-4)<0.01
assert doc.styles['Referencia ABNT'].font.size.pt==12 and doc.styles['Referencia ABNT'].paragraph_format.line_spacing==1
for i,sec in enumerate(doc.sections):
    tem_page=any('PAGE' in (x.text or '') for x in sec.header._element.iter(qn('w:instrText')))
    assert tem_page==(i==2), f'Campo PAGE em seção indevida: {i}'
    assert not any('PAGE' in (x.text or '') for x in sec.footer._element.iter(qn('w:instrText')))
assert doc.sections[1]._sectPr.find(qn('w:pgNumType')).get(qn('w:start'))=='1'
assert doc.sections[2]._sectPr.find(qn('w:pgNumType')) is None
instrucoes=[x.text or '' for x in doc.element.iter(qn('w:instrText'))]
assert any('TOC ' in s and 'Titulo pos-textual' in s for s in instrucoes)

checagens=[]
for secao,(minimo,maximo) in config['limites'].items():
    numeros=[]
    for i,item in enumerate(config['paginas']):
        if item['grupo']!=secao:continue
        primeiro=mapa[item['id']]['pagina_fisica']
        ultimo=mapa[config['paginas'][i+1]['id']]['pagina_fisica']-1 if i+1<len(config['paginas']) else len(reader.pages)
        numeros.extend(range(primeiro,ultimo+1))
    assert (minimo is None or len(numeros)>=minimo) and len(numeros)<=maximo,(secao,numeros)
    checagens.append({'secao':secao,'paginas_reservadas':len(numeros),'paginas_fisicas':numeros,'minimo_rubrica':minimo,'maximo_rubrica':maximo})
assert len(codigo.pages)<=10

pdf=fitz.open(principal_path)
primeira_textual=mapa['OBJETIVO_01']['pagina_fisica']
fontes=set(); excesso=[]; paginas_numeradas=[]
for n,page in enumerate(pdf,1):
    assert abs(page.rect.width-595.28)<1 and abs(page.rect.height-841.89)<1
    cabecalhos=[]
    # Caixas de spans justificados podem incluir espaço terminal além da margem;
    # a verificação usa os glifos visíveis, sem ampliar a área permitida.
    for bloco in page.get_text('rawdict')['blocks']:
        for linha in bloco.get('lines',[]):
            for s in linha.get('spans',[]):
                texto_span = ''.join(c['c'] for c in s['chars'])
                visiveis = [c for c in s['chars'] if not c['c'].isspace()]
                if not visiveis:continue
                fontes.add(s['font'])
                x0=min(c['bbox'][0] for c in visiveis);y0=min(c['bbox'][1] for c in visiveis)
                x1=max(c['bbox'][2] for c in visiveis);y1=max(c['bbox'][3] for c in visiveis)
                if y0<80 and texto_span.strip().isdigit():
                    cabecalhos.append({'text':texto_span,'bbox':(x0,y0,x1,y1)})
                elif x0<84 or x1>540 or y0<83 or y1>787:
                    excesso.append({'pagina':n,'texto':texto_span[:65],'bbox':(x0,y0,x1,y1)})
    if n<primeira_textual:assert not cabecalhos,(n,cabecalhos)
    else:
        assert len(cabecalhos)==1,(n,cabecalhos)
        h=cabecalhos[0];assert h['text'].strip()==str(n-1),(n,h['text'])
        assert 54<=h['bbox'][1]<=62 and abs(h['bbox'][2]-538.6)<2
        paginas_numeradas.append(n)
    for imagem in page.get_image_info():
        x0,y0,x1,y1=imagem['bbox'];assert x0>=84 and x1<=540 and y0>=83 and y1<=787,(n,imagem['bbox'])
assert not excesso,excesso

sumario_pagina=mapa['SUMARIO']['pagina_fisica']
sumario='\n'.join(pdf[n-1].get_text() for n in range(sumario_pagina, primeira_textual))
for item in config['sumario']:
    numero=mapa[item['id']]['pagina_exibida']
    linhas=[l for l in sumario.splitlines() if normalizar(item['texto']) in normalizar(l)]
    assert linhas and any(re.search(r'(?:\.{2,}|\s)'+str(numero)+r'\s*$',l) for l in linhas),(item['texto'],numero,linhas)
assert 'CAPA' not in sumario and 'RESUMO' not in sumario and 'ABSTRACT' not in sumario
for i,item in enumerate(config['figuras'],1):
    t=pdf[mapa[item['id']]['pagina_fisica']-1].get_text()
    assert normalizar(item['texto']) in normalizar(t) and 'Fonte:' in t
with zipfile.ZipFile(PASTA/'FONTE_REFERENCIA_PARA_PREPARAR_NO_WINRAR.zip') as z:
    assert z.testzip() is None
    assert not any(n.endswith(('.db','/.env')) or '/uploads/' in n or '/node_modules/' in n for n in z.namelist())
relatorio={
    'verificado_em_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'natureza':'Checagem técnica de formatação ABNT adotada e orçamento de um modelo; não certifica texto final, vigência normativa ou aceitação acadêmica.',
    'paginas_pdf_modelo':len(reader.pages),'paginas_pdf_codigo_selecionado':len(codigo.pages),
    'primeira_pagina_textual_fisica':primeira_textual,'primeiro_numero_exibido':primeira_textual-1,
    'geometria':'A4; superior/esquerda 3 cm; inferior/direita 2 cm; somente frente.',
    'corpo_word':'Arial 12; entrelinhas 1,5; justificado; recuo inicial 1,25 cm adotado.',
    'fontes_pdf_renderizadas':sorted(fontes),
    'observacao_fontes':'O Word solicita Arial/Courier New; o LibreOffice deste ambiente pode substituí-las por Liberation Sans/Mono. A família é uma escolha editorial, não imposição única da ABNT.',
    'checagens':checagens,'sumario_conferido':True,'figuras_com_identificacao_e_fonte':5,'texto_fora_margens':excesso,
    'limites_da_conclusao':['São espaços para redação própria; não comprovam conteúdo concluído.','Recalcular páginas e sumário depois de editar.','Não há nomes, horas reais, assinatura ou ficha oficial preenchida.','Código apresentado é seleção de 135 linhas; fonte integral separado.','A rubrica proíbe trabalho elaborado por IA; esclarecer com o professor o auxílio já utilizado.','ZIP não é RAR/WinRAR e não foi renomeado a .doc.'],
}
(PASTA/'VALIDACAO_PAGINAS.json').write_text(json.dumps(relatorio,ensure_ascii=False,indent=2)+'\n')
(PASTA/'MAPA_PAGINAS_ABNT.json').write_text(json.dumps(mapa,ensure_ascii=False,indent=2)+'\n')
arquivos=sorted(p for p in PASTA.rglob('*') if p.is_file() and p.name!='SHA256_ARTEFATOS.txt')
(PASTA/'SHA256_ARTEFATOS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(PASTA))+'\n' for p in arquivos))
print(json.dumps({'paginas_modelo':len(reader.pages),'paginas_codigo':len(codigo.pages),'primeiro_numero_textual':primeira_textual-1,'reservas':{x['secao']:x['paginas_reservadas'] for x in checagens},'margens_oo_xml_e_pdf':'conferidas','sumario':'conferido','fontes_pdf':sorted(fontes)},ensure_ascii=False))
