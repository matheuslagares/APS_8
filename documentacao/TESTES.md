# Testes e demonstração

Use dados fictícios. Registre a data real, os aparelhos, as versões e uma evidência de cada execução. A tabela manual começa como **pendente**: os passos abaixo são um roteiro, não uma alegação de teste realizado em celulares.

## Testes automatizados

No terminal da API, com o ambiente virtual ativado e na pasta `backend`:

```sh
python -m unittest discover -s tests -v
```

A suíte usa bancos temporários para não apagar nem alterar os dados da demonstração. Os testes HTTP locais e de banco não comprovam a rede Wi-Fi ou a compatibilidade com o Expo Go de um aparelho específico.

### Resultados executados no ambiente de desenvolvimento

Execução de 7 de novembro de 2026:

| Verificação | Resultado observado |
| --- | --- |
| `python -m unittest discover -s tests -v`, em `backend` | 21 testes passaram |
| `python -m pip check`, no ambiente virtual da API | Dependências sem incompatibilidades detectadas |
| `npm run lint`, em `mobile` | Passou |
| `npm run typecheck`, em `mobile` | Passou |
| `bash scripts/configurar_nuvem.sh`, na raiz | Passou; instalação repetida com `pip` e `npm ci`, banco inicializado sem apagar dados |
| `tests/fluxo_web.py`: Expo web, API real e SQLite temporário | 7 cenários passaram, sem erros de JavaScript capturados nas páginas |
| `npx expo export --platform all --max-workers 2 --output-dir dist`, em `mobile` | Exportação dos bundles web, Android e iOS passou |
| Demonstração em dois celulares físicos | Pendente |

Os testes da API exercitam saúde antes da criação do banco, lista vazia, cadastro, detalhes, alteração da situação, persistência em outra instância da aplicação, ordenação, campos definidos pelo servidor, tipos e limites, códigos de erro, SQL parametrizado, inicialização sem perda de dados e falhas de acesso ao banco. Isso comprova essas operações locais, sem comprovar a conectividade de aparelhos físicos.

A execução integrada usou dois contextos isolados de Chromium com dimensões de celular. Foram verificados: lista vazia; validação e preenchimento do formulário; falha de rede simulada mantendo os campos; cadastro HTTP real com bloqueio de toques repetidos; consulta e resolução pelo segundo cliente com atualização manual no primeiro; mensagem de erro após realmente encerrar o processo da API; e recuperação após iniciar outra API usando o mesmo SQLite temporário. O estado resolvido permaneceu salvo.

As evidências dessa execução no ambiente são `test-results/resultado.json`, `test-results/api.log` e as capturas `01-cadastro.png`, `02-detalhes.png` e `03-lista.png`. São arquivos gerados e ignorados pelo Git, disponíveis na máquina que executou o teste. Copie as evidências necessárias para o relatório do grupo antes de descartar o ambiente.

A exportação do Expo gerou bundles de aplicação para web (237 módulos, aproximadamente 452 KB), Android e iOS (596 módulos e aproximadamente 1,5 MB por plataforma). São bundles JavaScript/Hermes, não arquivos APK ou IPA instaláveis. A exportação valida o empacotamento do código, sem comprovar a execução em aparelhos físicos.

## Teste integrado opcional da interface web

O script `tests/fluxo_web.py` abre dois contextos de navegador com dimensões de celular e armazenamento isolado. Ele usa uma API real e um **banco temporário**, verifica o fluxo de cadastro/consulta/resolução e para e reinicia sua própria API para testar recuperação. Não substitui dois celulares físicos e não utiliza o banco de demonstração.

Pré-requisitos:

1. Instale a API em `backend/.venv` e o aplicativo em `mobile/node_modules`, conforme o README.
2. Pare sua API habitual: a porta `5000` deve estar livre. O script inicia e encerra somente a API do teste.
3. Inicie o Expo web na porta `8081` com a URL local de teste. A variável abaixo deve prevalecer sobre qualquer endereço de rede de `mobile/.env`.

No terminal do Expo, Windows CMD, a partir da raiz:

```bat
cd mobile
set "EXPO_PUBLIC_API_URL=http://127.0.0.1:5000"
npx expo start --web --port 8081
```

No Linux/macOS:

```sh
cd mobile
EXPO_PUBLIC_API_URL=http://127.0.0.1:5000 npx expo start --web --port 8081
```

Em outro terminal, na raiz do repositório, prepare as dependências opcionais. No Windows CMD:

```bat
py -m venv .venv-e2e
.venv-e2e\Scripts\activate.bat
python -m pip install -r tests/requirements-e2e.txt
python -m playwright install chromium
python tests/fluxo_web.py
```

No Linux/macOS:

```sh
python3 -m venv .venv-e2e
. .venv-e2e/bin/activate
python -m pip install -r tests/requirements-e2e.txt
python -m playwright install chromium
python tests/fluxo_web.py
```

O Playwright requer as bibliotecas de sistema necessárias ao Chromium; siga a orientação oficial da ferramenta se indicar alguma ausente. Quando houver um Chromium do sistema já disponível e compatível, `CHROMIUM_PATH` permite informar seu caminho sem baixar outro navegador. Essa variável é opcional e não deve ser copiada de outra máquina sem conferir o caminho real.

