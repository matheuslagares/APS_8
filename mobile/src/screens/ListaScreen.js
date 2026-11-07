import { useCallback, useEffect, useRef, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { listarOcorrencias } from '../services/api';
import { AvisoRelatos, Botao, Cabecalho, Carregamento, Mensagem } from '../components/Interface';
import { cores, estilos, rotuloGravidade, rotuloSituacao } from '../theme';

export default function ListaScreen({ onNovoRegistro, onAbrirDetalhes, mensagem }) {
  const [ocorrencias, setOcorrencias] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const montada = useRef(false);
  const consultando = useRef(false);

  const carregar = useCallback(async () => {
    // A referência bloqueia cliques antes mesmo de o React redesenhar o botão.
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
    // O carregamento já começa como true. O efeito só altera o estado quando
    // a operação externa termina, evitando uma renderização inicial extra.
    listarOcorrencias()
      .then((dados) => { if (montada.current) setOcorrencias(dados); })
      .catch((falha) => { if (montada.current) setErro(falha.message); })
      .finally(() => {
        consultando.current = false;
        if (montada.current) setCarregando(false);
      });
    // Uma resposta atrasada não deve atualizar uma tela que já foi fechada.
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
        data={erro ? [] : ocorrencias}
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
              {erro ? (
                <View style={locais.erro}>
                  <Mensagem texto={erro} erro />
                  <Botao titulo="Tentar novamente" onPress={atualizar} secundario />
                </View>
              ) : null}
            </View>
          </View>
        )}
        ListEmptyComponent={carregando ? <Carregamento /> : !erro ? (
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
});
