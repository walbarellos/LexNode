"""
base_crawler.py — ProcessoLivreAC

Responsabilidade única: gerenciar sessão HTTP, rate-limiting e retry
para consultas ao e-SAJ do TJAC. Não faz parsing de conteúdo — isso é
responsabilidade do normalizer.py (Método Caracol: um arquivo, uma
responsabilidade).

Constraints de projeto (ver Ciclo 00, seção 3):
- Rate limit humano: sem paralelismo agressivo contra sistema do Judiciário.
- Sem bypass automatizado de captcha neste ciclo.
- User-Agent identificado, sem disfarce de navegador.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger("processolivre.base_crawler")

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

ESAJ_BASE_URL = "https://esaj.tjac.jus.br"
ESAJ_CPOPG_SEARCH_PATH = "/cpopg/search.do"  # action real do form (confirmado)
ESAJ_CPOSG5_SEARCH_PATH = "/cposg5/search.do"  # 2º Grau (Tribunal)

# Intervalo mínimo entre requisições, em segundos.
# Deliberadamente conservador — este é um sistema do Judiciário estadual,
# não uma API comercial. Ajustar com cautela.
MIN_REQUEST_INTERVAL_SECONDS = 3.0

# Retry
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5.0

# Identificação honesta. Nada de spoofing de navegador — se o TJAC quiser
# bloquear ou entrar em contato, deve conseguir identificar a origem.
USER_AGENT = (
    "ProcessoLivreAC/0.1 "
    "(projeto civico sem fins lucrativos; contato: <preencher-email>)"
)


class SigiloDetectadoError(Exception):
    """Levantada quando a resposta indica processo sob segredo de justiça.

    Isto NÃO é tratado como erro de rede — é um sinal de negócio que o
    normalizer.py deve capturar explicitamente e nunca ignorar
    silenciosamente (fail-closed).
    """


class ProcessoNaoEncontradoError(Exception):
    """Levantada quando o e-SAJ retorna 'Não existem informações
    disponíveis para os parâmetros informados' — o processo não
    existe ou o número está errado. Não é erro de rede."""


class ConsultaFalhouError(Exception):
    """Erro genérico de consulta após esgotar retries."""


@dataclass
class RespostaConsulta:
    numero_processo: str
    status_code: int
    html: str
    url_consultada: str


class BaseCrawler:
    """
    Encapsula uma sessão HTTP com rate-limiting e retry para consultas
    ao e-SAJ. Uso:

        crawler = BaseCrawler()
        resposta = crawler.consultar_processo_1grau("0000000-00.0000.0.00.0000")
    """

    def __init__(
        self,
        base_url: str = ESAJ_BASE_URL,
        min_interval: float = MIN_REQUEST_INTERVAL_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.base_url = base_url
        self.min_interval = min_interval
        self.max_retries = max_retries
        self._last_request_ts: Optional[float] = None
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})
        self._sessao_iniciada = False
        self._sessao_2grau_iniciada = False

    # -- rate limiting --------------------------------------------------

    def iniciar_sessao(self, grau: int = 1) -> None:
        """Faz uma requisição inicial para obter cookies de sessão e evitar captcha direto."""
        if grau == 1:
            if self._sessao_iniciada:
                return
            url = f"{self.base_url}/cpopg/open.do"
        else:
            if self._sessao_2grau_iniciada:
                return
            url = f"{self.base_url}/cposg5/open.do"
            
        self._respeitar_intervalo()
        try:
            self._session.get(url, timeout=15)
            self._last_request_ts = time.monotonic()
            if grau == 1:
                self._sessao_iniciada = True
            else:
                self._sessao_2grau_iniciada = True
        except requests.RequestException as exc:
            logger.warning("Erro ao inicializar sessão (open.do): %s", exc)

    def _respeitar_intervalo(self) -> None:
        if self._last_request_ts is None:
            return
        elapsed = time.monotonic() - self._last_request_ts
        remaining = self.min_interval - elapsed
        if remaining > 0:
            logger.debug("Rate limit: aguardando %.2fs", remaining)
            time.sleep(remaining)

    # -- consulta principal ----------------------------------------------

    def consultar_processo_1grau(self, numero_processo: str) -> RespostaConsulta:
        """
        Consulta um processo por número no e-SAJ, 1º grau (cpopg).

        Parâmetros de formulário CONFIRMADOS manualmente em 2026-07-27
        contra esaj.tjac.jus.br/cpopg/open.do (form#formConsulta).

        NOTA: o e-SAJ pode responder com um captcha em vez do conteúdo
        esperado. Este método NÃO tenta resolver o captcha — apenas
        detecta essa condição e levanta ConsultaFalhouError, deixando a
        decisão (resolução manual, retry mais tarde, etc.) para a camada
        chamadora. Ver Ciclo 00, restrição 3.
        """
        digito_ano, foro = self._formatar_numero_cnj(numero_processo)

        # Campos confirmados via inspeção do formulário real:
        # form#formConsulta → action=/cpopg/search.do method=GET
        params = {
            "conversationId": "",
            "cbPesquisa": "NUMPROC",
            "dadosConsulta.tipoNuProcesso": "UNIFICADO",
            "numeroDigitoAnoUnificado": digito_ano,
            "foroNumeroUnificado": foro,
            "dadosConsulta.valorConsultaNuUnificado": numero_processo,
            "dadosConsulta.valorConsulta": "",
        }

        url = f"{self.base_url}{ESAJ_CPOPG_SEARCH_PATH}"
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            self.iniciar_sessao()
            self._respeitar_intervalo()
            try:
                resp = self._session.get(url, params=params, timeout=15)
                self._last_request_ts = time.monotonic()

                if resp.status_code != 200:
                    raise ConsultaFalhouError(
                        f"HTTP {resp.status_code} ao consultar {numero_processo}"
                    )

                if self._parece_captcha(resp.text):
                    raise ConsultaFalhouError(
                        f"Captcha detectado ao consultar {numero_processo}; "
                        "resolução automática não implementada neste ciclo."
                    )

                if self._processo_nao_encontrado(resp.text):
                    raise ProcessoNaoEncontradoError(
                        f"Processo {numero_processo} não encontrado no e-SAJ."
                    )

                return RespostaConsulta(
                    numero_processo=numero_processo,
                    status_code=resp.status_code,
                    html=resp.text,
                    url_consultada=resp.url,
                )

            except ProcessoNaoEncontradoError:
                raise  # Não faz retry — o processo não existe

            except (requests.RequestException, ConsultaFalhouError) as exc:
                last_error = exc
                logger.warning(
                    "Tentativa %d/%d falhou para %s: %s",
                    attempt,
                    self.max_retries,
                    numero_processo,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        raise ConsultaFalhouError(
            f"Falha ao consultar {numero_processo} após {self.max_retries} tentativas"
        ) from last_error

    def consultar_processo_2grau(self, numero_processo: str) -> RespostaConsulta:
        """
        Consulta um processo por número no e-SAJ, 2º grau (cposg5).
        
        NOTA: o e-SAJ pode responder com um captcha em vez do conteúdo
        esperado. Este método NÃO tenta resolver o captcha — apenas
        detecta essa condição e levanta ConsultaFalhouError, deixando a
        decisão (resolução manual, retry mais tarde, etc.) para a camada
        chamadora. Ver Ciclo 00, restrição 3.
        """
        digito_ano, foro = self._formatar_numero_cnj(numero_processo)

        params = {
            "conversationId": "",
            "paginaConsulta": "0",
            "cbPesquisa": "NUMPROC",
            "tipoNuProcesso": "UNIFICADO",
            "numeroDigitoAnoUnificado": digito_ano,
            "foroNumeroUnificado": foro,
            "dePesquisaNuUnificado": numero_processo,
            "dePesquisa": "",
        }

        url = f"{self.base_url}{ESAJ_CPOSG5_SEARCH_PATH}"
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            self.iniciar_sessao(grau=2)
            self._respeitar_intervalo()
            try:
                resp = self._session.get(url, params=params, timeout=15)
                self._last_request_ts = time.monotonic()

                if resp.status_code != 200:
                    raise ConsultaFalhouError(
                        f"HTTP {resp.status_code} ao consultar {numero_processo}"
                    )

                if self._parece_captcha(resp.text):
                    raise ConsultaFalhouError(
                        f"Captcha detectado ao consultar {numero_processo}; "
                        "resolução automática não implementada neste ciclo."
                    )

                if self._processo_nao_encontrado(resp.text):
                    raise ProcessoNaoEncontradoError(
                        f"Processo {numero_processo} não encontrado no e-SAJ."
                    )

                return RespostaConsulta(
                    numero_processo=numero_processo,
                    status_code=resp.status_code,
                    html=resp.text,
                    url_consultada=resp.url,
                )

            except ProcessoNaoEncontradoError:
                raise  # Não faz retry — o processo não existe

            except (requests.RequestException, ConsultaFalhouError) as exc:
                last_error = exc
                logger.warning(
                    "Tentativa %d/%d falhou para %s: %s",
                    attempt,
                    self.max_retries,
                    numero_processo,
                    exc,
                )
                if attempt < self.max_retries:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        raise ConsultaFalhouError(
            f"Falha ao consultar {numero_processo} após {self.max_retries} tentativas"
        ) from last_error

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _formatar_numero_cnj(numero_processo: str) -> tuple[str, str]:
        """
        Converte número CNJ no formato esperado pelo formulário do e-SAJ.

        Entrada: "0700616-57.2024.8.01.0001" (formato CNJ completo)
        Saída:   ("0700616-57.2024", "0001")
                  ↑ numeroDigitoAnoUnificado   ↑ foroNumeroUnificado

        O formulário espera o número dividido em duas partes:
        - numeroDigitoAnoUnificado = NNNNNNN-DD.AAAA (7 dígitos, dígito
          verificador, ano)
        - foroNumeroUnificado = OOOO (4 últimos dígitos, comarca/foro)
        """
        digitos = "".join(ch for ch in numero_processo if ch.isdigit())
        if len(digitos) < 20:
            raise ValueError(
                f"Número de processo inválido (esperado 20 dígitos, "
                f"encontrado {len(digitos)}): {numero_processo}"
            )
        # NNNNNNN-DD.AAAA
        digito_ano = f"{digitos[:7]}-{digitos[7:9]}.{digitos[9:13]}"
        # OOOO (foro/comarca — últimos 4 dígitos)
        foro = digitos[16:20]
        return digito_ano, foro

    @staticmethod
    def _parece_captcha(html: str) -> bool:
        """
        Heurística refinada para detectar página de captcha em vez de
        conteúdo real. Evita falsos positivos com scripts de background.
        """
        html_lower = html.lower()
        # Procura por elementos estruturais típicos de um desafio ativo
        return (
            'class="g-recaptcha"' in html_lower or
            'id="rc-imageselect"' in html_lower or
            '/sysgen/captcha.do' in html_lower or
            'vc-captcha' in html_lower or
            'captcha' in html_lower
        )

    @staticmethod
    def _processo_nao_encontrado(html: str) -> bool:
        """
        Detecta resposta do tipo 'processo não encontrado' do e-SAJ.

        Confirmado em 2026-07-27: quando o processo não existe, o e-SAJ
        retorna a própria página de busca com um td#mensagemRetorno
        contendo 'Não existem informações disponíveis para os parâmetros
        informados'. O HTML tem ~39k chars mas nenhum dado de processo.
        """
        marcadores = (
            "não existem informações disponíveis",
            "nao existem informacoes disponiveis",
        )
        html_lower = html.lower()
        return any(marcador in html_lower for marcador in marcadores)
