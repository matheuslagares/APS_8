# Alerta de Alagamentos

Protótipo acadêmico para **registrar e consultar relatos de alagamentos urbanos**. As informações são fornecidas pelos participantes: **não são alertas oficiais nem ocorrências verificadas**.

A versão atual acrescenta **cadastro e login**, **localização opcional com GPS e mapa** e **uma foto ou um vídeo opcional por relato** ao fluxo de Ocorrências, Novo registro e Detalhes. Somente o autor autenticado pode resolver seu relato. A API guarda os registros em SQLite e os anexos no computador; o celular acessa os dados e os arquivos pela API.

Os registros da versão inicial são preservados na migração. Como não têm autor identificado, ficam disponíveis para consulta, sem atribuição automática a uma conta e sem alteração de situação.

## Estrutura

```text
backend/          API em Python/Flask e banco SQLite
mobile/           Aplicativo em JavaScript/React Native com Expo
documentacao/     Contrato da API, conceitos, diagramas e roteiro de testes
```

```mermaid
flowchart LR
    A[Celular: aplicativo Expo] -->|HTTP e JSON| B[Computador: API Flask]
    B -->|SQL| C[(SQLite: alagamentos.db)]
    B --> D[Anexos privados: uploads]
```

## Preparar o computador

Instale Python 3.11 ou superior (testado com 3.12.14), Node.js LTS e Git. A versão de Node usada nos testes foi **24.22.1**, registrada em `mobile/.nvmrc`. Use um editor como VS Code. O projeto usa **Expo SDK 57** (`expo ~57.0.32`), **React 19.2.3** e **React Native 0.86.3**, a partir do template oficial blank. No Android, instale Expo Go e confira a compatibilidade com esse SDK em [expo.dev/go](https://expo.dev/go). O arquivo de dependências e o lockfile definem a combinação usada pelo projeto; não atualize pacotes aleatoriamente para corrigir incompatibilidades.

Abra esta pasta no terminal. Os comandos abaixo usam dois terminais: um para a API e outro para o Expo.

### 1. API no Windows — Prompt de Comando (CMD)

```bat
py --version
node --version
npm --version
git --version

cd backend
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m flask --app app run
```

No navegador do computador, acesse `http://127.0.0.1:5000/saude`. A resposta deve ser `{"status":"ok"}`. Pare a API com **Ctrl+C** antes de inicializar o banco:

```bat
python init_db.py
python -m flask --app app run --host=0.0.0.0 --port=5000
```

Se `py` não existir e `python --version` funcionar, substitua `py` por `python`. O inicializador cria `backend/alagamentos.db`, aplica as alterações de estrutura necessárias e mantém os registros existentes. Execute-o após atualizar o projeto, antes de iniciar a API.

### API no Linux/macOS

Na raiz do repositório:

```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run
```

Confira `/saude`, pare com **Ctrl+C** e execute:

```sh
python init_db.py
python -m flask --app app run --host=0.0.0.0 --port=5000
```

Mantenha o modo de depuração desativado ao acessar pela rede. O servidor do Flask atende ao desenvolvimento e à demonstração local; esta configuração não é uma publicação em produção.

No ambiente Linux da nuvem, `bash scripts/configurar_nuvem.sh`, executado na raiz, reproduz a instalação da API e do aplicativo e inicializa o banco sem apagar registros. Esse script prepara as dependências; a API e o Expo continuam exigindo seus próprios comandos de inicialização. Para uso pessoal no computador, siga as etapas específicas do seu sistema acima.

### 2. Conectar o celular à API

1. Conecte computador e celular à mesma rede Wi-Fi.
2. Descubra o IPv4 do computador com `ipconfig` no Windows ou nas configurações de rede do Linux/macOS.
3. Abra `http://IP-DO-COMPUTADOR:5000/saude` no navegador do celular, usando o IP real.
4. Se não funcionar, verifique a rede, o endereço e a permissão do Python no firewall da rede privada. Não desative o firewall inteiro. Redes de convidados podem impedir a comunicação entre dispositivos.

`127.0.0.1` e `localhost` apontam para o próprio dispositivo. `0.0.0.0` é a configuração de escuta do servidor, não o endereço a colocar no aplicativo. Um ambiente na nuvem não está automaticamente na mesma rede Wi-Fi do celular: para a demonstração local, execute a API e o Expo no computador acessível pelos participantes.

### 3. Aplicativo móvel

Abra **outro terminal**, na raiz do repositório:

```sh
cd mobile
npm ci
```

Dentro de `mobile`, copie o exemplo sem sobrescrever uma configuração local que você já tenha. No Windows CMD:

```bat
copy .env.example .env
```

No Linux/macOS:

```sh
cp .env.example .env
```

Abra o arquivo `.env` criado e configure `EXPO_PUBLIC_API_URL` com o IPv4 real do computador:

```dotenv
EXPO_PUBLIC_API_URL=http://192.168.1.20:5000
```

O IP acima é fictício. O endereço da API fica centralizado em `mobile/src/config.js`. A variável é pública e não deve conter credenciais. Depois de alterar o endereço, reinicie o Expo para carregar a configuração:

```sh
npx expo start --lan --port 8081 --clear
```

Abra o Expo Go e escaneie o QR Code. Confira se o endereço mostrado pelo Expo usa o IPv4 LAN do computador e a porta `8081`. O formato escolhido para a demonstração é **Expo Go**. Mantenha os terminais da API e do Expo abertos: o Expo entrega o aplicativo em desenvolvimento e o Flask recebe as consultas e grava os relatos.

O celular precisa alcançar **dois serviços**: Python/Flask na porta `5000` e Node/Metro na `8081`. Se `/saude` abre, mas o QR Code não carrega o aplicativo, confira o endereço LAN do Expo e a permissão do Node no firewall **da rede privada**. A permissão do Python não libera automaticamente o Node. Não desative o firewall inteiro; redes de convidados também podem impedir essa comunicação.

## Usar o protótipo

1. Crie uma conta com nome, e-mail e senha ou entre com uma conta existente.
2. Em **Ocorrências**, consulte a lista ou alterne para o mapa. Somente relatos com coordenadas aparecem no mapa; todos continuam na lista.
3. Toque em **Nova ocorrência** e preencha bairro, endereço, descrição e gravidade.
4. Opcionalmente, solicite a localização atual e autorize seu compartilhamento no relato. Você também pode selecionar **uma foto ou um vídeo**. Salve.
5. Abra os detalhes. Se você for o autor de um relato ativo, poderá tocar em **Marcar como resolvido**. Outros participantes podem consultar, mas a API recusa a alteração feita por outra conta.
6. No outro dispositivo autenticado, toque em **Atualizar** para consultar o estado salvo. Para encerrar a sessão, use **Sair** com acesso à API.

O identificador, a data de cadastro e a situação inicial `ativo` são definidos pelo servidor. A data é armazenada em UTC. Falhas no envio devem manter os campos preenchidos para permitir uma nova tentativa.

### Sessão, localização e arquivos

A sessão dura até sete dias e é revogada ao sair. No Expo Go, o token é guardado com SecureStore; no navegador, fica somente em memória e recarregar a página exige entrar novamente. Senhas e tokens não devem ser colocados em `.env`, no código ou nos relatos. O servidor guarda hash da senha e hash do token, sem armazenar esses valores em texto puro.

O GPS é opcional, solicitado somente por uma ação do usuário, em primeiro plano. Negar a permissão não impede o cadastro sem coordenadas; não há rastreamento contínuo. Coordenadas enviadas ficam visíveis aos participantes autenticados que consultam o relato. No celular, os mapas usam os recursos nativos do Expo Go. A versão web usa Leaflet e mapas do OpenStreetMap, com atribuição e acesso à Internet. O GPS no navegador exige contexto seguro (HTTPS ou localhost); abrir a versão web por HTTP no IP da rede pode bloquear a localização, mesmo que o GPS funcione no aplicativo nativo.

O anexo é opcional: **um arquivo JPEG, PNG ou MP4 de até 20 MiB**, sem promessa de limite de duração para vídeo. Um arquivo de vídeo pequeno pode ter duração variável. A API valida o conteúdo; as imagens são reprocessadas para remover metadados EXIF. O aplicativo não converte automaticamente formatos incompatíveis. Os arquivos ficam em `backend/uploads/`, fora do Git, e só são entregues pela API após autenticação.

## Verificar o projeto

Com o ambiente virtual ativado:

```sh
cd backend
python -m unittest discover -s tests -v
```

Se já estiver em `backend`, execute apenas o segundo comando. Os testes usam banco temporário, separado do banco de demonstração.

No terminal móvel, dentro de `mobile`, verifique também o código da interface:

```sh
npm run lint
npm run typecheck
```

Opcionalmente, `npm run web` permite inspecionar as telas no navegador do mesmo computador. Para esse teste local, a API aceita as origens `http://localhost:8081` e `http://127.0.0.1:8081`; o cliente web usa `http://127.0.0.1:5000` quando a variável de endereço não está definida. Esse teste auxilia o desenvolvimento, mas a entrega móvel deve ser conferida no Expo Go.

Consulte [o roteiro e o registro de validação](documentacao/TESTES.md) para o teste integrado opcional com Playwright e os testes de persistência, rede, indisponibilidade e demonstração com dois dispositivos. Testes automatizados locais não substituem o teste em celulares físicos.

## Limitações da versão atual

- Há login e autoria, mas não há verificação de e-mail, recuperação de senha ou moderação. Use contas e dados próprios de uma demonstração acadêmica.
- Os relatos não recebem verificação de uma autoridade. Gravidade e situação refletem o que os participantes informam.
- A atualização é manual ao consultar novamente. Não há sincronização em tempo real.
- Existe uma API e um arquivo de banco no servidor. SQLite não está distribuído; o projeto não implementa replicação ou tolerância a falhas.
- A operação depende do computador e da rede disponíveis. Não há modo offline nem fila de envio.
- Os mapas dependem dos provedores externos e da Internet. Um relato sem GPS permanece consultável pela lista.
- Não há notificações, rastreamento contínuo ou sincronização em tempo real.
- O servidor de desenvolvimento e HTTP na rede local destinam-se à demonstração. Uma publicação real exigiria HTTPS e preparação adequada do serviço, especialmente para credenciais e anexos.

## Documentação

- [Checklist das próximas etapas e da entrega](documentacao/ENTREGA.md)
- [Roteiro de apresentação de 5 a 8 minutos](documentacao/APRESENTACAO.md)
- [Base do relatório para revisão e preenchimento pelo grupo](documentacao/RELATORIO_BASE.md)
- [Evidências atuais: login, autoria, GPS simulado, mapa e anexos](documentacao/evidencias-v2/index.html)
- [Vídeos e capturas históricos da primeira versão, sem login](documentacao/evidencias/index.html)
- [Contrato da API](documentacao/API.md)
- [Arquitetura, conceitos e diagramas preparatórios](documentacao/ARQUITETURA.md)
- [Roteiro de testes e demonstração](documentacao/TESTES.md)
- [Modelo de diário de atividades e fontes](documentacao/DIARIO.md)
- [Instruções locais e situação da configuração da nuvem](documentacao/AMBIENTE_NUVEM.md)

O banco e os anexos ficam fora do Git. Para preservar a demonstração, **pare a API e copie juntos `backend/alagamentos.db` e `backend/uploads/`**. Restaurar somente o banco não restaura os arquivos anexados. Não apague esses arquivos ao reiniciar o servidor.
