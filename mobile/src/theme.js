import { StyleSheet } from 'react-native';

// Cores e espaçamentos compartilhados mantêm as três telas consistentes.
export const cores = {
  fundo: '#F1F6F7',
  papel: '#FFFFFF',
  texto: '#163344',
  secundario: '#4D6571',
  borda: '#CBDADF',
  verde: '#166C51',
  verdeClaro: '#E5F3EC',
  erro: '#9D2B30',
  erroClaro: '#FFF0F0',
};

export const gravidades = [
  { valor: 'baixa', rotulo: 'Baixa' },
  { valor: 'media', rotulo: 'Média' },
  { valor: 'alta', rotulo: 'Alta' },
];

export function rotuloGravidade(valor) {
  return gravidades.find((item) => item.valor === valor)?.rotulo || valor;
}

export function rotuloSituacao(valor) {
  return valor === 'resolvido' ? 'Resolvido' : 'Ativo';
}

export const estilos = StyleSheet.create({
  tela: { flex: 1 },
  cabecalho: { paddingHorizontal: 22, paddingTop: 26, paddingBottom: 20, gap: 8 },
  marca: { fontSize: 12, fontWeight: '800', letterSpacing: 1.4, color: cores.verde },
  titulo: { fontSize: 30, lineHeight: 36, fontWeight: '800', color: cores.texto },
  subtitulo: { color: cores.secundario, fontSize: 15, lineHeight: 22 },
  linha: { flexDirection: 'row', gap: 10, flexWrap: 'wrap', alignItems: 'center' },
  cartao: {
    backgroundColor: cores.papel, borderRadius: 16,
    borderWidth: 1, borderColor: cores.borda, padding: 18, gap: 12,
  },
  texto: { fontSize: 16, color: cores.texto, lineHeight: 24 },
  rotulo: { fontSize: 15, fontWeight: '700', color: cores.texto },
  pequeno: { fontSize: 13, color: cores.secundario, lineHeight: 19 },
  campo: {
    backgroundColor: cores.papel, borderWidth: 1, borderColor: cores.borda,
    borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12,
    fontSize: 16, color: cores.texto, minHeight: 48,
  },
});
