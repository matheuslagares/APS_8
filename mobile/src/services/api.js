// api.js - todas as chamadas pro servidor ficam aqui
// parte do Saad (revisar com Matheus a parte do login)
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// endereco do servidor vem do arquivo .env (EXPO_PUBLIC_API_URL)
// no navegador se n tiver nada usa o localhost msm
let API_URL = process.env.EXPO_PUBLIC_API_URL || '';
if (!API_URL && Platform.OS === 'web') API_URL = 'http://127.0.0.1:5000';
API_URL = API_URL.trim().replace(/\/+$/, ''); // tira a barra do final

const CHAVE_TOKEN = 'alagamentos.token';
let token = null;

// funcao que o App.js registra pra saber qdo a sessao expirou
let avisarSessaoExpirada = null;
export function aoExpirarSessao(funcao) {
  avisarSessaoExpirada = funcao;
}

// guarda o token no celular (no navegador fica so na memoria)
async function salvarToken(novoToken) {
  token = novoToken;
  if (Platform.OS !== 'web') await SecureStore.setItemAsync(CHAVE_TOKEN, novoToken);
}

async function apagarToken() {
  token = null;
  if (Platform.OS !== 'web') await SecureStore.deleteItemAsync(CHAVE_TOKEN);
}

// funcao principal, todas as outras usam ela
async function requisitar(caminho, metodo = 'GET', corpo = null) {
  if (!API_URL || API_URL.includes('IP-DO-COMPUTADOR')) {
    throw new Error('Configure EXPO_PUBLIC_API_URL em mobile/.env com o IP do computador e reinicie o Expo.');
  }

  /** @type {Record<string, string>} */
  const headers = {};
  if (token) headers.Authorization = 'Bearer ' + token;

  // se for FormData (tem arquivo) o proprio fetch coloca o content-type
  let body = corpo;
  if (corpo && !(corpo instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(corpo);
  }

  let resposta;
  try {
    resposta = await fetch(API_URL + caminho, { method: metodo, headers, body });
  } catch {
    throw new Error('Não foi possível acessar a API. Confira se o servidor está ligado, o IP e a rede Wi-Fi.');
  }

  let dados = null;
  try {
    dados = await resposta.json();
  } catch {
    throw new Error('A API retornou uma resposta inválida. Confira o endereço configurado.');
  }

  if (!resposta.ok) {
    // 401 = token invalido/expirado, ai desloga o usuario
    // (menos no login, q ai e so senha errada)
    if (resposta.status === 401 && token && !caminho.startsWith('/auth/login')) {
      await apagarToken();
      if (avisarSessaoExpirada) avisarSessaoExpirada();
    }
    throw new Error(dados.erro || 'Erro HTTP ' + resposta.status);
  }
  return dados;
}

// ---------- usuario (Matheus) ----------

export async function registrarUsuario(dados) {
  const resposta = await requisitar('/auth/cadastro', 'POST', dados);
  await salvarToken(resposta.token);
  return resposta.usuario;
}

export async function entrar(dados) {
  const resposta = await requisitar('/auth/login', 'POST', dados);
  await salvarToken(resposta.token);
  return resposta.usuario;
}

// qdo abre o app tenta usar o token q ja tava salvo
export async function restaurarSessao() {
  if (Platform.OS !== 'web') token = await SecureStore.getItemAsync(CHAVE_TOKEN);
  if (!token) return null;
  try {
    const resposta = await requisitar('/auth/me');
    return resposta.usuario;
  } catch {
    return null; // token velho, pede login d novo
  }
}

export async function sair() {
  try {
    await requisitar('/auth/logout', 'POST');
  } catch {
    // se der erro tanto faz, apaga o token local mesmo assim
  }
  await apagarToken();
}

// ---------- ocorrencias (Guilherme) ----------

export function listarOcorrencias() {
  return requisitar('/ocorrencias');
}

export function buscarOcorrencia(id) {
  return requisitar('/ocorrencias/' + id);
}

export function alterarSituacao(id, situacao) {
  return requisitar('/ocorrencias/' + id + '/situacao', 'PATCH', { situacao });
}

export function criarOcorrencia(dados, anexo) {
  // sem anexo manda JSON normal
  if (!anexo) return requisitar('/ocorrencias', 'POST', dados);

  // com anexo tem q mandar como formulario (multipart)
  const formulario = new FormData();
  for (const campo in dados) {
    if (dados[campo] != null) formulario.append(campo, String(dados[campo]));
  }
  if (Platform.OS === 'web') {
    formulario.append('arquivo', anexo.file, anexo.fileName);
  } else {
    // no celular o react native aceita esse objeto com uri
    formulario.append('arquivo', /** @type {any} */ ({ uri: anexo.uri, name: anexo.fileName, type: anexo.mimeType }));
  }
  return requisitar('/ocorrencias', 'POST', formulario);
}

// ---------- anexos (Henrique) ----------

// retorna o endereco do arquivo pra mostrar a foto/video
export async function carregarMidia(anexo) {
  const url = API_URL + '/anexos/' + anexo.id;

  // no celular da pra mandar o header de login junto com a imagem
  if (Platform.OS !== 'web') {
    return { uri: url, headers: { Authorization: 'Bearer ' + token } };
  }

  // no navegador nao da, entao baixa o arquivo e cria um link local
  const resposta = await fetch(url, { headers: { Authorization: 'Bearer ' + token } });
  if (!resposta.ok) throw new Error('Não foi possível abrir o anexo.');
  const arquivo = await resposta.blob();
  return { uri: URL.createObjectURL(arquivo), headers: {} };
}
