"""Autenticação, autoria, localização, anexos privados e migração sem perda."""

from io import BytesIO
from pathlib import Path
import sqlite3
import tempfile
import unittest

from PIL import Image
from werkzeug.datastructures import MultiDict
from werkzeug.security import check_password_hash

from app import create_app
from autenticacao import hash_token
from database import conectar, inicializar_banco


class RecursosNovosTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.banco = Path(self.pasta.name) / 'teste.db'
        self.uploads = Path(self.pasta.name) / 'uploads'
        inicializar_banco(self.banco)
        self.app = create_app({'TESTING': True, 'DATABASE': str(self.banco),
                               'UPLOAD_FOLDER': str(self.uploads)})
        self.cliente = self.app.test_client()
        self.sessao = self.cadastrar('pessoa@example.com')
        self.token = self.sessao['token']
        self.cliente.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {self.token}'
        self.dados = {'bairro': 'Centro', 'endereco': 'Rua 1', 'descricao': 'Água na via', 'gravidade': 'alta'}

    def cadastrar(self, email):
        resposta = self.cliente.post('/auth/cadastro', json={
            'nome': ' Pessoa de teste ', 'email': email, 'senha': 'senha-teste-123',
        })
        self.assertEqual(resposta.status_code, 201)
        return resposta.get_json()

    def verificar_erro(self, resposta, codigo):
        self.assertEqual(resposta.status_code, codigo, resposta.get_data(as_text=True))
        self.assertEqual(set(resposta.get_json()), {'erro'})

    def foto(self, formato='JPEG'):
        saida = BytesIO()
        Image.new('RGB', (8, 6), 'blue').save(saida, formato)
        saida.seek(0)
        return saida

    def criar(self, **campos):
        return self.cliente.post('/ocorrencias', json={**self.dados, **campos})

    def enviar_foto(self, **campos):
        return self.cliente.post('/ocorrencias', data={
            **self.dados, **campos, 'arquivo': (self.foto(), '../../nome-malicioso.svg', 'image/svg+xml'),
        })

    def test_cadastro_login_me_logout_e_hashes(self):
        self.assertEqual(set(self.sessao), {'usuario', 'token', 'expira_em'})
        self.assertEqual(set(self.sessao['usuario']), {'id', 'nome', 'email'})
        self.assertEqual(self.sessao['usuario']['nome'], 'Pessoa de teste')
        self.assertEqual(self.cliente.get('/auth/me').get_json(), {'usuario': self.sessao['usuario']})
        with conectar(self.banco) as conexao:
            usuario = conexao.execute('SELECT * FROM usuarios').fetchone()
            sessao = conexao.execute('SELECT * FROM sessoes').fetchone()
        self.assertTrue(usuario['senha_hash'].startswith('scrypt:'))
        self.assertNotIn('senha-teste-123', usuario['senha_hash'])
        self.assertTrue(check_password_hash(usuario['senha_hash'], 'senha-teste-123'))
        self.assertEqual(sessao['token_hash'], hash_token(self.token))
        self.assertNotEqual(sessao['token_hash'], self.token)
        login = self.cliente.post('/auth/login', json={'email': ' PESSOA@EXAMPLE.COM ', 'senha': 'senha-teste-123'})
        self.assertEqual(login.status_code, 200)
        self.assertNotEqual(login.get_json()['token'], self.token)
        self.assertEqual(login.get_json()['usuario'], self.sessao['usuario'])
        self.assertEqual(self.cliente.post('/auth/logout').status_code, 200)
        self.verificar_erro(self.cliente.get('/auth/me'), 401)
        outro_token = login.get_json()['token']
        self.assertEqual(self.cliente.get('/auth/me', headers={'Authorization': f'Bearer {outro_token}'}).status_code, 200)

    def test_hashes_de_senha_tem_salt_diferente(self):
        self.cadastrar('outra@example.com')
        with conectar(self.banco) as conexao:
            hashes = [linha[0] for linha in conexao.execute('SELECT senha_hash FROM usuarios')]
        self.assertNotEqual(hashes[0], hashes[1])

    def test_email_duplicado_independe_de_maiusculas(self):
        resposta = self.cliente.post('/auth/cadastro', json={
            'nome': 'Outra', 'email': ' PESSOA@EXAMPLE.COM ', 'senha': 'senha-teste-123',
        })
        self.verificar_erro(resposta, 409)
        with conectar(self.banco) as conexao:
            self.assertEqual(conexao.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0], 1)

    def test_login_incorreto_ou_conta_inexistente_mesma_mensagem(self):
        incorreta = self.cliente.post('/auth/login', json={'email': 'pessoa@example.com', 'senha': 'senha-incorreta'})
        ausente = self.cliente.post('/auth/login', json={'email': 'ausente@example.com', 'senha': 'senha-incorreta'})
        self.verificar_erro(incorreta, 401)
        self.verificar_erro(ausente, 401)
        self.assertEqual(incorreta.get_json(), ausente.get_json())

    def test_validacao_cadastro_e_login(self):
        base = {'nome': 'Nome', 'email': 'novo@example.com', 'senha': 'senha-teste-123'}
        for campo, valores in (
            ('nome', [None, '', '  ', 12, 'n' * 101]),
            ('email', [None, '', 'sem-arroba', 'a@b', 12, 'e' * 255 + '@a.com']),
            ('senha', [None, 12, 'curta', ' ' * 8, 'x' * 129]),
        ):
            for valor in valores:
                with self.subTest(campo=campo, valor=valor):
                    self.verificar_erro(self.cliente.post('/auth/cadastro', json={**base, campo: valor}), 400)
        for rota in ('/auth/cadastro', '/auth/login'):
            self.verificar_erro(self.cliente.post(rota, data='{}', content_type='text/plain'), 415)
            self.verificar_erro(self.cliente.post(rota, json=[]), 400)

    def test_sessao_expirada_e_token_invalido(self):
        with conectar(self.banco) as conexao:
            conexao.execute('UPDATE sessoes SET expira_em = ?', ('2000-01-01T00:00:00+00:00',))
        self.verificar_erro(self.cliente.get('/auth/me'), 401)
        for cabecalho in ('Bearer desconhecido', 'Basic abc', 'Bearer', 'Bearer a b'):
            self.verificar_erro(self.cliente.get('/ocorrencias', headers={'Authorization': cabecalho}), 401)

    def test_rotas_privadas_e_preflight_sem_token(self):
        anonimo = self.app.test_client()
        for metodo, rota in (
            ('GET', '/ocorrencias'), ('POST', '/ocorrencias'), ('GET', '/ocorrencias/1'),
            ('PATCH', '/ocorrencias/1/situacao'), ('GET', '/anexos/1'),
            ('GET', '/auth/me'), ('POST', '/auth/logout'),
        ):
            self.verificar_erro(anonimo.open(rota, method=metodo), 401)
        self.assertEqual(anonimo.get('/saude').status_code, 200)
        resposta = anonimo.options('/ocorrencias', headers={
            'Origin': 'http://localhost:8081', 'Access-Control-Request-Headers': 'Authorization, Content-Type',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('Authorization', resposta.headers['Access-Control-Allow-Headers'])

    def test_somente_autor_altera_e_autoria_nao_vem_do_cliente(self):
        ocorrencia = self.criar(autor_id=987).get_json()
        self.assertEqual(ocorrencia['autor_id'], self.sessao['usuario']['id'])
        self.assertTrue(ocorrencia['pode_alterar'])
        outra = self.cadastrar('outra@example.com')
        cabecalho = {'Authorization': f"Bearer {outra['token']}"}
        consulta = self.cliente.get(f"/ocorrencias/{ocorrencia['id']}", headers=cabecalho)
        self.assertEqual(consulta.status_code, 200)
        self.assertFalse(consulta.get_json()['pode_alterar'])
        resposta = self.cliente.patch(f"/ocorrencias/{ocorrencia['id']}/situacao", json={'situacao': 'resolvido'}, headers=cabecalho)
        self.verificar_erro(resposta, 403)
        self.assertEqual(self.cliente.get('/ocorrencias').get_json()[0]['situacao'], 'ativo')

    def test_coordenadas_validas_e_sem_localizacao(self):
        for latitude, longitude in ((-23.55, -46.63), (0, 0), (-90, -180), (90, 180)):
            resposta = self.criar(latitude=latitude, longitude=longitude)
            self.assertEqual(resposta.status_code, 201)
            self.assertEqual(resposta.get_json()['latitude'], latitude)
            self.assertEqual(resposta.get_json()['longitude'], longitude)
        sem = self.criar().get_json()
        self.assertIsNone(sem['latitude'])
        self.assertIsNone(sem['longitude'])
        self.assertEqual(sem['anexos'], [])
        self.assertEqual(self.criar(latitude=None, longitude=None).status_code, 201)

    def test_coordenadas_invalidas_nao_cadastram(self):
        for campos in (
            {'latitude': 1}, {'longitude': 1}, {'latitude': None, 'longitude': 1},
            {'latitude': True, 'longitude': 1}, {'latitude': 1, 'longitude': False},
            {'latitude': '1', 'longitude': 1}, {'latitude': [], 'longitude': 1},
            {'latitude': 91, 'longitude': 0}, {'latitude': 0, 'longitude': -181},
            {'latitude': float('nan'), 'longitude': 0}, {'latitude': 0, 'longitude': float('inf')},
            {'latitude': 10 ** 1000, 'longitude': 1},
        ):
            with self.subTest(campos=campos):
                self.verificar_erro(self.criar(**campos), 400)
        self.assertEqual(self.cliente.get('/ocorrencias').get_json(), [])

    def test_multipart_coordenadas_foto_privada_e_metadados(self):
        resposta = self.enviar_foto(latitude='-23.55', longitude='-46.63')
        self.assertEqual(resposta.status_code, 201)
        ocorrencia = resposta.get_json()
        self.assertEqual(ocorrencia['latitude'], -23.55)
        anexo = ocorrencia['anexos'][0]
        self.assertEqual(set(anexo), {'id', 'tipo', 'mime_type', 'tamanho', 'url'})
        self.assertEqual(anexo['tipo'], 'imagem')
        self.assertEqual(anexo['mime_type'], 'image/jpeg')
        arquivos = list(self.uploads.iterdir())
        self.assertEqual(len(arquivos), 1)
        self.assertRegex(arquivos[0].name, r'^[a-f0-9]{32}\.jpg$')
        self.assertNotIn('nome_arquivo', str(ocorrencia))
        self.verificar_erro(self.app.test_client().get(anexo['url']), 401)
        arquivo = self.cliente.get(anexo['url'])
        self.assertEqual(arquivo.status_code, 200)
        self.assertEqual(arquivo.mimetype, 'image/jpeg')
        self.assertEqual(arquivo.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(arquivo.headers['Cache-Control'], 'no-store')
        with Image.open(BytesIO(arquivo.data)) as foto:
            self.assertEqual(foto.size, (8, 6))
        arquivo.close()
        self.verificar_erro(self.cliente.get('/anexos/999'), 404)

    def test_multipart_localizacao_invalida_nao_deixa_arquivo(self):
        for campos in ({'latitude': 'abc', 'longitude': '1'}, {'latitude': '1'},
                       {'latitude': 'NaN', 'longitude': '1'}, {'latitude': '1', 'longitude': '181'}):
            with self.subTest(campos=campos):
                self.verificar_erro(self.enviar_foto(**campos), 400)
        self.assertEqual(self.cliente.get('/ocorrencias').get_json(), [])
        self.assertFalse(self.uploads.exists())

    def test_somente_um_arquivo_com_nome_correto(self):
        dados = MultiDict(list(self.dados.items()) + [
            ('arquivo', (self.foto(), 'a.jpg')), ('arquivo', (self.foto(), 'b.jpg')),
        ])
        self.verificar_erro(self.cliente.post('/ocorrencias', data=dados), 400)
        self.verificar_erro(self.cliente.post('/ocorrencias', data={**self.dados, 'outro': (self.foto(), 'a.jpg')}), 400)
        self.assertFalse(self.uploads.exists())

    def test_falso_jpeg_e_svg_rejeitados_sem_ocorrencia(self):
        for conteudo, codigo in ((b'\xff\xd8arquivo falso', 400), (b'<svg><script>alert(1)</script></svg>', 415)):
            resposta = self.cliente.post('/ocorrencias', data={
                **self.dados, 'arquivo': (BytesIO(conteudo), 'foto.jpg', 'image/jpeg'),
            })
            self.verificar_erro(resposta, codigo)
        self.assertEqual(self.cliente.get('/ocorrencias').get_json(), [])
        self.assertFalse(self.uploads.exists())

    def test_upload_mp4_real(self):
        fixture = Path(__file__).parent / 'fixtures' / 'curto.mp4'
        with fixture.open('rb') as video:
            resposta = self.cliente.post('/ocorrencias', data={
                **self.dados, 'arquivo': (video, 'video.mp4', 'video/mp4'),
            })
        self.assertEqual(resposta.status_code, 201)
        anexo = resposta.get_json()['anexos'][0]
        self.assertEqual(anexo['tipo'], 'video')
        self.assertEqual(anexo['mime_type'], 'video/mp4')
        arquivo = self.cliente.get(anexo['url'])
        self.assertEqual(arquivo.data, fixture.read_bytes())
        arquivo.close()

    def test_erro_de_banco_remove_upload_e_desfaz_ocorrencia(self):
        with conectar(self.banco) as conexao:
            conexao.execute("""CREATE TRIGGER falhar_anexo BEFORE INSERT ON anexos
                               BEGIN SELECT RAISE(ABORT, 'falha de teste'); END""")
        with self.assertLogs(self.app.logger, level='ERROR'):
            resposta = self.enviar_foto()
        self.verificar_erro(resposta, 500)
        self.assertEqual(self.cliente.get('/ocorrencias').get_json(), [])
        self.assertEqual(list(self.uploads.iterdir()), [])
        with conectar(self.banco) as conexao:
            self.assertEqual(conexao.execute('SELECT COUNT(*) FROM anexos').fetchone()[0], 0)

    def test_limite_total_da_requisicao(self):
        self.app.config['MAX_CONTENT_LENGTH'] = 64
        self.verificar_erro(self.criar(descricao='d' * 100), 413)
        self.assertEqual(self.cliente.get('/ocorrencias').get_json(), [])

    def test_chaves_estrangeiras_ativadas(self):
        with conectar(self.banco) as conexao:
            self.assertEqual(conexao.execute('PRAGMA foreign_keys').fetchone()[0], 1)
        with self.assertRaises(sqlite3.IntegrityError):
            with conectar(self.banco) as conexao:
                conexao.execute('INSERT INTO sessoes(usuario_id, token_hash, expira_em) VALUES (?, ?, ?)',
                                (999, 'hash', '2099-01-01T00:00:00+00:00'))


class MigracaoTest(unittest.TestCase):
    def test_banco_antigo_preserva_relato_sem_atribuir_autoria(self):
        with tempfile.TemporaryDirectory() as pasta:
            banco = Path(pasta) / 'legado.db'
            with sqlite3.connect(banco) as conexao:
                conexao.executescript("""
                    CREATE TABLE ocorrencias (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bairro TEXT NOT NULL, endereco TEXT NOT NULL, descricao TEXT NOT NULL,
                        gravidade TEXT NOT NULL, situacao TEXT NOT NULL, criado_em TEXT NOT NULL
                    );
                    INSERT INTO ocorrencias VALUES
                    (42, 'Bairro antigo', 'Rua antiga', 'Relato preservado', 'baixa', 'ativo', '2026-01-01T00:00:00+00:00');
                """)
            inicializar_banco(banco)
            inicializar_banco(banco)
            app = create_app({'TESTING': True, 'DATABASE': str(banco), 'UPLOAD_FOLDER': str(Path(pasta) / 'uploads')})
            cliente = app.test_client()
            sessao = cliente.post('/auth/cadastro', json={'nome': 'Primeira pessoa', 'email': 'primeira@example.com', 'senha': 'senha-teste-123'}).get_json()
            cliente.environ_base['HTTP_AUTHORIZATION'] = f"Bearer {sessao['token']}"
            resposta = cliente.get('/ocorrencias/42')
            self.assertEqual(resposta.status_code, 200)
            antigo = resposta.get_json()
            self.assertEqual(antigo['bairro'], 'Bairro antigo')
            self.assertIsNone(antigo['autor_id'])
            self.assertIsNone(antigo['latitude'])
            self.assertIsNone(antigo['longitude'])
            self.assertFalse(antigo['pode_alterar'])
            self.assertEqual(antigo['anexos'], [])
            self.assertEqual(cliente.patch('/ocorrencias/42/situacao', json={'situacao': 'resolvido'}).status_code, 403)
            nova = cliente.post('/ocorrencias', json={'bairro': 'Novo', 'endereco': 'Rua 2', 'descricao': 'Novo relato', 'gravidade': 'media'}).get_json()
            self.assertGreater(nova['id'], 42)
            self.assertEqual(nova['autor_id'], sessao['usuario']['id'])
            self.assertIsNone(cliente.get('/ocorrencias/42').get_json()['autor_id'])


if __name__ == '__main__':
    unittest.main()
