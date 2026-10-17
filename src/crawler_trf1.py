"""
crawler_trf1.py — JusBrasil

Crawler para o PJe (Processo Judicial Eletrônico) do TRF1 (Justiça Federal).
Cobre crimes federais, execuções fiscais, ações contra o INSS, CEF, etc.

Endpoint: https://pje1g-consultapublica.trf1.jus.br/consultapublica/ConsultaPublica/listView.seam
Arquitetura: JavaServer Faces (JSF) com RichFaces.
hCaptcha: Presente no código-fonte, porém DESATIVADO (if false).
"""

import logging
import re
import time
import warnings
import requests
from dataclasses import dataclass
from bs4 import BeautifulSoup, SoupStrainer

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

logger = logging.getLogger("lexnode.crawler_trf1")

BASE_URL = "https://pje1g-consultapublica.trf1.jus.br/consultapublica/ConsultaPublica/listView.seam"
DETALHE_BASE = "https://pje1g-consultapublica.trf1.jus.br"

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

_RE_WHITESPACE = re.compile(r"\s+")


@dataclass
class ResumoProcessoFederal:
    numero: str
    classe: str
    assunto: str
    partes: str
    ultima_movimentacao: str
    link_detalhe: str


@dataclass
class ProcessoDetalhadoFederal:
    numero: str
    data_distribuicao: str
    classe: str
    assunto: str
    jurisdicao: str
    orgao_julgador: str
    endereco: str
    polo_ativo: list[dict]
    polo_passivo: list[dict]
    movimentacoes: list[dict]


