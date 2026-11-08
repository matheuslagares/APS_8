"""Gera material de organização; não redige o trabalho acadêmico do grupo."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import textwrap
import zipfile

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image as Imagem

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / 'documentacao' / 'modelo_aps'
DADOS = json.loads((SAIDA / 'INVENTARIO_TECNICO.json').read_text())
BASE = DADOS['base_commit']
DIAGRAMAS = ['01_casos_uso', '02_classes', '03_sequencia', '04_atividades', '05_der']
LIMITES = {'objetivo': (1, 2), 'introducao': (2, 4), 'fundamentos': (4, 8), 'plano': (5, 15), 'projeto': (3, 8), 'codigo': (None, 10)}


def fonte(arquivo):
    return subprocess.check_output(['git', '-C', str(RAIZ), 'show', f'{BASE}:{arquivo}'])


def configurar(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    sec.left_margin = sec.right_margin = Cm(2)
    n = doc.styles['Normal']
    n.font.name, n.font.size = 'Arial', Pt(11)
    n.paragraph_format.line_spacing = 1.15
    n.paragraph_format.space_after = Pt(7)
    for nome, tamanho in [('Title', 23), ('Heading 1', 16), ('Heading 2', 12)]:
        s = doc.styles[nome]
        s.font.name, s.font.size = 'Arial', Pt(tamanho)
        s.font.color.rgb = RGBColor.from_string('163344')
    p = sec.header.paragraphs[0]
    p.text = 'MODELO DE ORGANIZAÇÃO — redação e validação pelo grupo'
    p.runs[0].font.size = Pt(8)
    p.runs[0].font.color.rgb = RGBColor.from_string('667777')
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run('Modelo • referência de código ' + BASE[:7] + ' • página ')
    f = OxmlElement('w:fldSimple'); f.set(qn('w:instr'), 'PAGE'); p._p.append(f)
    for r in p.runs: r.font.size = Pt(8)
    doc.core_properties.title = 'Alerta de Alagamentos — modelo preenchível da APS'
    doc.core_properties.author = 'Modelo de organização assistido por IA'
    doc.core_properties.subject = 'Não é trabalho acadêmico final; contém campos e referências técnicas.'


def tabela(doc, cabecalhos, linhas, tamanho=9):
    t = doc.add_table(rows=1, cols=len(cabecalhos)); t.style = 'Table Grid'
    for cel, txt in zip(t.rows[0].cells, cabecalhos): cel.text = str(txt)
    for linha in linhas:
        for cel, txt in zip(t.add_row().cells, linha): cel.text = str(txt)
    for i, row in enumerate(t.rows):
        for cel in row.cells:
            for p in cel.paragraphs:
                p.paragraph_format.space_after = Pt(2)
                for r in p.runs: r.font.size = Pt(tamanho); r.bold = i == 0
    return t


def texto(doc, txt, negrito=False):
    p = doc.add_paragraph()
    p.add_run(txt).bold = negrito
    return p


def figura(doc, caminho):
    with Imagem.open(caminho) as imagem:
        largura, altura = imagem.size
    fator = min(16 / largura, 18 / altura)
    doc.add_picture(str(caminho), width=Cm(largura * fator), height=Cm(altura * fator))


def iniciar_pagina(doc, marcador, titulo, primeira=False):
    if not primeira: doc.add_page_break()
    p = doc.add_paragraph(marcador)
    p.paragraph_format.space_after = Pt(3)
    for r in p.runs: r.font.size = Pt(7); r.font.color.rgb = RGBColor.from_string('889999')
    doc.add_heading(titulo, 1)


def area_redacao(doc, perguntas, referencia, linhas=12):
    texto(doc, 'ROTEIRO PARA REDAÇÃO PRÓPRIA — substituir as orientações pelo texto do grupo.', True)
    for p in perguntas: texto(doc, '• ' + p)
    texto(doc, 'Evidências / referências a consultar: ' + referencia)
    texto(doc, '[REDAÇÃO PRÓPRIA / CITAÇÕES / ANÁLISE DO GRUPO]')
    for _ in range(linhas):
        p = doc.add_paragraph('____________________________________________________________________')
        p.paragraph_format.space_after = Pt(4)
        for r in p.runs: r.font.size = Pt(9); r.font.color.rgb = RGBColor.from_string('C0CACA')


def trecho(doc, item):
    texto(doc, f"{item['arquivo']} • linhas {item['linha_inicial']}–{item['linha_final']}", True)
    p = doc.add_paragraph('Foco para o grupo explicar: ' + item['foco_tecnico'])
    for r in p.runs: r.font.size = Pt(9)
    for numero, linha in enumerate(item['conteudo_existente'].splitlines(), item['linha_inicial']):
        partes = textwrap.wrap(linha, width=82, replace_whitespace=False, drop_whitespace=False) or ['']
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1
        p.paragraph_format.keep_together = True
        for i, parte in enumerate(partes):
            if i: p.add_run().add_break()
            r = p.add_run((f'{numero:>3} | ' if i == 0 else '    > ') + parte)
            r.font.name, r.font.size = 'DejaVu Sans Mono', Pt(9)
    texto(doc, 'Comentário do grupo sobre este trecho: ___________________________________')


def paginas_codigo(doc, prefixo='APS_COD', primeira=False):
    iniciar_pagina(doc, f'{prefixo}_01', '8. Relatório de código — inventário e seleção', primeira)
    texto(doc, 'RELATÓRIO TÉCNICO PARCIAL, NÃO É O FONTE INTEGRAL.', True)
    texto(doc, '# Título: Alerta de Alagamentos\n# Participantes: preencher nos arquivos finais conforme orientação do professor.\n# Referência: ' + BASE[:7])
    texto(doc, 'Produção: 2.096 linhas físicas em 21 arquivos (606 backend e 1.490 mobile). A métrica inclui linhas vazias e comentários; não é contagem de instruções executáveis. Testes, dependências, lockfile, configuração e mídias ficam separados.')
    linhas = [(a['arquivo'], a['linhas_fisicas']) for a in DADOS['modulos'] if a['categoria'] in ('producao_backend', 'producao_mobile')]
    tabela(doc, ['Arquivo de produção', 'Linhas físicas'], linhas, 9)
    texto(doc, 'As páginas seguintes reproduzem 135 linhas selecionadas do código existente, com numeração original. Quebras visuais com > não pertencem ao fonte. O fonte completo está no ZIP de referência. Confirmar com o professor se aceita seleção + fonte separado dentro da regra de até dez páginas.')
    itens = DADOS['trechos_existentes_sugeridos']
    for i in range(5):
        iniciar_pagina(doc, f'{prefixo}_{i+2:02}', f'8. Código — seleção {i+1}/5')
        texto(doc, 'Extratos técnicos para estudo e revisão; inserir identificação e comentários próprios na entrega autorizada.')
        for item in itens[i*2:i*2+2]: trecho(doc, item)


def montar():
    doc = Document(); configurar(doc)
    marcadores = []
    def pagina(grupo, titulo, perguntas=None, referencia='', linhas=12):
        indice = sum(g == grupo for g, _ in marcadores) + 1
        m = f'APS_{grupo.upper()}_{indice:02}'
        iniciar_pagina(doc, m, titulo, not marcadores); marcadores.append((grupo, m))
        if perguntas: area_redacao(doc, perguntas, referencia, linhas)

    pagina('capa', 'ALERTA DE ALAGAMENTOS')
    texto(doc, 'MODELO PREENCHÍVEL DE ORGANIZAÇÃO DA APS', True)
    texto(doc, 'Documento de apoio para o grupo produzir e revisar sua própria redação. Não representa trabalho acadêmico pronto para submissão.')
    texto(doc, 'Identificação pessoal não preenchida, conforme solicitado. A capa final deverá observar os dados exigidos pela instituição.')
    texto(doc, 'O item 6 da rubrica informa que não serão aceitos trabalhos elaborados por Inteligência Artificial. O código e materiais anteriores tiveram auxílio de IA; a aceitação precisa ser esclarecida com o professor. Revisar ou assinar não garante conformidade com essa regra.')
    texto(doc, 'Os espaços reservados não contam como capítulos concluídos. Depois de escrever, conferir novamente conteúdo e paginação.')
    texto(doc, 'Base técnica inspecionada: ' + BASE)
    texto(doc, 'Data de organização: 08/11/2026. Não é declaração de data de entrega ou de horas realizadas.')
    pagina('indice', '2. Índice de organização')
    tabela(doc, ['Seção', 'Páginas previstas no modelo'], [
        ('1. Capa', '1'), ('2. Índice', '2'), ('3. Objetivo e motivação', '3'),
        ('4. Introdução', '4–5'), ('5. Fundamentos', '6–9'), ('6. Plano de desenvolvimento', '10–14'),
        ('7. Projeto: requisitos, quatro UML e DER', '15–20'), ('8. Relatório de código selecionado', '21–26'),
        ('9. Preparação da apresentação', '27'), ('10. Bibliografia a completar', '28'),
        ('11. Instrução para anexar fichas oficiais', '29')], 10)
    texto(doc, 'Atualizar o índice após qualquer edição ou inserção. O modelo usa quebras de página para reservar espaço; isso não comprova que um capítulo escrito atende ao mínimo exigido.')
    texto(doc, 'Orçamento: objetivo 1/2; introdução 2/4; fundamentos 4/8; plano 5/15; projeto 6/8; código 6/10 páginas (reservadas / máximo). A ficha incluída é uma orientação, não o formulário oficial.')
    pagina('objetivo', '3. Objetivo e motivação — 1 página reservada', [
        'Qual problema concreto o grupo pretende tratar e por que escolheu esse tema?',
        'Formule o objetivo geral e os específicos, vinculando-os ao cadastro e consulta entre dispositivos.',
        'Defina um critério observável de conclusão e deixe explícito que os relatos não são alertas oficiais.'], 'README.md; roteiro de validação física em TESTES.md.', 15)
    intro = [
        ('Contexto e delimitação', ['Que contexto urbano justifica o tema? Apoiar afirmações e estatísticas em fontes realmente consultadas.', 'Quem são os participantes e quais situações o protótipo cobre?', 'Delimitar informações relatadas, localização opcional, mídia e ausência de verificação oficial.']),
        ('Visão do trabalho e organização', ['Apresentar as partes do sistema sem antecipar toda a fundamentação.', 'Explicar o fluxo móvel escolhido com Expo Go e a dependência do computador servidor.', 'Orientar o leitor sobre os próximos capítulos e declarar quais validações ainda estão pendentes.'])]
    for titulo, perguntas in intro: pagina('introducao', '4. Introdução — ' + titulo, perguntas, 'README.md; ARQUITETURA.md; fontes de contexto a registrar pelo grupo.')
    fundamentos = [
        ('Sistemas distribuídos e middleware', ['Definir sistema distribuído, processos, heterogeneidade e modelo cliente-servidor com bibliografia.', 'Explicar a função de middleware e relacioná-la à intermediação entre aplicativo, serviço e armazenamento.', 'Distinguir comunicação entre processos de banco distribuído, replicação e tolerância a falhas.']),
        ('Comunicação e representação', ['Explicar requisição/resposta, métodos, recursos e códigos HTTP.', 'Comparar JSON e multipart, indicando seu uso em relatos e anexos.', 'Discutir serialização, tempo limite e significado de erro de rede versus erro HTTP.']),
        ('Mobilidade, localização e mapas', ['Explicar características e restrições de dispositivos móveis e de uma rede variável.', 'Definir posicionamento/GNSS, permissões e coleta em primeiro plano, sem chamar o GPS simulado de teste real.', 'Descrever coordenadas, mapas e mosaicos, provedores externos, atribuição e compartilhamento opcional.']),
        ('Segurança, persistência e falhas', ['Diferenciar autenticação, autorização, hash de senha, sessão e transporte HTTPS.', 'Explicar persistência, transações, concorrência e a diferença entre banco e arquivos anexados.', 'Analisar falha parcial, atualização manual e o risco de repetir cadastro quando a confirmação se perde.'])]
    for titulo, perguntas in fundamentos: pagina('fundamentos', '5. Fundamentos — ' + titulo, perguntas, 'Bibliografia efetivamente estudada; contrato API.md e módulos indicados no inventário para aplicação dos conceitos.')
    planos = [
        ('Escopo e requisitos', ['Identificar requisitos funcionais, restrições e critérios de aceitação.', 'Distinguir versão inicial e ampliação com login, GPS, mapa e anexos.', 'Descrever prioridades sem acrescentar funções não implementadas.']),
        ('Elementos, ferramentas e ambiente', ['Justificar Python/JavaScript, Flask/React Native/Expo como ferramentas de implementação.', 'Registrar versões e recursos reais usados pelo grupo.', 'Explicar duas aplicações servidoras no desenvolvimento, dependências e configurações locais.']),
        ('Etapas e integração', ['Separar planejamento inicial de execução efetivamente observada.', 'Relacionar etapas de banco, API, sessão, interface e integração.', 'Preencher responsáveis e datas reais; não converter o plano de 21 dias em diário realizado.']),
        ('Verificação e evidências', ['Definir como requisitos serão testados e associar cada um a evidências.', 'Explicar o alcance de 56 testes da API e 15 cenários web documentados, sem atribuir execução a alunos sem confirmação.', 'Planejar teste com dois celulares, GPS real, mídia, autorização e recuperação de falhas.']),
        ('Riscos, backup e demonstração', ['Identificar dependência de rede/servidor/provedores e medidas de diagnóstico.', 'Descrever backup consistente do SQLite e uploads com API parada.', 'Planejar ensaio e divisão real de apresentação, incluindo todos os integrantes.'])]
    for titulo, perguntas in planos: pagina('plano', '6. Plano de desenvolvimento — ' + titulo, perguntas, 'README.md; TESTES.md; ENTREGA.md; DIARIO.md; dados de execução a confirmar pelo grupo.')
    pagina('projeto', '7. Projeto — levantamento de requisitos', [
        'Construir uma tabela com identificador, descrição, prioridade, regra e evidência por requisito.',
        'Cobrir cadastro/login/logout, relatos, autoria, GPS opcional, lista/mapa, mídia privada e migração.',
        'Relacionar cada requisito ao módulo existente; separar limitação, regra de negócio e requisito não funcional.'], 'INVENTARIO_TECNICO.json; API.md; ARQUITETURA.md.', 9)
    for titulo, nome, observacao in [
        ('Casos de uso', DIAGRAMAS[0], 'Validar atores, fronteira do sistema e operações disponíveis para participante e autor.'),
        ('Classes', DIAGRAMAS[1], 'Modelo conceitual: as entidades não são classes Python implementadas. Explicar o mapeamento para tabelas e serviços funcionais.'),
        ('Sequência', DIAGRAMAS[2], 'Conferir ordem de autenticação, validação, arquivo, transação, resposta e compensação em falha.'),
        ('Atividades', DIAGRAMAS[3], 'Conferir início/fim, decisões, localização opcional e retorno ao formulário em falha, sem inventar paralelismo.')]:
        pagina('projeto', '7. Projeto — UML: ' + titulo)
        texto(doc, 'REFERÊNCIA TÉCNICA ASSISTIDA — o grupo deve conferir e elaborar a versão aceita para entrega.', True)
        imagem = SAIDA / 'diagramas' / (nome + '.png')
        figura(doc, imagem)
        texto(doc, observacao)
        texto(doc, 'Revisão e explicação próprias do grupo: ____________________________________')
    pagina('projeto', '7. Projeto — DER do banco')
    texto(doc, 'Modelo físico extraído de schema.sql; DER é separado dos quatro diagramas UML.', True)
    figura(doc, SAIDA / 'diagramas' / (DIAGRAMAS[4] + '.png'))
    texto(doc, 'No banco, uma ocorrência admite 0..N anexos; a API limita a um no cadastro. Autor ausente é permitido para o legado. CHECK de coordenadas em par existe no schema novo, com validação também na API.')
    texto(doc, 'Confirmar os atributos, tipos, PK/FK e regras no inventário. Explicação própria do grupo: __________________')
    paginas_codigo(doc)
    marcadores += [('codigo', f'APS_COD_{i:02}') for i in range(1, 7)]
    pagina('oral', '9. Apresentação do programa em funcionamento')
    texto(doc, 'Todos os integrantes devem participar. A rubrica informa perda de 50% da nota para quem não participar.', True)
    tabela(doc, ['Etapa a ensaiar', 'Participante / tempo real'], [
        ('Objetivo e arquitetura', ''), ('Demonstração no computador e Expo Go', ''),
        ('Cadastro e consulta entre duas contas/dispositivos', ''), ('GPS, mapa, imagem e vídeo', ''),
        ('Autoria, falha parcial e persistência', ''), ('Limitações, evidências e perguntas', '')], 10)
    texto(doc, 'Usar APRESENTACAO.md. Registrar quem realmente apresentou e os resultados observados. Dois contextos de navegador não comprovam dois celulares, GPS real, SecureStore ou mapa nativo.')
    pagina('bibliografia', '10. Bibliografia — completar com fontes reais')
    texto(doc, 'Registrar somente fontes efetivamente consultadas pelo grupo, no padrão determinado pela instituição.')
    tabela(doc, ['Autor / organização', 'Título / edição / URL', 'Data real de acesso'], [('', '', '') for _ in range(6)], 10)
    texto(doc, 'Pontos de partida para estudo (não são declaração de leitura): bibliografia de Sistemas Distribuídos indicada pelo professor; especificação UML da OMG; RFC 9110 (HTTP), RFC 8259 (JSON) e RFC 7578 (multipart); documentação oficial das APIs móveis e do SQLite.')
    texto(doc, 'A fundamentação não deve ser composta apenas por páginas de ferramentas. Conferir conceitos, referências e citações na redação própria.')
    pagina('fichas', '11. Fichas individuais de APS — usar o modelo oficial')
    texto(doc, 'ESTA PÁGINA NÃO SUBSTITUI A FICHA PADRÃO DA INSTITUIÇÃO.', True)
    texto(doc, 'Anexar uma ficha oficial por aluno, com atividades cronológicas, horas reais por atividade, total e assinatura manuscrita do próprio aluno. A rubrica identifica a assinatura como requisito jurídico.')
    tabela(doc, ['Data real', 'Atividade realizada', 'Horas reais', 'Evidência'], [('', '', '', '') for _ in range(7)], 10)
    texto(doc, 'Tabela auxiliar para conferência — sem atribuição de autoria ou horas. Transcrever para o formulário oficial apenas o que cada aluno efetivamente realizou.')
    texto(doc, 'Total real de horas: ________   Assinatura manuscrita: somente na ficha oficial.')
    doc.save(SAIDA / 'MODELO_PREENCHIVEL_APS.docx')
    codigo = Document(); configurar(codigo); paginas_codigo(codigo, primeira=True)
    codigo.save(SAIDA / 'RELATORIO_TECNICO_CODIGO_SELECIONADO.docx')
    (SAIDA / 'ORCAMENTO_PAGINAS.json').write_text(json.dumps({'natureza': 'Planejamento do modelo; não atesta conteúdo acadêmico final.', 'base_commit': BASE, 'marcadores': marcadores, 'limites': LIMITES}, ensure_ascii=False, indent=2) + '\n')


def empacotar():
    arquivos = subprocess.check_output(['git', '-C', str(RAIZ), 'ls-tree', '-r', '--name-only', BASE]).decode().splitlines()
    arquivos = [n for n in arquivos if n.startswith(('backend/', 'mobile/', 'scripts/', 'tests/')) or n in ('README.md', 'LICENSE', '.gitignore')]
    manifesto = []
    with zipfile.ZipFile(SAIDA / 'FONTE_REFERENCIA_PARA_PREPARAR_NO_WINRAR.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for nome in arquivos:
            assert '/node_modules/' not in nome and '/uploads/' not in nome and not nome.endswith(('.db', '.env'))
            dados = fonte(nome); z.writestr('APS_8/' + nome, dados)
            manifesto.append(hashlib.sha256(dados).hexdigest() + '  ' + nome)
        z.writestr('APS_8/ORIGEM_DO_PACOTE.txt', 'ZIP de referência, não produzido pelo WinRAR e não pronto para upload UNIP.\nCommit: ' + BASE + '\nPreparar o arquivo definitivo com o WinRAR segundo a rubrica.\n')
    (SAIDA / 'SHA256_FONTES.txt').write_text('\n'.join(manifesto) + '\n')


if __name__ == '__main__':
    SAIDA.mkdir(parents=True, exist_ok=True)
    montar(); empacotar()
    print('Modelos DOCX e ZIP de referência gerados; converter e conferir a paginação PDF.')
