// tela inicial com a lista (ou mapa) das ocorrencias - Gustavo
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import { listarOcorrencias } from '../services/api';
import MapaOcorrencias from '../components/MapaOcorrencias';
import { AvisoRelatos, Botao, Cabecalho, Carregamento, Mensagem } from '../components/Interface';
import { cores, estilos, rotuloGravidade, rotuloSituacao } from '../theme';

export default function ListaScreen({ onNovoRegistro, onAbrirDetalhes, mensagem }) {
  const [ocorrencias, setOcorrencias] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');
  const [verMapa, setVerMapa] = useState(false); // false = lista, true = mapa

  async function carregar() {
    setCarregando(true);
    setErro('');
    try {
      const dados = await listarOcorrencias();
      setOcorrencias(dados);
    } catch (falha) {
      setErro(falha.message);
    }
    setCarregando(false);
  }

  // [] no final = roda so uma vez qdo a tela abre
  useEffect(() => {
    listarOcorrencias()
      .then((dados) => setOcorrencias(dados))
      .catch((falha) => setErro(falha.message))
      .finally(() => setCarregando(false));
  }, []);

  return (
    <ScrollView contentContainerStyle={estilos.rolagem}>
      <Cabecalho titulo="Ocorrências" descricao="Consulte e compartilhe relatos de alagamentos na cidade." />
      <View style={estilos.conteudo}>
        <AvisoRelatos />
        <Mensagem texto={mensagem} />

        <View style={estilos.linha}>
          <Botao titulo="Nova ocorrência" onPress={onNovoRegistro} />
          <Botao titulo="Atualizar" onPress={carregar} secundario disabled={carregando} />
          <Botao titulo={verMapa ? 'Ver lista' : 'Ver mapa'} onPress={() => setVerMapa(!verMapa)} secundario />
        </View>

        <Mensagem texto={erro} erro />
        {carregando && <Carregamento />}

        {!carregando && !erro && ocorrencias.length === 0 && (
          <View style={estilos.cartao}>
            <Text style={estilos.rotulo}>Nenhuma ocorrência cadastrada.</Text>
            <Text style={estilos.subtitulo}>Use Nova ocorrência para compartilhar o primeiro relato.</Text>
          </View>
        )}

        {/* modo mapa */}
        {!carregando && verMapa && ocorrencias.length > 0 && (
          <MapaOcorrencias ocorrencias={ocorrencias} onAbrirDetalhes={onAbrirDetalhes} />
        )}

        {/* modo lista - um cartao pra cada ocorrencia */}
        {!carregando && !verMapa && ocorrencias.map((item) => (
          <Pressable key={item.id} onPress={() => onAbrirDetalhes(item.id)} style={estilos.cartao}>
            <Text style={estilos.rotulo}>{item.bairro}  <Text style={estilos.pequeno}>#{item.id}</Text></Text>
            <Text style={estilos.subtitulo} numberOfLines={2}>{item.endereco}</Text>
            <Text style={estilos.pequeno}>
              Gravidade: {rotuloGravidade(item.gravidade)} · {rotuloSituacao(item.situacao)}
            </Text>
            <Text style={{ color: cores.verde, fontWeight: '700' }}>Ver detalhes →</Text>
          </Pressable>
        ))}

        {!carregando && ocorrencias.length > 0 && (
          <Text style={[estilos.pequeno, { textAlign: 'center' }]}>{ocorrencias.length} relato(s) cadastrado(s)</Text>
        )}
      </View>
    </ScrollView>
  );
}
