"""Versão integral produzida com IA; não simula autoria, assinatura ou pesquisa de alunos."""
from pathlib import Path
import json
import shutil
import gerar_modelo_aps as g

DESTINO=g.RAIZ/'documentacao/rascunho_integral'
TEXTOS=json.loads((DESTINO/'TEXTOS_BASE.json').read_text())
ORIGEM=g.SAIDA
for nome in ['INVENTARIO_TECNICO.json','ESTRUTURA_ABNT.json','FONTE_REFERENCIA_PARA_PREPARAR_NO_WINRAR.zip','SHA256_FONTES.txt']:
    shutil.copy2(ORIGEM/nome,DESTINO/nome)
shutil.copytree(ORIGEM/'diagramas',DESTINO/'diagramas',dirs_exist_ok=True)
g.SAIDA=DESTINO
g.OUTPUT_MAIN='RASCUNHO_INTEGRAL_APS_ABNT'
g.OUTPUT_CODE='RELATORIO_CODIGO'
g.MAPA=json.loads((DESTINO/'MAPA_PAGINAS_ABNT.json').read_text()) if (DESTINO/'MAPA_PAGINAS_ABNT.json').exists() else {}
original_texto,original_nova,original_trecho,original_tabela=g.texto,g.nova_pagina,g.trecho,g.tabela
atual=[None]
RESUMO='''O projeto Alerta de Alagamentos é um protótipo acadêmico para registrar e consultar relatos de alagamentos urbanos por meio de um aplicativo móvel conectado a uma API. O objetivo é permitir que contas diferentes compartilhem registros mantidos em um servidor, com localização e mídia opcionais. A implementação utiliza arquitetura cliente-servidor, comunicação HTTP, JSON e multipart, autenticação por sessão e persistência em SQLite e arquivos privados. O aplicativo permite criar conta, entrar, consultar lista ou mapa, cadastrar, abrir detalhes e resolver relatos pela conta autora. A análise técnica considera autenticação, autorização, transações, concorrência e falhas parciais. Os registros disponíveis documentam 56 testes da API aprovados e 15 cenários integrados web aprovados, com dados fictícios, GPS simulado e arquivos PNG e MP4 de teste. Esses resultados abrangem as operações exercitadas e a persistência após reiniciar a API. A execução em dois celulares com Expo Go, os recursos nativos e o mapa base online permanecem pendentes de validação física. O protótipo conserva armazenamento centralizado, atualização manual e dependência da rede. Os relatos são informações dos participantes, sem verificação oficial. A versão integral deste documento foi produzida com auxílio de inteligência artificial e deve ser avaliada pelo grupo e pelo professor segundo a regra de autoria recebida.'''
ABSTRACT='''Alerta de Alagamentos is an academic prototype for registering and consulting user reports of urban flooding through a mobile application connected to an API. Its objective is to allow different accounts to share records stored on a server, with optional location and media. The implementation uses a client-server architecture, HTTP communication, JSON and multipart representations, session authentication, and persistence in SQLite and private files. Users can register an account, sign in, consult a list or map, create reports, view details, and resolve reports through the author's account. The technical analysis addresses authentication, authorization, transactions, concurrency, and partial failures. The available records document 56 successful API tests and 15 successful integrated web scenarios using fictitious data, simulated geolocation, and PNG and MP4 test files. These results cover the exercised operations and persistence after restarting the API. Execution on two physical phones using Expo Go, native capabilities, and online base maps still requires physical validation. Storage remains centralized, updates are requested manually, and operation depends on connectivity. Reports are participant statements without official verification. This draft was produced with artificial intelligence assistance and requires review under the stated authorship requirements.'''
FIGURAS={
1:'A Figura 1 apresenta os atores e as funcionalidades disponibilizadas. O visitante cria conta ou entra; o participante autenticado consulta e cadastra. O papel de autor depende do relato selecionado e permite resolver o próprio registro. Localização e anexo ampliam o cadastro de forma opcional.',
2:'A Figura 2 representa entidades conceituais e módulos funcionais. Usuário, sessão, ocorrência e anexo descrevem conceitos de dados. A implementação utiliza funções e SQL, sem classes Python correspondentes a cada entidade. As dependências indicam o acesso da API aos serviços de sessão e armazenamento.',
3:'A Figura 3 descreve um cadastro autenticado. A API identifica a sessão, valida a entrada e prepara o arquivo opcional antes dos registros no banco. Após a confirmação, a resposta permite atualizar a lista. Uma falha de transação provoca rollback e remoção compensatória do arquivo preparado.',
4:'A Figura 4 apresenta as decisões do fluxo de cadastro. GPS e mídia são opcionais. Uma entrada inválida retorna ao formulário, enquanto uma sessão recusada exige novo acesso. Os estados de erro preservam os dados quando possível e o sucesso leva à consulta da lista atualizada.',
5:'A Figura 5 apresenta o modelo físico. As chaves estrangeiras relacionam sessões e relatos às contas e os metadados dos arquivos às ocorrências. O autor pode ser nulo nos dados legados. O banco permite vários anexos associados, enquanto a API restringe o cadastro atual a um arquivo.'}
CONCLUSAO='''O protótipo implementa o fluxo de relatos com autenticação, autoria, localização e mídia opcionais. Os testes documentados demonstram as operações locais exercitadas, a interação entre duas contas web e a persistência de dados e arquivos após reiniciar o serviço. A regra de alteração exclusiva pelo autor é aplicada no servidor e refletida pela interface.

A avaliação deve considerar as limitações observadas: armazenamento e API centralizados, atualização manual, dependência de rede e de provedores de mapas, ausência de moderação e de operação offline. Os testes web utilizaram coordenadas simuladas e não substituem os recursos de celulares físicos. O critério móvel final depende do ensaio em dois aparelhos com Expo Go e do registro de seus resultados.

A organização em cliente, API e armazenamento permite relacionar a implementação aos conceitos de comunicação entre processos, representação de dados, autenticação, autorização e transações. A continuidade do trabalho deve priorizar a validação física e a preparação da demonstração, conservando a rastreabilidade entre requisito, código e evidência. Informações acadêmicas individuais permanecem sujeitas à confirmação de cada participante.'''
COMENTARIOS=[
'A conexão é configurada com acesso por nome de coluna e chaves estrangeiras ativas. O bloco confirma a transação no sucesso, desfaz em exceção e fecha o recurso ao terminar.',
'O token aleatório é entregue ao cliente, enquanto apenas seu hash é registrado. A validade de sete dias limita a sessão, e a consulta posterior usa o hash para identificar a conta.',
'A requisição protegida precisa apresentar Bearer válido. A associação entre sessão e conta é consultada antes de disponibilizar a operação; uma sessão ausente ou vencida recebe 401.',
'Latitude e longitude são aceitas em conjunto. A validação rejeita tipos indevidos, valores não finitos e coordenadas fora dos intervalos, evitando posições inválidas no mapa.',
'Os valores são passados separadamente ao comando SQL. A ocorrência e seus metadados são confirmados na transação; a exceção também remove o arquivo preparado.',
'A autorização compara a conta da sessão com o autor antes do UPDATE. Outra conta pode consultar o registro compartilhado, mas recebe 403 ao tentar resolver a ocorrência.',
'A imagem é orientada e recriada a partir dos pixels. O arquivo resultante não conserva os metadados EXIF da imagem de entrada, incluindo sua possível localização.',
'A função centraliza o envio da sessão e o cancelamento por prazo. No multipart, o cliente define o boundary; a resposta precisa ser verificada antes de indicar sucesso.',
'A permissão é solicitada por ação do participante e a espera tem prazo. O resultado não deve alterar uma tela desmontada ou um formulário que já esteja bloqueado para envio.',
'O mapa apresenta somente as coordenadas existentes nos relatos. O marcador usa os dados retornados pela API e oferece acesso ao registro correspondente.'
]

