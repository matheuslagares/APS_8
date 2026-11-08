-- A inicialização preserva os registros que já existem.
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    senha_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expira_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ocorrencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bairro TEXT NOT NULL CHECK (length(bairro) BETWEEN 1 AND 100),
    endereco TEXT NOT NULL CHECK (length(endereco) BETWEEN 1 AND 200),
    descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 1000),
    gravidade TEXT NOT NULL CHECK (gravidade IN ('baixa', 'media', 'alta')),
    situacao TEXT NOT NULL DEFAULT 'ativo' CHECK (situacao IN ('ativo', 'resolvido')),
    criado_em TEXT NOT NULL,
    autor_id INTEGER REFERENCES usuarios(id),
    latitude REAL CHECK(latitude BETWEEN -90 AND 90),
    longitude REAL CHECK(longitude BETWEEN -180 AND 180),
    CHECK ((latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS anexos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ocorrencia_id INTEGER NOT NULL REFERENCES ocorrencias(id) ON DELETE CASCADE,
    nome_arquivo TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL CHECK(tipo IN ('imagem', 'video')),
    mime_type TEXT NOT NULL,
    tamanho INTEGER NOT NULL CHECK(tamanho > 0)
);

CREATE INDEX IF NOT EXISTS anexos_ocorrencia ON anexos(ocorrencia_id);
