# Inventário técnico de referência

**Material factual de apoio; não é a redação acadêmica final.**

Base inspecionada: `028b7041702f68e1a473d57acbe95037a8341a79`. Nenhum dado do banco real foi consultado para este inventário.

## Produção e métrica

São **2.096 linhas físicas em 21 arquivos**: 606 no backend e 1.490 no aplicativo. Linhas vazias e comentários estão incluídos; isso não é contagem de instruções executáveis. Testes, configurações, lockfiles e arquivos gerados estão separados no JSON.

| Arquivo | Linhas físicas |
| --- | ---: |
| `backend/app.py` | 315 |
| `backend/autenticacao.py` | 23 |
| `backend/database.py` | 43 |
| `backend/init_db.py` | 17 |
| `backend/midia.py` | 169 |
| `backend/schema.sql` | 39 |
| `mobile/App.js` | 192 |
| `mobile/index.js` | 8 |
| `mobile/src/components/AnexoViewer.js` | 109 |
| `mobile/src/components/Interface.js` | 76 |
| `mobile/src/components/LocalizacaoCampos.js` | 77 |
| `mobile/src/components/MapaOcorrencias.native.js` | 68 |
| `mobile/src/components/MapaOcorrencias.web.js` | 107 |
| `mobile/src/components/SeletorAnexo.js` | 85 |
| `mobile/src/config.js` | 30 |
| `mobile/src/screens/AuthScreen.js` | 115 |
| `mobile/src/screens/CadastroScreen.js` | 123 |
| `mobile/src/screens/DetalhesScreen.js` | 134 |
| `mobile/src/screens/ListaScreen.js` | 155 |
| `mobile/src/services/api.js` | 162 |
| `mobile/src/theme.js` | 49 |

## Rotas declaradas

| Método | Rota | Sessão | Referência |
| --- | --- | --- | --- |
| GET | `/saude` | Pública | `backend/app.py:119` |
| POST | `/auth/cadastro` | Pública | `backend/app.py:123` |
| POST | `/auth/login` | Pública | `backend/app.py:151` |
| GET | `/auth/me` | Bearer | `backend/app.py:168` |
| POST | `/auth/logout` | Bearer | `backend/app.py:172` |
| GET | `/ocorrencias` | Bearer | `backend/app.py:192` |
| POST | `/ocorrencias` | Bearer | `backend/app.py:234` |
| GET | `/ocorrencias/<int:id>` | Bearer | `backend/app.py:276` |
| PATCH | `/ocorrencias/<int:id>/situacao` | Bearer | `backend/app.py:285` |
| GET | `/anexos/<int:id>` | Bearer | `backend/app.py:304` |

## Banco físico e regras

| Tabela | Colunas | Relacionamentos |
| --- | --- | --- |
| usuarios | `id`, `nome`, `email`, `senha_hash` | Sem FK |
| sessoes | `id`, `usuario_id`, `token_hash`, `expira_em` | usuario_id → usuarios.id |
| ocorrencias | `id`, `bairro`, `endereco`, `descricao`, `gravidade`, `situacao`, `criado_em`, `autor_id`, `latitude`, `longitude` | autor_id → usuarios.id |
| anexos | `id`, `ocorrencia_id`, `nome_arquivo`, `tipo`, `mime_type`, `tamanho` | ocorrencia_id → ocorrencias.id |

A cardinalidade física de ocorrência para anexo é 0..N: não existe UNIQUE em `anexos.ocorrencia_id`. A API atual limita um arquivo por cadastro. `autor_id` admite nulo para registros legados; eles são somente leitura. O schema novo contém CHECK do par de coordenadas; a migração acrescenta os campos e a API também valida o par.

## Relatório de código e fonte completo

O relatório seleciona dez trechos existentes (135 linhas de origem), além do inventário. Ele é parcial. O fonte completo está no ZIP de referência; esse ZIP não foi criado com WinRAR e não deve ser apresentado como RAR nem como documento Word.

O item 8 exige comentário com título e participantes. A identificação pessoal foi omitida conforme solicitado e deve ser tratada pelo grupo/professor antes da entrega.

## Validação conhecida

Há 56 métodos de teste unitário identificados no código. Os resultados executados e seus limites estão em [TESTES.md](../TESTES.md); o inventário estático não equivale a nova execução. GPS e mapa nativos em celulares continuam pendentes.

Quatro UML confirmados: casos de uso, classes, sequência e atividades. O diagrama de classes é conceitual e distingue entidades de dados de módulos/funções existentes. O DER é uma quinta referência separada.

As fontes `.puml`, imagens PNG e vetores SVG ficam em [diagramas/](diagramas/). Todos são referências técnicas assistidas para validação do grupo.
