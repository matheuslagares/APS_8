// tela de nova ocorrencia - parte do Guilherme
// (localizacao e anexo sao componentes separados, feitos pelo Henrique)
import { useState } from 'react';
import { Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { criarOcorrencia } from '../services/api';
import LocalizacaoCampos from '../components/LocalizacaoCampos';
import SeletorAnexo from '../components/SeletorAnexo';
import { AvisoRelatos, Botao, Cabecalho, Mensagem } from '../components/Interface';
import { cores, estilos, gravidades } from '../theme';

export default function CadastroScreen({ onVoltar, onSalvo }) {
  // um state pra cada campo do formulario
  const [bairro, setBairro] = useState('');
  const [endereco, setEndereco] = useState('');
  const [descricao, setDescricao] = useState('');
  const [gravidade, setGravidade] = useState('media');
  const [localizacao, setLocalizacao] = useState(null);
  const [anexo, setAnexo] = useState(null);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  async function salvar() {
    if (!bairro.trim() || !endereco.trim() || !descricao.trim()) {
      setErro('Preencha bairro, endereço e descrição.');
      return;
    }

    const dados = {
      bairro: bairro.trim(),
      endereco: endereco.trim(),
      descricao: descricao.trim(),
      gravidade: gravidade,
    };
    // so manda latitude/longitude se o usuario pegou a localizacao
    if (localizacao) {
      dados.latitude = localizacao.latitude;
      dados.longitude = localizacao.longitude;
    }

    setSalvando(true);
    setErro('');
    try {
      await criarOcorrencia(dados, anexo);
      onSalvo(); // volta pra lista
    } catch (falha) {
      setErro(falha.message);
      setSalvando(false);
    }
  }

  return (
    <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={estilos.rolagem}>
      <Cabecalho titulo="Novo registro" descricao="Preencha os dados do relato. Localização e anexo são opcionais." />
      <View style={estilos.conteudo}>
        <AvisoRelatos />

        <View style={estilos.grupo}>
          <Text style={estilos.rotulo}>Bairro</Text>
          <TextInput
            placeholder="Ex.: Centro" placeholderTextColor={cores.secundario}
            value={bairro} onChangeText={setBairro} maxLength={100} style={estilos.campo}
          />
        </View>

        <View style={estilos.grupo}>
          <Text style={estilos.rotulo}>Endereço</Text>
          <TextInput
            placeholder="Rua, referência e número aproximado" placeholderTextColor={cores.secundario}
            value={endereco} onChangeText={setEndereco} maxLength={200} style={estilos.campo}
          />
        </View>

        <View style={estilos.grupo}>
          <Text style={estilos.rotulo}>Descrição</Text>
          <TextInput
            placeholder="Conte como está a água e o acesso à via" placeholderTextColor={cores.secundario}
            value={descricao} onChangeText={setDescricao} maxLength={1000} multiline
            textAlignVertical="top" style={[estilos.campo, { minHeight: 130 }]}
          />
          <Text style={estilos.pequeno}>{descricao.length}/1000 caracteres</Text>
        </View>

        {/* botoes de escolher a gravidade, o selecionado fica verde */}
        <View style={estilos.grupo}>
          <Text style={estilos.rotulo}>Gravidade relatada</Text>
          <View style={estilos.linha}>
            {gravidades.map((item) => {
              const selecionado = gravidade === item.valor;
              return (
                <Pressable
                  key={item.valor}
                  onPress={() => setGravidade(item.valor)}
                  style={[estilos.cartao, { paddingVertical: 12 }, selecionado && { backgroundColor: cores.verde }]}
                >
                  <Text style={[estilos.rotulo, selecionado && { color: '#FFFFFF' }]}>{item.rotulo}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        <LocalizacaoCampos value={localizacao} onChange={setLocalizacao} disabled={salvando} />
        <SeletorAnexo value={anexo} onChange={setAnexo} disabled={salvando} />

        <Mensagem texto={erro} erro />
        <Botao titulo={salvando ? 'Salvando…' : 'Salvar'} onPress={salvar} carregando={salvando} />
        <Botao titulo="Voltar" onPress={onVoltar} secundario disabled={salvando} />
      </View>
    </ScrollView>
  );
}
