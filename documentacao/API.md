# Contrato da API

As operações representam **relatos de usuários**, não alertas oficiais. Todas as rotas respondem em JSON. O celular acessa a API por HTTP; não abre o arquivo SQLite.

## Operações

| Método e endereço | Operação | Sucesso |
| --- | --- | --- |
| `GET /saude` | Verificar o processo da API | `200`, `{"status":"ok"}` |
| `GET /ocorrencias` | Listar por identificador decrescente | `200`, array; vazio: `[]` |
| `POST /ocorrencias` | Criar um relato | `201`, objeto criado |
| `GET /ocorrencias/<id>` | Consultar detalhes | `200`, objeto |
| `PATCH /ocorrencias/<id>/situacao` | Atualizar situação | `200`, objeto atualizado |

O teste de saúde confirma uma resposta da API. Para confirmar o acesso ao banco, consulte também `/ocorrencias` após inicializá-lo.

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

O servidor atribui `id`, `situacao: "ativo"` e `criado_em`. A data usa uma representação textual ISO 8601 em UTC. O cliente não escolhe esses valores ao cadastrar.

Exemplo de formato de resposta; o número e a data são ilustrativos:

```json
{
  "id": 1,
  "bairro": "Centro",
  "endereco": "Rua de exemplo, próximo ao número 100",
  "descricao": "Água acumulada bloqueando parte da rua",
  "gravidade": "media",
  "situacao": "ativo",
  "criado_em": "2026-11-07T23:00:00+00:00"
}
```

## Alteração da situação

```http
PATCH /ocorrencias/1/situacao
Content-Type: application/json
```

```json
{"situacao": "resolvido"}
```

A API aceita `ativo` e `resolvido`. A tela de detalhes oferece a ação de resolver um relato ativo. A confirmação vem da API e permanece no banco; trocar somente um texto na tela não altera o registro.

## Falhas

Erros seguem o formato:

```json
{"erro": "O bairro é obrigatório."}
```

| Código | Significado |
| --- | --- |
| `400` | JSON malformado, conteúdo que não é objeto ou campos inválidos |
| `404` | Identificador inexistente |
| `415` | Requisição de gravação sem conteúdo JSON |
| `500` | Falha inesperada; detalhes técnicos ficam no terminal da API |

Um retorno HTTP `400` ou `500` não rejeita automaticamente a promessa do `fetch`. O cliente precisa conferir `response.ok` e mostrar a mensagem da API. O cliente também cancela requisições demoradas para sair do carregamento e permitir uma tentativa manual.

## Exemplo no PowerShell

Com a API iniciada em outro terminal:

```powershell
$dadosTeste = @{
    bairro = "Centro"
    endereco = "Rua de exemplo, 100"
    descricao = "Acumulo de agua na via"
    gravidade = "media"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:5000/ocorrencias" `
    -Method Post `
    -ContentType "application/json" `
    -Body $dadosTeste

Invoke-RestMethod -Uri "http://127.0.0.1:5000/ocorrencias"
```

Para testar fora do computador servidor, substitua `127.0.0.1` pelo IPv4 real acessível pela rede.
