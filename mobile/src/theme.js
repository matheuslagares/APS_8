// cores e estilos usados em varias telas - Gustavo
// se for mudar alguma cor muda aqui q muda no app todo
import { StyleSheet } from 'react-native';

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

// opcoes de gravidade (valor vai pro banco, rotulo aparece na tela)
export const gravidades = [
  { valor: 'baixa', rotulo: 'Baixa' },
  { valor: 'media', rotulo: 'Média' },
  { valor: 'alta', rotulo: 'Alta' },
];

export function rotuloGravidade(valor) {
  if (valor === 'baixa') return 'Baixa';
  if (valor === 'media') return 'Média';
  if (valor === 'alta') return 'Alta';
  return valor;
}

export function rotuloSituacao(valor) {
  return valor === 'resolvido' ? 'Resolvido' : 'Ativo';
}

// cor do pino no mapa de acordo com a gravidade
export function corGravidade(valor) {
  if (valor === 'alta') return '#A73535';
  if (valor === 'media') return '#B2750B';
  return cores.verde;
}

export const estilos = StyleSheet.create({
  tela: { flex: 1 },
  rolagem: { paddingBottom: 28 },
  conteudo: { paddingHorizontal: 22, gap: 18 },
  grupo: { gap: 8 },
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
  // usado no link de cada ponto do mapa
  link: { borderRadius: 10, padding: 12, borderWidth: 1, borderColor: cores.borda, backgroundColor: cores.papel },
  textoLink: { fontSize: 14, color: cores.verde, fontWeight: '700' },
  midia: { width: '100%', height: 260, backgroundColor: cores.fundo, borderRadius: 10 },
});
