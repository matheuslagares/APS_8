// mapa do navegador usando a biblioteca leaflet - Guilherme
// o react-native-maps nao funciona na web, por isso esse arquivo separado
// TODO: ver com o Gustavo se da pra deixar igual o do celular
import { useEffect, useRef } from 'react';
import { Pressable, Text, View } from 'react-native';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { cores, corGravidade, estilos, rotuloGravidade } from '../theme';

export default function MapaOcorrencias({ ocorrencias, onAbrirDetalhes = (id) => {}, compacto = false }) {
  const div = useRef(null); // a <div> onde o mapa vai ser desenhado
  const pontos = ocorrencias.filter((item) => item.latitude != null && item.longitude != null);

  useEffect(() => {
    if (pontos.length === 0) return;

    // cria o mapa e coloca as imagens do OpenStreetMap
    const mapa = L.map(div.current, { scrollWheelZoom: false });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(mapa);

    // uma bolinha colorida pra cada ocorrencia
    pontos.forEach((item) => {
      const bolinha = L.circleMarker([item.latitude, item.longitude], {
        radius: 10, color: '#FFFFFF', weight: 2, fillColor: corGravidade(item.gravidade), fillOpacity: 0.95,
      }).addTo(mapa);
      bolinha.bindTooltip('#' + item.id + ' · ' + item.bairro);
      bolinha.on('click', () => onAbrirDetalhes(item.id));
    });

    // ajusta o zoom pra caber todos os pontos
    mapa.fitBounds(pontos.map((item) => [item.latitude, item.longitude]), { padding: [35, 35], maxZoom: 15 });

    // qdo sair da tela apaga o mapa (se nao der erro de "map already initialized")
    return () => mapa.remove();
  }, [ocorrencias]); // eslint-disable-line react-hooks/exhaustive-deps

  if (pontos.length === 0) {
    return <Text style={estilos.subtitulo}>Nenhum relato com localização para mostrar no mapa.</Text>;
  }

  return (
    <View style={{ gap: 10 }}>
      <div ref={div} style={{ width: '100%', height: compacto ? 220 : 320, border: '1px solid ' + cores.borda, borderRadius: 14 }} />
      <Text style={estilos.pequeno}>Pontos informados pelos participantes, sem verificação. Mapa base: © OpenStreetMap contributors.</Text>
      {!compacto && pontos.map((item) => (
        <Pressable key={item.id} onPress={() => onAbrirDetalhes(item.id)} style={estilos.link}>
          <Text style={estilos.textoLink}>#{item.id} · {item.bairro} · {rotuloGravidade(item.gravidade)}</Text>
        </Pressable>
      ))}
    </View>
  );
}