O teste cobre lista vazia, validação do formulário, preservação dos campos em falha de rede, cadastro persistido, bloqueio de envio duplicado, consulta por outro cliente, resolução, atualização manual, erro com API desligada e recuperação com persistência após reiniciar a API. Capturas de tela, registro da API e `resultado.json` ficam em `test-results/`, fora do Git. Confira que as evidências pertencem à execução atual; um resultado antigo não prova que uma execução nova terminou com sucesso.

Depois do teste, pare o Expo e remova a variável temporária do terminal antes de voltar ao celular. No CMD, use `set EXPO_PUBLIC_API_URL=`; no shell Linux/macOS, o prefixo usado acima se aplica apenas àquele comando. Configure novamente o IP real em `mobile/.env` e reinicie o Expo.

## Roteiro manual

| Teste | Procedimento e resultado esperado | Estado inicial |
| --- | --- | --- |
| Lista vazia | Em banco de teste novo, abrir Ocorrências: mostrar “Nenhuma ocorrência cadastrada.” | Pendente |
| Cadastro válido | Preencher e salvar; voltar à lista com o relato criado | Pendente |
| Bairro vazio | Enviar pela API: `400`; na tela: mensagem sem envio inválido | Pendente |
| Gravidade inválida | Enviar valor fora de baixa/media/alta pela API: `400` | Pendente |
| ID inexistente | Consultar e alterar identificador que não existe: `404` | Pendente |
| Detalhes | Abrir relato: conferir id, bairro, endereço, descrição, gravidade, situação e data | Pendente |
| Resolver | Tocar em “Marcar como resolvido”, voltar e reabrir: situação permanece resolvida | Pendente |
| Persistência | Cadastrar, parar API com Ctrl+C, iniciar novamente e consultar: registro permanece | Pendente |
| Falha da API | Parar API e atualizar a lista: encerrar carregamento e mostrar erro com opção de tentar novamente | Pendente |
| Recuperação | Iniciar API e tentar novamente: lista volta a carregar | Pendente |
| Preservar formulário | Parar API e salvar: mostrar falha sem perder os campos | Pendente |
| Dois dispositivos | Cadastrar no celular A; atualizar no B: encontrar o mesmo id e os mesmos dados | Pendente |
| Atualizar entre aparelhos | Resolver no B; atualizar no A: exibir resolvido | Pendente |
| Toques repetidos | Durante o envio, tocar várias vezes em salvar: ação permanece bloqueada até concluir | Pendente |
| Limites | Texto no limite é aceito; acima de 100/200/1.000 em bairro/endereço/descrição é recusado pela API | Pendente |
| JSON e conteúdo | Enviar lista JSON, JSON malformado e corpo sem Content-Type JSON: retornar erro coerente | Pendente |

Para o teste de lista vazia, use uma cópia de teste do projeto e um banco novo. Não apague um banco com dados que o grupo precisa preservar.

## Registro de execução manual

Copie este formulário para cada rodada:

```text
Data e horário reais:
Responsável:
Computador e sistema operacional:
Python / Node / Expo SDK / Expo Go:
Dispositivo A:
Dispositivo B:
Rede usada:
Passos executados:
Resultado observado:
Passou / falhou / não executado:
Evidência (arquivo ou referência):
Problema e correção, se houver:
```

Não registre “passou” para testes apenas planejados. Se a API rodar na nuvem e o telefone não tiver uma rota até ela, isso é um bloqueio de conectividade da demonstração; um teste no mesmo computador não comprova o requisito de dois dispositivos.

## Preparar a demonstração

1. Pare a API e copie `backend/alagamentos.db` para um local de backup fora do Git. Copie também o código do projeto.
2. Confirme com o professor se a apresentação pode usar Expo Go ou se exige APK. Este projeto usa o fluxo de desenvolvimento com Expo Go.
3. Confirme computador e celulares na mesma rede e verifique se a rede permite comunicação entre participantes.
4. Ajuste o IPv4 da API em `mobile/.env` (`EXPO_PUBLIC_API_URL`) e reinicie o Expo.
5. Ative o ambiente virtual e inicie a API com `--host=0.0.0.0 --port=5000`, sem depuração.
6. Inicie o Expo no segundo terminal.
7. Abra `/saude` no navegador do celular e depois abra o aplicativo no Expo Go.

Durante a apresentação:

1. Mostre a lista inicial e explique que são relatos não verificados.
2. Cadastre um relato fictício no celular A.
3. Atualize a lista do celular B e encontre o mesmo registro.
4. Abra os detalhes no B e marque como resolvido.
5. Atualize no A e mostre a alteração persistida.
6. Explique o caminho aplicativo → HTTP/JSON → API → SQLite e a atualização manual.
7. Mostre o efeito de parar e reiniciar a API, se houver tempo e uma cópia de segurança.

Uma gravação de apoio pode ajudar em caso de falha da rede, mas sua aceitação como entrega depende do professor.