def nova(doc,identificador,grupo,titulo,**kwargs):
    if identificador=='CAPA':titulo='RASCUNHO INTEGRAL PRODUZIDO COM IA'
    return original_nova(doc,identificador,grupo,titulo,**kwargs)

def orientacoes(doc,perguntas,ref,linhas=0):
    chave=g.PAGINAS[-1]['id']
    for p in TEXTOS[chave].split('\n\n'):original_texto(doc,p)

def texto(doc,valor,estilo_nome='Normal',negrito=None):
    if valor.startswith('[Redigir, em um único'):valor=RESUMO
    elif valor.startswith('[Redigir a versão em língua'):valor=ABSTRACT
    elif valor.startswith('Palavras-chave:'):valor='Palavras-chave: sistemas distribuídos; aplicativo móvel; relatos de alagamentos; persistência.'
    elif valor.startswith('Keywords:'):valor='Keywords: distributed systems; mobile application; flood reports; persistence.'
    elif valor.startswith('[Apresentar e discutir a Figura'):
        import re
        valor=FIGURAS[int(re.search(r'Figura (\d+)',valor).group(1))];estilo_nome='Normal'
    elif valor.startswith('[Sintetizar, em redação própria'):
        for p in CONCLUSAO.split('\n\n'):original_texto(doc,p)
        return doc.paragraphs[-1]
    elif valor.startswith('[Citação curta') or valor.startswith('[Modelo de citação longa'):return doc.add_paragraph(style='Fonte ABNT')
    elif valor.startswith('Comentário próprio do grupo:'):
        valor=COMENTARIOS[atual[0]];estilo_nome='Fonte ABNT'
    elif valor.startswith('[Substituir por referências'):
        valor='As referências técnicas abaixo identificam documentos e o código que fundamentam a descrição. As referências externas devem ser conferidas pelo grupo; não foi atribuída uma data de consulta aos integrantes.'
    elif valor.startswith('[SOBRENOME, Prenome.'):
        for r in [
            'FIELDING, Roy T.; NOTTINGHAM, Mark; RESCHKE, Julian. HTTP Semantics. IETF, 2022. RFC 9110. DOI: 10.17487/RFC9110.',
            'BRAY, Tim. The JavaScript Object Notation (JSON) Data Interchange Format. IETF, 2017. RFC 8259. DOI: 10.17487/RFC8259.',
            'MASINTER, Larry. Returning Values from Forms: multipart/form-data. IETF, 2015. RFC 7578. DOI: 10.17487/RFC7578.',
            'ALERTA DE ALAGAMENTOS. Código-fonte do projeto. GitHub, 2026. Versão 028b7041702f68e1a473d57acbe95037a8341a79. Disponível em: https://github.com/matheuslagares/APS_8. Base técnica inspecionada e identificada nos anexos.'
        ]:
            original_texto(doc,r,'Referencia ABNT');doc.add_paragraph(style='Referencia ABNT')
        return doc.add_paragraph(style='Fonte ABNT')
    elif valor.startswith('[AUTOR/ENTIDADE.') or valor.startswith('[Preencher as demais referências'):return doc.add_paragraph(style='Fonte ABNT')
    elif valor=='MODELO PREENCHÍVEL DE APS':valor='RASCUNHO INTEGRAL PRODUZIDO COM IA'
    elif valor=='Modelo de organização com formatação ABNT':valor='Documentação técnica em formato acadêmico — versão para revisão'
    elif valor.startswith('Modelo de organização da Atividade'):valor='Documentação do protótipo Alerta de Alagamentos, organizada para Atividade Prática Supervisionada. Versão integral produzida com auxílio de inteligência artificial; sua utilização depende da regra de autoria e da orientação do professor. Identificação pessoal omitida conforme solicitado.'
    return original_texto(doc,valor,estilo_nome,negrito)

