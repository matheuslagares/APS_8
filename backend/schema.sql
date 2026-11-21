-- tabelas do sistema (Gustavo e Henrique)
-- IF NOT EXISTS pra nao apagar os dados qdo rodar d novo

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    senha_hash TEXT NOT NULL
);

-- cada login gera um token, ele fica guardado aqui ate expirar ou o usuario sair
CREATE TABLE IF NOT EXISTS sessoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expira_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ocorrencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bairro TEXT NOT NULL,
    endereco TEXT NOT NULL,
    descricao TEXT NOT NULL,
    gravidade TEXT NOT NULL,      -- baixa, media ou alta
    situacao TEXT NOT NULL DEFAULT 'ativo',  -- ativo ou resolvido
    criado_em TEXT NOT NULL,
    autor_id INTEGER REFERENCES usuarios(id),
    latitude REAL,   -- latitude e longitude sao opcionais
    longitude REAL
);

-- foto ou video de uma ocorrencia (o arquivo msm fica na pasta uploads/)
CREATE TABLE IF NOT EXISTS anexos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ocorrencia_id INTEGER NOT NULL REFERENCES ocorrencias(id) ON DELETE CASCADE,
    nome_arquivo TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL,       -- imagem ou video
    mime_type TEXT NOT NULL,
    tamanho INTEGER NOT NULL
);
