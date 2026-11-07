import { useCallback, useEffect, useState } from 'react';
import { BackHandler, StyleSheet, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import ListaScreen from './src/screens/ListaScreen';
import CadastroScreen from './src/screens/CadastroScreen';
import DetalhesScreen from './src/screens/DetalhesScreen';
import { cores } from './src/theme';

export default function App() {
  // Três telas cabem em uma navegação por estado: não precisamos de outra biblioteca.
  const [tela, setTela] = useState('lista');
  const [idSelecionado, setIdSelecionado] = useState(null);
  const [mensagem, setMensagem] = useState('');
  const [ocupado, setOcupado] = useState(false);

  const voltarParaLista = useCallback(() => {
    setTela('lista');
    setIdSelecionado(null);
  }, []);

  useEffect(() => {
    // O botão físico do Android volta para a lista. Durante uma gravação, aguardamos
    // a resposta para não deixar a pessoa sem saber se o servidor recebeu o pedido.
    const evento = BackHandler.addEventListener('hardwareBackPress', () => {
      if (ocupado) return true;
      if (tela === 'lista') return false;
      voltarParaLista();
      return true;
    });
    return () => evento.remove();
  }, [tela, ocupado, voltarParaLista]);

  function abrirCadastro() {
    setMensagem('');
    setTela('cadastro');
  }

  function abrirDetalhes(id) {
    setMensagem('');
    setIdSelecionado(id);
    setTela('detalhes');
  }

  function cadastroConcluido() {
    setMensagem('Relato cadastrado com sucesso.');
    voltarParaLista();
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={estilos.areaSegura}>
        <StatusBar style="dark" />
        <View style={estilos.conteudo}>
          {tela === 'lista' && (
            <ListaScreen
              mensagem={mensagem}
              onNovoRegistro={abrirCadastro}
              onAbrirDetalhes={abrirDetalhes}
            />
          )}
          {tela === 'cadastro' && (
            <CadastroScreen
              onVoltar={voltarParaLista}
              onSalvo={cadastroConcluido}
              onOcupadoChange={setOcupado}
            />
          )}
          {tela === 'detalhes' && (
            <DetalhesScreen
              id={idSelecionado}
              onVoltar={voltarParaLista}
              onOcupadoChange={setOcupado}
            />
          )}
        </View>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const estilos = StyleSheet.create({
  areaSegura: { flex: 1, backgroundColor: cores.fundo },
  conteudo: { flex: 1, width: '100%', maxWidth: 760, alignSelf: 'center' },
});
