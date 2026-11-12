import { useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { entrar, registrarUsuario } from '../services/api';
import { AvisoRelatos, Botao, Cabecalho, Mensagem } from '../components/Interface';
import { cores, estilos } from '../theme';

export default function AuthScreen({ onAutenticado, mensagem = '' }) {
  const [criandoConta, setCriandoConta] = useState(false);
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState('');
  const enviandoRef = useRef(false);

  function alternarModo() {
    if (enviandoRef.current) return;
    setCriandoConta((anterior) => !anterior);
    setSenha('');
    setErro('');
  }

  async function enviar() {
    if (enviandoRef.current) return;
    const emailLimpo = email.trim();
    if (criandoConta && !nome.trim()) {
      setErro('Informe seu nome.');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailLimpo)) {
      setErro('Informe um e-mail válido.');
      return;
    }
    if (!senha || (criandoConta && (senha.length < 8 || senha.length > 128))) {
      setErro(criandoConta ? 'A senha deve ter entre 8 e 128 caracteres.' : 'Informe sua senha.');
      return;
    }
    enviandoRef.current = true;
    setEnviando(true);
    setErro('');
    try {
      const pessoa = criandoConta
        ? await registrarUsuario({ nome: nome.trim(), email: emailLimpo, senha })
        : await entrar({ email: emailLimpo, senha });
      setSenha('');
      onAutenticado(pessoa);
    } catch (falha) {
      setErro(falha.message);
    } finally {
      enviandoRef.current = false;
      setEnviando(false);
    }
  }

  return (
    <KeyboardAvoidingView style={estilos.tela} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={locais.rolagem}>
        <Cabecalho
          titulo={criandoConta ? 'Criar conta' : 'Entrar'}
          descricao="Acesse sua conta para consultar relatos e compartilhar o que você observou."
        />
        <View style={locais.conteudo}>
          <AvisoRelatos />
          <Mensagem texto={mensagem} />
          {criandoConta && (
            <View style={locais.grupo}>
              <Text style={estilos.rotulo}>Nome</Text>
              <TextInput
                accessibilityLabel="Nome" placeholder="Seu nome" placeholderTextColor={cores.secundario}
                value={nome} onChangeText={setNome} maxLength={100} editable={!enviando}
                autoCapitalize="words" autoComplete="name" style={estilos.campo}
              />
            </View>
          )}
          <View style={locais.grupo}>
            <Text style={estilos.rotulo}>E-mail</Text>
            <TextInput
              accessibilityLabel="E-mail" placeholder="voce@exemplo.com" placeholderTextColor={cores.secundario}
              value={email} onChangeText={setEmail} maxLength={254} editable={!enviando}
              keyboardType="email-address" autoCapitalize="none" autoCorrect={false}
              autoComplete="email" style={estilos.campo}
            />
          </View>
          <View style={locais.grupo}>
            <Text style={estilos.rotulo}>Senha</Text>
            <TextInput
              accessibilityLabel="Senha" placeholder={criandoConta ? 'Entre 8 e 128 caracteres' : 'Sua senha'}
              placeholderTextColor={cores.secundario} value={senha} onChangeText={setSenha}
              maxLength={128} editable={!enviando} secureTextEntry autoCapitalize="none" autoCorrect={false}
              autoComplete={criandoConta ? 'new-password' : 'current-password'}
              style={estilos.campo} onSubmitEditing={enviar}
            />
          </View>
          <Mensagem texto={erro} erro />
          <Botao
            titulo={enviando ? 'Aguarde…' : criandoConta ? 'Criar conta' : 'Entrar'}
            onPress={enviar} carregando={enviando}
          />
          <Botao
            titulo={criandoConta ? 'Já tenho uma conta' : 'Quero criar uma conta'}
            onPress={alternarModo} secundario disabled={enviando}
          />
          <Text style={estilos.pequeno}>Você pode consultar os relatos de todos os participantes. Somente o autor pode alterar a situação do próprio relato.</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const locais = StyleSheet.create({
  rolagem: { paddingBottom: 28 },
  conteudo: { paddingHorizontal: 22, gap: 18 },
  grupo: { gap: 8 },
});
