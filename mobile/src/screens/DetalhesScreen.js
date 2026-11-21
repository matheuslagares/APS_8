// tela de detalhes de uma ocorrencia - Guilherme
// revisar com Saad: a parte de marcar como resolvido
import { useEffect, useState } from 'react';
import { ScrollView, Text, View } from 'react-native';
import { alterarSituacao, buscarOcorrencia } from '../services/api';
import MapaOcorrencias from '../components/MapaOcorrencias';
import AnexoViewer from '../components/AnexoViewer';
import { AvisoRelatos, Botao, Cabecalho, Carregamento, Mensagem } from '../components/Interface';
import { estilos, rotuloGravidade, rotuloSituacao } from '../theme';

// mostra um titulo pequeno com o valor embaixo
function Campo({ titulo, valor }) {
  return (
    <View style={{ gap: 4 }}>
      <Text style={estilos.pequeno}>{titulo}</Text>
      <Text style={estilos.texto}>{valor}</Text>
    </View>
  );
}

export default function DetalhesScreen({ id, onVoltar }) {
  const [ocorrencia, setOcorrencia] = useState(null);
  const [erro, setErro] = useState('');
  const [mensagem, setMensagem] = useState('');
  const [atualizando, setAtualizando] = useState(false);

  // busca a ocorrencia qdo abre a tela
  useEffect(() => {
    buscarOcorrencia(id)
      .then((dados) => setOcorrencia(dados))
      .catch((falha) => setErro(falha.message));
  }, [id]);

  async function marcarResolvido() {
    setAtualizando(true);
    setErro('');
    try {
      const dados = await alterarSituacao(id, 'resolvido');
      setOcorrencia(dados);
      setMensagem('Situação atualizada para resolvido.');
    } catch (falha) {
      setErro(falha.message);
    }
    setAtualizando(false);
  }

  return (
    <ScrollView contentContainerStyle={estilos.rolagem}>
      <Cabecalho titulo="Detalhes" descricao={'Informações do relato #' + id + '.'} />
      <View style={estilos.conteudo}>
        <AvisoRelatos />
        <Mensagem texto={erro} erro />
        {!ocorrencia && !erro && <Carregamento texto="Carregando detalhes…" />}

        {ocorrencia && (
          <>
            <View style={estilos.cartao}>
              <Text style={estilos.titulo}>{ocorrencia.bairro}</Text>
              <Campo titulo="Endereço" valor={ocorrencia.endereco} />
              <Campo titulo="Descrição" valor={ocorrencia.descricao} />
              <Campo titulo="Gravidade relatada" valor={rotuloGravidade(ocorrencia.gravidade)} />
              <Campo titulo="Situação" valor={rotuloSituacao(ocorrencia.situacao)} />
              <Campo titulo="Data de cadastro" valor={new Date(ocorrencia.criado_em).toLocaleString('pt-BR')} />
            </View>

            {/* mapa pequeno so se tiver localizacao */}
            {ocorrencia.latitude != null && (
              <View style={estilos.grupo}>
                <Text style={estilos.rotulo}>Localização informada</Text>
                <MapaOcorrencias ocorrencias={[ocorrencia]} compacto />
              </View>
            )}

            {ocorrencia.anexos.map((anexo) => <AnexoViewer key={anexo.id} anexo={anexo} />)}

            <Mensagem texto={mensagem} />

            {/* so o autor consegue marcar como resolvido */}
            {ocorrencia.pode_alterar && ocorrencia.situacao === 'ativo' && (
              <Botao titulo="Marcar como resolvido" onPress={marcarResolvido} carregando={atualizando} />
            )}
            {!ocorrencia.pode_alterar && (
              <Text style={estilos.pequeno}>Somente o autor deste relato pode alterar a situação.</Text>
            )}
          </>
        )}

        <Botao titulo="Voltar" onPress={onVoltar} secundario disabled={atualizando} />
      </View>
    </ScrollView>
  );
}
