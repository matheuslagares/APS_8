// escolher foto ou video da galeria - Henrique
// obs: o servidor tb confere o tipo do arquivo, aqui e so pra avisar antes
import { useState } from 'react';
import { Image, Text, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Botao, Mensagem } from './Interface';
import { estilos } from '../theme';

const LIMITE = 20 * 1024 * 1024; // 20 MB

export default function SeletorAnexo({ value, onChange, disabled = false }) {
  const [erro, setErro] = useState('');

  async function selecionar() {
    setErro('');
    // abre a galeria do celular
    const resultado = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images', 'videos'],
      quality: 0.8,
    });
    if (resultado.canceled) return; // usuario desistiu

    const arquivo = resultado.assets[0];
    // descobre o tipo, se o picker nao informar chuta pelo tipo do asset
    let tipo = arquivo.mimeType || arquivo.file?.type || '';
    if (!tipo) tipo = arquivo.type === 'video' ? 'video/mp4' : 'image/jpeg';

    if (!['image/jpeg', 'image/png', 'video/mp4'].includes(tipo)) {
      setErro('Selecione uma foto JPEG ou PNG, ou um vídeo MP4.');
      return;
    }
    if (arquivo.fileSize > LIMITE) {
      setErro('O anexo deve ter no máximo 20 MiB. Escolha um arquivo menor.');
      return;
    }

    const nome = arquivo.fileName || arquivo.file?.name || 'anexo';
    onChange({ ...arquivo, mimeType: tipo, fileName: nome });
  }

  return (
    <View style={{ gap: 10 }}>
      <Text style={estilos.rotulo}>Foto ou vídeo (opcional)</Text>
      <Text style={estilos.pequeno}>Um arquivo JPEG, PNG ou MP4 de até 20 MiB. O anexo ficará acessível aos participantes com login.</Text>
      <Botao titulo="Anexar foto ou vídeo" onPress={selecionar} secundario disabled={disabled} />
      {value && (
        <>
          <Text style={estilos.texto}>Arquivo selecionado: {value.fileName}</Text>
          {/* previa so se for imagem */}
          {value.mimeType.startsWith('image/') && (
            <Image source={{ uri: value.uri }} style={{ width: '100%', height: 160, borderRadius: 10 }} resizeMode="contain" />
          )}
          <Botao titulo="Remover anexo" onPress={() => onChange(null)} secundario disabled={disabled} />
        </>
      )}
      <Mensagem texto={erro} erro />
    </View>
  );
}
