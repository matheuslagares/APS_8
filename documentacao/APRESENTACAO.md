# Roteiro de apresentação — 5 a 8 minutos

O formato definido para a demonstração móvel é **Expo Go**. O roteiro abaixo dura aproximadamente sete minutos; o grupo deve ensaiar e ajustar ao tempo permitido pelo professor. Os nomes de quem apresenta devem ser preenchidos pelo grupo.

**Situação da validação:** os resultados antigos de 21 testes da API e sete cenários web pertencem à primeira versão, sem login, GPS ou anexos. Consulte [TESTES.md](TESTES.md) para os resultados da versão atual. A compatibilidade do Expo SDK 57 com o Expo Go instalado e a demonstração com dois celulares físicos continuam pendentes até a execução registrada pelo grupo.

## Preparar antes de falar

Siga a instalação do [README](../README.md) e a preparação de [TESTES.md](TESTES.md). Pare a API para copiar o banco e a pasta `uploads` antes do ensaio. Depois, mantenha API e Expo abertos em dois terminais e confirme `/saude` no celular. Prepare duas contas distintas e use apenas relatos e anexos fictícios. Não exiba senhas ou tokens na projeção.

A [galeria de apoio](evidencias/index.html) já contém vídeos e capturas de uma execução web real com dados fictícios. Baixe a pasta completa para exibi-la sem Internet. Identifique esse material como clientes de navegador, mantendo o teste em celulares registrado separadamente.

| Papel no ensaio | Integrante |
| --- | --- |
| Explicar objetivo e arquitetura | A preencher: __________ |
| Operar o dispositivo A | A preencher: __________ |
| Operar o dispositivo B | A preencher: __________ |
| Explicar testes e limitações | A preencher: __________ |

Uma pessoa pode assumir mais de um papel. Todos devem conseguir explicar o fluxo completo.

## Sequência e falas sugeridas

| Tempo | O que mostrar | Fala sugerida |
| --- | --- | --- |
| 0:00–0:40 | Nome e objetivo | “Nosso projeto se chama Alerta de Alagamentos. Ele permite cadastrar e consultar relatos de alagamentos urbanos. São informações dos participantes, sem verificação: não são alertas oficiais.” |
| 0:40–1:30 | Diagrama de componentes de [ARQUITETURA.md](ARQUITETURA.md) | “O aplicativo é o cliente. Ele envia pedidos HTTP para uma API em Flask. A sessão identifica a conta. A API valida os campos, acessa o SQLite e fornece os anexos autenticados. O celular não abre o arquivo do banco.” |
| 1:30–4:10 | Login, cadastro com localização e mídia opcionais, consulta e autoria | Siga o roteiro prático abaixo. Explique cada ação enquanto ela acontece. |
| 4:10–5:10 | Reiniciar a API e consultar o registro | “O dado foi salvo em disco. Vamos encerrar e iniciar a API usando o mesmo banco. Depois de consultar novamente, o registro deve permanecer com a situação resolvida.” Diga que isso foi comprovado neste ensaio somente se o resultado aparecer. |
| 5:10–6:20 | Testes e comportamento quando o servidor para | “Os resultados da versão atual estão registrados na documentação. Os clientes web automatizados são navegadores isolados. Quando a API para, a interface mostra erro e permite tentar novamente; ela não consegue consultar sozinha.” Cite somente os testes da versão atual que efetivamente passaram. |
| 6:20–7:00 | Limitações e conclusão da demonstração | “Só o autor pode resolver seu relato. Isso controla a alteração, mas não verifica o conteúdo. A atualização entre clientes é manual. O servidor e o banco são únicos: não implementamos banco distribuído nem tolerância a falhas.” |

Para reduzir a cinco minutos, apresente a persistência pelo registro de teste e concentre a demonstração no cadastro, na consulta pelo outro cliente e na resolução. Para chegar a oito minutos, inclua uma consulta com a API parada e a recuperação após reiniciá-la. Não altere o código durante a apresentação.

## Demonstração prática — dois clientes

No ensaio físico, A e B são os celulares. Em uma gravação de apoio web, são contextos independentes de navegador, e isso deve ser informado ao público. A gravação web não comprova o requisito de uso em dois celulares.

1. **A e B: entrar com contas diferentes.** Diga: “O token de sessão identifica cada conta. Ambos podem consultar; somente o autor pode resolver seu próprio relato.” Abra Ocorrências e informe que os dados são fictícios.
2. **A: tocar em Nova ocorrência e preencher:**

   | Campo | Dado fictício do ensaio |
   | --- | --- |
   | Bairro | Centro — demonstração acadêmica |
   | Endereço | Rua fictícia, próximo ao número 100 |
   | Descrição | Relato fictício: água acumulada em parte da rua |
   | Gravidade | Média |

