#!/usr/bin/env bash
# Instala as dependências no Linux da nuvem sem alterar o código ou os lockfiles.
set -euo pipefail

RAIZ_PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ_PROJETO/backend"
python3 -m venv .venv
.venv/bin/python -m pip install --cache-dir /workspace/.cache/pip -r requirements.txt
# A inicialização pode ser repetida: não apaga relatos já cadastrados.
.venv/bin/python init_db.py

cd "$RAIZ_PROJETO/mobile"
# npm ci usa exatamente as versões registradas no package-lock.json.
npm_config_cache=/workspace/.npm-cache npm ci --no-audit --no-fund
