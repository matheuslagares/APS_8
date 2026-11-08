# Mídias sintéticas para o teste integrado

`foto-teste.png` é uma imagem RGB azul de 64 × 48 pixels, gerada localmente com o formato PNG. `video-teste.mp4` mostra a mesma cor por aproximadamente 0,8 segundo, em H.264/yuv420p, 160 × 120 pixels, sem áudio. Não contêm pessoas, locais ou dados reais.

O vídeo foi gerado com FFmpeg:

```sh
ffmpeg -f lavfi -i color=c=0x2584a8:s=160x120:d=0.8 -an -c:v libx264 -pix_fmt yuv420p -movflags +faststart video-teste.mp4
```

Os arquivos pequenos ficam versionados para executar `tests/fluxo_web.py` sem precisar de FFmpeg. A opção de gravação `--gravar` continua exigindo FFmpeg no computador.
