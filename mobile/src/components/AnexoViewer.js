import { useEffect, useMemo, useState } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { useEvent } from 'expo';
import { useVideoPlayer, VideoView } from 'expo-video';
import { carregarMidia } from '../services/api';
import { Botao, Carregamento, Mensagem } from './Interface';
import { cores, estilos } from '../theme';

function ImagemAnexo({ recurso, onTentarNovamente }) {
  const [erro, setErro] = useState(false);
  return erro ? (
    <View style={locais.grupo}>
      <Mensagem texto="Não foi possível abrir a imagem anexada." erro />
      <Botao titulo="Tentar abrir anexo novamente" onPress={onTentarNovamente} secundario />
    </View>
  ) : (
    <Image
      accessibilityLabel="Imagem anexada pelo autor do relato" accessible
      source={{ uri: recurso.uri, headers: recurso.headers }}
      style={locais.midia} resizeMode="contain" onError={() => setErro(true)}
    />
  );
}

function VideoAnexo({ recurso, onTentarNovamente }) {
  const fonte = useMemo(() => ({ uri: recurso.uri, headers: recurso.headers }), [recurso]);
  // O hook do expo-video libera o player ao desmontar. O vídeo começa pausado.
  const player = useVideoPlayer(fonte, (instancia) => { instancia.loop = false; });
  const { status } = useEvent(player, 'statusChange', { status: player.status });
  return (
    <View style={locais.grupo}>
      {status === 'error' ? (
        <>
          <Mensagem texto="Não foi possível reproduzir o vídeo anexado." erro />
          <Botao titulo="Tentar abrir anexo novamente" onPress={onTentarNovamente} secundario />
        </>
      ) : (
        <>
          <VideoView
            player={player} style={locais.midia} nativeControls contentFit="contain"
            accessibilityLabel="Vídeo anexado pelo autor do relato"
          />
          {status === 'loading' && <Carregamento texto="Preparando vídeo…" />}
          <Text style={estilos.pequeno}>Use os controles do vídeo para reproduzir ou pausar.</Text>
        </>
      )}
    </View>
  );
}

export default function AnexoViewer({ anexo }) {
  const id = anexo.id;
  const [recurso, setRecurso] = useState(null);
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(true);
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    let ativa = true;
    let liberar;
    // O serviço protege a requisição: Bearer em cabeçalho no celular, blob na web.
    // O token nunca entra na URL do arquivo ou no texto exibido na interface.
    carregarMidia({ id })
      .then((resposta) => {
        if (!ativa) {
          resposta.liberar?.();
          return;
        }
        liberar = resposta.liberar;
        setRecurso(resposta);
      })
      .catch((falha) => { if (ativa) setErro(falha.message); })
      .finally(() => { if (ativa) setCarregando(false); });
    return () => {
      ativa = false;
      // Revoga o blob da web mesmo quando a pessoa volta antes do download terminar.
      liberar?.();
    };
  }, [id, tentativa]);

  function tentarNovamente() {
    setRecurso(null);
    setErro('');
    setCarregando(true);
    setTentativa((anterior) => anterior + 1);
  }

  return (
    <View style={[estilos.cartao, locais.grupo]}>
      <Text style={estilos.rotulo}>{anexo.tipo === 'video' ? 'Vídeo do relato' : 'Imagem do relato'}</Text>
      {carregando ? <Carregamento texto="Abrindo anexo…" /> : erro ? (
        <>
          <Mensagem texto={erro} erro />
          <Botao titulo="Tentar abrir anexo novamente" onPress={tentarNovamente} secundario />
        </>
      ) : recurso ? (
        anexo.tipo === 'video'
          ? <VideoAnexo recurso={recurso} onTentarNovamente={tentarNovamente} />
          : <ImagemAnexo recurso={recurso} onTentarNovamente={tentarNovamente} />
      ) : null}
      <Text style={estilos.pequeno}>Anexo enviado pelo autor, sem verificação independente.</Text>
    </View>
  );
}

const locais = StyleSheet.create({
  grupo: { gap: 12 },
  midia: { width: '100%', height: 260, backgroundColor: cores.fundo, borderRadius: 10 },
});
