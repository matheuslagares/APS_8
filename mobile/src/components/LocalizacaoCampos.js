// botao de pegar a localizacao do GPS - parte do Henrique
import { useState } from 'react';
import { Text, View } from 'react-native';
import * as Location from 'expo-location';
import { Botao, Mensagem } from './Interface';
import { estilos } from '../theme';

export default function LocalizacaoCampos({ value, onChange, disabled = false }) {
  const [buscando, setBuscando] = useState(false);
  const [erro, setErro] = useState('');

  async function usarLocalizacao() {
    setBuscando(true);
    setErro('');
    try {
      // primeiro pede permissao pro usuario
      const permissao = await Location.requestForegroundPermissionsAsync();
      if (!permissao.granted) {
        setErro('Localização não autorizada. Você pode continuar sem GPS e informar o endereço.');
        return;
      }
      const local = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      onChange({ latitude: local.coords.latitude, longitude: local.coords.longitude });
    } catch {
      setErro('Não foi possível obter a localização. Confira a permissão e o GPS do aparelho.');
    } finally {
      // finally roda sempre, dando certo ou errado
      setBuscando(false);
    }
  }

  return (
    <View style={{ gap: 10 }}>
      <Text style={estilos.rotulo}>Localização no mapa (opcional)</Text>
      <Text style={estilos.pequeno}>Use o GPS somente se você estiver no local do relato. A coordenada salva poderá ser vista pelos participantes com login.</Text>
      <Botao
        titulo={buscando ? 'Buscando localização…' : 'Usar minha localização'}
        onPress={usarLocalizacao} secundario carregando={buscando} disabled={disabled}
      />
      {/* so mostra as coordenadas se ja pegou */}
      {value && (
        <>
          <Text style={estilos.texto}>
            Latitude: {value.latitude.toFixed(6)} · Longitude: {value.longitude.toFixed(6)}
          </Text>
          <Botao titulo="Remover localização" onPress={() => onChange(null)} secundario disabled={disabled} />
        </>
      )}
      <Mensagem texto={erro} erro />
    </View>
  );
}
