// mostra a foto ou o video de uma ocorrencia - Henrique
import { useEffect, useState } from 'react';
import { Image, Text, View } from 'react-native';
import { useVideoPlayer, VideoView } from 'expo-video';
import { carregarMidia } from '../services/api';
import { Carregamento, Mensagem } from './Interface';
import { estilos } from '../theme';

// o player de video precisa ficar num componente separado pq usa hook
function Video({ recurso }) {
  const player = useVideoPlayer({ uri: recurso.uri, headers: recurso.headers });
  return <VideoView player={player} style={estilos.midia} nativeControls contentFit="contain" />;
}

export default function AnexoViewer({ anexo }) {
  const [recurso, setRecurso] = useState(null);
  const [erro, setErro] = useState('');

  // busca o arquivo qdo o componente aparece na tela
  useEffect(() => {
    carregarMidia(anexo)
      .then((resultado) => setRecurso(resultado))
      .catch((falha) => setErro(falha.message));
  }, [anexo]);

  const ehVideo = anexo.tipo === 'video';

  return (
    <View style={[estilos.cartao, { gap: 12 }]}>
      <Text style={estilos.rotulo}>{ehVideo ? 'Vídeo do relato' : 'Imagem do relato'}</Text>

      {erro ? <Mensagem texto={erro} erro /> : null}
      {!recurso && !erro && <Carregamento texto="Abrindo anexo…" />}

      {recurso && ehVideo && <Video recurso={recurso} />}
      {recurso && !ehVideo && (
        <Image
          source={{ uri: recurso.uri, headers: recurso.headers }}
          style={estilos.midia} resizeMode="contain"
          onError={() => setErro('Não foi possível abrir a imagem anexada.')}
        />
      )}

      <Text style={estilos.pequeno}>Anexo enviado pelo autor, sem verificação independente.</Text>
    </View>
  );
}
