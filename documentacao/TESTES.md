# Testes e demonstração

Use dados fictícios. Registre a data real, os aparelhos, as versões e uma evidência de cada execução. A tabela manual começa como **pendente**: os passos abaixo são um roteiro, não uma alegação de teste realizado em celulares.

## Testes automatizados

No terminal da API, com o ambiente virtual ativado e na pasta `backend`:

```sh
python -m unittest discover -s tests -v
```

A suíte usa bancos temporários para não apagar nem alterar os dados da demonstração. Os testes HTTP locais e de banco não comprovam a rede Wi-Fi ou a compatibilidade com o Expo Go de um aparelho específico.

### Versão atual — login, autoria, GPS, mapas e anexos

Os comandos deste documento se referem ao código atual. Os totais de **21 testes da API e sete cenários web**, apresentados adiante, pertencem ao histórico da primeira versão e não validam os recursos novos.

| Verificação da versão atual | Estado de registro |
| --- | --- |
| Suíte da API: autenticação, autoria, coordenadas, upload e migração | 56 testes passaram; dependências Python verificadas com pip check |
| Fluxo integrado web com duas contas, localização simulada e mídia | 15 cenários passaram, sem erros de JavaScript |
| Lint, checagem de tipos e exportação da interface atual | Passaram; bundles Android, iOS e web gerados |
| Expo Go, GPS e anexos em dois celulares físicos | Pendente |

A evidência atual foi preservada em [evidencias-v2/](evidencias-v2/index.html), com execução de 07/11/2026 22:43:30 no fuso America/Sao_Paulo. A execução atual verificou cadastro/login/logout, expiração/revogação, duas contas com autoria, upload real de PNG/MP4 e reprodução do vídeo, GPS simulado, persistência de dados e arquivos, falha de rede e recuperação. Os tiles OpenStreetMap foram deliberadamente bloqueados para testar o fallback: não houve validação do mapa base online. A validação física ainda deve verificar a sessão obrigatória, o bloqueio de alteração por outra conta e a leitura autenticada de anexos. Localização simulada no navegador não comprova o sensor GPS de um celular. Mosaicos de mapa carregados pela rede comprovam somente o provedor e a conexão exercitados.

### Histórico da primeira versão — sem login, GPS ou anexos

Execução histórica de 7 de novembro de 2026, anterior à ampliação de escopo:

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

### Ensaio de apoio histórico da primeira versão

Em 7 de novembro de 2026, das **21:54:03 às 21:54:20 (America/Sao_Paulo)**, o fluxo integrado foi executado novamente com gravação: **sete cenários passaram**, sem erros de JavaScript nas páginas. A suíte da API também passou novamente nos 21 testes, assim como lint e checagem de tipos. O resultado em UTC e os hashes do código estão em [evidencias/resultado.json](evidencias/resultado.json).

Foram preservados dois vídeos WebM VP9 (cliente A: aproximadamente 15,0 segundos; cliente B: 9,0 segundos), oito capturas e o registro JSON. A [galeria local](evidencias/index.html) permite visualizar esse conjunto sem Internet. A abertura das oito imagens e a reprodução dos dois vídeos foram verificadas em Chromium; o layout foi conferido nas larguras de 390 e 1.280 pixels. Na nuvem, essa checagem usou um servidor HTTP local temporário para servir os arquivos da pasta.

O conjunto usa dados fictícios e clientes web isolados, com a regra antiga de atualização sem login. **Ele não demonstra autenticação, autorização, GPS ou mídia da versão atual. A execução em dois celulares físicos com Expo Go permanece pendente.** As mídias selecionadas em `documentacao/evidencias/` são versionadas; os arquivos brutos de cada nova rodada em `test-results/` continuam locais e ignorados pelo Git. Não substitua evidências antigas por uma execução nova sem revisar também o registro e os hashes correspondentes.

## Teste integrado opcional da interface web

