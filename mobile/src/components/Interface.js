import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { cores, estilos } from '../theme';

export function Cabecalho({ titulo, descricao }) {
  return (
    <View style={estilos.cabecalho}>
      <Text style={estilos.marca}>ALERTA DE ALAGAMENTOS</Text>
      <Text accessibilityRole="header" style={estilos.titulo}>{titulo}</Text>
      <Text style={estilos.subtitulo}>{descricao}</Text>
    </View>
  );
}

export function Botao({ titulo, onPress, secundario = false, disabled = false, carregando = false }) {
  const bloqueado = disabled || carregando;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={titulo}
      accessibilityState={{ disabled: bloqueado, busy: carregando }}
      disabled={bloqueado}
      onPress={onPress}
      style={({ pressed }) => [
        locais.botao, secundario && locais.botaoSecundario,
        bloqueado && locais.bloqueado, pressed && locais.pressionado,
      ]}
    >
      {carregando && <ActivityIndicator size="small" color={secundario ? cores.texto : '#FFFFFF'} />}
      <Text style={[locais.textoBotao, secundario && locais.textoSecundario]}>{titulo}</Text>
    </Pressable>
  );
}

export function Mensagem({ texto, erro = false }) {
  if (!texto) return null;
  return (
    <View style={[locais.mensagem, erro && locais.mensagemErro]}>
      <Text
        accessibilityLiveRegion="polite"
        accessibilityRole={erro ? 'alert' : 'text'}
        style={[locais.textoMensagem, erro && locais.textoErro]}
      >{texto}</Text>
    </View>
  );
}

export function Carregamento({ texto = 'Carregando relatos…' }) {
  return (
    <View style={locais.carregamento}>
      <ActivityIndicator size="large" color={cores.verde} />
      <Text accessibilityLiveRegion="polite" style={estilos.subtitulo}>{texto}</Text>
    </View>
  );
}

export function AvisoRelatos() {
  return <Text style={estilos.pequeno}>Relatos de usuários, sem verificação. Não são alertas oficiais.</Text>;
}

const locais = StyleSheet.create({
  botao: {
    backgroundColor: cores.verde, borderRadius: 12, minHeight: 48,
    paddingHorizontal: 17, paddingVertical: 13, flexDirection: 'row', gap: 9,
    alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: cores.verde,
  },
  botaoSecundario: { backgroundColor: cores.papel, borderColor: cores.borda },
  textoBotao: { color: '#FFFFFF', fontWeight: '700', fontSize: 15, textAlign: 'center' },
  textoSecundario: { color: cores.texto },
  bloqueado: { opacity: 0.55 },
  pressionado: { opacity: 0.75 },
  mensagem: { backgroundColor: cores.verdeClaro, borderRadius: 12, padding: 14 },
  mensagemErro: { backgroundColor: cores.erroClaro },
  textoMensagem: { color: cores.verde, fontSize: 15, lineHeight: 22 },
  textoErro: { color: cores.erro },
  carregamento: { padding: 28, alignItems: 'center', gap: 12 },
});
