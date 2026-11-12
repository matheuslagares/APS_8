import { useCallback, useEffect, useRef, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { listarOcorrencias } from '../services/api';
import MapaOcorrencias from '../components/MapaOcorrencias';
import { AvisoRelatos, Botao, Cabecalho, Carregamento, Mensagem } from '../components/Interface';
import { cores, estilos, rotuloGravidade, rotuloSituacao } from '../theme';

export default function ListaScreen({ onNovoRegistro, onAbrirDetalhes, mensagem }) {
  const [ocorrencias, setOcorrencias] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [modo, setModo] = useState('lista');
  const montada = useRef(false);
  const consultando = useRef(false);

  const carregar = useCallback(async () => {
    if (consultando.current) return;
    consultando.current = true;
    try {
      const dados = await listarOcorrencias();
      if (montada.current) setOcorrencias(dados);
    } catch (falha) {
      if (montada.current) setErro(falha.message);
    } finally {
      consultando.current = false;
      if (montada.current) setCarregando(false);
    }
  }, []);

  function atualizar() {
    setCarregando(true);
    setErro('');
    carregar();
  }

  useEffect(() => {
    montada.current = true;
    consultando.current = true;
    listarOcorrencias()
      .then((dados) => { if (montada.current) setOcorrencias(dados); })
      .catch((falha) => { if (montada.current) setErro(falha.message); })
      .finally(() => {
        consultando.current = false;
        if (montada.current) setCarregando(false);
      });
    return () => { montada.current = false; };
  }, []);

  function renderizarOcorrencia({ item }) {
    return (
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Abrir relato ${item.id}, ${item.bairro}, gravidade ${rotuloGravidade(item.gravidade)}, ${rotuloSituacao(item.situacao)}`}
        onPress={() => onAbrirDetalhes(item.id)}
        style={({ pressed }) => [estilos.cartao, locais.item, pressed && locais.pressionado]}
      >
        <View style={locais.linhaTitulo}>
          <Text style={locais.bairro}>{item.bairro}</Text>
          <Text style={estilos.pequeno}>#{item.id}</Text>
        </View>
        <Text style={estilos.subtitulo} numberOfLines={2}>{item.endereco}</Text>
        <View style={estilos.linha}>
          <Text style={locais.etiqueta}>Gravidade: {rotuloGravidade(item.gravidade)}</Text>
          <Text style={[locais.etiqueta, item.situacao === 'resolvido' && locais.resolvido]}>
            {rotuloSituacao(item.situacao)}
          </Text>
        </View>
        <Text style={locais.abrir}>Ver detalhes →</Text>
      </Pressable>
    );
  }

  return (
    <View style={estilos.tela}>
      <FlatList
        data={erro || modo === 'mapa' ? [] : ocorrencias}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderizarOcorrencia}
        contentContainerStyle={locais.lista}
        refreshing={carregando}
        onRefresh={atualizar}
        ListHeaderComponent={(
          <View>
            <Cabecalho titulo="Ocorrências" descricao="Consulte e compartilhe relatos de alagamentos na cidade." />
            <View style={locais.controles}>
              <AvisoRelatos />
              <Mensagem texto={mensagem} />
              <View style={estilos.linha}>
                <Botao titulo="Nova ocorrência" onPress={onNovoRegistro} />
                <Botao titulo="Atualizar" onPress={atualizar} secundario disabled={carregando} />
              </View>
              <Text style={estilos.pequeno}>A lista é atualizada ao abrir esta tela ou tocar em Atualizar.</Text>
              <View style={estilos.linha} accessibilityRole="tablist">
                {['lista', 'mapa'].map((opcao) => (
                  <Pressable
                    key={opcao} accessibilityRole="tab" accessibilityLabel={opcao === 'lista' ? 'Lista' : 'Mapa'}
                    accessibilityState={{ selected: modo === opcao }}
                    onPress={() => setModo(opcao)}
                    style={[locais.aba, modo === opcao && locais.abaSelecionada]}
                  >
                    <Text style={[locais.textoAba, modo === opcao && locais.textoAbaSelecionada]}>{opcao === 'lista' ? 'Lista' : 'Mapa'}</Text>
                  </Pressable>
                ))}
              </View>
              {!erro && !carregando && modo === 'mapa' && ocorrencias.length > 0 && (
                <MapaOcorrencias ocorrencias={ocorrencias} onAbrirDetalhes={onAbrirDetalhes} />
              )}
              {erro ? (
                <View style={locais.erro}>
                  <Mensagem texto={erro} erro />
                  <Botao titulo="Tentar novamente" onPress={atualizar} secundario />
                </View>
              ) : null}
            </View>
          </View>
        )}
        ListEmptyComponent={carregando ? <Carregamento /> : !erro && ocorrencias.length === 0 ? (
          <View style={[estilos.cartao, locais.vazio]}>
            <Text style={locais.bairro}>Nenhuma ocorrência cadastrada.</Text>
            <Text style={estilos.subtitulo}>Use Nova ocorrência para compartilhar o primeiro relato.</Text>
          </View>
        ) : null}
        ListFooterComponent={!erro && ocorrencias.length > 0 ? (
          <Text style={locais.total}>{ocorrencias.length} {ocorrencias.length === 1 ? 'relato cadastrado' : 'relatos cadastrados'}</Text>
        ) : null}
      />
    </View>
  );
}

const locais = StyleSheet.create({
  lista: { paddingBottom: 24 },
  controles: { paddingHorizontal: 22, paddingBottom: 20, gap: 16 },
  erro: { gap: 12 },
  item: { marginHorizontal: 22, marginBottom: 12 },
  linhaTitulo: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  bairro: { fontSize: 19, fontWeight: '700', color: cores.texto, flex: 1 },
  etiqueta: {
    backgroundColor: '#ECF1F4', color: cores.texto, borderRadius: 8,
    paddingHorizontal: 10, paddingVertical: 6, fontSize: 13, fontWeight: '600',
  },
  resolvido: { backgroundColor: cores.verdeClaro, color: cores.verde },
  abrir: { color: cores.verde, fontWeight: '700', fontSize: 14 },
  pressionado: { backgroundColor: '#EAF3EF' },
  vazio: { marginHorizontal: 22 },
  total: { textAlign: 'center', padding: 16, fontSize: 13, color: cores.secundario },
  aba: { minHeight: 44, paddingVertical: 10, paddingHorizontal: 22, borderRadius: 10, backgroundColor: cores.papel, borderWidth: 1, borderColor: cores.borda },
  abaSelecionada: { backgroundColor: cores.texto, borderColor: cores.texto },
  textoAba: { color: cores.texto, fontWeight: '700', fontSize: 15 },
  textoAbaSelecionada: { color: '#FFFFFF' },
});
