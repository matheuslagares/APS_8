// mapa do celular (android/ios) - parte do Guilherme
// obs: tem outro arquivo .web.js pro navegador, o expo escolhe sozinho qual usar
import { Pressable, Text, View } from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import { cores, corGravidade, estilos, rotuloGravidade } from '../theme';

export default function MapaOcorrencias({ ocorrencias, onAbrirDetalhes = (id) => {}, compacto = false }) {
  // so as ocorrencias q tem localizacao
  const pontos = ocorrencias.filter((item) => item.latitude != null && item.longitude != null);

  if (pontos.length === 0) {
    return <Text style={estilos.subtitulo}>Nenhum relato com localização para mostrar no mapa.</Text>;
  }

  return (
    <View style={{ gap: 10 }}>
      <View style={{ height: compacto ? 220 : 320, borderRadius: 14, overflow: 'hidden', borderWidth: 1, borderColor: cores.borda }}>
        {/* o mapa comeca centralizado no primeiro ponto */}
        <MapView
          style={{ flex: 1 }}
          initialRegion={{
            latitude: pontos[0].latitude,
            longitude: pontos[0].longitude,
            latitudeDelta: 0.05,
            longitudeDelta: 0.05,
          }}
        >
          {pontos.map((item) => (
            <Marker
              key={item.id}
              coordinate={{ latitude: item.latitude, longitude: item.longitude }}
              title={item.bairro}
              description={'Gravidade relatada: ' + rotuloGravidade(item.gravidade)}
              pinColor={corGravidade(item.gravidade)}
              onCalloutPress={() => onAbrirDetalhes(item.id)}
            />
          ))}
        </MapView>
      </View>
      <Text style={estilos.pequeno}>Pontos informados pelos participantes, sem verificação. O mapa base depende de Internet.</Text>

      {/* lista de links embaixo do mapa (nao aparece no modo compacto) */}
      {!compacto && pontos.map((item) => (
        <Pressable key={item.id} onPress={() => onAbrirDetalhes(item.id)} style={estilos.link}>
          <Text style={estilos.textoLink}>#{item.id} · {item.bairro} · {rotuloGravidade(item.gravidade)}</Text>
        </Pressable>
      ))}
    </View>
  );
}
