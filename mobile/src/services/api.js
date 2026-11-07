import { API_URL, TEMPO_LIMITE_MS, verificarEnderecoApi } from '../config';

// Toda leitura e alteração passa pela API. O aplicativo não abre o arquivo SQLite.
async function requisitar(caminho, opcoes = {}) {
  verificarEnderecoApi();
  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), TEMPO_LIMITE_MS);
  let resposta;
  let dados;

  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      ...opcoes,
      headers: {
        Accept: 'application/json',
        ...(opcoes.body ? { 'Content-Type': 'application/json' } : {}),
      },
      signal: controlador.signal,
    });
    // O limite de tempo cobre também a leitura do corpo, não apenas os cabeçalhos.
    const corpo = await resposta.text();
    try {
      dados = JSON.parse(corpo);
    } catch {
      throw new Error('A API retornou uma resposta inválida. Confira o endereço configurado.');
    }
  } catch (erro) {
    if (erro.name === 'AbortError') {
      throw new Error('A API demorou para responder. Confira a conexão e tente novamente.');
    }
    if (resposta) throw erro;
    throw new Error(
      'Não foi possível acessar a API. Confira se o servidor está ligado, o IP e a rede Wi-Fi.',
    );
  } finally {
    // Evita manter temporizadores depois do sucesso ou de uma falha.
    clearTimeout(temporizador);
  }

  // fetch NÃO rejeita automaticamente respostas 400, 404 ou 500.
  if (!resposta.ok) {
    throw new Error(dados?.erro || `Não foi possível concluir o pedido (HTTP ${resposta.status}).`);
  }
  return dados;
}

export function listarOcorrencias() {
  return requisitar('/ocorrencias');
}

export function criarOcorrencia(dados) {
  return requisitar('/ocorrencias', { method: 'POST', body: JSON.stringify(dados) });
}

export function buscarOcorrencia(id) {
  return requisitar(`/ocorrencias/${id}`);
}

export function alterarSituacao(id, situacao) {
  return requisitar(`/ocorrencias/${id}/situacao`, {
    method: 'PATCH',
    body: JSON.stringify({ situacao }),
  });
}
