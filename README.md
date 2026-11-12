# Alerta de Alagamentos

Aplicativo para cadastrar e consultar relatos de alagamentos, com autenticação, mapa e anexos de foto ou vídeo. O servidor usa Flask e SQLite; o aplicativo usa React Native e Expo.

## Requisitos

- Python 3.11 ou superior.
- Node.js na versão indicada em `mobile/.nvmrc`, com npm.
- Expo Go compatível com o SDK definido em `mobile/package.json`, para executar no celular.

## Servidor

No PowerShell, a partir desta pasta:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe init_db.py
.\.venv\Scripts\python.exe -m flask --app app run --host=0.0.0.0 --port=5000
```

No Linux/macOS, use `python3 -m venv .venv` e substitua `.\.venv\Scripts\python.exe` por `.venv/bin/python` nos demais comandos.

Confira `http://127.0.0.1:5000/saude`: a resposta deve ser `{"status":"ok"}`. O inicializador cria `backend/alagamentos.db` sem apagar registros existentes. Os anexos são armazenados em `backend/uploads/`.

## Aplicativo

Abra outro terminal nesta pasta:

```powershell
cd mobile
npm ci
Copy-Item .env.example .env
```

No Linux/macOS, use `cp .env.example .env` para copiar a configuração.

Edite `mobile/.env` e substitua `IP-DO-COMPUTADOR` pelo IPv4 do computador que executa o servidor. No Windows, consulte esse endereço com `ipconfig`.

```dotenv
EXPO_PUBLIC_API_URL=http://IP-DO-COMPUTADOR:5000
```

Conecte o celular e o computador à mesma rede Wi-Fi. Confira `http://IP-DO-COMPUTADOR:5000/saude` no navegador do celular. Libere Python e Node no firewall da rede privada, se necessário.

```powershell
npm start -- --lan --port 8081
```

Abra o QR Code no Expo Go. Mantenha os dois terminais abertos. Após alterar `.env`, reinicie o Expo. No celular, `localhost` aponta para o próprio aparelho.

Para executar no navegador do computador, configure `EXPO_PUBLIC_API_URL=http://127.0.0.1:5000` e use `npm run web -- --port 8081`.

## Uso

Crie uma conta, entre e cadastre uma ocorrência. A localização e o anexo são opcionais. São aceitos JPEG, PNG ou MP4 de até 20 MiB. Somente o autor pode alterar a situação do relato. Os relatos são informações dos participantes, sem verificação oficial.

Para verificar o código do aplicativo, execute `npm run lint` e `npm run typecheck` em `mobile`.
