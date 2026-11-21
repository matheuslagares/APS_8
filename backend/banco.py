# banco.py - parte do Gustavo
# aqui fica so a conexao com o sqlite e a criacao das tabelas

import os
import sqlite3

# pasta onde esta esse arquivo (backend/)
PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_BANCO = os.path.join(PASTA, "alagamentos.db")


def conectar():
    conexao = sqlite3.connect(ARQUIVO_BANCO, timeout=10)
    # row_factory faz o resultado vir tipo dicionario (linha["nome"]), bem mais facil
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    # le o schema.sql e roda tudo de uma vez
    # obs: usa IF NOT EXISTS entao nao apaga nd q ja tava salvo
    with open(os.path.join(PASTA, "schema.sql"), encoding="utf-8") as arq:
        comandos = arq.read()
    conexao = conectar()
    conexao.executescript(comandos)
    conexao.commit()
    conexao.close()


# se rodar "python banco.py" direto ele so cria o banco
if __name__ == "__main__":
    criar_tabelas()
    print("Banco criado em", ARQUIVO_BANCO)
