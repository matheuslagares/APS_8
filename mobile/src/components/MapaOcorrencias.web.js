import { useEffect, useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import 'leaflet/dist/leaflet.css';
import { Botao, Mensagem } from './Interface';
import { cores, estilos, rotuloGravidade } from '../theme';

function coordenadaValida(item) {
  return Number.isFinite(item.latitude) && Number.isFinite(item.longitude) &&
    Math.abs(item.latitude) <= 90 && Math.abs(item.longitude) <= 180;
}

export default function MapaOcorrencias({ ocorrencias, onAbrirDetalhes = undefined, compacto = false }) {
  const pontos = useMemo(() => ocorrencias.filter(coordenadaValida), [ocorrencias]);
  const elemento = useRef(null);
  const mapa = useRef(null);
  const leaflet = useRef(null);
  const marcadores = useRef(null);
  const tiles = useRef(null);
  const abrir = useRef(onAbrirDetalhes);
  useEffect(() => { abrir.current = onAbrirDetalhes; }, [onAbrirDetalhes]);
  const [pronto, setPronto] = useState(false);
  const [erro, setErro] = useState('');
  const possuiPontos = pontos.length > 0;

  useEffect(() => {
    if (!possuiPontos) return;
    let ativa = true;
    let observer;
    // O import fica no efeito para não acessar window durante a preparação web.
    import('leaflet').then((modulo) => {
      if (!ativa || !elemento.current) return;
      const L = modulo.default || modulo;
      leaflet.current = L;
      const atual = L.map(elemento.current, { scrollWheelZoom: false });
      mapa.current = atual;
      // OSM exige atribuição. Nenhuma coordenada pessoal é enviada à API de relatos
      // só por mover o mapa: o servidor recebe GPS apenas ao salvar o formulário.
      tiles.current = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(atual);
      tiles.current.on('tileerror', () => {
        if (ativa) setErro('Não foi possível carregar o mapa base. Confira a Internet; os dados dos relatos continuam disponíveis.');
      });
      marcadores.current = L.layerGroup().addTo(atual);
      if (typeof ResizeObserver !== 'undefined') {
        observer = new ResizeObserver(() => atual.invalidateSize());
        observer.observe(elemento.current);
      }
      setPronto(true);
    }).catch(() => {
      if (ativa) setErro('Não foi possível abrir o mapa. Você pode consultar os relatos pela lista.');
    });
    return () => {
      ativa = false;
      observer?.disconnect();
      mapa.current?.remove();
      mapa.current = null;
      marcadores.current = null;
      tiles.current = null;
      setPronto(false);
    };
  }, [possuiPontos]);

  useEffect(() => {
    if (!pronto || !mapa.current || !marcadores.current) return;
    const L = leaflet.current;
    marcadores.current.clearLayers();
    pontos.forEach((item) => {
      const cor = item.gravidade === 'alta' ? '#A73535' : item.gravidade === 'media' ? '#B2750B' : cores.verde;
      const marcador = L.circleMarker([item.latitude, item.longitude], {
        radius: 10, color: '#FFFFFF', weight: 2, fillColor: cor, fillOpacity: 0.95,
      }).addTo(marcadores.current);
      // Dados de participantes entram como texto; nunca são interpolados em HTML.
      const legenda = document.createElement('span');
      legenda.textContent = `#${item.id} · ${item.bairro} · ${rotuloGravidade(item.gravidade)}`;
      marcador.bindTooltip(legenda);
      marcador.on('click', () => abrir.current?.(item.id));
    });
    if (pontos.length === 1) mapa.current.setView([pontos[0].latitude, pontos[0].longitude], 15);
    else if (pontos.length > 1) mapa.current.fitBounds(pontos.map((item) => [item.latitude, item.longitude]), { padding: [35, 35], maxZoom: 16 });
  }, [pontos, pronto]);

  if (!possuiPontos) return <Text style={estilos.subtitulo}>Nenhum relato com localização para mostrar no mapa.</Text>;
  return (
    <View style={locais.grupo}>
      <div
        ref={elemento} role="img" aria-label="Mapa dos relatos com localização"
        style={{ width: '100%', height: compacto ? 220 : 320, border: `1px solid ${cores.borda}`, borderRadius: 14 }}
      />
      <Mensagem texto={erro} erro />
      {erro && pronto ? <Botao titulo="Tentar carregar mapa" onPress={() => { setErro(''); tiles.current?.redraw(); }} secundario /> : null}
      <Text style={estilos.pequeno}>Pontos informados pelos participantes, sem verificação. Mapa base: © OpenStreetMap contributors.</Text>
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
  link: { borderRadius: 10, padding: 12, borderWidth: 1, borderColor: cores.borda, backgroundColor: cores.papel },
  textoLink: { fontSize: 14, color: cores.verde, fontWeight: '700' },
});
