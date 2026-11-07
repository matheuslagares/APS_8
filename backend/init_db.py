"""Cria o banco sem apagar ocorrências existentes: python init_db.py."""

import argparse

from database import DEFAULT_DATABASE, inicializar_banco


def main():
    parser = argparse.ArgumentParser(description="Inicializa o banco de ocorrências.")
    parser.add_argument("--database", default=str(DEFAULT_DATABASE), help="Caminho do SQLite")
    args = parser.parse_args()
    inicializar_banco(args.database)
    print(f"Banco inicializado: {args.database}")


if __name__ == "__main__":
    main()