def trecho(doc,item):
    atual[0]=g.DADOS['trechos_existentes_sugeridos'].index(item)
    original_trecho(doc,item)

def tabela(doc,cabecalhos,linhas,titulo,*args,**kwargs):
    if titulo=='Matriz de requisitos a preencher':
        titulo='Rastreabilidade dos requisitos implementados'
        linhas=[('Conta e sessão','API e AuthScreen','Login válido; 401 sem sessão'),('Autoria','API e Detalhes','403 para outra conta'),('Relato','API e Cadastro','Campos válidos e persistência'),('GPS e mapa','LocalizacaoCampos e Mapas','Coordenadas válidas e fallback'),('Mídia privada','midia.py e AnexoViewer','Upload e acesso autenticado')]
    return original_tabela(doc,cabecalhos,linhas,titulo,*args,**kwargs)

g.nova_pagina,g.orientacoes,g.texto,g.trecho,g.tabela=nova,orientacoes,texto,trecho,tabela
if __name__=='__main__':
    g.montar()
    from docx import Document
    caminho=DESTINO/(g.OUTPUT_MAIN+'.docx')
    documento=Document(caminho)
    for paragrafo in list(documento.paragraphs):
        if paragrafo.text.startswith(('Título: subtítulo.', 'Título da página.')):
            paragrafo._element.getparent().remove(paragrafo._element)
    documento.core_properties.title='Alerta de Alagamentos — documentação integral'
    documento.save(caminho)
    print('Rascunho integral gerado; conferir PDF, sumário e limites antes de compartilhar.')
