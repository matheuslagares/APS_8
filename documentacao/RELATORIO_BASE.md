# Alerta de Alagamentos — base para o relatório

Este texto organiza a parte técnica já implementada. O grupo deve revisar a redação, completar os campos em branco e adequar o documento às normas e à rubrica recebidas. Ele não comprova, por si só, o atendimento a exigências acadêmicas que ainda não foram fornecidas.

## Identificação — preencher com dados reais

```text
Instituição: __________________________________________________
Curso: ________________________________________________________
Disciplina / atividade: ________________________________________
Turma / período: _______________________________________________
Professor(a) / orientador(a): __________________________________
Integrantes / matrículas: ______________________________________
_______________________________________________________________
Cidade: _______________________________________________________
Data de entrega: _______________________________________________
Período real de desenvolvimento: _______________________________
Versão / commit efetivamente entregue: _________________________
```

## Resumo

O projeto Alerta de Alagamentos é um protótipo acadêmico para cadastrar e consultar relatos de alagamentos urbanos. A interface móvel, desenvolvida com JavaScript, React Native e Expo, comunica-se por HTTP com uma API em Python e Flask. A API autentica os participantes, valida os dados e mantém os registros em SQLite e os anexos no computador servidor. O fluxo permite listar relatos ou consultar um mapa, cadastrar com GPS e uma imagem ou vídeo opcionais, abrir detalhes e resolver um relato somente pela conta autora. O projeto permite estudar comunicação cliente-servidor, HTTP, persistência, autenticação, autorização, concorrência e falhas parciais. Os relatos são informações de participantes, sem verificação oficial. A versão atual depende da rede e de um único servidor e utiliza atualização manual entre clientes.

Palavras-chave sugeridas, sujeitas ao padrão da instituição: cliente-servidor; HTTP; API; persistência; aplicativo móvel.

## 1. Problema e objetivo

O problema proposto é organizar relatos de alagamentos urbanos em um local consultável por outros participantes. Um relato descreve uma situação informada por alguém; o sistema não confirma sua veracidade nem emite alertas oficiais.

O objetivo geral é permitir que um participante autenticado registre um relato pelo aplicativo e outro o consulte pela mesma API. Os objetivos específicos são validar os campos, manter registros e anexos após reiniciar a API, apresentar localização e mídia opcionais e restringir a alteração de situação ao autor.

O critério funcional de conclusão é cadastrar pelo celular, manter o dado no servidor e consultá-lo em outro dispositivo. A validação física desse critério deve ser registrada pelo grupo; os testes web com navegadores isolados não a substituem.

## 2. Escopo implementado

| Tela | Responsabilidade | Ações |
| --- | --- | --- |
| Entrar / Criar conta | Identificar o participante e criar uma sessão | Cadastrar conta, entrar, sair |
| Ocorrências | Consultar e apresentar a lista | Atualizar, abrir detalhes, iniciar cadastro |
| Mapa da listagem | Exibir os relatos com coordenadas | Alternar lista/mapa, abrir o relato |
| Novo registro | Receber textos, gravidade e campos opcionais | Obter localização com permissão, escolher uma foto ou vídeo, salvar, voltar |
| Detalhes | Mostrar o relato, mapa e anexo quando presentes | Autor pode marcar como resolvido; voltar |

Cada ocorrência possui identificador, bairro, endereço, descrição, gravidade, situação, data e autoria. O servidor gera o identificador e a data, usa o autor da sessão e atribui a situação inicial `ativo`. A gravidade aceita `baixa`, `media` ou `alta`; a situação aceita `ativo` ou `resolvido`. Latitude e longitude são opcionais, em par. Cada relato pode conter uma imagem JPEG/PNG ou vídeo MP4 de até 20 MiB.

Login, GPS, mapas e anexos ampliam o escopo da primeira versão. Notificações, rastreamento contínuo, moderação e sincronização em tempo real continuam fora do projeto. O formato de demonstração móvel definido é Expo Go; este trabalho não inclui a geração de um APK independente.

## 3. Fundamentação técnica aplicada

Na arquitetura cliente-servidor, o aplicativo solicita operações e a API processa essas solicitações. HTTP transporta os pedidos e as respostas. Métodos como `GET`, `POST` e `PATCH` expressam a operação desejada; códigos como `200`, `201`, `400` e `404` informam o resultado. JSON representa os campos; multipart permite enviar o anexo junto aos dados do relato.

A API constitui o contrato entre cliente e servidor. O celular não conhece o caminho do arquivo SQLite nem executa SQL diretamente. A mesma validação do servidor se aplica a qualquer cliente, mesmo que ele não utilize a interface do aplicativo.

Autenticação e autorização têm papéis diferentes. O token de sessão identifica uma conta; a verificação de autoria decide se ela pode alterar um relato específico. A API executa ambas as verificações. O login não verifica a identidade civil nem a veracidade das informações cadastradas.

Persistência significa manter os registros em armazenamento durável, permitindo consultá-los após reiniciar a API. Ela é diferente do estado temporário da tela. Neste projeto, o banco é um arquivo centralizado e não é distribuído.

