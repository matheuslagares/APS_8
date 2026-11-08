import { useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import { cores, estilos, rotuloGravidade } from '../theme';

function coordenadaValida(item) {
  return Number.isFinite(item.latitude) && Number.isFinite(item.longitude) &&
    Math.abs(item.latitude) <= 90 && Math.abs(item.longitude) <= 180;
}

export default function MapaOcorrencias({ ocorrencias, onAbrirDetalhes = undefined, compacto = false }) {
  const pontos = useMemo(() => ocorrencias.filter(coordenadaValida), [ocorrencias]);
  const mapa = useRef(null);
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    if (!pronto || !mapa.current || !pontos.length) return;
    if (pontos.length === 1) {
      mapa.current.animateToRegion({
        latitude: pontos[0].latitude, longitude: pontos[0].longitude,
        latitudeDelta: 0.02, longitudeDelta: 0.02,
      }, 250);
    } else {
      mapa.current.fitToCoordinates(pontos.map(({ latitude, longitude }) => ({ latitude, longitude })), {
        edgePadding: { top: 45, right: 45, bottom: 45, left: 45 }, animated: false,
      });
    }
  }, [pontos, pronto]);

  if (!pontos.length) {
    return <Text style={estilos.subtitulo}>Nenhum relato com localização para mostrar no mapa.</Text>;
  }
  return (
    <View style={locais.grupo}>
      <View style={[locais.moldura, { height: compacto ? 220 : 320 }]}>
        {/* O provedor padrão já está no Expo Go: Google no Android, Apple no iOS. */}
        <MapView
          ref={mapa} style={locais.mapa} onMapReady={() => setPronto(true)}
          accessibilityLabel="Mapa dos relatos com localização"
          initialRegion={{ latitude: pontos[0].latitude, longitude: pontos[0].longitude, latitudeDelta: 0.02, longitudeDelta: 0.02 }}
        >
          {pontos.map((item) => (
            <Marker
              key={item.id} coordinate={{ latitude: item.latitude, longitude: item.longitude }}
              title={item.bairro} description={`Gravidade relatada: ${rotuloGravidade(item.gravidade)}`}
              pinColor={item.gravidade === 'alta' ? '#A73535' : item.gravidade === 'media' ? '#B2750B' : cores.verde}
              onPress={() => onAbrirDetalhes?.(item.id)}
            />
          ))}
        </MapView>
      </View>
      <Text style={estilos.pequeno}>Pontos informados pelos participantes, sem verificação. O mapa base depende de Internet.</Text>
      {!compacto && pontos.map((item) => (
        <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={`Abrir relato ${item.id} no mapa, ${item.bairro}`} onPress={() => onAbrirDetalhes?.(item.id)} style={locais.link}>
          <Text style={locais.textoLink}>#{item.id} · {item.bairro} · {rotuloGravidade(item.gravidade)}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const locais = StyleSheet.create({
  grupo: { gap: 10 },
  mapa: { flex: 1 },
  moldura: { borderRadius: 14, overflow: 'hidden', borderWidth: 1, borderColor: cores.borda },
  link: { borderRadius: 10, padding: 12, borderWidth: 1, borderColor: cores.borda, backgroundColor: cores.papel },
  textoLink: { fontSize: 14, color: cores.verde, fontWeight: '700' },
});
