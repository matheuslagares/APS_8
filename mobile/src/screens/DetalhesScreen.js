import { useCallback, useEffect, useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { alterarSituacao, buscarOcorrencia } from '../services/api';
import MapaOcorrencias from '../components/MapaOcorrencias';
import AnexoViewer from '../components/AnexoViewer';
import { AvisoRelatos, Botao, Cabecalho, Carregamento, Mensagem } from '../components/Interface';
import { cores, estilos, rotuloGravidade, rotuloSituacao } from '../theme';

function Campo({ titulo, valor }) {
  return (
    <View style={locais.campo}>
      <Text style={estilos.pequeno}>{titulo}</Text>
      <Text selectable style={estilos.texto}>{valor}</Text>
    </View>
  );
}

function formatarData(valor) {
  const data = new Date(valor);
  return Number.isNaN(data.getTime()) ? valor : data.toLocaleString('pt-BR');
}

export default function DetalhesScreen({ id, onVoltar, onOcupadoChange }) {
  const [ocorrencia, setOcorrencia] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [atualizando, setAtualizando] = useState(false);
  const [erro, setErro] = useState('');
  const [mensagem, setMensagem] = useState('');
  const montada = useRef(false);
  const envioEmAndamento = useRef(false);

  const carregar = useCallback(async () => {
    try {
      const dados = await buscarOcorrencia(id);
      if (montada.current) setOcorrencia(dados);
    } catch (falha) {
      if (montada.current) setErro(falha.message);
    } finally {
      if (montada.current) setCarregando(false);
    }
  }, [id]);

  function tentarNovamente() {
    setCarregando(true);
    setErro('');
    carregar();
  }

  useEffect(() => {
    montada.current = true;
    buscarOcorrencia(id)
      .then((dados) => { if (montada.current) setOcorrencia(dados); })
      .catch((falha) => { if (montada.current) setErro(falha.message); })
      .finally(() => { if (montada.current) setCarregando(false); });
    return () => { montada.current = false; };
  }, [id]);

  async function resolver() {
    if (envioEmAndamento.current || ocorrencia?.pode_alterar !== true) return;
    envioEmAndamento.current = true;
    setAtualizando(true);
    onOcupadoChange(true);
    setErro('');
    setMensagem('');
    try {
      // Só mostramos a nova situação depois de a API confirmar a gravação no banco.
      const dados = await alterarSituacao(id, 'resolvido');
      setOcorrencia(dados);
      setMensagem('Situação atualizada para resolvido.');
    } catch (falha) {
      setErro(falha.message);
    } finally {
      envioEmAndamento.current = false;
      setAtualizando(false);
      onOcupadoChange(false);
    }
  }

  return (
    <ScrollView style={estilos.tela} contentContainerStyle={locais.rolagem}>
      <Cabecalho titulo="Detalhes" descricao={`Informações do relato #${id}.`} />
      <View style={locais.conteudo}>
        <AvisoRelatos />
        {carregando && <Carregamento texto="Carregando detalhes…" />}
        <Mensagem texto={erro} erro />
        {!carregando && !ocorrencia && erro ? (
          <Botao titulo="Tentar novamente" onPress={tentarNovamente} secundario />
        ) : null}
        {!carregando && ocorrencia && (
          <>
            <View style={estilos.cartao}>
              <Text accessibilityRole="header" style={locais.bairro}>{ocorrencia.bairro}</Text>
              <Campo titulo="Identificador" valor={String(ocorrencia.id)} />
              <Campo titulo="Endereço" valor={ocorrencia.endereco} />
              <Campo titulo="Descrição" valor={ocorrencia.descricao} />
              <Campo titulo="Gravidade relatada" valor={rotuloGravidade(ocorrencia.gravidade)} />
              <Campo titulo="Situação" valor={rotuloSituacao(ocorrencia.situacao)} />
              <Campo titulo="Data de cadastro (horário local)" valor={formatarData(ocorrencia.criado_em)} />
            </View>
            {ocorrencia.latitude != null && ocorrencia.longitude != null && (
              <View style={locais.campo}>
                <Text style={estilos.rotulo}>Localização informada</Text>
                <MapaOcorrencias ocorrencias={[ocorrencia]} onAbrirDetalhes={() => {}} compacto />
              </View>
            )}
            {ocorrencia.anexos?.map((anexo) => <AnexoViewer key={anexo.id} anexo={anexo} />)}
            <Mensagem texto={mensagem} />
            {ocorrencia.pode_alterar === true && ocorrencia.situacao === 'ativo' && (
              <Botao
                titulo={atualizando ? 'Atualizando…' : 'Marcar como resolvido'}
                onPress={resolver} carregando={atualizando}
              />
            )}
            <Text style={estilos.pequeno}>
              {ocorrencia.autor_id == null
                ? 'Este relato foi criado antes do login e está disponível apenas para consulta.'
                : ocorrencia.pode_alterar
                  ? 'Você é o autor deste relato. Somente você pode alterar a situação.'
                  : 'Somente o autor deste relato pode alterar a situação. Você pode consultar suas informações.'}
            </Text>
          </>
        )}
        <Botao titulo="Voltar" onPress={onVoltar} secundario disabled={atualizando} />
      </View>
    </ScrollView>
  );
}

const locais = StyleSheet.create({
  rolagem: { paddingBottom: 28 },
  conteudo: { paddingHorizontal: 22, gap: 18 },
  campo: { gap: 4 },
  bairro: { color: cores.texto, fontWeight: '800', fontSize: 24, lineHeight: 30 },
});
