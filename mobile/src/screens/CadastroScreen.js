import { useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { criarOcorrencia } from '../services/api';
import LocalizacaoCampos from '../components/LocalizacaoCampos';
import SeletorAnexo from '../components/SeletorAnexo';
import { AvisoRelatos, Botao, Cabecalho, Mensagem } from '../components/Interface';
import { cores, estilos, gravidades } from '../theme';

export default function CadastroScreen({ onVoltar, onSalvo, onOcupadoChange }) {
  const [bairro, setBairro] = useState('');
  const [endereco, setEndereco] = useState('');
  const [descricao, setDescricao] = useState('');
  const [gravidade, setGravidade] = useState('media');
  const [localizacao, setLocalizacao] = useState(null);
  const [anexo, setAnexo] = useState(null);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');
  const envioEmAndamento = useRef(false);

  async function salvar() {
    if (envioEmAndamento.current) return;
    const dados = {
      bairro: bairro.trim(), endereco: endereco.trim(), descricao: descricao.trim(), gravidade,
      ...(localizacao || {}),
    };
    if (!dados.bairro || !dados.endereco || !dados.descricao) {
      setErro('Preencha bairro, endereço e descrição.');
      return;
    }

    envioEmAndamento.current = true;
    setSalvando(true);
    onOcupadoChange(true);
    setErro('');
    try {
      await criarOcorrencia(dados, anexo);
      onSalvo();
    } catch (falha) {
      setErro(falha.message);
    } finally {
      envioEmAndamento.current = false;
      setSalvando(false);
      onOcupadoChange(false);
    }
  }

  return (
    <KeyboardAvoidingView style={estilos.tela} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={locais.rolagem}>
        <Cabecalho titulo="Novo registro" descricao="Preencha os dados do relato. Localização e anexo são opcionais." />
        <View style={locais.conteudo}>
          <AvisoRelatos />
          <View style={locais.grupo}>
            <Text style={estilos.rotulo}>Bairro</Text>
            <TextInput
              accessibilityLabel="Bairro" placeholder="Ex.: Centro" placeholderTextColor={cores.secundario}
              value={bairro} onChangeText={setBairro} maxLength={100} editable={!salvando}
              style={estilos.campo} autoCapitalize="words" returnKeyType="next"
            />
            <Text style={estilos.pequeno}>{bairro.length}/100 caracteres</Text>
          </View>
          <View style={locais.grupo}>
            <Text style={estilos.rotulo}>Endereço</Text>
            <TextInput
              accessibilityLabel="Endereço" placeholder="Rua, referência e número aproximado"
              placeholderTextColor={cores.secundario} value={endereco} onChangeText={setEndereco}
              maxLength={200} editable={!salvando} style={estilos.campo} autoCapitalize="sentences"
            />
            <Text style={estilos.pequeno}>{endereco.length}/200 caracteres</Text>
          </View>
          <View style={locais.grupo}>
            <Text style={estilos.rotulo}>Descrição</Text>
            <TextInput
              accessibilityLabel="Descrição" placeholder="Conte como está a água e o acesso à via"
              placeholderTextColor={cores.secundario} value={descricao} onChangeText={setDescricao}
              maxLength={1000} editable={!salvando} multiline textAlignVertical="top"
              style={[estilos.campo, locais.descricao]} autoCapitalize="sentences"
            />
            <Text style={estilos.pequeno}>{descricao.length}/1.000 caracteres</Text>
          </View>
          <View style={locais.grupo}>
            <Text style={estilos.rotulo}>Gravidade relatada</Text>
            <View style={estilos.linha}>
              {gravidades.map((item) => (
                <Pressable
                  key={item.valor} accessibilityRole="radio" accessibilityLabel={item.rotulo}
                  accessibilityState={{ checked: gravidade === item.valor, disabled: salvando }}
                  disabled={salvando} onPress={() => setGravidade(item.valor)}
                  style={[locais.opcao, gravidade === item.valor && locais.selecionada]}
                >
                  <Text style={[locais.rotuloOpcao, gravidade === item.valor && locais.rotuloSelecionado]}>{item.rotulo}</Text>
                </Pressable>
              ))}
            </View>
          </View>
          <LocalizacaoCampos value={localizacao} onChange={setLocalizacao} disabled={salvando} />
          <SeletorAnexo value={anexo} onChange={setAnexo} disabled={salvando} />
          <Mensagem texto={erro} erro />
          <Botao titulo={salvando ? 'Salvando…' : 'Salvar'} onPress={salvar} carregando={salvando} />
          <Botao titulo="Voltar" onPress={onVoltar} secundario disabled={salvando} />
          <Text style={estilos.pequeno}>O cadastro fica salvo no servidor. Outros participantes podem consultá-lo ao atualizar a lista.</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const locais = StyleSheet.create({
  rolagem: { paddingBottom: 28 },
  conteudo: { paddingHorizontal: 22, gap: 20 },
  grupo: { gap: 8 },
  descricao: { minHeight: 130 },
  opcao: {
    minHeight: 48, paddingHorizontal: 22, paddingVertical: 13, borderRadius: 12,
    borderWidth: 1, borderColor: cores.borda, backgroundColor: cores.papel,
  },
  selecionada: { backgroundColor: cores.verde, borderColor: cores.verde },
  rotuloOpcao: { fontSize: 15, color: cores.texto, fontWeight: '600' },
  rotuloSelecionado: { color: '#FFFFFF' },
});
