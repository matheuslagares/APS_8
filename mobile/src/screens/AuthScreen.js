// tela de login e de criar conta (as duas na msm tela) - Matheus
import { useState } from 'react';
import { ScrollView, Text, TextInput, View } from 'react-native';
import { entrar, registrarUsuario } from '../services/api';
import { AvisoRelatos, Botao, Cabecalho, Mensagem } from '../components/Interface';
import { cores, estilos } from '../theme';

export default function AuthScreen({ onAutenticado, mensagem = '' }) {
  // criandoConta = true mostra o campo de nome tb
  const [criandoConta, setCriandoConta] = useState(false);
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState('');

  function trocarModo() {
    setCriandoConta(!criandoConta);
    setSenha('');
    setErro('');
  }

  async function enviar() {
    // validacao simples antes de mandar pro servidor
    if (criandoConta && nome.trim() === '') {
      setErro('Informe seu nome.');
      return;
    }
    if (!email.includes('@')) {
      setErro('Informe um e-mail válido.');
      return;
    }
    if (senha.length < 8) {
      setErro('A senha deve ter pelo menos 8 caracteres.');
      return;
    }

    setEnviando(true);
    setErro('');
    try {
      let usuario;
      if (criandoConta) {
        usuario = await registrarUsuario({ nome: nome.trim(), email: email.trim(), senha });
      } else {
        usuario = await entrar({ email: email.trim(), senha });
      }
      onAutenticado(usuario); // avisa o App.js q logou
    } catch (falha) {
      setErro(falha.message);
      setEnviando(false);
    }
  }

  return (
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={estilos.rolagem}>
      <Cabecalho
        titulo={criandoConta ? 'Criar conta' : 'Entrar'}
        descricao="Acesse sua conta para consultar relatos e compartilhar o que você observou."
      />
      <View style={estilos.conteudo}>
        <AvisoRelatos />
        <Mensagem texto={mensagem} />

        {criandoConta && (
          <View style={estilos.grupo}>
            <Text style={estilos.rotulo}>Nome</Text>
            <TextInput
              placeholder="Seu nome" placeholderTextColor={cores.secundario}
              value={nome} onChangeText={setNome} maxLength={100} style={estilos.campo}
            />
          </View>
        )}

        <View style={estilos.grupo}>
          <Text style={estilos.rotulo}>E-mail</Text>
          <TextInput
            placeholder="voce@exemplo.com" placeholderTextColor={cores.secundario}
            value={email} onChangeText={setEmail} keyboardType="email-address"
            autoCapitalize="none" style={estilos.campo}
          />
        </View>

        <View style={estilos.grupo}>
          <Text style={estilos.rotulo}>Senha</Text>
          {/* secureTextEntry esconde a senha com bolinhas */}
          <TextInput
            placeholder="Mínimo 8 caracteres" placeholderTextColor={cores.secundario}
            value={senha} onChangeText={setSenha} maxLength={128} secureTextEntry
            autoCapitalize="none" style={estilos.campo} onSubmitEditing={enviar}
          />
        </View>

        <Mensagem texto={erro} erro />
        <Botao titulo={criandoConta ? 'Criar conta' : 'Entrar'} onPress={enviar} carregando={enviando} />
        <Botao
          titulo={criandoConta ? 'Já tenho uma conta' : 'Quero criar uma conta'}
          onPress={trocarModo} secundario disabled={enviando}
        />
      </View>
    </ScrollView>
  );
}
