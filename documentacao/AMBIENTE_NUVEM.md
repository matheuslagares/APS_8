# Ambiente na nuvem

O projeto foi instalado e validado nesta instância. A ferramenta de configuração não confirmou o salvamento de `install_script` e `start_skill`; portanto, estas instruções são uma cópia local para reutilização, e não comprovam publicação do ambiente.

## Script de instalação proposto

Na instância atual, `bash scripts/configurar_nuvem.sh` foi executado com sucesso. Conteúdo equivalente preparado para o campo `install_script`:

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

Use o checkout existente /workspace/APS_8; cada tarefa já é isolada. Não crie worktree, a menos que o usuário peça. Leia README.md. As dependências backend/.venv e mobile/node_modules e o banco SQLite são arquivos retidos; os processos devem ser iniciados novamente.

API: em /workspace/APS_8/backend, execute `.venv/bin/python init_db.py` (idempotente, não apaga dados), depois `.venv/bin/python -m flask --app app run --host=0.0.0.0 --port=5000` em um terminal persistente, sem debug. Confira com `curl -fsS http://127.0.0.1:5000/saude` (status ok) e GET /ocorrencias (lista JSON).

Interface: em /workspace/APS_8/mobile, para validação local web execute `EXPO_PUBLIC_API_URL=http://127.0.0.1:5000 XDG_CACHE_HOME=/workspace/.cache EXPO_OFFLINE=1 EXPO_NO_TELEMETRY=1 npx expo start --web --localhost --port 8081` em outro terminal persistente. O modo offline do CLI evita consultas de metadados Expo não liberadas; não muda o acesso do aplicativo à API. Não publique links loopback como previews. Em celular físico siga o README: API e Expo em computador alcançável na rede, EXPO_PUBLIC_API_URL com IPv4 real em mobile/.env, `npx expo start`, e Expo Go compatível com SDK57. Celular não alcança automaticamente o localhost da nuvem.

Verificações: em backend/ `.venv/bin/python -m unittest discover -s tests -v`; em mobile/ `npm run lint` e `npm run typecheck`. O teste opcional tests/fluxo_web.py usa SQLite temporário e inicia sua própria API: pare apenas a API que você iniciou antes do teste, mantendo Expo web na 8081. Leia documentacao/TESTES.md. Não apague bancos ou processos de outras pessoas. Relatos não são oficiais/verificados; sem login qualquer participante altera a situação. Testes web não substituem demonstração com dois celulares.

Os arquivos estão preservados no repositório. A publicação e a restauração em uma nova tarefa ainda não foram verificadas.
