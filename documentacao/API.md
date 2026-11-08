# Contrato da API

As operações representam **relatos de usuários**, não alertas oficiais. As respostas de dados e erros usam JSON; a leitura de um anexo retorna os bytes do arquivo. O celular acessa a API por HTTP e não abre o SQLite ou a pasta de uploads diretamente.

## Autenticação

| Método e endereço | Corpo ou autenticação | Resposta |
| --- | --- | --- |
| `POST /auth/cadastro` | JSON com `nome`, `email`, `senha` | `201`, usuário e sessão |
| `POST /auth/login` | JSON com `email`, `senha` | `200`, usuário e sessão |
| `GET /auth/me` | Bearer | `200`, `{"usuario": {"id": 1, "nome": "...", "email": "..."}}` |
| `POST /auth/logout` | Bearer | `200`, objeto com `mensagem`; revoga a sessão |

Nome: texto de 1 a 100 caracteres. E-mail: formato válido, até 254 caracteres, com espaços das pontas removidos e normalização para minúsculas. Senha: de 8 a 128 caracteres. O servidor guarda a senha com hash scrypt e não a inclui nas respostas.

Cadastro e login retornam este formato; dados e token abaixo são ilustrativos:

```json
{
  "usuario": {"id": 1, "nome": "Participante", "email": "pessoa@example.com"},
  "token": "TOKEN_OPACO_RECEBIDO_NA_RESPOSTA",
  "expira_em": "2026-11-15T12:00:00+00:00"
}
```

A sessão tem validade de sete dias. Nas operações protegidas, envie `Authorization: Bearer TOKEN_RECEBIDO`. Não coloque o token no endereço, em logs ou nos arquivos do projeto. O servidor armazena apenas o hash SHA-256 do token. `/saude`, cadastro, login e requisições de preflight `OPTIONS` não exigem sessão. As operações de relatos, anexos, consulta da sessão e logout exigem Bearer válido.

## Operações

| Método e endereço | Operação | Sucesso |
| --- | --- | --- |
| `GET /saude` | Verificar o processo da API | `200`, `{"status":"ok"}` |
| `GET /ocorrencias` | Listar por identificador decrescente | `200`, array; vazio: `[]` |
| `POST /ocorrencias` | Criar um relato | `201`, objeto criado |
| `GET /ocorrencias/<id>` | Consultar detalhes | `200`, objeto |
| `PATCH /ocorrencias/<id>/situacao` | Atualizar situação | `200`, objeto atualizado |
| `GET /anexos/<id>` | Consultar arquivo com Bearer | `200`, bytes com MIME validado |

O teste de saúde confirma uma resposta da API. Para confirmar o acesso ao banco, consulte também `/ocorrencias` com autenticação após inicializá-lo. A lista é compartilhada entre os participantes autenticados, não limitada ao autor.

## Cadastro

Envie `Content-Type: application/json` com um objeto:

```json
{
  "bairro": "Centro",
  "endereco": "Rua de exemplo, próximo ao número 100",
  "descricao": "Água acumulada bloqueando parte da rua",
  "gravidade": "media"
}
```

| Campo | Regra |
| --- | --- |
| `bairro` | Texto obrigatório, até 100 caracteres após remover espaços nas pontas |
| `endereco` | Texto obrigatório, até 200 caracteres após remover espaços nas pontas |
| `descricao` | Texto obrigatório, até 1.000 caracteres após remover espaços nas pontas |
| `gravidade` | Texto: `baixa`, `media` ou `alta` |
| `latitude` e `longitude` | Opcionais; ambos ausentes/nulos ou ambos presentes. Números finitos, latitude entre -90 e 90 e longitude entre -180 e 180 |

O servidor atribui `id`, `autor_id`, `situacao: "ativo"` e `criado_em`. A autoria vem da sessão. A data usa uma representação textual ISO 8601 em UTC. O cliente não escolhe esses valores ao cadastrar. Em JSON, as coordenadas devem ser números, sem aspas; booleanos não são aceitos como números.

Exemplo de formato de resposta; o número e a data são ilustrativos:

```json
{
  "id": 1,
  "bairro": "Centro",
  "endereco": "Rua de exemplo, próximo ao número 100",
  "descricao": "Água acumulada bloqueando parte da rua",
  "gravidade": "media",
  "situacao": "ativo",
  "criado_em": "2026-11-07T23:00:00+00:00",
  "autor_id": 1,
  "pode_alterar": true,
  "latitude": null,
  "longitude": null,
  "anexos": []
}
```

