# Guia de organização da APS — rubrica recebida

Este guia transforma as exigências informadas em uma lista de trabalho. O grupo deve escrever e revisar o próprio texto, preencher dados reais e conferir a versão oficial da rubrica. Não é um relatório pronto nem uma declaração de aprovação acadêmica.

**Autoria e uso de IA:** o item 6 afirma: “Não serão aceitos trabalhos: elaborados por Inteligência Artificial”. O código e materiais deste repositório receberam auxílio de IA; a aceitação desse uso depende da orientação do professor. Antes de apresentá-los como entrega, o grupo precisa informar isso ao professor e obter orientação/autorização expressa sobre o que pode ser usado. Editar ou reescrever trechos não garante conformidade com essa regra.

## Ordem dos 11 itens

Os limites abaixo são os fornecidos na rubrica. Onde não foi informado um limite, não se deve inventar um.

| Ordem | Item | Limite informado | O que o grupo deve preparar |
| --- | --- | --- | --- |
| 1 | Capa | Não informado | Curso, tema, nome, RA e turma de cada aluno, conforme modelo exigido |
| 2 | Índice | Não informado | Seções na ordem solicitada, com páginas conferidas após a edição final |
| 3 | Objetivo e motivação | 1 a 2 páginas | Problema, finalidade, motivação e resultado pretendido, em palavras do grupo |
| 4 | Introdução | 2 a 4 páginas | Contexto, delimitação do tema e apresentação do trabalho |
| 5 | Fundamentos das tecnologias para dispositivos móveis, Sistema Distribuído e Middleware | 4 a 8 páginas | Conceitos gerais apoiados em fontes efetivamente consultadas e relacionados ao projeto |
| 6 | Plano de desenvolvimento: elementos e ferramentas | 5 a 15 páginas | Decisões, recursos, etapas, planejamento e justificativas; observar a regra de autoria e IA |
| 7 | Projeto: estrutura e módulos | 3 a 8 páginas | Organização e responsabilidades dos componentes, dados, fluxos e diagramas exigidos |
| 8 | Relatório com linhas de código comentadas | Até 10 páginas | Título, participantes e código comentado; preparar também o fonte completo no formato de envio exigido |
| 9 | Apresentação do programa funcionando | Sem limite de páginas informado | Demonstrar no computador todas as funções e os extras implementados, com participação de todos os membros |
| 10 | Bibliografia | Não informado | Fontes realmente usadas, no padrão solicitado pela instituição |
| 11 | Ficha de APS de cada aluno | Não informado | Modelo oficial individual, atividades e horas reais, total e assinatura manuscrita |

A indicação de que os “tópicos 1 a 6” compõem a atividade/nota do primeiro bimestre deve ser confirmada com o professor, pois há ambiguidade de numeração no material recebido. Não deduza dessa frase um prazo, uma dispensa de itens ou uma nova divisão de capítulos.

## Perguntas para escrever os itens 3 a 7

Use as perguntas para orientar a pesquisa e a redação. Não transforme as respostas em afirmações de testes ou atividades ainda não realizados.

### 3. Objetivo e motivação

- Qual problema o grupo pretende tratar com o registro de relatos de alagamentos?
- Quem consulta e quem cadastra? Qual resultado permite avaliar o objetivo?
- Por que registrar e consultar relatos em dispositivos diferentes é adequado ao tema?
- O que está fora do escopo? Como deixar claro que são relatos não verificados, e não alertas oficiais?

### 4. Introdução

- Qual é o contexto do problema e quais fontes sustentam esse contexto?
- Como o trabalho está delimitado, sem prometer monitoramento oficial ou prevenção de desastres?
- Quais partes compõem a solução e como o leitor encontrará os próximos capítulos?

Não inclua estatísticas sem fonte nem invente entrevistas, levantamentos ou validação de usuários.

### 5. Fundamentos

| Assunto | Pergunta orientadora e vínculo com o programa |
| --- | --- |
| Dispositivos móveis e mobilidade | Quais características do celular afetam a interface, as permissões e a dependência de rede? |
| Sistema distribuído | Quais processos estão em dispositivos distintos? O que é centralizado? Por que haver dois clientes não significa ter um banco distribuído? |
| Middleware | O que a bibliografia define como middleware? Que mediação entre cliente, serviço e armazenamento existe aqui? Evitar chamar qualquer biblioteca de middleware sem explicar a definição adotada. |
| HTTP e serialização | Como métodos, rotas e códigos expressam operações? Como JSON e multipart representam dados e anexos? |
| Localização e mapas | Como funciona a obtenção opcional da posição em primeiro plano? Quais permissões e serviços externos estão envolvidos? |
| Segurança | Qual a diferença entre autenticar uma conta e autorizar a alteração de um relato? Para que servem hash de senha, token de sessão e transporte HTTPS? |
| Persistência e concorrência | O que `commit` confirma? Onde ficam banco e anexos? Como o SQLite coordena gravações concorrentes? |
| Falhas parciais | O que acontece se a API parar enquanto a interface permanece aberta? Quais garantias o protótipo não oferece? |

