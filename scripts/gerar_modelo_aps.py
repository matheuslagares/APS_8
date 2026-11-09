"""Modelo ABNT preenchível; não produz redação acadêmica final ou autoria de alunos."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import subprocess
import textwrap
import zipfile
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / 'documentacao/modelo_aps'
DADOS = json.loads((SAIDA / 'INVENTARIO_TECNICO.json').read_text())
ESTRUTURA = json.loads((SAIDA / 'ESTRUTURA_ABNT.json').read_text())
BASE = DADOS['base_commit']
OUTPUT_MAIN = 'MODELO_PREENCHIVEL_APS'
OUTPUT_CODE = 'RELATORIO_TECNICO_CODIGO_SELECIONADO'
LIMITES = {'objetivo': [1, 2], 'introducao': [2, 4], 'fundamentos': [4, 8], 'plano': [5, 15], 'projeto': [3, 8], 'codigo': [None, 10]}
CONTADORES = defaultdict(lambda: defaultdict(int))
MAPA = json.loads((SAIDA / 'MAPA_PAGINAS_ABNT.json').read_text()) if (SAIDA / 'MAPA_PAGINAS_ABNT.json').exists() else {}
PAGINAS, SUMARIO, FIGURAS = [], [], []


def campo(p, instrucao, resultado=''):
    for tipo in ['begin', 'separate', 'end']:
        if tipo == 'separate':
            r = OxmlElement('w:r'); i = OxmlElement('w:instrText'); i.set(qn('xml:space'), 'preserve'); i.text = ' ' + instrucao + ' '; r.append(i); p._p.append(r)
        r = OxmlElement('w:r'); f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), tipo); r.append(f); p._p.append(r)
        if tipo == 'separate' and resultado: p.add_run(str(resultado))


def estilo(doc, nome, tamanho=12, espaco=1.5, recuo=0, alinhamento=WD_ALIGN_PARAGRAPH.LEFT):
    s = doc.styles.add_style(nome, 1) if nome not in doc.styles else doc.styles[nome]
    s.font.name, s.font.size = 'Arial', Pt(tamanho)
    fontes = s.element.get_or_add_rPr().get_or_add_rFonts()
    for chave in ['asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme']:
        fontes.attrib.pop(qn('w:' + chave), None)
    for chave in ['ascii', 'hAnsi', 'eastAsia', 'cs']: fontes.set(qn('w:' + chave), 'Arial')
    s.font.color.rgb = RGBColor(0, 0, 0)
    f = s.paragraph_format; f.line_spacing = espaco; f.space_before = f.space_after = Pt(0)
    f.first_line_indent = Cm(recuo); f.alignment = alinhamento
    return s


def geometria(sec):
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.left_margin = Cm(3)
    sec.right_margin = sec.bottom_margin = Cm(2)
    sec.header_distance = Cm(2)
    sec.footer_distance = Cm(1)


def configurar(doc):
    geometria(doc.sections[0])
    estilo(doc, 'Normal', recuo=1.25, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY)
    estilo(doc, 'Resumo ABNT', alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY)
    for nome in ['Orientacao', 'TOC 1', 'TOC 2']: estilo(doc, nome)
    for nome in ['Legenda ABNT', 'Fonte ABNT', 'Nota ABNT', 'Referencia ABNT']:
        estilo(doc, nome, 10 if nome != 'Referencia ABNT' else 12, 1)
    estilo(doc, 'Codigo ABNT', 10, 1)
    doc.styles['Codigo ABNT'].font.name = 'Courier New'
    s = estilo(doc, 'Citacao longa ABNT', 10, 1, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY)
    s.paragraph_format.left_indent = Cm(4)
    for nome in ['Heading 1', 'Heading 2']:
        s = estilo(doc, nome); s.font.bold = True
        s.paragraph_format.space_after = Pt(18)
        s.paragraph_format.keep_with_next = True
    doc.styles['Heading 2'].paragraph_format.space_before = Pt(18)
    s = estilo(doc, 'Titulo sem numero'); s.font.bold = True
    s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s.paragraph_format.space_after = Pt(18)
    s.paragraph_format.keep_with_next = True
    s = estilo(doc, 'Titulo pos-textual'); s.font.bold = True
    s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    s.paragraph_format.space_after = Pt(18)
    nivel = OxmlElement('w:outlineLvl'); nivel.set(qn('w:val'), '0'); s.element.get_or_add_pPr().append(nivel)
    estilo(doc, 'Capa ABNT', alinhamento=WD_ALIGN_PARAGRAPH.CENTER)
    estilo(doc, 'Natureza ABNT', 12, 1, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY).paragraph_format.left_indent = Cm(8)
    doc.core_properties.title = 'Alerta de Alagamentos — modelo preenchível com formatação ABNT'
    doc.core_properties.author = 'Modelo assistido por IA; sem autoria atribuída aos integrantes'
    doc.core_properties.subject = 'Organização para redação própria; normas e escolhas em NORMAS_ABNT_ADOTADAS.md'
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    doc.core_properties.created = doc.core_properties.modified = agora
    for sec in doc.sections:
        sec.header.is_linked_to_previous = False; sec.footer.is_linked_to_previous = False
    atualizar = OxmlElement('w:updateFields'); atualizar.set(qn('w:val'), 'true'); doc.settings.element.append(atualizar)


def texto(doc, valor, estilo_nome='Normal', negrito=None):
    p = doc.add_paragraph(style=estilo_nome); r = p.add_run(valor)
    if negrito is not None: r.bold = negrito
    return p


def espaco(doc, linhas=1):
    for _ in range(linhas): doc.add_paragraph(style='Orientacao')


def nova_pagina(doc, identificador, grupo, titulo, nivel=None, numero=None, primeira=False):
    if not primeira: doc.add_page_break()
    if nivel:
        completo = f'{numero} {titulo}'
        p = doc.add_heading(completo, nivel)
        SUMARIO.append({'id': identificador, 'texto': completo, 'nivel': nivel})
    else:
        completo = titulo; p = texto(doc, titulo, 'Titulo pos-textual' if grupo in ['referencias', 'fichas'] else 'Titulo sem numero')
    ini = OxmlElement('w:bookmarkStart'); ini.set(qn('w:id'), str(len(PAGINAS) + 1)); ini.set(qn('w:name'), identificador)
    fim = OxmlElement('w:bookmarkEnd'); fim.set(qn('w:id'), str(len(PAGINAS) + 1)); p._p.insert(0, ini); p._p.append(fim)
    PAGINAS.append({'id': identificador, 'grupo': grupo, 'titulo': completo})
    return p


def titulo_primario(doc, numero, titulo, identificador):
    p = doc.add_heading(f'{numero} {titulo}', 1)
    SUMARIO.append({'id': identificador, 'texto': f'{numero} {titulo}', 'nivel': 1})
    return p


def orientacoes(doc, perguntas, ref, linhas=6):
    texto(doc, '[MODELO: substituir as orientações pela redação própria do grupo.]', 'Orientacao')
    for pergunta in perguntas: texto(doc, '• ' + pergunta, 'Orientacao')
    texto(doc, 'Evidências a consultar: ' + ref, 'Orientacao')
    texto(doc, '[REDAÇÃO PRÓPRIA, CITAÇÕES E ANÁLISE]', 'Orientacao')
    for _ in range(linhas): doc.add_paragraph(style='Normal')


def tabela(doc, cabecalhos, linhas, titulo, tipo='Quadro', fonte='Modelo de planejamento, sem dados de integrantes.'):
    CONTADORES[id(doc)][tipo] += 1
    p = texto(doc, f'{tipo} {CONTADORES[id(doc)][tipo]} – {titulo}', 'Legenda ABNT')
    p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(cabecalhos)); t.style = 'Table Grid'
    if tipo == 'Tabela':
        bordas = OxmlElement('w:tblBorders')
        for lado in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            b = OxmlElement('w:' + lado); b.set(qn('w:val'), 'single' if lado in ['top', 'bottom'] else 'nil'); b.set(qn('w:sz'), '4'); bordas.append(b)
        t._tbl.tblPr.append(bordas)
        if len(cabecalhos) == 2:
            t.autofit = False
            t.columns[0].width, t.columns[1].width = Cm(13), Cm(3)
    for cel, val in zip(t.rows[0].cells, cabecalhos): cel.text = str(val)
    for linha in linhas:
        for cel, val in zip(t.add_row().cells, linha): cel.text = str(val)
    for i, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr(); cant = OxmlElement('w:cantSplit'); trPr.append(cant)
        for cel in row.cells:
            for p in cel.paragraphs:
                p.style = doc.styles['Fonte ABNT']
                for run in p.runs: run.bold = i == 0
        if tipo == 'Tabela' and len(row.cells) == 2:
            row.cells[0].width, row.cells[1].width = Cm(13), Cm(3)
    texto(doc, 'Fonte: ' + fonte, 'Fonte ABNT')
    return t


def figura(doc, nome, titulo, numero, pagina_id):
    FIGURAS.append({'id': pagina_id, 'texto': f'Figura {numero} – {titulo}'})
    texto(doc, f'[Apresentar e discutir a Figura {numero} em palavras próprias.]', 'Orientacao')
    p = texto(doc, f'Figura {numero} – {titulo}', 'Legenda ABNT'); p.paragraph_format.keep_with_next = True
    caminho = SAIDA / 'diagramas' / (nome + '.png')
    with Image.open(caminho) as img: w, h = img.size
    escala = min(16 / w, 16 / h)
    p = doc.add_paragraph(style='Fonte ABNT'); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.left_indent = p.paragraph_format.right_indent = p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next = True
    desenho = p.add_run().add_picture(str(caminho), width=Cm(w * escala), height=Cm(h * escala))
    for distancia in ['distT', 'distB', 'distL', 'distR']: desenho._inline.set(distancia, '0')
    texto(doc, f'Fonte: elaboração assistida por IA, com base no código do projeto ({BASE[:7]}, 2026).', 'Fonte ABNT')


def trecho(doc, item):
    texto(doc, 'Foco a explicar pelo grupo: ' + item['foco_tecnico'], 'Orientacao')
    CONTADORES[id(doc)]['Quadro'] += 1
    n = CONTADORES[id(doc)]['Quadro']
    p = texto(doc, f"Quadro {n} – Trecho de {item['arquivo']}", 'Legenda ABNT'); p.paragraph_format.keep_with_next = True
    for numero, linha in enumerate(item['conteudo_existente'].splitlines(), item['linha_inicial']):
        p = doc.add_paragraph(style='Codigo ABNT'); p.paragraph_format.keep_together = True
        partes = textwrap.wrap(linha, width=68, replace_whitespace=False, drop_whitespace=False) or ['']
        for i, parte in enumerate(partes):
            if i: p.add_run().add_break()
            p.add_run((f'{numero:>3} | ' if i == 0 else '    > ') + parte)
    texto(doc, f"Fonte: código existente do projeto ({BASE[:7]}), {item['arquivo']}, linhas {item['linha_inicial']}–{item['linha_final']}.", 'Fonte ABNT')
    texto(doc, 'Comentário próprio do grupo: ______________________________', 'Orientacao')


def paginas_codigo(doc, independente=False):
    if independente: nova_pagina(doc, 'CODIGO_01', 'codigo', 'RELATÓRIO DE CÓDIGO SELECIONADO', primeira=True)
    else: nova_pagina(doc, 'CODIGO_01', 'codigo', 'RELATÓRIO DE CÓDIGO', nivel=1, numero='6')
    texto(doc, 'Seleção técnica parcial, não é o fonte integral.', 'Orientacao', True)
    texto(doc, '# Título: Alerta de Alagamentos\n# Participantes: identificação omitida conforme solicitado.\n# Referência: ' + BASE[:7], 'Codigo ABNT')
    texto(doc, 'Produção: 2.096 linhas físicas em 21 arquivos; inclui comentários e linhas vazias. As páginas seguintes selecionam 135 linhas existentes. Testes, configurações e arquivos gerados ficam separados.', 'Orientacao')
    linhas = [(a['arquivo'], a['linhas_fisicas']) for a in DADOS['modulos'] if a['categoria'] in ('producao_backend', 'producao_mobile')]
    tabela(doc, ['Arquivo de produção', 'Linhas'], linhas, 'Inventário de linhas físicas', 'Tabela', 'contagem dos arquivos do commit ' + BASE[:7] + ' (2026).')
    texto(doc, 'Confirmar a aceitação de seleção legível + fonte completo separado. > indica quebra visual, sem alterar a linha original.', 'Nota ABNT')
    grupos = [[0, 1], [2, 3], [4], [5, 6], [7, 8], [9]]
    for i, indices in enumerate(grupos, 2):
        if independente: nova_pagina(doc, f'CODIGO_{i:02}', 'codigo', f'Trechos selecionados – parte {i-1}', nivel=2, numero=f'1.{i-1}')
        else: nova_pagina(doc, f'CODIGO_{i:02}', 'codigo', f'Trechos selecionados – parte {i-1}', nivel=2, numero=f'6.{i-1}')
        for j in indices: trecho(doc, DADOS['trechos_existentes_sugeridos'][j])


def preencher_lista(doc, ancora, entradas, toc=False):
    corpo = doc.element.body; pos = list(corpo).index(ancora._p)
    if not entradas: return
    novos = []
    for item in entradas:
        p = doc.add_paragraph(style='TOC 1' if item.get('nivel', 1) == 1 else 'TOC 2')
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.9), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        p.paragraph_format.keep_with_next = False
        r = p.add_run(item['texto']); r.bold = item.get('nivel') == 1
        p.add_run('\t' + str(MAPA.get(item['id'], {}).get('pagina_exibida', '...')))
        corpo.remove(p._p); corpo.insert(pos, p._p); pos += 1; novos.append(p)
    if toc:
        p = novos[0]; r = OxmlElement('w:r'); b = OxmlElement('w:fldChar'); b.set(qn('w:fldCharType'), 'begin'); r.append(b); p._p.insert(1, r)
        r = OxmlElement('w:r'); ins = OxmlElement('w:instrText'); ins.set(qn('xml:space'), 'preserve'); ins.text = ' TOC \\o "1-2" \\h \\z \\u \\t "Titulo pos-textual,1" '; r.append(ins); p._p.insert(2, r)
        r = OxmlElement('w:r'); sep = OxmlElement('w:fldChar'); sep.set(qn('w:fldCharType'), 'separate'); r.append(sep); p._p.insert(3, r)
        r = OxmlElement('w:r'); end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end'); r.append(end); novos[-1]._p.append(r)
    corpo.remove(ancora._p)


def configurar_numeros(sec):
    sec.header.is_linked_to_previous = False; sec.footer.is_linked_to_previous = False
    p = sec.header.paragraphs[0]; p.style = 'Fonte ABNT'; p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    campo(p, 'PAGE', '1')


def montar():
    doc = Document(); configurar(doc)
    nova_pagina(doc, 'CAPA', 'capa', 'MODELO PREENCHÍVEL DE APS', primeira=True)
    # Capa: sem contagem, sem número e sem atribuição de nomes não informados.
    p = doc.paragraphs[-1]; p.style = 'Capa ABNT'; p.runs[0].bold = True
    espaco(doc, 4)
    texto(doc, 'Identificação pessoal não preenchida', 'Capa ABNT')
    espaco(doc, 8); texto(doc, 'ALERTA DE ALAGAMENTOS', 'Capa ABNT', True)
    texto(doc, 'Modelo de organização com formatação ABNT', 'Capa ABNT')
    espaco(doc, 9); texto(doc, 'LOCAL NÃO INFORMADO', 'Capa ABNT'); texto(doc, '2026', 'Capa ABNT')
    sec = doc.add_section(WD_SECTION_START.NEW_PAGE); geometria(sec)
    sec.header.is_linked_to_previous = False; sec.footer.is_linked_to_previous = False
    n = OxmlElement('w:pgNumType'); n.set(qn('w:start'), '1'); sec._sectPr.append(n)
    nova_pagina(doc, 'ROSTO', 'pretextual', 'IDENTIFICAÇÃO NÃO PREENCHIDA', primeira=True)
    doc.paragraphs[-1].style = 'Capa ABNT'
    espaco(doc, 6); texto(doc, 'ALERTA DE ALAGAMENTOS', 'Capa ABNT', True); espaco(doc, 4)
    texto(doc, 'Modelo de organização da Atividade Prática Supervisionada. Preencher a natureza do trabalho, objetivo, instituição, área e orientação conforme exigências confirmadas. Não é trabalho acadêmico final.', 'Natureza ABNT')
    espaco(doc, 7); texto(doc, 'LOCAL NÃO INFORMADO', 'Capa ABNT'); texto(doc, '2026', 'Capa ABNT')
    nova_pagina(doc, 'APROVACAO', 'pretextual', 'FOLHA DE APROVAÇÃO – MODELO')
    texto(doc, 'ALERTA DE ALAGAMENTOS', 'Capa ABNT', True); espaco(doc, 3)
    texto(doc, '[Preencher natureza e dados reais se esta folha for exigida para a APS.]', 'Natureza ABNT')
    espaco(doc, 3); texto(doc, 'Aprovado em: ____ / ____ / ______', 'Orientacao')
    texto(doc, '[Banca / avaliadores: preencher apenas conforme orientação institucional.]', 'Orientacao')
    espaco(doc, 4); texto(doc, '________________________________________\n[Avaliador e instituição]', 'Capa ABNT')
    espaco(doc, 2); texto(doc, '________________________________________\n[Avaliador e instituição]', 'Capa ABNT')
    nova_pagina(doc, 'RESUMO', 'pretextual', 'RESUMO')
    texto(doc, '[Redigir, em um único parágrafo, o resumo do trabalho efetivamente escrito. Apresentar objetivo, método, resultados e conclusão sem inventar execução. Para trabalhos acadêmicos, adotar a extensão de 150 a 500 palavras como referência da NBR 6028:2021, sujeita à regra institucional.]', 'Resumo ABNT')
    espaco(doc, 5); texto(doc, 'Palavras-chave: [termo 1]; [termo 2]; [termo 3].', 'Orientacao')
    nova_pagina(doc, 'ABSTRACT', 'pretextual', 'ABSTRACT')
    texto(doc, '[Redigir a versão em língua estrangeira do resumo produzido pelo grupo. Não declarar resultados diferentes. A escolha do inglês neste modelo é editorial.]', 'Resumo ABNT')
    espaco(doc, 5); texto(doc, 'Keywords: [term 1]; [term 2]; [term 3].', 'Orientacao')
    nova_pagina(doc, 'LISTA_FIGURAS', 'pretextual', 'LISTA DE FIGURAS')
    ancora_figuras = doc.add_paragraph()
    nova_pagina(doc, 'SUMARIO', 'pretextual', 'SUMÁRIO')
    ancora_sumario = doc.add_paragraph()
    sec = doc.add_section(WD_SECTION_START.NEW_PAGE); geometria(sec)
    # A parte textual continua a contagem iniciada na folha de rosto.
    for n in list(sec._sectPr.findall(qn('w:pgNumType'))): sec._sectPr.remove(n)
    configurar_numeros(sec)
    nova_pagina(doc, 'OBJETIVO_01', 'objetivo', 'OBJETIVO E MOTIVAÇÃO', nivel=1, numero='1', primeira=True)
    orientacoes(doc, ['Definir o problema e a motivação em palavras próprias, com contexto sustentado por fontes.', 'Formular objetivo geral, objetivos específicos e resultado observável entre dispositivos.', 'Delimitar relatos não verificados e o que fica fora do escopo.'], 'README.md e TESTES.md.', 6)
    for i, (titulo, perguntas) in enumerate(ESTRUTURA['intro'], 1):
        if i == 1:
            nova_pagina(doc, 'INTRODUCAO_01', 'introducao', 'INTRODUÇÃO', nivel=1, numero='2')
            texto(doc, '2.1 ' + titulo, 'Heading 2'); SUMARIO.append({'id':'INTRODUCAO_01','texto':'2.1 '+titulo,'nivel':2})
        else: nova_pagina(doc, f'INTRODUCAO_{i:02}', 'introducao', titulo, nivel=2, numero=f'2.{i}')
        orientacoes(doc, perguntas, 'README.md; ARQUITETURA.md; fontes de contexto realmente consultadas.', 6)
    for i, (titulo, perguntas) in enumerate(ESTRUTURA['fundamentos'], 1):
        if i == 1:
            nova_pagina(doc, 'FUNDAMENTOS_01', 'fundamentos', 'FUNDAMENTOS', nivel=1, numero='3')
            texto(doc, '3.1 ' + titulo, 'Heading 2'); SUMARIO.append({'id':'FUNDAMENTOS_01','texto':'3.1 '+titulo,'nivel':2})
        else: nova_pagina(doc, f'FUNDAMENTOS_{i:02}', 'fundamentos', titulo, nivel=2, numero=f'3.{i}')
        orientacoes(doc, perguntas, 'Bibliografia estudada pelo grupo; tecnologias e conceitos de SD, middleware e mobilidade. Ferramentas ficam no plano.', 4)
        if i == 2:
            texto(doc, '[Citação curta a inserir: autor, ano e página/localizador, conforme a fonte real.]', 'Orientacao')
            texto(doc, '[Modelo de citação longa: inserir apenas texto realmente consultado, sem aspas, recuo de 4 cm adotado, fonte 10 e espaço simples. Completar autoria, ano e página/localizador.]', 'Citacao longa ABNT')
    for i, (titulo, perguntas) in enumerate(ESTRUTURA['planos'], 1):
        if i == 1:
            nova_pagina(doc, 'PLANO_01', 'plano', 'PLANO DE DESENVOLVIMENTO', nivel=1, numero='4')
            texto(doc, '4.1 ' + titulo, 'Heading 2'); SUMARIO.append({'id':'PLANO_01','texto':'4.1 '+titulo,'nivel':2})
        else: nova_pagina(doc, f'PLANO_{i:02}', 'plano', titulo, nivel=2, numero=f'4.{i}')
        orientacoes(doc, perguntas, 'README.md; TESTES.md; ENTREGA.md; DIARIO.md. Preencher responsáveis, datas e horas reais.', 5)
    nova_pagina(doc, 'PROJETO_01', 'projeto', 'PROJETO DO PROGRAMA', nivel=1, numero='5')
    texto(doc, '5.1 Requisitos e módulos', 'Heading 2'); SUMARIO.append({'id':'PROJETO_01','texto':'5.1 Requisitos e módulos','nivel':2})
    orientacoes(doc, ['Relacionar requisitos, regras, módulos e evidências.', 'Cobrir login, autoria, relatos, localização opcional, mapa, mídia privada e migração.'], 'INVENTARIO_TECNICO.md; API.md; ARQUITETURA.md.', 2)
    tabela(doc, ['Requisito', 'Módulo', 'Critério / evidência'], [('', '', '') for _ in range(4)], 'Matriz de requisitos a preencher')
    for i, (arquivo, titulo) in enumerate([('01_casos_uso','Diagrama de casos de uso'),('02_classes','Diagrama de classes conceituais'),('03_sequencia','Diagrama de sequência'),('04_atividades','Diagrama de atividades'),('05_der','Diagrama entidade-relacionamento físico')], 2):
        pid = f'PROJETO_{i:02}'; nova_pagina(doc, pid, 'projeto', titulo, nivel=2, numero=f'5.{i}')
        figura(doc, arquivo, titulo, i-1, pid)
        texto(doc, 'Nota: referência técnica assistida para validação do grupo; classes são conceituais, não classes Python. No DER, banco permite 0..N anexos e a API limita um por cadastro.', 'Nota ABNT')
    paginas_codigo(doc)
    nova_pagina(doc, 'ORAL_01', 'oral', 'CONSIDERAÇÕES FINAIS', nivel=1, numero='7')
    texto(doc, '[Sintetizar, em redação própria, o atendimento aos objetivos, os resultados comprovados, as limitações e o que permanece pendente. Não apresentar testes físicos não executados como concluídos.]', 'Orientacao')
    texto(doc, '7.1 Apresentação do programa', 'Heading 2')
    SUMARIO.append({'id':'ORAL_01','texto':'7.1 Apresentação do programa','nivel':2})
    texto(doc, 'Todos os integrantes devem participar. A rubrica informa perda de 50% para quem não participar. Registrar apenas participação real.', 'Orientacao')
    tabela(doc, ['Etapa a ensaiar', 'Participante / tempo real'], [('Objetivo e arquitetura',''),('Demonstração no computador e Expo Go',''),('Duas contas / dispositivos',''),('GPS, mapa, imagem e vídeo',''),('Autoria e persistência','')], 'Divisão do ensaio a preencher')
    texto(doc, 'O teste físico em dois celulares permanece pendente. Ver APRESENTACAO.md e TESTES.md.', 'Orientacao')
    nova_pagina(doc, 'REFERENCIAS_01', 'referencias', 'REFERÊNCIAS')
    SUMARIO.append({'id':'REFERENCIAS_01','texto':'REFERÊNCIAS','nivel':1})
    texto(doc, '[Substituir por referências de fontes efetivamente consultadas. Modelos abaixo não são referências reais.]', 'Orientacao')
    p = texto(doc, '[SOBRENOME, Prenome. ', 'Referencia ABNT'); p.add_run('Título').bold = True; p.add_run(': subtítulo. Edição. Local: editora, ano.]')
    doc.add_paragraph(style='Referencia ABNT')
    p = texto(doc, '[AUTOR/ENTIDADE. ', 'Referencia ABNT'); p.add_run('Título da página').bold = True; p.add_run('. Data. Disponível em: URL. Acesso em: dia mês abreviado ano.]')
    doc.add_paragraph(style='Referencia ABNT')
    texto(doc, '[Preencher as demais referências no sistema adotado, alinhadas à esquerda, em espaço simples e separadas por uma linha em branco.]', 'Referencia ABNT')
    espaco(doc, 5)
    texto(doc, 'Não declarar leitura de fontes não consultadas. Ver NORMAS_ABNT_ADOTADAS.md para as edições e escolhas de formatação utilizadas no modelo.', 'Orientacao')
    nova_pagina(doc, 'FICHAS_01', 'fichas', 'APÊNDICE A – ORIENTAÇÕES PARA FICHAS DE APS')
    SUMARIO.append({'id':'FICHAS_01','texto':'APÊNDICE A – ORIENTAÇÕES PARA FICHAS DE APS','nivel':1})
    texto(doc, 'Esta orientação não substitui a ficha oficial. Anexar uma ficha por aluno, com atividades cronológicas, horas reais, total e assinatura manuscrita. Não foram atribuídas horas nem produzidas assinaturas.', 'Orientacao')
    tabela(doc, ['Data', 'Atividade real', 'Horas', 'Evidência'], [('', '', '', '') for _ in range(6)], 'Conferência auxiliar das atividades')
    texto(doc, 'As fichas oficiais externas podem integrar um anexo, conforme a orientação institucional. Não apresentar este quadro auxiliar como formulário oficial.', 'Orientacao')
    preencher_lista(doc, ancora_figuras, FIGURAS)
    preencher_lista(doc, ancora_sumario, SUMARIO, toc=True)
    doc.save(SAIDA / (OUTPUT_MAIN + '.docx'))
    principal = list(PAGINAS); entradas = list(SUMARIO)
    PAGINAS.clear(); SUMARIO.clear(); codigo = Document(); configurar(codigo); configurar_numeros(codigo.sections[0]); paginas_codigo(codigo, independente=True)
    codigo.save(SAIDA / (OUTPUT_CODE + '.docx'))
    (SAIDA / 'ORCAMENTO_PAGINAS.json').write_text(json.dumps({'natureza':'Modelo de formatação ABNT; não atesta texto final ou aceitação acadêmica.','base_commit':BASE,'paginas':principal,'sumario':entradas,'figuras':FIGURAS,'paginas_codigo':list(PAGINAS),'limites':LIMITES,'elementos_pretextuais_contados':6,'observacao_pretextuais':'A quantidade de páginas é apurada no PDF; o sumário pode ocupar mais de uma página.','formato':'A4 frente; Arial 12; 1,5; margens 3/2 cm; primeira linha 1,25 cm escolhida.'},ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    montar()
    print('DOCX ABNT gerados. Converter PDFs e executar validar_modelo_aps.py; gerar novamente para atualizar o sumário com páginas reais.')
