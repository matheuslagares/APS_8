# Alerta de Alagamentos

App pra cadastrar e consultar relatos de alagamentos, com login, mapa e foto/video.
Servidor em Flask + SQLite, app em React Native com Expo.

Grupo: Saad, Matheus, Guilherme, Gustavo e Henrique.

## Estrutura

```
backend/
  app.py        -> todas as rotas da API (login, ocorrencias, anexos)
  banco.py      -> conexao com o SQLite e criacao das tabelas
  schema.sql    -> tabelas do banco
mobile/
  App.js        -> controla qual tela aparece
  src/services/api.js   -> chamadas pro servidor
  src/screens/          -> telas (login, lista, cadastro, detalhes)
  src/components/       -> pedacos reutilizados (botao, mapa, anexo, GPS)
  src/theme.js          -> cores e estilos
```

## Servidor

Requisito: Python 3.11 ou superior. No PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

O banco (`backend/alagamentos.db`) e a pasta `backend/uploads/` são criados sozinhos.
Teste em `http://127.0.0.1:5000/saude`: deve aparecer `{"status":"ok"}`.

## Aplicativo

Requisito: Node.js (versão em `mobile/.nvmrc`). Em outro terminal:

```powershell
cd mobile
npm ci
Copy-Item .env.example .env
```

No `mobile/.env`, troque `IP-DO-COMPUTADOR` pelo IPv4 do computador (veja com `ipconfig`).
Celular e computador precisam estar na mesma rede Wi-Fi.

```powershell
npm start -- --lan --port 8081
```

Abra o QR Code no Expo Go. Se mudar o `.env`, reinicie o Expo.

Pra rodar no navegador: use `EXPO_PUBLIC_API_URL=http://127.0.0.1:5000` e `npm run web -- --port 8081`.

## Uso

Crie uma conta, entre e cadastre uma ocorrência. Localização e anexo (JPEG, PNG ou MP4 até 20 MiB) são opcionais.
Só o autor pode marcar o relato como resolvido.
