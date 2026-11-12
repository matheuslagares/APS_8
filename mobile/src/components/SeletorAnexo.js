import { useEffect, useRef, useState } from 'react';
import { Image, Platform, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Botao, Mensagem } from './Interface';
import { estilos } from '../theme';

const LIMITE_BYTES = 20 * 1024 * 1024;
const TIPOS = ['image/jpeg', 'image/png', 'video/mp4'];

function prepararArquivo(asset) {
  const nomeInformado = asset.fileName || asset.file?.name || '';
  const caminho = (asset.uri || '').split('?')[0];
  const extensao = (caminho.match(/\.([a-z0-9]+)$/i)?.[1] || nomeInformado.match(/\.([a-z0-9]+)$/i)?.[1] || '').toLowerCase();
  const porExtensao = { jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', mp4: 'video/mp4' };
  const mimeType = (asset.mimeType || asset.file?.type || porExtensao[extensao] || '').toLowerCase();
  if (!TIPOS.includes(mimeType)) {
    throw new Error('Selecione uma foto JPEG ou PNG, ou um vídeo MP4. Outros formatos precisam ser convertidos antes do envio.');
  }
  const fileSize = asset.fileSize ?? asset.file?.size;
  if (fileSize > LIMITE_BYTES) throw new Error('O anexo deve ter no máximo 20 MiB. Escolha um arquivo menor.');
  const extensaoFinal = mimeType === 'video/mp4' ? 'mp4' : mimeType === 'image/png' ? 'png' : 'jpg';
  return { ...asset, mimeType, fileSize, fileName: nomeInformado || `anexo.${extensaoFinal}` };
}

export default function SeletorAnexo({ value, onChange, disabled = false }) {
  const [selecionando, setSelecionando] = useState(false);
  const [erro, setErro] = useState('');
  const emAndamento = useRef(false);
  const montada = useRef(true);
  const bloqueado = useRef(disabled);
  useEffect(() => { bloqueado.current = disabled; }, [disabled]);
  useEffect(() => {
    montada.current = true;
    return () => { montada.current = false; };
  }, []);

  async function selecionar() {
    if (emAndamento.current || disabled) return;
    emAndamento.current = true;
    setSelecionando(true);
    setErro('');
    try {
      if (Platform.OS === 'ios') {
        const permissao = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permissao.granted) throw new Error('Autorize o acesso às fotos para selecionar o anexo, ou continue sem arquivo.');
      }
      if (!montada.current || bloqueado.current) return;
      const resultado = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images', 'videos'], allowsMultipleSelection: false,
        allowsEditing: false, quality: 0.8, exif: false, base64: false,
      });
      if (!resultado.canceled && resultado.assets?.[0]) {
        const arquivo = prepararArquivo(resultado.assets[0]);
        if (montada.current && !bloqueado.current) onChange(arquivo);
      }
    } catch (falha) {
      if (montada.current) setErro(falha.message || 'Não foi possível selecionar o arquivo. Tente novamente.');
    } finally {
      emAndamento.current = false;
      if (montada.current) setSelecionando(false);
    }
  }

  return (
    <View style={{ gap: 10 }}>
      <Text style={estilos.rotulo}>Foto ou vídeo (opcional)</Text>
      <Text style={estilos.pequeno}>Um arquivo JPEG, PNG ou MP4 de até 20 MiB. O anexo ficará acessível aos participantes com login. Escolha somente conteúdo que você pode compartilhar.</Text>
      <Botao titulo={selecionando ? 'Selecionando arquivo…' : 'Anexar foto ou vídeo'} onPress={selecionar} secundario disabled={disabled || selecionando} />
      {value && (
        <>
          <Text accessibilityLiveRegion="polite" style={estilos.texto}>Arquivo selecionado: {value.fileName || 'anexo'}</Text>
          {value.mimeType?.startsWith('image/') && (
            <Image accessibilityLabel="Prévia da foto selecionada" source={{ uri: value.uri }} style={{ width: '100%', height: 160, borderRadius: 10 }} resizeMode="contain" />
          )}
          <Botao titulo="Remover anexo" onPress={() => { onChange(null); setErro(''); }} secundario disabled={disabled || selecionando} />
        </>
      )}
      <Mensagem texto={erro} erro />
    </View>
  );
}
