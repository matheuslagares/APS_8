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

O projeto Alerta de Alagamentos é um protótipo acadêmico para cadastrar e consultar relatos de alagamentos urbanos. A interface móvel, desenvolvida com JavaScript, React Native e Expo, comunica-se por HTTP com uma API em Python e Flask. A API valida os dados, executa operações parametrizadas e mantém os registros em um banco SQLite no computador servidor. O fluxo implementado permite listar relatos, cadastrar um novo registro, consultar seus detalhes e atualizar a situação para resolvido. O projeto permite estudar comunicação cliente-servidor, JSON, persistência, concorrência e falhas parciais. Os relatos são informações de participantes, sem verificação oficial. A primeira versão depende da rede e de um único servidor, usa atualização manual e não possui autenticação.

Palavras-chave sugeridas, sujeitas ao padrão da instituição: cliente-servidor; HTTP; API; persistência; aplicativo móvel.

## 1. Problema e objetivo

O problema proposto é organizar relatos de alagamentos urbanos em um local consultável por outros participantes. Um relato descreve uma situação informada por alguém; o sistema não confirma sua veracidade nem emite alertas oficiais.

O objetivo geral é permitir que um participante registre um relato pelo aplicativo e outro o consulte por meio da mesma API. Os objetivos específicos são validar os campos no servidor, manter os registros após reiniciar a API, apresentar os detalhes e salvar alterações de situação.

O critério funcional de conclusão é cadastrar pelo celular, manter o dado no servidor e consultá-lo em outro dispositivo. A validação física desse critério deve ser registrada pelo grupo; os testes web com navegadores isolados não a substituem.

## 2. Escopo implementado

| Tela | Responsabilidade | Ações |
| --- | --- | --- |
| Ocorrências | Consultar e apresentar a lista | Atualizar, abrir detalhes, iniciar cadastro |
| Novo registro | Receber os dados digitados | Validar, salvar, voltar |
| Detalhes | Mostrar o relato completo | Marcar como resolvido, voltar |

Cada ocorrência possui identificador, bairro, endereço, descrição, gravidade, situação e data de cadastro. O servidor gera o identificador e a data e atribui a situação inicial `ativo`. A gravidade aceita `baixa`, `media` ou `alta`; a situação aceita `ativo` ou `resolvido`.

Login, mapas, fotos, GPS, notificações e sincronização em tempo real ficam fora desta versão. O formato de demonstração móvel definido é Expo Go; este trabalho não inclui a geração de um APK independente.

## 3. Fundamentação técnica aplicada

Na arquitetura cliente-servidor, o aplicativo solicita operações e a API processa essas solicitações. HTTP transporta os pedidos e as respostas. Métodos como `GET`, `POST` e `PATCH` expressam a operação desejada; códigos como `200`, `201`, `400` e `404` informam o resultado. JSON representa os campos trocados entre os processos.

A API constitui o contrato entre cliente e servidor. O celular não conhece o caminho do arquivo SQLite nem executa SQL diretamente. A mesma validação do servidor se aplica a qualquer cliente, mesmo que ele não utilize a interface do aplicativo.

Persistência significa manter os registros em armazenamento durável, permitindo consultá-los após reiniciar a API. Ela é diferente do estado temporário da tela. Neste projeto, o banco é um arquivo centralizado e não é distribuído.

Uma falha parcial ocorre quando uma parte do sistema continua disponível enquanto outra deixa de responder. O aplicativo pode permanecer aberto com a API desligada, mas suas consultas falham. A interface apresenta uma mensagem e permite tentar novamente após o serviço retornar. Isso trata o erro de comunicação; não oferece tolerância a falhas ou operação offline.

Concorrência significa a possibilidade de diferentes clientes enviarem pedidos em períodos sobrepostos. O SQLite coordena o acesso ao arquivo e serializa as gravações. A implementação não demonstra capacidade para um número ilimitado de clientes e não inclui teste de carga.

O grupo deve associar estes conceitos à bibliografia exigida na disciplina. As referências técnicas de ferramentas listadas em [DIARIO.md](DIARIO.md) apoiam o estudo, mas não substituem a fundamentação bibliográfica solicitada pelo professor.

## 4. Arquitetura e implementação

O sistema é composto por três partes:

| Parte | Tecnologia | Papel |
| --- | --- | --- |
| Aplicativo | JavaScript, React Native e Expo | Receber informações e apresentar os estados da interface |
| API | Python e Flask | Validar, consultar e alterar relatos |
| Banco | SQLite, acessado com `sqlite3` | Manter os registros no servidor |

O aplicativo utiliza `fetch`, verifica os códigos HTTP e cancela requisições que ultrapassam o tempo limite. A interface apresenta carregamento, lista vazia, erro ou conteúdo, preserva os campos após falha de envio e bloqueia ações de gravação enquanto aguarda a resposta. A navegação usa o estado da aplicação para coordenar as três telas.

