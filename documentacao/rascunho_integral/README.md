# Alerta de Alagamentos — documentação integral

Documento com textos completos, organizado conforme as escolhas ABNT registradas em `../NORMAS_ABNT_ADOTADAS.md`. A formatação foi verificada, sem certificação normativa ou institucional.

- [Documento Word editável](RASCUNHO_INTEGRAL_APS_ABNT.docx)
- [Documento PDF](RASCUNHO_INTEGRAL_APS_ABNT.pdf)
- [Relatório de código em PDF](RELATORIO_CODIGO.pdf)
- [Relatório de código editável](RELATORIO_CODIGO.docx)
- [Textos-base completos](TEXTOS_BASE.json)
- [Diagramas e fontes PlantUML](diagramas/)
- [Conferência de páginas e formatação](VALIDACAO_PAGINAS.json)

São 36 páginas no documento: objetivo 1; introdução 2; fundamentos 4; plano 5; projeto 6; código 7. Os demais elementos incluem capa, resumos, sumário, referências e orientações de atividades. O relatório separado tem 7 páginas. As cinco figuras compreendem casos de uso, classes conceituais, sequência, atividades e modelo ER.

## Autoria e pendências reais

Este rascunho integral foi produzido com IA. O enunciado recebido diz que não serão aceitos trabalhos elaborados por Inteligência Artificial. Portanto, estes arquivos não podem ser apresentados como autoria independente dos alunos nem como entrega já aprovada: o grupo precisa discutir sua utilização com o professor e produzir sua contribuição autoral conforme a orientação recebida.

A identificação dos integrantes foi omitida a pedido. Horas, assinaturas manuscritas, dados da banca e resultados em dois celulares físicos não foram inventados. A tabela auxiliar de atividades não substitui a ficha oficial individual da UNIP. Os textos descrevem evidências técnicas existentes: 56 testes de API e 15 cenários web registrados, sem afirmar validação nativa no Expo Go.

O relatório apresenta trechos comentados e o inventário das 2.096 linhas físicas de produção, incluindo linhas vazias e comentários. A aceitação de trechos com fonte completo separado precisa ser confirmada com o professor. O ZIP de referência contém o código completo da base técnica indicada; não é um RAR. Para a carga exigida, criar o arquivo pelo WinRAR e renomear uma cópia para `.doc`, conforme a instrução institucional, mantendo o original. Renomear não transforma o conteúdo em documento Word.

## Reprodução

Na raiz do repositório, executar `python scripts/gerar_rascunho_integral.py`, converter os dois DOCX para PDF com LibreOffice e executar:

```sh
python scripts/validar_modelo_aps.py --pasta documentacao/rascunho_integral --principal RASCUNHO_INTEGRAL_APS_ABNT --codigo RELATORIO_CODIGO
```

Se o conteúdo mudar e alterar a paginação, executar o validador primeiro com `--atualizar-mapa`, gerar novamente os documentos e PDFs e repetir a validação final. As fontes Arial/Courier configuradas no Word são substituídas por Liberation no PDF deste ambiente, conforme a verificação registrada.