O script `tests/fluxo_web.py` abre dois contextos de navegador com dimensões de celular e armazenamento isolado. Ele usa uma API real e um **banco e uploads temporários**, com duas contas diferentes. Verifica o fluxo com autenticação e autoria, localização simulada e mídia e para e reinicia sua própria API para testar recuperação. Não substitui dois celulares físicos e não utiliza o banco de demonstração.

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

Confira no relatório gerado os cenários realmente executados, sua conclusão e a versão/hash do código. A conta A deve resolver somente seu próprio relato; B deve consultar e ser impedida de alterar o relato de A. Os recursos de mapa usam serviços externos, enquanto o GPS web pode ser simulado pelo teste. Capturas, registro da API e `resultado.json` ficam em `test-results/`, fora do Git. Um resultado antigo não prova que uma execução nova terminou com sucesso.

Depois do teste, pare o Expo e remova a variável temporária do terminal antes de voltar ao celular. No CMD, use `set EXPO_PUBLIC_API_URL=`; no shell Linux/macOS, o prefixo usado acima se aplica apenas àquele comando. Configure novamente o IP real em `mobile/.env` e reinicie o Expo.

### Gravação de apoio reproduzível

Com os mesmos pré-requisitos do teste integrado, instale o FFmpeg pelo canal oficial do seu sistema e confira `ffmpeg -version`. Depois execute, na raiz:

```sh
python tests/fluxo_web.py --gravar
```

A opção grava as páginas Chromium usando CDP e o FFmpeg já instalado. Não baixa um codificador adicional. As pausas de leitura são usadas apenas durante a gravação. O teste continua verificando as condições da interface e o banco real temporário.

São gerados vídeos dos clientes, capturas e `resultado.json` em `test-results/`. Consulte os nomes e a quantidade no resultado da execução atual. O relatório registra o início/fim em UTC, os cenários, os erros de JavaScript e os hashes SHA-256 dos arquivos de código exercitados. Um resultado de sucesso só é escrito após as verificações e a finalização dos vídeos. O banco e os uploads de demonstração não são alterados.

Os vídeos mostram clientes de navegador, não gravações de Expo Go. A [galeria da primeira versão](evidencias/index.html) mantém o ensaio antigo e não comprova os recursos atuais. Ao selecionar uma nova gravação para o relatório, preserve a identificação da versão e não apresente localização simulada como teste de GPS físico.

## Roteiro manual