Python, JavaScript, Flask, React Native e Expo devem ser tratados como ferramentas no plano de desenvolvimento. A fundamentação deve estudar conceitos, com referências, e depois relacioná-los ao projeto. Uma descrição de comandos de instalação ou uma lista de frameworks não substitui esse capítulo. A comunicação HTTP é um mecanismo técnico do aplicativo; não se deve transformar o tema da APS em chat ou acrescentar funções de comunicação vedadas pela rubrica.

### 6. Plano de desenvolvimento

- Que requisitos foram definidos e quais decisões mudaram durante o trabalho?
- Quais ferramentas, versões e recursos foram usados e por quê?
- Como as etapas foram distribuídas? Qual era o planejamento e qual foi a execução real?
- Que dificuldades ocorreram e que evidências sustentam as soluções registradas?
- Como foram planejados testes, integração, backup e demonstração?

Separe estimativa de esforço de horas efetivamente realizadas. Consulte [DIARIO.md](DIARIO.md) para registrar o trabalho real e respeite a regra de autoria/IA indicada no início deste guia.

### 7. Estrutura e módulos

- Qual a responsabilidade do aplicativo, da API, do SQLite e da pasta de anexos?
- Como login, cadastro de relato, GPS opcional, mídia e autorização se conectam?
- Como um dado atravessa cliente, HTTP, validação, transação e resposta?
- Quais telas e módulos correspondem aos requisitos efetivamente implementados?

**Diagramas confirmados pelo usuário:** casos de uso, classes, sequência e atividades. O grupo deve validar o conteúdo e a notação de cada diagrama com o código e o professor. O DER representa o modelo de dados e deve ser tratado separadamente, sem ser contado automaticamente como um desses quatro UML. [ARQUITETURA.md](ARQUITETURA.md) fornece material preparatório para revisão.

## Código e forma de envio — item 8

O relatório de código tem limite de dez páginas e deve identificar título e participantes. O fonte completo também precisa estar disponível. Se todas as linhas não couberem de forma legível, confirme com o professor se aceita duas partes: relatório de até dez páginas com seleção comentada e fonte completo no arquivo compactado. Não omita código obrigatório nem reduza a fonte a ponto de impedir a leitura para contornar o limite.

O roteiro recebido solicita **compactar o fonte com WinRAR e renomear o arquivo para `.doc`** para o envio. Isso não converte o conteúdo em documento do Word: ele continua sendo um arquivo RAR com outro nome. Mantenha uma cópia original `.rar` e siga a orientação oficial de envio. Um ZIP renomeado para `.rar` ou `.doc` não é um RAR. O relatório Word real e o pacote de fonte são objetos diferentes.

## Apresentação, bibliografia e fichas — itens 9 a 11

- **Apresentação:** ensaiar o programa funcionando no computador e o fluxo escolhido com Expo Go, mostrando todas as funções e os extras implementados. A rubrica exige todos os membros e informa perda de 50% para quem não participar. Registrar o que cada integrante realmente apresentou; não simular participação ausente. [APRESENTACAO.md](APRESENTACAO.md) ajuda a organizar o ensaio.
- **Bibliografia:** registrar autores/organizações, títulos, endereços e datas reais de consulta conforme o padrão exigido. Não inventar fontes nem declarar leitura de referências não consultadas.
- **Ficha por aluno:** utilizar a ficha oficial, com atividades, horas reais, total e assinatura manuscrita. A assinatura é obrigatória e foi indicada como requisito jurídico. Este guia não substitui o formulário oficial; não gerar assinatura nem atribuir horas automaticamente.

Plágio, texto mal redigido e entrega sem código não são aceitos pela rubrica. A revisão final deve conferir autoria, clareza, limites de páginas, índice, código, arquivos e evidências correspondentes à versão apresentada.

## Pendências a resolver antes da entrega

- [ ] Orientação/autorização expressa do professor sobre o auxílio de IA já utilizado.
- [x] Tipos dos quatro UML confirmados: casos de uso, classes, sequência e atividades; DER separado.
- [ ] Validação da notação e do conteúdo dos diagramas pelo grupo/professor.
- [ ] Interpretação dos “tópicos 1 a 6” no primeiro bimestre e prazos oficiais.
- [ ] Forma aceita para relatório de código até dez páginas e fonte completo, se necessário.
- [ ] Fichas oficiais individuais preenchidas com dados reais e assinaturas manuscritas.
- [ ] Teste físico com Expo Go e participação de todos no ensaio e na apresentação.
