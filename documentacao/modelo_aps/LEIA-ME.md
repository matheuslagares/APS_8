# Modelo preenchível da documentação da APS

Este material organiza a rubrica recebida; não é um trabalho acadêmico pronto para entrega. O item 6 diz que não serão aceitos trabalhos elaborados por IA. O código e os materiais tiveram esse auxílio: é necessário esclarecer sua aceitação com o professor. Os capítulos possuem perguntas, campos e espaços para redação própria do grupo. Páginas reservadas não substituem conteúdo.

## Arquivos principais

- [Modelo Word editável](MODELO_PREENCHIVEL_APS.docx) e [prévia PDF](MODELO_PREENCHIVEL_APS.pdf): 29 páginas de organização, incluindo quatro UML e DER como referências técnicas para revisão.
- [Relatório técnico de código selecionado em Word](RELATORIO_TECNICO_CODIGO_SELECIONADO.docx) e [PDF](RELATORIO_TECNICO_CODIGO_SELECIONADO.pdf): seis páginas, inventário e 135 linhas selecionadas; não é o fonte integral.
- [Inventário técnico](INVENTARIO_TECNICO.md) e [JSON de origem](INVENTARIO_TECNICO.json): dados extraídos do commit `028b7041702f68e1a473d57acbe95037a8341a79`.
- [Diagramas](diagramas/): fontes PlantUML, PNG e SVG. São casos de uso, classes conceituais, sequência, atividades e DER físico.
- [ZIP de referência do fonte](FONTE_REFERENCIA_PARA_PREPARAR_NO_WINRAR.zip): fonte completo e recursos da versão inspecionada, sem banco, uploads, dependências instaladas ou credenciais locais.
- [Validação de páginas](VALIDACAO_PAGINAS.json): contagem dos PDFs e limites da verificação. [Checksums](SHA256_ARTEFATOS.txt) permitem conferir os arquivos.

A identificação pessoal foi deixada sem preenchimento, conforme solicitado. Na versão final, o grupo deverá tratar os itens de identificação e comentários de título/participantes conforme a orientação recebida.

## Orçamento confirmado no PDF do modelo

| Capítulo | Páginas reservadas | Limite da rubrica |
| --- | ---: | --- |
| Objetivo e motivação | 1 | 1–2 |
| Introdução | 2 | 2–4 |
| Fundamentos | 4 | 4–8 |
| Plano de desenvolvimento | 5 | 5–15 |
| Projeto: requisitos + quatro UML + DER | 6 | 3–8 |
| Código selecionado | 6 | Até 10 |

As páginas restantes são capa, índice, preparação da apresentação, bibliografia e orientação para anexar fichas. O índice corresponde ao modelo atual; depois de editar, atualizar páginas e conferir novamente os limites. A formatação final deve seguir o padrão institucional confirmado pelo professor.

A produção contém 2.096 linhas físicas em 21 arquivos (incluindo comentários e linhas vazias). Não se tentou encolher o código integral em dez páginas. Confirmar com o professor se aceita o relatório parcial de seis páginas acompanhado do fonte completo separado.

## Fonte para o WinRAR e extensão .doc

O ZIP fornecido é apenas uma referência transportável, produzido por script; não foi criado pelo WinRAR. Não o renomeie fingindo ser RAR ou documento Word. Nesta máquina não há WinRAR/RAR disponível, por isso não foi gerado um arquivo de upload `.doc`.

No computador com WinRAR:

1. Extraia o ZIP e confira o conteúdo da pasta `APS_8`.
2. Prepare a identificação e os comentários exigidos nos arquivos finais, usando apenas informações reais e a orientação sobre IA.
3. Use **Adicionar para o arquivo…** do WinRAR, selecione o formato **RAR** e crie o arquivo do código. Preserve a versão original `.rar`.
4. Teste o arquivo no próprio WinRAR e confirme que abre e contém o fonte completo.
5. Com as extensões visíveis no Explorador de Arquivos, faça uma cópia e renomeie a extensão da cópia de `.rar` para `.doc`, conforme a regra de envio recebida.

Esse `.doc` continua sendo um RAR com outro nome. Ele é diferente do relatório Word real `.docx` e da prévia PDF. Não houve envio ao sistema da UNIP.

## Fichas e apresentação

A última página do modelo é uma orientação e uma tabela auxiliar; não é a ficha oficial da instituição. Cada aluno precisa preencher o formulário oficial com atividades cronológicas e horas reais, totalizar e assinar de próprio punho. Não foram geradas assinaturas nem atribuídas horas.

A apresentação deve incluir todos os integrantes e demonstrar o programa em funcionamento no computador e o fluxo móvel escolhido. A rubrica informa perda de 50% para quem não participar. Os testes físicos com dois celulares, GPS real, SecureStore e mapas nativos continuam pendentes no projeto.

## Como reproduzir a geração técnica

As dependências opcionais estão em `scripts/requirements-documentacao.txt`; elas não são dependências da API. Requer Python 3.11+, LibreOffice e Java/Graphviz para renderização. Os diagramas foram renderizados com PlantUML 1.2026.9, cujo SHA-256 foi conferido com o checksum publicado no Maven Central.

Com os PNG/SVG dos diagramas já presentes:

```sh
python scripts/gerar_modelo_aps.py
soffice --headless --convert-to pdf --outdir documentacao/modelo_aps documentacao/modelo_aps/MODELO_PREENCHIVEL_APS.docx documentacao/modelo_aps/RELATORIO_TECNICO_CODIGO_SELECIONADO.docx
python scripts/validar_modelo_aps.py
```

A geração substitui somente os modelos gerados nesta pasta. Salve sua redação editada em uma cópia diferente antes de executar novamente. O inventário e o pacote são vinculados ao commit inspecionado: mudanças futuras no código exigem nova inspeção, seleção e conferência.
