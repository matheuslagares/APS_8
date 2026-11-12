import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { API_URL, TEMPO_LIMITE_MS, verificarEnderecoApi } from '../config';

const CHAVE_SESSAO = 'alagamentos.token.v2';
let token = null;
const ouvintesExpiracao = new Set();

class ErroApi extends Error {
  constructor(mensagem, status) {
    super(mensagem);
    this.status = status;
  }
}

async function apagarSessaoLocal() {
  token = null;
  if (Platform.OS !== 'web') {
    try { await SecureStore.deleteItemAsync(CHAVE_SESSAO); } catch { /* Tenta novamente ao restaurar. */ }
  }
  ouvintesExpiracao.forEach((ouvinte) => ouvinte());
}

async function guardarToken(novoToken) {
  if (Platform.OS !== 'web') {
    try {
      await SecureStore.setItemAsync(CHAVE_SESSAO, novoToken);
    } catch {
      throw new Error('Não foi possível guardar a sessão no dispositivo. Tente entrar novamente.');
    }
  }
  token = novoToken;
}

export function aoExpirarSessao(ouvinte) {
  ouvintesExpiracao.add(ouvinte);
  return () => { ouvintesExpiracao.delete(ouvinte); };
}

async function requisitar(caminho, opcoes = {}, { publica = false, arquivo = false, tempo = TEMPO_LIMITE_MS } = {}) {
  verificarEnderecoApi();
  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), tempo);
  let resposta;
  try {
    const formulario = opcoes.body instanceof FormData;
    resposta = await fetch(`${API_URL}${caminho}`, {
      ...opcoes,
      headers: {
        Accept: arquivo ? '*/*' : 'application/json',
        ...(!publica && token ? { Authorization: `Bearer ${token}` } : {}),
        ...(opcoes.body && !formulario ? { 'Content-Type': 'application/json' } : {}),
      },
      signal: controlador.signal,
    });
    if (arquivo && resposta.ok) return await resposta.blob();
    let dados;
    try {
      dados = JSON.parse(await resposta.text());
    } catch (erro) {
      if (erro.name === 'AbortError') throw erro;
      throw new Error('A API retornou uma resposta inválida. Confira o endereço configurado.');
    }
    if (!resposta.ok) {
      if (resposta.status === 401 && !publica) await apagarSessaoLocal();
      throw new ErroApi(dados?.erro || `Não foi possível concluir o pedido (HTTP ${resposta.status}).`, resposta.status);
    }
    return dados;
  } catch (erro) {
    if (erro.name === 'AbortError') {
      throw new Error('A API demorou para responder. Confira a conexão e tente novamente.');
    }
    if (resposta) throw erro;
    throw new Error('Não foi possível acessar a API. Confira se o servidor está ligado, o IP e a rede Wi-Fi.');
  } finally {
    clearTimeout(temporizador);
  }
}

export async function registrarUsuario(dados) {
  const resposta = await requisitar('/auth/cadastro', { method: 'POST', body: JSON.stringify(dados) }, { publica: true });
  await guardarToken(resposta.token);
  return resposta.usuario;
}

export async function entrar(dados) {
  const resposta = await requisitar('/auth/login', { method: 'POST', body: JSON.stringify(dados) }, { publica: true });
  await guardarToken(resposta.token);
  return resposta.usuario;
}

export async function consultarPerfil() {
  return (await requisitar('/auth/me')).usuario;
}

export async function restaurarSessao() {
  if (Platform.OS !== 'web') token = await SecureStore.getItemAsync(CHAVE_SESSAO);
  if (!token) return null;
  try {
    return await consultarPerfil();
  } catch (erro) {
    if (erro.status === 401) return null;
    throw erro;
  }
}

export async function sair() {
  if (token) {
    try { await requisitar('/auth/logout', { method: 'POST' }); }
    catch (erro) { if (erro.status !== 401) throw erro; }
  }
  await apagarSessaoLocal();
}

export function listarOcorrencias() {
  return requisitar('/ocorrencias');
}

export function criarOcorrencia(dados, anexo = null) {
  if (!anexo) return requisitar('/ocorrencias', { method: 'POST', body: JSON.stringify(dados) });
  const formulario = new FormData();
  Object.entries(dados).forEach(([campo, valor]) => {
    if (valor !== null && valor !== undefined) formulario.append(campo, String(valor));
  });
  if (Platform.OS === 'web') {
    if (!anexo.file) throw new Error('Selecione o arquivo novamente antes de salvar.');
    formulario.append('arquivo', anexo.file, anexo.fileName || anexo.file.name);
  } else {
    formulario.append('arquivo', /** @type {any} */ ({
      uri: anexo.uri, name: anexo.fileName || 'anexo',
      type: anexo.mimeType || (anexo.type === 'video' ? 'video/mp4' : 'image/jpeg'),
    }));
  }
  return requisitar('/ocorrencias', { method: 'POST', body: formulario }, { tempo: 60000 });
}

export function buscarOcorrencia(id) {
  return requisitar(`/ocorrencias/${id}`);
}

export function alterarSituacao(id, situacao) {
  return requisitar(`/ocorrencias/${id}/situacao`, { method: 'PATCH', body: JSON.stringify({ situacao }) });
}

export async function carregarMidia(anexo) {
  if (!Number.isSafeInteger(anexo.id) || anexo.id <= 0) throw new Error('Anexo inválido.');
  const caminho = `/anexos/${anexo.id}`;
  if (Platform.OS !== 'web') {
    verificarEnderecoApi();
    return { uri: `${API_URL}${caminho}`, headers: { Authorization: `Bearer ${token}` }, liberar: () => {} };
  }
  const arquivo = await requisitar(caminho, {}, { arquivo: true, tempo: 60000 });
  const uri = URL.createObjectURL(arquivo);
  return { uri, headers: {}, liberar: () => { URL.revokeObjectURL(uri); } };
}
