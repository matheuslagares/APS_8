# Evidências da demonstração de apoio

Execução automatizada de 07/11/2026, das 21:54:03 às 21:54:20 (America/Sao_Paulo). O JSON preserva os horários em UTC.

Abra [index.html](index.html) com todos os arquivos desta pasta juntos. O navegador foi configurado em português e no fuso America/Sao_Paulo. São dados fictícios em dois clientes isolados do Chromium, usando a versão web do aplicativo, uma API real e um SQLite temporário. O banco de demonstração não foi utilizado.

Resultado: **sete cenários passaram**, com zero erros de JavaScript capturados. O [registro JSON](resultado.json) lista os cenários e os hashes SHA-256 dos arquivos de código exercitados. [SHA256SUMS](SHA256SUMS) identifica os arquivos de mídia e o registro preservados nesta pasta.

Os vídeos WebM VP9 não possuem narração e têm durações diferentes. Eles mostram páginas distintas da mesma execução; os controles de reprodução são independentes. Não são uma gravação do Expo Go nem um teste com celulares físicos.

Para reproduzir, siga [TESTES.md](../TESTES.md) e execute `python tests/fluxo_web.py --gravar` com FFmpeg e as dependências opcionais disponíveis. Nesta máquina foi usado `CHROMIUM_PATH=/usr/bin/chromium`.

O formato móvel escolhido é **Expo Go**. Ainda é necessário registrar o cadastro em um celular, a consulta no outro, a resolução, a atualização manual e a persistência após reiniciar a API na rede real da demonstração. Complete também os dados acadêmicos e o diário com informações reais.