3. **A: mostrar os campos opcionais.** Obtenha a localização somente após autorizar o compartilhamento e selecione uma imagem JPEG/PNG ou um MP4 fictício de até 20 MiB. Se negar o GPS, explique que pode salvar sem coordenadas. Não use imagens ou coordenadas pessoais na demonstração.
4. **A: salvar uma vez.** Diga: “A tela bloqueia o envio enquanto aguarda a resposta. O servidor valida, usa o autor da sessão, gera o identificador e a data e confirma o cadastro com seu anexo.” Anote o identificador.
5. **B: atualizar, abrir o relato e consultar o mapa/anexo.** Encontre o mesmo identificador e mostre que não há ação de resolver para outra conta. Diga: “O mapa organiza os relatos com coordenadas; os demais continuam na lista. A mídia é fornecida pela API após autenticação.”
6. **A: abrir o próprio relato e marcar como resolvido.** Aguarde a confirmação. **B: atualizar** e conferir **Resolvido**. Diga: “A autoria é conferida na API; esconder um botão não seria suficiente. A alteração aparece após nova consulta.”
7. **Computador: parar e reiniciar somente a API.** Não apague nem troque o banco ou os uploads. Consulte novamente. Se o relato, a mídia e a situação permanecerem, mostre a evidência de persistência.

Se a rede falhar, descreva o resultado observado. Consulte a lista antes de repetir um cadastro sem confirmação: o servidor pode ter gravado antes de a resposta se perder. Use a gravação de apoio identificada como web e registre o teste físico como pendente ou falhou, conforme o caso.

## Perguntas para ensaiar

| Pergunta possível | Resposta em linguagem simples |
| --- | --- |
| Por que o celular não acessa o SQLite diretamente? | A API concentra o acesso, valida os pedidos e oferece as mesmas operações a todos os clientes. |
| Onde os registros permanecem? | No arquivo `backend/alagamentos.db`, no computador da API. Parar a API não apaga o arquivo. |
| O que é uma falha parcial? | Uma parte pode continuar aberta enquanto outra não responde. A tela pode funcionar, mas uma API desligada impede a consulta. |
| O sistema atende mais de um cliente? | Clientes podem enviar pedidos ao mesmo servidor. O SQLite coordena o acesso e serializa gravações; não fizemos teste de carga para definir capacidade. |
| Está tudo sincronizado automaticamente? | Não. O outro cliente precisa consultar novamente, por exemplo pelo botão Atualizar. |
| Quem pode marcar como resolvido? | Somente o autor autenticado. A API recusa outra conta, mesmo que ela envie o pedido sem usar o botão da tela. |
| O que acontece com relatos antigos? | São preservados, mas não recebem um autor inventado. Sem autoria, ficam disponíveis somente para consulta. |
| O GPS acompanha a pessoa? | Não. Ele é opcional, solicitado pela pessoa em primeiro plano, para associar uma posição ao relato. |
| Por que o mapa pode não carregar? | Depende da Internet e do provedor externo. O relato continua consultável na lista. |
| Onde ficam as fotos e os vídeos? | Nos uploads do servidor. A API exige sessão para entregá-los. O backup precisa incluir banco e uploads. |
| Um relato de gravidade alta é um alerta oficial? | Não. A gravidade foi informada por um participante e não foi verificada. |
| O banco é distribuído? | Não. A comunicação envolve processos em dispositivos distintos, mas o banco é centralizado. |
| O sistema continua salvando sem rede? | Não. Não há modo offline nem fila de envio; o formulário mantém os campos quando o envio falha. |
| O login comprova a identidade ou verifica o relato? | Não. Não há verificação de e-mail nem moderação. O login controla acesso e autoria da alteração. |

## Registro do ensaio

```text
Data: __________   Horário: __________
Integrantes e papéis: ________________________________________
Tempo total medido: __________
Dispositivos e versões reais: ________________________________
Contas distintas usadas (sem senhas): _________________________
GPS permitido / negado e resultado: ___________________________
Anexo fictício / tipo / tamanho: ______________________________
Relato fictício usado / identificador: _______________________
Resultado da consulta no segundo dispositivo: ________________
Resultado após reiniciar a API: ______________________________
Falhas observadas e correções: ________________________________
Evidência guardada em: ________________________________________
```