class CrawlerTRF1:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self._view_state = None

    def _request_with_retry(self, method: str, url: str, **kwargs):
        """HTTP com retry em timeout/conexão. O PJe do TRF1 é intermitente."""
        kwargs.setdefault("verify", False)
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self._session.request(method, url, **kwargs)
                resp.raise_for_status()
                return resp
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exc = exc
                logger.warning(
                    "TRF1 tentativa %s/%s falhou (%s): %s",
                    attempt, MAX_RETRIES, type(exc).__name__, exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF * attempt)
            except requests.HTTPError:
                raise
        raise last_exc

    def _iniciar_sessao(self):
        """GET inicial para obter o JSESSIONID e o javax.faces.ViewState."""
        r = self._request_with_retry("GET", BASE_URL)
        # ⚡ Bolt Optimization: Use SoupStrainer to avoid loading massive JSF DOM into memory
        strainer = SoupStrainer("input", {"name": "javax.faces.ViewState"})
        soup = BeautifulSoup(r.text, "lxml", parse_only=strainer)
        vs = soup.find("input", {"name": "javax.faces.ViewState"})
        if vs:
            self._view_state = vs["value"]
        else:
            raise RuntimeError("Não foi possível obter o ViewState do PJe/TRF1.")

    def buscar_por_nome(self, nome: str) -> list[ResumoProcessoFederal]:
        """Busca processos federais pelo nome da parte."""
        self._iniciar_sessao()
        data = self._montar_payload()
        data["fPP:dnp:nomeParte"] = nome
        return self._executar_busca(data)

    def buscar_por_documento(self, documento: str) -> list[ResumoProcessoFederal]:
        """Busca processos federais por CPF ou CNPJ."""
        self._iniciar_sessao()
        doc_limpo = re.sub(r"[^0-9]", "", documento)
        data = self._montar_payload()
        data["fPP:dpDec:documentoParte"] = doc_limpo
        return self._executar_busca(data)

    def buscar_por_numero(self, numero: str) -> list[ResumoProcessoFederal]:
        """Busca por número de processo unificado (CNJ)."""
        self._iniciar_sessao()
        data = self._montar_payload()
        data["fPP:numProcesso-inputNumeroProcessoDecoration:numProcesso-inputNumeroProcesso"] = numero
        return self._executar_busca(data)

    def _montar_payload(self) -> dict:
        # Botão real do formulário público (A4J): fPP:searchProcessos
        return {
            "AJAXREQUEST": "_viewRoot",
            "fPP": "fPP",
            "fPP:dnp:nomeParte": "",
            "fPP:dpDec:documentoParte": "",
            "fPP:j_id184:nomeAdv": "",
            "fPP:numProcesso-inputNumeroProcessoDecoration:numProcesso-inputNumeroProcesso": "",
            "fPP:j_id166:processoReferenciaInput": "",
            "fPP:j_id193:classeJudicial": "",
            "fPP:Decoration:numeroOAB": "",
            "fPP:Decoration:j_id227": "",
            "fPP:Decoration:estadoComboOAB": "org.jboss.seam.ui.NoSelectionConverter.noSelectionValue",
            "fPP:dataAutuacaoDecoration:dataAutuacaoInicioInputDate": "",
            "fPP:dataAutuacaoDecoration:dataAutuacaoFimInputDate": "",
            "javax.faces.ViewState": self._view_state,
            "fPP:searchProcessos": "fPP:searchProcessos",
            "AJAX:EVENTS_COUNT": "1",
        }

    def _executar_busca(self, data: dict) -> list[ResumoProcessoFederal]:
        headers = {
            "Faces-Request": "partial/ajax",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "Referer": BASE_URL,
        }
        r = self._request_with_retry("POST", BASE_URL, data=data, headers=headers)
        body = r.text or ""
        content_type = (r.headers.get("content-type") or "").lower()
        if "xml" in content_type or body.lstrip().startswith("<?xml"):
            html = self._extrair_html_ajax(body)
            return self._parsear_resultados(html)
        return self._parsear_resultados(body)

    def _extrair_html_ajax(self, body: str) -> str:
        """Extrai fragmentos HTML de resposta A4J/JSF (XML com CDATA)."""
        if not body:
            return ""
        chunks = re.findall(
            r"<update[^>]*>\s*<!\[CDATA\[(.*?)\]\]>\s*</update>",
            body,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if chunks:
            return "\n".join(chunks)
        chunks = re.findall(
            r"<update[^>]*>(.*?)</update>",
            body,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if chunks:
            return "\n".join(chunks)
        return body

    def _parsear_resultados(self, html: str) -> list[ResumoProcessoFederal]:
        # ⚡ Bolt Optimization: Use SoupStrainer to avoid loading massive JSF DOM into memory
        strainer = SoupStrainer("table", id="fPP:processosTable")
        soup = BeautifulSoup(html, "lxml", parse_only=strainer)
        table = soup.find("table", id="fPP:processosTable")
        if not table:
            return []

        tbody = table.find("tbody")
        if not tbody:
            return []

        resultados = []
        for tr in tbody.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 3:
                continue

            link_tag = cells[0].find("a")
            link_detalhe = ""
            if link_tag:
                onclick = link_tag.get("onclick", "")
                match = re.search(r"openPopUp\([^,]+,\s*'([^']+)'\)", onclick)
                if match:
                    link_detalhe = DETALHE_BASE + match.group(1)

            cell_proc = cells[1]
            b_tag = cell_proc.find("b")

            numero = ""
            classe = ""
            assunto = ""
            if b_tag:
                texto_b = b_tag.get_text(strip=True)
                match_num = re.search(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", texto_b)
                if match_num:
                    numero = match_num.group(1)
                partes_texto = texto_b.split(numero) if numero else [texto_b]
                classe = partes_texto[0].strip() if partes_texto else ""
                if " - " in texto_b:
                    assunto = texto_b.split(" - ", 1)[-1].strip()

            texto_completo = cell_proc.get_text(" ", strip=True)
            texto_b_full = b_tag.get_text(" ", strip=True) if b_tag else ""
            partes = texto_completo
            if texto_b_full:
                partes = partes.replace(texto_b_full, "").strip()

            ultima = cells[2].get_text(" ", strip=True) if len(cells) > 2 else ""

            if numero:
                resultados.append(ResumoProcessoFederal(
                    numero=numero,
                    classe=classe,
                    assunto=assunto,
                    partes=_RE_WHITESPACE.sub(" ", partes).strip(),
                    ultima_movimentacao=ultima,
                    link_detalhe=link_detalhe,
                ))
        return resultados

    def detalhar_processo(self, link_detalhe: str) -> ProcessoDetalhadoFederal:
        """Abre a página de detalhe e extrai dados estruturados."""
        r = self._request_with_retry("GET", link_detalhe)
        soup = BeautifulSoup(r.text, "lxml")

        def get_prop(label):
            b = soup.find("b", string=re.compile(label, re.I))
            if not b:
                return ""
            parent = b.parent
            val_div = parent.find("div") if parent else None
            if val_div:
                return val_div.get_text(" ", strip=True)
            return parent.get_text(" ", strip=True).replace(label, "", 1).strip() if parent else ""

        numero = get_prop("Número Processo")
        data_dist = get_prop("Data da Distribuição")
        classe = get_prop("Classe Judicial")
        assunto = get_prop("Assunto")
        jurisdicao = get_prop("Jurisdição")

        orgao_julgador = ""
        endereco = ""
        b_orgao = soup.find("b", string=re.compile("Órgão Julgador", re.I))
        if b_orgao:
            parent_div = b_orgao.parent
            texto = parent_div.get_text(" ", strip=True)
            match_orgao = re.search(r"Órgão Julgador\s+(.*?)(?:Endereço|$)", texto, re.I)
            if match_orgao:
                orgao_julgador = match_orgao.group(1).strip()
            match_end = re.search(r"Endereço\s+(.*)", texto, re.I)
            if match_end:
                endereco = match_end.group(1).strip()

        def extrair_tabela_partes(table_id):
            partes = []
            table = soup.find("table", id=table_id)
            if table and table.find("tbody"):
                for tr in table.find("tbody").find_all("tr"):
                    cells = tr.find_all("td")
                    if cells:
                        span = cells[0].find("span", class_="text-bold")
                        nome = span.get_text(strip=True) if span else cells[0].get_text(" ", strip=True)
                        nome = re.sub(r"\s+", " ", nome).strip()
                        sit = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        partes.append({"nome": nome, "situacao": sit})
            return partes

        polo_ativo = extrair_tabela_partes("j_id150:processoPartesPoloAtivoResumidoTableBinding")
        polo_passivo = extrair_tabela_partes("j_id150:processoPartesPoloPassivoResumidoTableBinding")

        movimentacoes = []
        table_mov = soup.find("table", id="j_id150:processoEvento")
        if table_mov and table_mov.find("tbody"):
            for tr in table_mov.find("tbody").find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) >= 2:
                    data = cells[0].get_text(strip=True)
                    doc_mov = cells[1].get_text(" ", strip=True)
                    movimentacoes.append({"data": data, "descricao": doc_mov})

        return ProcessoDetalhadoFederal(
            numero=numero,
            data_distribuicao=data_dist,
            classe=classe,
            assunto=assunto,
            jurisdicao=jurisdicao,
            orgao_julgador=orgao_julgador,
            endereco=endereco,
            polo_ativo=polo_ativo,
            polo_passivo=polo_passivo,
            movimentacoes=movimentacoes,
        )
