# Ambiente na nuvem

Durante a preparação inicial, a ferramenta não confirmou o salvamento de `install_script` e `start_skill`. Posteriormente, o usuário informou a publicação do ambiente da primeira versão. Na instância restaurada, o checkout e as dependências estavam presentes e os 21 testes antigos da API, lint e checagem de tipos passaram novamente antes do envio inicial ao GitHub. Esses resultados não validam a ampliação posterior com login, GPS e anexos.

As instruções abaixo preservam a referência local de instalação e inicialização. Elas não foram reaplicadas ao rascunho publicado. Processos precisam ser iniciados novamente em cada instância.

## Script de instalação proposto

O comando `bash scripts/configurar_nuvem.sh` reproduz a instalação usando os manifests e lockfiles atuais. Sua execução bem-sucedida registrada na preparação inicial pertence ao histórico da primeira versão. Conteúdo equivalente preparado como referência local para `install_script`:

```bash
set -euo pipefail
cd /workspace/APS_8/backend
python3 -m venv .venv
.venv/bin/python -m pip install --cache-dir /workspace/.cache/pip -r requirements.txt
.venv/bin/python init_db.py
cd /workspace/APS_8/mobile
npm_config_cache=/workspace/.npm-cache npm ci --no-audit --no-fund
```

## Instruções de inicialização propostas

Conteúdo preparado para `start_skill`:

Use o checkout existente /workspace/APS_8; cada tarefa já é isolada. Não crie worktree, a menos que o usuário peça. Leia README.md. As dependências backend/.venv e mobile/node_modules, o banco SQLite e a pasta backend/uploads são arquivos retidos; os processos devem ser iniciados novamente. Após atualizar o código, instale as dependências e execute o inicializador para migrar a estrutura sem apagar os relatos antigos.

API: em /workspace/APS_8/backend, execute `.venv/bin/python init_db.py` (idempotente, não apaga dados), depois `.venv/bin/python -m flask --app app run --host=0.0.0.0 --port=5000` em um terminal persistente, sem debug. Confira com `curl -fsS http://127.0.0.1:5000/saude` (status ok). A consulta GET /ocorrencias exige sessão Bearer; sem autenticação o resultado esperado é 401. Para validar o fluxo completo, crie uma conta de demonstração pela interface e consulte os relatos.

Interface: em /workspace/APS_8/mobile, para validação local web execute `EXPO_PUBLIC_API_URL=http://127.0.0.1:5000 XDG_CACHE_HOME=/workspace/.cache EXPO_OFFLINE=1 EXPO_NO_TELEMETRY=1 npx expo start --web --localhost --port 8081` em outro terminal persistente. O modo offline do CLI evita consultas de metadados Expo não liberadas; não muda o acesso do aplicativo à API. Não publique links loopback como previews. Em celular físico siga o README: API e Expo em computador alcançável na rede, EXPO_PUBLIC_API_URL com IPv4 real em mobile/.env, `npx expo start`, e Expo Go compatível com SDK57. Celular não alcança automaticamente o localhost da nuvem.

Verificações: em backend/ `.venv/bin/python -m unittest discover -s tests -v`; em mobile/ `npm run lint` e `npm run typecheck`. O teste opcional tests/fluxo_web.py usa SQLite e uploads temporários e inicia sua própria API: pare apenas a API que você iniciou antes do teste, mantendo Expo web na 8081. Leia documentacao/TESTES.md. Não apague bancos ou processos de outras pessoas. Relatos não são oficiais/verificados; somente o autor autenticado pode alterar a situação. Relatos antigos sem autor permanecem somente para consulta. Testes web não substituem demonstração com dois celulares. GPS web exige HTTPS ou localhost, e mapas dependem de provedores externos. Preserve banco e uploads juntos em backups com a API parada.

Os arquivos estão preservados no repositório. A publicação foi informada pelo usuário; a presença do projeto e o funcionamento das verificações acima foram observados na instância restaurada. Isso não comprova o acesso de celulares físicos à rede da nuvem.
