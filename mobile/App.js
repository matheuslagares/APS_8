import { useCallback, useEffect, useRef, useState } from 'react';
import { BackHandler, Keyboard, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import ListaScreen from './src/screens/ListaScreen';
import CadastroScreen from './src/screens/CadastroScreen';
import DetalhesScreen from './src/screens/DetalhesScreen';
import AuthScreen from './src/screens/AuthScreen';
import { Botao, Cabecalho, Carregamento, Mensagem } from './src/components/Interface';
import { aoExpirarSessao, restaurarSessao, sair } from './src/services/api';
import { cores } from './src/theme';

export default function App() {
  // A sessão controla o acesso; a navegação do protótipo continua por estado.
  const [tela, setTela] = useState('lista');
  const [idSelecionado, setIdSelecionado] = useState(null);
  const [mensagem, setMensagem] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [usuario, setUsuario] = useState(null);
  const [restaurando, setRestaurando] = useState(true);
  const [erroRestauracao, setErroRestauracao] = useState('');
  const [avisoAcesso, setAvisoAcesso] = useState('');
  const [saindo, setSaindo] = useState(false);
  const [erroSaida, setErroSaida] = useState('');
  const acaoSessaoEmAndamento = useRef(false);

  const limparNavegacao = useCallback(() => {
    setTela('lista');
    setIdSelecionado(null);
    setMensagem('');
    setOcupado(false);
    setErroSaida('');
  }, []);

  useEffect(() => {
    let ativa = true;
    // A sessão nativa vem do SecureStore. Na web ela existe só na memória.
    restaurarSessao()
      .then((pessoa) => { if (ativa) setUsuario(pessoa); })
      .catch((falha) => { if (ativa) setErroRestauracao(falha.message); })
      .finally(() => { if (ativa) setRestaurando(false); });
    const removerObservador = aoExpirarSessao(() => {
      if (!ativa) return;
      setUsuario(null);
      setAvisoAcesso('Sua sessão expirou. Entre novamente.');
      setErroRestauracao('');
      limparNavegacao();
    });
    return () => {
      ativa = false;
      removerObservador();
    };
  }, [limparNavegacao]);

  async function tentarRestaurar() {
    if (acaoSessaoEmAndamento.current) return;
    acaoSessaoEmAndamento.current = true;
    setRestaurando(true);
    setErroRestauracao('');
    try {
      setUsuario(await restaurarSessao());
    } catch (falha) {
      // Uma falha de rede não deve descartar uma sessão ainda válida no aparelho.
      setErroRestauracao(falha.message);
    } finally {
      acaoSessaoEmAndamento.current = false;
      setRestaurando(false);
    }
  }

  function acessoConfirmado(pessoa) {
    limparNavegacao();
    setUsuario(pessoa);
    setAvisoAcesso('');
  }

  async function encerrarSessao() {
    if (acaoSessaoEmAndamento.current || ocupado) return;
    acaoSessaoEmAndamento.current = true;
    setSaindo(true);
    Keyboard.dismiss();
    setErroSaida('');
    try {
      // Só saímos depois da confirmação: apagar a tela não revoga o token no servidor.
      await sair();
      setUsuario(null);
      limparNavegacao();
      setAvisoAcesso('Você saiu da sua conta.');
    } catch (falha) {
      setErroSaida(falha.message);
    } finally {
      acaoSessaoEmAndamento.current = false;
      setSaindo(false);
    }
  }

  const voltarParaLista = useCallback(() => {
    setTela('lista');
    setIdSelecionado(null);
  }, []);

  useEffect(() => {
    // O botão físico do Android volta para a lista. Durante uma gravação, aguardamos
    // a resposta para não deixar a pessoa sem saber se o servidor recebeu o pedido.
    const evento = BackHandler.addEventListener('hardwareBackPress', () => {
      if (ocupado || saindo) return true;
      if (tela === 'lista') return false;
      voltarParaLista();
      return true;
    });
    return () => evento.remove();
  }, [tela, ocupado, saindo, voltarParaLista]);

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
          {restaurando ? (
            <View>
              <Cabecalho titulo="Verificando acesso" descricao="Aguarde enquanto consultamos sua sessão." />
              <Carregamento texto="Restaurando sessão…" />
            </View>
          ) : erroRestauracao ? (
            <View style={estilos.erroAcesso}>
              <Cabecalho titulo="Acesso indisponível" descricao="Não foi possível conferir sua sessão no servidor." />
              <Mensagem texto={erroRestauracao} erro />
              <Botao titulo="Tentar novamente" onPress={tentarRestaurar} />
            </View>
          ) : !usuario ? (
            <AuthScreen onAutenticado={acessoConfirmado} mensagem={avisoAcesso} />
          ) : (
            <>
              <View style={estilos.conta}>
                <Text numberOfLines={2} style={estilos.nomeUsuario}>Conta: {usuario.nome}</Text>
                <Botao titulo={saindo ? 'Saindo…' : 'Sair'} onPress={encerrarSessao} secundario disabled={ocupado} carregando={saindo} />
              </View>
              {erroSaida ? <View style={estilos.aviso}><Mensagem texto={erroSaida} erro /></View> : null}
              <View style={estilos.telas} pointerEvents={saindo ? 'none' : 'auto'}>
                {tela === 'lista' ? (
                  <ListaScreen
                    mensagem={mensagem}
                    onNovoRegistro={abrirCadastro}
                    onAbrirDetalhes={abrirDetalhes}
                  />
                ) : tela === 'cadastro' ? (
                  <CadastroScreen
                    onVoltar={voltarParaLista}
                    onSalvo={cadastroConcluido}
                    onOcupadoChange={setOcupado}
                  />
                ) : (
                  <DetalhesScreen
                    id={idSelecionado}
                    onVoltar={voltarParaLista}
                    onOcupadoChange={setOcupado}
                  />
                )}
              </View>
            </>
          )}
        </View>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const estilos = StyleSheet.create({
  areaSegura: { flex: 1, backgroundColor: cores.fundo },
  conteudo: { flex: 1, width: '100%', maxWidth: 760, alignSelf: 'center' },
  conta: { paddingHorizontal: 22, paddingTop: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  nomeUsuario: { color: cores.secundario, flex: 1, fontSize: 14 },
  aviso: { paddingHorizontal: 22, paddingTop: 12 },
  erroAcesso: { padding: 22, gap: 16 },
  telas: { flex: 1 },
});