`pode_alterar` é calculado para a conta da requisição e não deve ser enviado no cadastro. É falso para outras contas e para relatos antigos sem autor identificado. Registros da primeira versão permanecem no banco com `autor_id: null` e não são atribuídos automaticamente a uma conta.

### Cadastro com um anexo

Também é aceito `multipart/form-data`, com os mesmos campos textuais, coordenadas como textos numéricos opcionais e **um único arquivo no campo `arquivo`**. O cliente deve deixar a biblioteca HTTP montar o `Content-Type` e seu boundary, sem fixar manualmente o cabeçalho de multipart.

- Formatos aceitos: imagem JPEG ou PNG; vídeo MP4.
- Limite por arquivo: 20 MiB (20 × 1.024 × 1.024 bytes).
- Limite da requisição completa: 24 MiB.
- Imagens: até 20 milhões de pixels; são verificadas, orientadas e reprocessadas com Pillow para remover EXIF.
- Vídeos: a estrutura MP4 é validada, sem afirmar decodificação completa ou duração máxima.
- Relato e arquivo são cadastrados na mesma operação. Arquivo inválido ou falha de gravação não deve deixar um novo relato parcialmente cadastrado.

Com anexo, a resposta inclui um item no array `anexos`, neste formato ilustrativo:

```json
{
  "id": 1,
  "tipo": "imagem",
  "mime_type": "image/jpeg",
  "tamanho": 120000,
  "url": "/anexos/1"
}
```

A URL é relativa à API e exige o mesmo cabeçalho Bearer. Abrir a URL diretamente no navegador sem sessão não dá acesso ao arquivo. O caminho de armazenamento não é exposto. A resposta de arquivo usa o MIME validado e `X-Content-Type-Options: nosniff`.

## Alteração da situação

```http
PATCH /ocorrencias/1/situacao
Authorization: Bearer TOKEN_RECEBIDO
Content-Type: application/json
```

```json
{"situacao": "resolvido"}
```

A API aceita `ativo` e `resolvido`, **somente para o autor autenticado**. A tela de detalhes oferece a ação de resolver um relato próprio ativo. Outra conta recebe `403`, inclusive se enviar o pedido diretamente à API. Relatos legados sem autor são somente leitura. A confirmação vem da API e permanece no banco; trocar somente um texto na tela não altera o registro.

## Falhas

Erros seguem o formato:

```json
{"erro": "O bairro é obrigatório."}
```

| Código | Significado |
| --- | --- |
| `400` | JSON malformado, conteúdo que não é objeto ou campos inválidos |
| `401` | Sessão ausente, inválida, revogada ou expirada; credenciais inválidas no login |
| `403` | Conta não autorizada a alterar esse relato |
| `404` | Identificador inexistente |
| `409` | E-mail já cadastrado |
| `413` | Arquivo, imagem ou requisição excede os limites |
| `415` | Formato de conteúdo ou mídia não aceito |
| `500` | Falha inesperada; detalhes técnicos ficam no terminal da API |

Um retorno HTTP `400` ou `500` não rejeita automaticamente a promessa do `fetch`. O cliente precisa conferir `response.ok` e mostrar a mensagem da API. O cliente também cancela requisições demoradas para sair do carregamento e permitir uma tentativa manual.

## Exemplo no PowerShell

Com uma conta criada no aplicativo e a API iniciada em outro terminal, obtenha o login pelo diálogo de credenciais e guarde a resposta em uma variável. Não projete ou imprima o token:

```powershell
$acesso = Get-Credential -Message "Informe o e-mail e a senha de uma conta do prototipo"
$corpoLogin = @{
    email = $acesso.UserName
    senha = $acesso.GetNetworkCredential().Password
} | ConvertTo-Json

$sessao = Invoke-RestMethod `
    -Uri "http://127.0.0.1:5000/auth/login" `
    -Method Post -ContentType "application/json" -Body $corpoLogin
$cabecalhos = @{ Authorization = "Bearer $($sessao.token)" }

$dadosTeste = @{
    bairro = "Centro"
    endereco = "Rua de exemplo, 100"
    descricao = "Acumulo de agua na via"
    gravidade = "media"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:5000/ocorrencias" `
    -Method Post `
    -Headers $cabecalhos `
    -ContentType "application/json" `
    -Body $dadosTeste

Invoke-RestMethod -Uri "http://127.0.0.1:5000/ocorrencias" -Headers $cabecalhos

Invoke-RestMethod -Uri "http://127.0.0.1:5000/auth/logout" -Method Post -Headers $cabecalhos
```

Para testar fora do computador servidor, substitua `127.0.0.1` pelo IPv4 real acessível pela rede.
