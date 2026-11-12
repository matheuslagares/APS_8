import { Platform } from 'react-native';

const enderecoConfigurado = process.env.EXPO_PUBLIC_API_URL?.trim();
export const API_URL = (
  enderecoConfigurado || (Platform.OS === 'web' ? 'http://127.0.0.1:5000' : '')
).replace(/\/+$/, '');

export const TEMPO_LIMITE_MS = 10000;

export function verificarEnderecoApi() {
  if (!API_URL || API_URL.includes('IP-DO-COMPUTADOR')) {
    throw new Error(
      'Configure EXPO_PUBLIC_API_URL em mobile/.env com o IP do computador e reinicie o Expo.',
    );
  }
  try {
    const endereco = new URL(API_URL);
    if (!['http:', 'https:'].includes(endereco.protocol) || !endereco.hostname ||
        endereco.hostname === '0.0.0.0' || endereco.search || endereco.hash ||
        endereco.username || endereco.password) {
      throw new Error('Endereço inválido');
    }
  } catch {
    throw new Error('O endereço da API deve usar http:// ou https:// e o IP real do servidor, sem parâmetros ou credenciais.');
  }
}