Uma falha parcial ocorre quando uma parte do sistema continua disponível enquanto outra deixa de responder. O aplicativo pode permanecer aberto com a API desligada, mas suas consultas falham. A interface apresenta uma mensagem e permite tentar novamente após o serviço retornar. Isso trata o erro de comunicação; não oferece tolerância a falhas ou operação offline.

Concorrência significa a possibilidade de diferentes clientes enviarem pedidos em períodos sobrepostos. O SQLite coordena o acesso ao arquivo e serializa as gravações. A implementação não demonstra capacidade para um número ilimitado de clientes e não inclui teste de carga.

O grupo deve associar estes conceitos à bibliografia exigida na disciplina. As referências técnicas de ferramentas listadas em [DIARIO.md](DIARIO.md) apoiam o estudo, mas não substituem a fundamentação bibliográfica solicitada pelo professor.

## 4. Arquitetura e implementação

O sistema é composto por três partes:

| Parte | Tecnologia | Papel |
| --- | --- | --- |
| Aplicativo | JavaScript, React Native e Expo | Autenticar, receber informações, solicitar GPS e mostrar relatos, mapa e mídia |
| API | Python, Flask e Pillow | Validar, autenticar, autorizar alterações e fornecer anexos |
| Armazenamento | SQLite com `sqlite3` e pasta de uploads | Manter contas, sessões, relatos e anexos no servidor |

O aplicativo utiliza `fetch`, verifica os códigos HTTP e cancela requisições que ultrapassam o tempo limite. A interface apresenta carregamento, lista vazia, erro ou conteúdo, preserva os campos após falha de envio e bloqueia ações de gravação enquanto aguarda a resposta. A navegação coordena a autenticação e as telas de relatos.

As senhas são armazenadas com hash scrypt. Tokens aleatórios identificam sessões de até sete dias; o servidor armazena o hash SHA-256 do token. O aplicativo nativo usa SecureStore, enquanto a versão web mantém a sessão somente em memória e exige novo login ao recarregar. Sair revoga a sessão pela API.

O GPS é solicitado pelo participante em primeiro plano e pode ser recusado sem impedir o cadastro. As coordenadas são compartilhadas junto ao relato, sem acompanhamento contínuo. Os mapas nativos utilizam os provedores do dispositivo; a versão web usa Leaflet e OpenStreetMap com atribuição. O GPS web depende de HTTPS ou localhost, e o mapa depende da Internet.

O anexo é validado no servidor. Imagens são reprocessadas para remover EXIF; vídeos aceitos são MP4 dentro do limite de tamanho, sem garantia de duração máxima. Relato e anexo são cadastrados na mesma operação, evitando registros parciais. A leitura dos arquivos passa por uma rota autenticada.

A API disponibiliza saúde pública, cadastro de conta, login, consulta da sessão, logout e as operações de relatos e anexos autenticadas. Somente a conta autora pode atualizar a situação. O contrato completo consta em [API.md](API.md). Bairro, endereço e descrição são textos obrigatórios, com limites de 100, 200 e 1.000 caracteres após remover espaços nas pontas.

As consultas SQL usam parâmetros, mantendo os valores do usuário separados da instrução. As operações abrem e fecham suas conexões e confirmam transações antes de informar sucesso. Em falhas de gravação, alterações ainda não confirmadas são desfeitas e o detalhe técnico fica no terminal do servidor. As mensagens devolvidas ao aplicativo usam o formato `{"erro": "mensagem"}`.

O caminho padrão do banco é calculado a partir do arquivo do módulo, evitando criar bancos diferentes por iniciar o programa em outra pasta. O inicializador não apaga os registros e migra a estrutura anterior. Relatos sem autor identificado são preservados para consulta, sem atribuição automática e sem permissão de alteração. O banco e os uploads ficam fora do Git; o backup deve copiá-los juntos com a API parada.

Os diagramas de casos de uso, componentes, sequência, atividades e modelo do banco estão em [ARQUITETURA.md](ARQUITETURA.md). São preparatórios: o grupo deve selecionar e adequar os diagramas conforme a exigência recebida, sem assumir que a quantidade ou a notação já foram aprovadas.

## 5. Método de validação e resultados conhecidos

Na versão ampliada, 56 testes da API e 15 cenários integrados web passaram; lint, checagem de tipos e exportação Android/iOS/web também passaram. Os cenários integrados usaram duas contas, arquivos reais PNG/MP4, GPS simulado e tiles bloqueados para verificar o fallback do mapa. Isso não comprova GPS real, SecureStore ou mapas nativos em dois celulares. Consulte [TESTES.md](TESTES.md) para os detalhes e evidências atuais.

O registro histórico de desenvolvimento de 7 de novembro de 2026, em [TESTES.md](TESTES.md), informa os resultados abaixo para a **primeira versão, anterior a login, GPS, mapa e anexos**. Eles não validam as funcionalidades acrescentadas:

