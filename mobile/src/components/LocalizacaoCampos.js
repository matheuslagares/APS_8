import { useEffect, useRef, useState } from 'react';
import { Text, View } from 'react-native';
import * as Location from 'expo-location';
import { Botao, Mensagem } from './Interface';
import { estilos } from '../theme';

export default function LocalizacaoCampos({ value, onChange, disabled = false }) {
  const [buscando, setBuscando] = useState(false);
  const [erro, setErro] = useState('');
  const emAndamento = useRef(false);
  const montada = useRef(true);
  const bloqueado = useRef(disabled);
  useEffect(() => { bloqueado.current = disabled; }, [disabled]);

  useEffect(() => {
    montada.current = true;
    return () => { montada.current = false; };
  }, []);

  async function usarLocalizacao() {
    if (emAndamento.current || disabled) return;
    emAndamento.current = true;
    setBuscando(true);
    setErro('');
    let temporizador;
    try {
      // A permissão só é solicitada após o toque. Não há rastreamento em segundo plano.
      const permissao = await Location.requestForegroundPermissionsAsync();
      if (!permissao.granted) {
        throw new Error('Localização não autorizada. Você pode continuar sem GPS e informar o endereço.');
      }
      if (!montada.current || bloqueado.current) return;
      /** @type {Promise<never>} */
      const prazo = new Promise((_, rejeitar) => {
        temporizador = setTimeout(() => rejeitar(new Error('O GPS demorou para responder. Tente novamente ou continue sem localização.')), 15000);
      });
      const local = await Promise.race([
        Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }), prazo,
      ]);
      const { latitude, longitude } = local.coords;
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        throw new Error('O dispositivo não informou uma localização válida.');
      }
      // Uma resposta atrasada não pode alterar um formulário que já foi enviado.
      if (montada.current && !bloqueado.current) onChange({ latitude, longitude });
    } catch (falha) {
      if (montada.current) {
        setErro(falha.message || 'Não foi possível obter a localização. Confira a permissão e o GPS do aparelho.');
      }
    } finally {
      clearTimeout(temporizador);
      emAndamento.current = false;
      if (montada.current) setBuscando(false);
    }
  }

  const possuiCoordenadas = Number.isFinite(value?.latitude) && Number.isFinite(value?.longitude);
  return (
    <View style={{ gap: 10 }}>
      <Text style={estilos.rotulo}>Localização no mapa (opcional)</Text>
      <Text style={estilos.pequeno}>Use o GPS somente se você estiver no local do relato. A coordenada salva poderá ser vista pelos participantes com login.</Text>
      <Botao
        titulo={buscando ? 'Buscando localização…' : 'Usar minha localização'}
        onPress={usarLocalizacao} secundario carregando={buscando} disabled={disabled}
      />
      {possuiCoordenadas && (
        <>
          <Text accessibilityLiveRegion="polite" style={estilos.texto}>
            Latitude: {value.latitude.toFixed(6)} · Longitude: {value.longitude.toFixed(6)}
          </Text>
          <Botao titulo="Remover localização" onPress={() => onChange(null)} secundario disabled={disabled || buscando} />
        </>
      )}
      <Mensagem texto={erro} erro />
    </View>
  );
}
