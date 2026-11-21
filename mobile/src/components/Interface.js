// componentes pequenos q se repetem em todas as telas - Gustavo
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { cores, estilos } from '../theme';

// titulo grande do topo da tela
export function Cabecalho({ titulo, descricao }) {
  return (
    <View style={estilos.cabecalho}>
      <Text style={estilos.marca}>ALERTA DE ALAGAMENTOS</Text>
      <Text accessibilityRole="header" style={estilos.titulo}>{titulo}</Text>
      <Text style={estilos.subtitulo}>{descricao}</Text>
    </View>
  );
}

// botao padrao. secundario = botao branco
export function Botao({ titulo, onPress, secundario = false, disabled = false, carregando = false }) {
  const bloqueado = disabled || carregando;
  return (
    <Pressable
      accessibilityRole="button"
      disabled={bloqueado}
      onPress={onPress}
      style={[locais.botao, secundario && locais.botaoSecundario, bloqueado && locais.bloqueado]}
    >
      {carregando && <ActivityIndicator size="small" color={secundario ? cores.texto : '#FFFFFF'} />}
      <Text style={[locais.textoBotao, secundario && { color: cores.texto }]}>{titulo}</Text>
    </Pressable>
  );
}

// caixinha de aviso (verde) ou erro (vermelha). se o texto for vazio n mostra nd
export function Mensagem({ texto, erro = false }) {
  if (!texto) return null;
  return (
    <View style={[locais.mensagem, erro && { backgroundColor: cores.erroClaro }]}>
      <Text style={[locais.textoMensagem, erro && { color: cores.erro }]}>{texto}</Text>
    </View>
  );
}

// rodinha girando
export function Carregamento({ texto = 'Carregando relatos…' }) {
  return (
    <View style={locais.carregamento}>
      <ActivityIndicator size="large" color={cores.verde} />
      <Text style={estilos.subtitulo}>{texto}</Text>
    </View>
  );
}

// aviso q aparece em varias telas (pedido do professor)
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
  bloqueado: { opacity: 0.55 },
  mensagem: { backgroundColor: cores.verdeClaro, borderRadius: 12, padding: 14 },
  textoMensagem: { color: cores.verde, fontSize: 15, lineHeight: 22 },
  carregamento: { padding: 28, alignItems: 'center', gap: 12 },
});
