-- A inicialização preserva os registros que já existem.
CREATE TABLE IF NOT EXISTS ocorrencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bairro TEXT NOT NULL CHECK (length(bairro) BETWEEN 1 AND 100),
    endereco TEXT NOT NULL CHECK (length(endereco) BETWEEN 1 AND 200),
    descricao TEXT NOT NULL CHECK (length(descricao) BETWEEN 1 AND 1000),
    gravidade TEXT NOT NULL CHECK (gravidade IN ('baixa', 'media', 'alta')),
    situacao TEXT NOT NULL DEFAULT 'ativo' CHECK (situacao IN ('ativo', 'resolvido')),
    criado_em TEXT NOT NULL
);