A API disponibiliza `GET /saude`, `GET /ocorrencias`, `POST /ocorrencias`, `GET /ocorrencias/<id>` e `PATCH /ocorrencias/<id>/situacao`. As regras completas constam em [API.md](API.md). Bairro, endereço e descrição são textos obrigatórios, com limites de 100, 200 e 1.000 caracteres após remover espaços nas pontas.

As consultas SQL usam parâmetros, mantendo os valores do usuário separados da instrução. As operações abrem e fecham suas conexões e confirmam transações antes de informar sucesso. Em falhas de gravação, alterações ainda não confirmadas são desfeitas e o detalhe técnico fica no terminal do servidor. As mensagens devolvidas ao aplicativo usam o formato `{"erro": "mensagem"}`.

O caminho padrão do banco é calculado a partir do arquivo do módulo, evitando criar bancos diferentes por iniciar o programa em outra pasta. O inicializador utiliza `CREATE TABLE IF NOT EXISTS` e não apaga a tabela existente. O arquivo do banco fica fora do Git e precisa de uma cópia separada para backup.

Os diagramas de casos de uso, componentes, sequência, atividades e modelo do banco estão em [ARQUITETURA.md](ARQUITETURA.md). São preparatórios: o grupo deve selecionar e adequar os diagramas conforme a exigência recebida, sem assumir que a quantidade ou a notação já foram aprovadas.

## 5. Método de validação e resultados conhecidos

O registro de desenvolvimento de 7 de novembro de 2026, em [TESTES.md](TESTES.md), informa os seguintes resultados:

| Verificação documentada | Resultado | Limite da conclusão |
| --- | --- | --- |
| Suíte da API com bancos temporários | 21 testes passaram | Comprova os casos locais exercitados, não a rede dos celulares |
| Fluxo integrado Expo web + API real + SQLite temporário | Sete cenários passaram | Dois contextos isolados de navegador, não dois celulares físicos |
| Checagem de dependências Python, lint e checagem de tipos da interface | Passaram | Auxiliam a manutenção; não substituem o fluxo funcional |
| Exportação de bundles web, Android e iOS | Passou | Não gera APK/IPA nem comprova execução em aparelho |
| Execução em dois celulares com Expo Go | Pendente de registro físico | Necessária para comprovar o critério móvel de conclusão |

O fluxo integrado verificou cadastro, consulta pelo segundo cliente, resolução, atualização manual, preservação do formulário em falha de rede, bloqueio de envio duplicado durante uma requisição e recuperação após parar e reiniciar a API com o mesmo banco temporário. As verificações da API incluem validação de campos, códigos de erro, persistência e inicialização repetida sem apagar dados.

Esses resultados são o histórico conhecido, não uma afirmação de execução feita pelos integrantes. Uma nova execução automatizada de apoio preservou os sete cenários aprovados, vídeos, capturas e hashes do código em [evidencias/](evidencias/LEIA-ME.md). Esse material também usa navegadores; não comprova aparelhos físicos. O grupo deve anexar a saída e as evidências da versão efetivamente apresentada. Arquivos brutos gerados em `test-results/` são ignorados pelo Git e podem não existir em um novo checkout; siga [TESTES.md](TESTES.md) para reproduzir a verificação.

Preencher após o ensaio físico:

```text
Data e horário reais: __________________________________________
Responsáveis pelo teste: _______________________________________
Versão / commit testado: _______________________________________
Computador / sistema / versões: ________________________________
Celular A / sistema / versão Expo Go: __________________________
Celular B / sistema / versão Expo Go: __________________________
Rede e configuração usadas: ___________________________________
Passos realmente executados: __________________________________
Resultado observado / passou / falhou / não executado: __________
Evidências anexadas: ___________________________________________
```

## 6. Limitações e discussão

Qualquer participante com acesso à API pode atualizar a situação, pois não há autenticação. Esta é uma limitação acadêmica explícita, não um controle adequado para uma operação pública. Os relatos e sua gravidade não são verificados.

Os clientes precisam consultar novamente para enxergar alterações de outros participantes. Não existe atualização em tempo real. Como a API e o banco estão em um único computador, a indisponibilidade desse servidor ou da rede interrompe as operações. Não há replicação ou tolerância a falhas.

O bloqueio do botão evita novos toques durante o mesmo envio na interface. Não garante uma única gravação em todas as falhas de rede: se a resposta se perder após o servidor salvar, repetir o cadastro pode gerar outro relato. O protótipo não implementa chaves de idempotência. Nessa situação, deve-se consultar a lista antes de repetir o envio.

## 7. Considerações sobre o estágio atual

O protótipo implementa o fluxo proposto e possui evidências automatizadas locais de funcionamento da API, da persistência e da interação entre dois clientes web. A comprovação do uso em dois dispositivos móveis depende do ensaio com Expo Go e do registro dos resultados físicos. A adequação final à avaliação depende da revisão do grupo e das exigências do professor.

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
