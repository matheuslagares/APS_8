// App.js - arquivo principal, controla qual tela aparece
// a navegacao e feita na mao com um state "tela" (mais facil q instalar react-navigation)
// parte do Saad
import { useEffect, useState } from 'react';
import { BackHandler, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import AuthScreen from './src/screens/AuthScreen';
import ListaScreen from './src/screens/ListaScreen';
import CadastroScreen from './src/screens/CadastroScreen';
import DetalhesScreen from './src/screens/DetalhesScreen';
import { Botao, Carregamento } from './src/components/Interface';
import { aoExpirarSessao, restaurarSessao, sair } from './src/services/api';
import { cores } from './src/theme';

export default function App() {
  const [usuario, setUsuario] = useState(null);       // null = ninguem logado
  const [iniciando, setIniciando] = useState(true);   // true enquanto verifica o login salvo
  const [tela, setTela] = useState('lista');          // 'lista', 'cadastro' ou 'detalhes'
  const [idSelecionado, setIdSelecionado] = useState(null);
  const [mensagem, setMensagem] = useState('');

  // qdo o app abre: ve se ja tinha login salvo
  useEffect(() => {
    restaurarSessao().then((pessoa) => {
      setUsuario(pessoa);
      setIniciando(false);
    });

    // se o servidor disser q a sessao expirou, volta pro login
    aoExpirarSessao(() => {
      setUsuario(null);
      setTela('lista');
      setMensagem('Sua sessão expirou. Entre novamente.');
    });
  }, []);

  // botao voltar do android: volta pra lista em vez de fechar o app
  useEffect(() => {
    const evento = BackHandler.addEventListener('hardwareBackPress', () => {
      if (tela === 'lista') return false; // false = deixa o android fechar o app
      setTela('lista');
      return true;
    });
    return () => evento.remove();
  }, [tela]);

  function logou(pessoa) {
    setUsuario(pessoa);
    setMensagem('');
    setTela('lista');
  }

  async function deslogar() {
    await sair();
    setUsuario(null);
    setMensagem('Você saiu da sua conta.');
  }

  function abrirDetalhes(id) {
    setIdSelecionado(id);
    setMensagem('');
    setTela('detalhes');
  }

  function abrirCadastro() {
    setMensagem('');
    setTela('cadastro');
  }

  function voltar() {
    setTela('lista');
  }

  function cadastroSalvo() {
    setMensagem('Relato cadastrado com sucesso.');
    setTela('lista');
  }

  // escolhe o q vai aparecer no meio da tela
  let conteudo;
  if (iniciando) {
    conteudo = <Carregamento texto="Verificando acesso…" />;
  } else if (!usuario) {
    conteudo = <AuthScreen onAutenticado={logou} mensagem={mensagem} />;
  } else if (tela === 'cadastro') {
    conteudo = <CadastroScreen onVoltar={voltar} onSalvo={cadastroSalvo} />;
  } else if (tela === 'detalhes') {
    conteudo = <DetalhesScreen id={idSelecionado} onVoltar={voltar} />;
  } else {
    conteudo = <ListaScreen mensagem={mensagem} onNovoRegistro={abrirCadastro} onAbrirDetalhes={abrirDetalhes} />;
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={{ flex: 1, backgroundColor: cores.fundo }}>
        <StatusBar style="dark" />
        {/* maxWidth pra nao ficar esticado demais no navegador */}
        <View style={{ flex: 1, width: '100%', maxWidth: 760, alignSelf: 'center' }}>
          {/* barra de cima com o nome do usuario e o botao sair */}
          {usuario && (
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 22, paddingTop: 10 }}>
              <Text style={{ flex: 1, color: cores.secundario }}>Conta: {usuario.nome}</Text>
              <Botao titulo="Sair" onPress={deslogar} secundario />
            </View>
          )}
          {conteudo}
        </View>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}