| Teste | Procedimento e resultado esperado | Estado inicial |
| --- | --- | --- |
| Cadastro de conta e login | Nome/e-mail/senha válidos criam conta; login inválido é recusado | Pendente |
| Sessão obrigatória | Sem Bearer ou com token revogado/expirado, API retorna `401` para relatos/anexos | Pendente |
| Logout | Sair com API acessível revoga a sessão; novo acesso exige login | Pendente |
| Sessão nativa e web | Expo Go restaura token; navegador exige login após recarregar | Pendente |
| Lista vazia | Em banco de teste novo, abrir Ocorrências: mostrar “Nenhuma ocorrência cadastrada.” | Pendente |
| Cadastro válido | Preencher e salvar; voltar à lista com o relato criado | Pendente |
| Bairro vazio | Enviar pela API: `400`; na tela: mensagem sem envio inválido | Pendente |
| Gravidade inválida | Enviar valor fora de baixa/media/alta pela API: `400` | Pendente |
| ID inexistente | Consultar e alterar identificador que não existe: `404` | Pendente |
| Detalhes | Abrir relato: conferir id, bairro, endereço, descrição, gravidade, situação e data | Pendente |
| Resolver como autor | A resolve seu relato, volta e reabre: situação permanece resolvida | Pendente |
| Outra conta | B consulta o relato de A, não recebe ação de resolver; PATCH direto autenticado como B retorna `403` | Pendente |
| Legado | Migrar banco da primeira versão: registro preservado com autor ausente e alteração recusada | Pendente |
| Persistência | Cadastrar, parar API com Ctrl+C, iniciar novamente e consultar: registro permanece | Pendente |
| Falha da API | Parar API e atualizar a lista: encerrar carregamento e mostrar erro com opção de tentar novamente | Pendente |
| Recuperação | Iniciar API e tentar novamente: lista volta a carregar | Pendente |
| Preservar formulário | Parar API e salvar: mostrar falha sem perder os campos | Pendente |
| Dois dispositivos | Cadastrar no celular A; atualizar no B: encontrar o mesmo id e os mesmos dados | Pendente |
| Atualizar entre aparelhos | Resolver no A; atualizar no B com outra conta: exibir resolvido | Pendente |
| GPS permitido | Pedir localização pela ação da tela, autorizar e conferir coordenadas e marcador | Pendente |
| GPS negado | Negar permissão e cadastrar sem coordenadas, sem bloqueio do fluxo | Pendente |
| Mapa sem GPS | Relato sem coordenadas continua na lista e não ganha marcador inventado | Pendente |
| Coordenadas inválidas | API recusa par incompleto, booleanos, valores não finitos ou fora do intervalo | Pendente |
| Imagem | JPEG/PNG válida aparece nos detalhes; arquivo servido sem EXIF e exige sessão | Pendente |
| Vídeo | MP4 válido até 20 MiB é aceito e reproduzido no aparelho | Pendente |
| Upload recusado | Arquivo inválido/acima do limite ou dois arquivos são recusados sem novo relato parcial | Pendente |
| Persistência de mídia | Reiniciar API com mesmo banco/uploads mantém acesso autenticado ao anexo | Pendente |
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
Contas diferentes (não anotar senhas ou tokens):
GPS / permissão / localização simulada ou sensor físico:
Anexo fictício / formato / tamanho:
Passos executados:
Resultado observado:
Passou / falhou / não executado:
Evidência (arquivo ou referência):
Problema e correção, se houver:
```

Não registre “passou” para testes apenas planejados. Se a API rodar na nuvem e o telefone não tiver uma rota até ela, isso é um bloqueio de conectividade da demonstração; um teste no mesmo computador não comprova o requisito de dois dispositivos.

## Preparar a demonstração

1. Pare a API e copie juntos `backend/alagamentos.db` e `backend/uploads/` para um backup fora do Git. Copie também o código do projeto.
2. O formato escolhido é Expo Go. Confira a compatibilidade do SDK 57 com o aplicativo instalado nos dois aparelhos.
3. Confirme computador e celulares na mesma rede e verifique se a rede permite comunicação entre participantes.
4. Ajuste o IPv4 da API em `mobile/.env` (`EXPO_PUBLIC_API_URL`) e reinicie o Expo.
5. Ative o ambiente virtual e inicie a API com `--host=0.0.0.0 --port=5000`, sem depuração.
6. Inicie o Expo no segundo terminal com `npx expo start --lan --port 8081 --clear`. Confira o IPv4 LAN no QR Code e o acesso do celular ao Node/Metro na porta 8081, além da API na 5000.
7. Abra `/saude` no navegador do celular e depois abra o aplicativo no Expo Go.

Durante a apresentação:

1. Entre com contas distintas nos dois celulares e explique que são relatos não verificados.
2. Cadastre um relato fictício no celular A, com GPS e mídia opcionais.
3. Atualize a lista do celular B, encontre o mesmo registro e abra os detalhes, o mapa e o anexo quando existirem.
4. Mostre que B não pode resolver o relato de A. No celular A, marque seu próprio relato como resolvido.
5. Atualize no B e mostre a alteração persistida.
6. Explique o caminho aplicativo → HTTP/JSON → API → SQLite e a atualização manual.
7. Mostre o efeito de parar e reiniciar a API, se houver tempo e uma cópia de segurança.

Uma gravação de apoio pode ajudar em caso de falha da rede, mas sua aceitação como entrega depende do professor.
