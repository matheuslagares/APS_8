"""Testes reais da API com arquivos SQLite temporários, sem tocar no banco local."""

import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app import create_app
from database import BASE_DIR, conectar, inicializar_banco


class SaudeSemBancoTest(unittest.TestCase):
    def test_saude_antes_de_criar_banco(self):
        with tempfile.TemporaryDirectory() as pasta:
            banco = Path(pasta) / "nao-criado.db"
            app = create_app({"TESTING": True, "DATABASE": str(banco)})
            resposta = app.test_client().get("/saude")
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.get_json(), {"status": "ok"})
            self.assertFalse(banco.exists())


class OcorrenciasTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.banco = Path(self.pasta.name) / "teste.db"
        inicializar_banco(self.banco)
        self.app = create_app({"TESTING": True, "DATABASE": str(self.banco),
                               "UPLOAD_FOLDER": str(Path(self.pasta.name) / "uploads")})
        self.cliente = self.app.test_client()
        sessao = self.cliente.post("/auth/cadastro", json={
            "nome": "Pessoa de teste", "email": "pessoa@example.com", "senha": "senha-teste-123",
        }).get_json()
        self.token = sessao["token"]
        self.cliente.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {self.token}"
        self.dados = {
            "bairro": "Centro",
            "endereco": "Rua das Flores, 10",
            "descricao": "Água acumulada na via.",
            "gravidade": "media",
        }

    def criar(self, **alteracoes):
        return self.cliente.post("/ocorrencias", json={**self.dados, **alteracoes})

    def verificar_erro(self, resposta, codigo):
        self.assertEqual(resposta.status_code, codigo)
        self.assertTrue(resposta.is_json)
        self.assertEqual(set(resposta.get_json()), {"erro"})
        self.assertIsInstance(resposta.get_json()["erro"], str)

    def test_fluxo_criar_listar_detalhar_e_resolver(self):
        self.assertEqual(self.cliente.get("/ocorrencias").get_json(), [])
        resposta = self.criar()
        self.assertEqual(resposta.status_code, 201)
        ocorrencia = resposta.get_json()
        self.assertIsInstance(ocorrencia["id"], int)
        self.assertEqual(ocorrencia["situacao"], "ativo")
        self.assertEqual(set(ocorrencia), set(self.dados) | {
            "id", "situacao", "criado_em", "autor_id", "pode_alterar", "latitude", "longitude", "anexos",
        })
        self.assertTrue(ocorrencia["pode_alterar"])
        self.assertEqual(datetime.fromisoformat(ocorrencia["criado_em"]).utcoffset().total_seconds(), 0)
        identificador = ocorrencia["id"]
        self.assertEqual(self.cliente.get("/ocorrencias").get_json(), [ocorrencia])
        self.assertEqual(self.cliente.get(f"/ocorrencias/{identificador}").get_json(), ocorrencia)
        resolvida = self.cliente.patch(
            f"/ocorrencias/{identificador}/situacao", json={"situacao": "resolvido"}
        )
        self.assertEqual(resolvida.status_code, 200)
        self.assertEqual(resolvida.get_json(), {**ocorrencia, "situacao": "resolvido"})
        reaberta = self.cliente.patch(
            f"/ocorrencias/{identificador}/situacao", json={"situacao": "ativo"}
        )
        self.assertEqual(reaberta.status_code, 200)
        self.assertEqual(reaberta.get_json(), ocorrencia)

    def test_persistencia_em_nova_instancia(self):
        ocorrencia = self.criar().get_json()
        outro_app = create_app({"TESTING": True, "DATABASE": str(self.banco)})
        resposta = outro_app.test_client().get(
            f"/ocorrencias/{ocorrencia['id']}", headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json(), ocorrencia)

    def test_lista_mais_recentes_primeiro(self):
        primeira = self.criar().get_json()
        segunda = self.criar(bairro="Outro bairro").get_json()
        self.assertEqual(self.cliente.get("/ocorrencias").get_json(), [segunda, primeira])

    def test_trim_e_campos_controlados_pelo_servidor(self):
        antes = datetime.now(timezone.utc)
        resposta = self.criar(
            bairro="  Centro  ", endereco=" Rua 10 ", descricao=" Relato ", gravidade=" media ",
            id=999, situacao="resolvido", criado_em="2000-01-01",
        )
        self.assertEqual(resposta.status_code, 201)
        dados = resposta.get_json()
        self.assertEqual(dados["bairro"], "Centro")
        self.assertEqual(dados["endereco"], "Rua 10")
        self.assertEqual(dados["descricao"], "Relato")
        self.assertEqual(dados["gravidade"], "media")
        self.assertNotEqual(dados["id"], 999)
        self.assertEqual(dados["situacao"], "ativo")
        self.assertGreaterEqual(
            datetime.fromisoformat(dados["criado_em"]), antes.replace(microsecond=0)
        )

    def test_textos_invalidos(self):
        for campo, limite in (("bairro", 100), ("endereco", 200), ("descricao", 1000)):
            for valor in (None, "", " \n\t ", 12, True, [], {}, "a" * (limite + 1)):
                with self.subTest(campo=campo, valor=valor):
                    self.verificar_erro(self.criar(**{campo: valor}), 400)
            with self.subTest(campo=campo, ausente=True):
                dados = dict(self.dados)
                del dados[campo]
                self.verificar_erro(self.cliente.post("/ocorrencias", json=dados), 400)
        self.assertEqual(self.cliente.get("/ocorrencias").get_json(), [])

    def test_limites_exatos_dos_textos_sao_aceitos(self):
        resposta = self.criar(bairro="b" * 100, endereco="e" * 200, descricao="d" * 1000)
        self.assertEqual(resposta.status_code, 201)

    def test_gravidades_validas(self):
        for gravidade in ("baixa", "media", "alta"):
            with self.subTest(gravidade=gravidade):
                self.assertEqual(self.criar(gravidade=gravidade).status_code, 201)

    def test_gravidade_invalida(self):
        for valor in (None, "", "média", "ALTA", 1, True, [], {}):
            with self.subTest(valor=valor):
                self.verificar_erro(self.criar(gravidade=valor), 400)
        dados = dict(self.dados)
        del dados["gravidade"]
        self.verificar_erro(self.cliente.post("/ocorrencias", json=dados), 400)

    def test_situacao_invalida_nao_modifica_registro(self):
        ocorrencia = self.criar().get_json()
        rota = f"/ocorrencias/{ocorrencia['id']}/situacao"
        for valor in (None, "", "resolvida", "RESOLVIDO", 1, [], {}):
            with self.subTest(valor=valor):
                self.verificar_erro(self.cliente.patch(rota, json={"situacao": valor}), 400)
        self.verificar_erro(self.cliente.patch(rota, json={}), 400)
        self.assertEqual(self.cliente.get(f"/ocorrencias/{ocorrencia['id']}").get_json(), ocorrencia)

    def test_situacao_remove_espacos(self):
        ocorrencia = self.criar().get_json()
        resposta = self.cliente.patch(
            f"/ocorrencias/{ocorrencia['id']}/situacao", json={"situacao": " resolvido "}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["situacao"], "resolvido")

    def test_identificadores_inexistentes(self):
        self.verificar_erro(self.cliente.get("/ocorrencias/999"), 404)
        self.verificar_erro(
            self.cliente.patch("/ocorrencias/999/situacao", json={"situacao": "resolvido"}), 404
        )
        self.verificar_erro(self.cliente.get("/rota-inexistente"), 404)

    def test_content_type_e_json_malformado(self):
        for rota, metodo in (
            ("/ocorrencias", self.cliente.post),
            ("/ocorrencias/1/situacao", self.cliente.patch),
        ):
            with self.subTest(rota=rota):
                self.verificar_erro(metodo(rota, data='{}', content_type="text/plain"), 415)
                self.verificar_erro(metodo(rota), 415)
                self.verificar_erro(metodo(rota, data='{', content_type="application/json"), 400)
                for valor in ("null", "[]", '"texto"', "42"):
                    self.verificar_erro(
                        metodo(rota, data=valor, content_type="application/json"), 400
                    )

    def test_texto_sql_e_armazenado_sem_executar(self):
        texto = "Centro'); DROP TABLE ocorrencias; --"
        resposta = self.criar(bairro=texto)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.get_json()["bairro"], texto)
        self.assertEqual(len(self.cliente.get("/ocorrencias").get_json()), 1)

    def test_inicializacao_idempotente_preserva_registros(self):
        ocorrencia = self.criar().get_json()
        for _ in range(2):
            resultado = subprocess.run(
                [sys.executable, str(BASE_DIR / "init_db.py"), "--database", str(self.banco)],
                cwd=self.pasta.name, capture_output=True, text=True, check=True,
            )
            self.assertIn("Banco inicializado", resultado.stdout)
        self.assertEqual(self.cliente.get("/ocorrencias").get_json(), [ocorrencia])

    def test_erro_sqlite_retorna_500_sem_detalhes_internos(self):
        self.app.config["DATABASE"] = str(Path(self.pasta.name) / "pasta-ausente" / "falha.db")
        with self.assertLogs(self.app.logger, level="ERROR"):
            resposta = self.cliente.get("/ocorrencias")
        self.verificar_erro(resposta, 500)
        self.assertNotIn(self.pasta.name, resposta.get_data(as_text=True))

    def test_excecao_inesperada_retorna_json_500(self):
        with patch("app.conectar", side_effect=RuntimeError("detalhe privado")):
            with self.assertLogs(self.app.logger, level="ERROR"):
                resposta = self.cliente.get("/ocorrencias")
        self.verificar_erro(resposta, 500)
        self.assertNotIn("detalhe privado", resposta.get_data(as_text=True))

    def test_rollback_em_falha_sqlite_preserva_situacao(self):
        ocorrencia = self.criar().get_json()
        with conectar(self.banco) as conexao:
            conexao.execute(
                """CREATE TRIGGER falhar_atualizacao AFTER UPDATE ON ocorrencias
                   BEGIN SELECT RAISE(ABORT, 'falha de teste'); END"""
            )
        with self.assertLogs(self.app.logger, level="ERROR"):
            resposta = self.cliente.patch(
                f"/ocorrencias/{ocorrencia['id']}/situacao", json={"situacao": "resolvido"}
            )
        self.verificar_erro(resposta, 500)
        self.assertEqual(self.cliente.get("/ocorrencias").get_json(), [ocorrencia])

    def test_transacao_desfaz_alteracoes_e_fecha_conexao(self):
        with self.assertRaisesRegex(RuntimeError, "falha simulada"):
            with conectar(self.banco) as conexao:
                conexao.execute(
                    """INSERT INTO ocorrencias
                       (bairro, endereco, descricao, gravidade, situacao, criado_em)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    ("Centro", "Rua 1", "Relato", "baixa", "ativo", "2026-01-01T00:00:00+00:00"),
                )
                raise RuntimeError("falha simulada")
        with self.assertRaises(sqlite3.ProgrammingError):
            conexao.execute("SELECT 1")
        self.assertEqual(self.cliente.get("/ocorrencias").get_json(), [])

    def test_conexao_fechada_apos_sucesso(self):
        with conectar(self.banco) as conexao:
            self.assertEqual(conexao.execute("SELECT 1").fetchone()[0], 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            conexao.execute("SELECT 1")

    def test_cors_expo_web_e_preflight(self):
        resposta = self.cliente.options(
            "/ocorrencias/1/situacao",
            headers={
                "Origin": "http://localhost:8081",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.headers["Access-Control-Allow-Origin"], "http://localhost:8081")
        self.assertIn("Content-Type", resposta.headers["Access-Control-Allow-Headers"])
        self.assertIn("Authorization", resposta.headers["Access-Control-Allow-Headers"])
        self.assertIn("PATCH", resposta.headers["Access-Control-Allow-Methods"])
        bloqueada = self.cliente.get("/saude", headers={"Origin": "https://desconhecido.example"})
        self.assertNotIn("Access-Control-Allow-Origin", bloqueada.headers)
        self.app.config["CORS_ORIGINS"] = ()
        desativada = self.cliente.get("/saude", headers={"Origin": "http://localhost:8081"})
        self.assertNotIn("Access-Control-Allow-Origin", desativada.headers)


if __name__ == "__main__":
    unittest.main()