| Verificação documentada | Resultado | Limite da conclusão |
| --- | --- | --- |
| Suíte da API com bancos temporários | 21 testes passaram | Comprova os casos locais exercitados, não a rede dos celulares |
| Fluxo integrado Expo web + API real + SQLite temporário | Sete cenários passaram | Dois contextos isolados de navegador, não dois celulares físicos |
| Checagem de dependências Python, lint e checagem de tipos da interface | Passaram | Auxiliam a manutenção; não substituem o fluxo funcional |
| Exportação de bundles web, Android e iOS | Passou | Não gera APK/IPA nem comprova execução em aparelho |
| Execução em dois celulares com Expo Go | Pendente de registro físico | Necessária para comprovar o critério móvel de conclusão |

O fluxo integrado verificou cadastro, consulta pelo segundo cliente, resolução, atualização manual, preservação do formulário em falha de rede, bloqueio de envio duplicado durante uma requisição e recuperação após parar e reiniciar a API com o mesmo banco temporário. As verificações da API incluem validação de campos, códigos de erro, persistência e inicialização repetida sem apagar dados.

Esses resultados são o histórico conhecido, não uma afirmação de nova execução feita pelos integrantes. Os resultados da versão atual devem ser consultados em [TESTES.md](TESTES.md) e anexados com a versão efetivamente apresentada. Arquivos gerados em `test-results/` são ignorados pelo Git e podem não existir em um novo checkout. As gravações em [evidencias/](evidencias/LEIA-ME.md) são históricas da primeira versão e não demonstram o controle de autoria atual.

Preencher após o ensaio físico:

```text
Data e horário reais: __________________________________________
Responsáveis pelo teste: _______________________________________
Versão / commit testado: _______________________________________
Computador / sistema / versões: ________________________________
Celular A / sistema / versão Expo Go: __________________________
Celular B / sistema / versão Expo Go: __________________________
Rede e configuração usadas: ___________________________________
Contas diferentes usadas, sem senhas: __________________________
GPS permitido / negado, mapa e resultado: ______________________
Imagem / MP4, tamanho e resultado: _____________________________
Tentativa de alterar relato de outra conta e resultado: ________
Passos realmente executados: __________________________________
Resultado observado / passou / falhou / não executado: __________
Evidências anexadas: ___________________________________________
```

## 6. Limitações e discussão

Somente o autor autenticado pode atualizar a situação. Ainda assim, não há verificação de e-mail, recuperação de senha ou moderação. O login não confirma a identidade do participante e os relatos e sua gravidade não são verificados.

Os clientes precisam consultar novamente para enxergar alterações de outros participantes. Não existe atualização em tempo real. Como a API e o banco estão em um único computador, a indisponibilidade desse servidor ou da rede interrompe as operações. Não há replicação ou tolerância a falhas.

Os mapas dependem de provedores externos e da Internet. A localização e a mídia são opcionais e ficam acessíveis aos participantes autenticados; não há rastreamento em segundo plano. O serviço continua voltado à demonstração acadêmica em rede controlada, sem afirmar prontidão para publicação pública.

O bloqueio do botão evita novos toques durante o mesmo envio na interface. Não garante uma única gravação em todas as falhas de rede: se a resposta se perder após o servidor salvar, repetir o cadastro pode gerar outro relato. O protótipo não implementa chaves de idempotência. Nessa situação, deve-se consultar a lista antes de repetir o envio.

## 7. Considerações sobre o estágio atual

O protótipo amplia o fluxo de relatos com autenticação, autoria, localização e mídia opcionais. A avaliação deve utilizar os resultados da versão atual, mantendo o histórico anterior identificado separadamente. A comprovação do uso em dois dispositivos móveis depende do ensaio com Expo Go e do registro dos resultados físicos. A adequação final à avaliação depende da revisão do grupo e das exigências do professor.

## 8. Contribuições e esforço — preencher

| Integrante | Atividade efetivamente realizada | Período / data | Tempo real | Evidência |
| --- | --- | --- | --- | --- |
| __________ | __________ | __________ | __________ | __________ |
| __________ | __________ | __________ | __________ | __________ |
| __________ | __________ | __________ | __________ | __________ |

Use o [diário](DIARIO.md) para detalhar dificuldades, soluções e fontes realmente consultadas. Não atribua autoria, horas ou participação sem confirmar com os integrantes.

## 9. Referências e anexos — completar e revisar

Para cada fonte efetivamente consultada, registre autor ou organização, título, endereço e data real de acesso, no padrão da instituição. Consulte a lista de pontos de partida em [DIARIO.md](DIARIO.md). Não use esta base como declaração de leitura de fontes que o grupo não consultou.

```text
Referência 1: __________________________________________________
Referência 2: __________________________________________________
Referência 3: __________________________________________________
```

Anexe os diagramas exigidos, as evidências de testes e as fichas individuais solicitadas. Numere os anexos e cite cada um no trecho correspondente do relatório. Os requisitos específicos ainda precisam ser conferidos com a rubrica recebida.
