"""
crawler_trf1.py — JusBrasil

Crawler para o PJe (Processo Judicial Eletrônico) do TRF1 (Justiça Federal).
Cobre crimes federais, execuções fiscais, ações contra o INSS, CEF, etc.

Endpoint: https://pje1g-consultapublica.trf1.jus.br/consultapublica/ConsultaPublica/listView.seam
Arquitetura: JavaServer Faces (JSF) com RichFaces.
hCaptcha: Presente no código-fonte, porém DESATIVADO (if false).
"""

import re
import warnings
import requests
from dataclasses import dataclass
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

BASE_URL = "https://pje1g-consultapublica.trf1.jus.br/consultapublica/ConsultaPublica/listView.seam"
DETALHE_BASE = "https://pje1g-consultapublica.trf1.jus.br"


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

    def _iniciar_sessao(self):
        """GET inicial para obter o JSESSIONID e o javax.faces.ViewState."""
        r = self._session.get(BASE_URL, verify=False, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
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
        return {
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
            "fPP:j_id245": "fPP:j_id245",
            "autoScroll": "",
        }

    def _executar_busca(self, data: dict) -> list[ResumoProcessoFederal]:
        r = self._session.post(BASE_URL, data=data, verify=False, timeout=20)
        r.raise_for_status()
        return self._parsear_resultados(r.text)

    def _parsear_resultados(self, html: str) -> list[ResumoProcessoFederal]:
        soup = BeautifulSoup(html, "html.parser")
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

            # Coluna 0: Link de detalhes
            link_tag = cells[0].find("a")
            link_detalhe = ""
            if link_tag:
                onclick = link_tag.get("onclick", "")
                match = re.search(r"openPopUp\([^,]+,\s*'([^']+)'\)", onclick)
                if match:
                    link_detalhe = DETALHE_BASE + match.group(1)

            # Coluna 1: Classe + Número + Partes
            cell_proc = cells[1]
            b_tag = cell_proc.find("b")

            numero = ""
            classe = ""
            assunto = ""
            if b_tag:
                texto_b = b_tag.get_text(strip=True)
                # Formato: "ExTiEx 0000001-64.1970.4.01.3300 - Mútuo"
                match_num = re.search(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", texto_b)
                if match_num:
                    numero = match_num.group(1)
                
                # Classe é o que vem antes do número
                partes_texto = texto_b.split(numero) if numero else [texto_b]
                classe = partes_texto[0].strip() if partes_texto else ""
                
                # Assunto é o que vem depois do " - "
                if " - " in texto_b:
                    assunto = texto_b.split(" - ", 1)[-1].strip()

            # Texto completo da célula excluindo o <b> e <a> = partes
            texto_completo = cell_proc.get_text(" ", strip=True)
            # Remover a parte do <b> tag para isolar as partes
            texto_b_full = b_tag.get_text(" ", strip=True) if b_tag else ""
            # Também remover a classe que aparece antes do <a>
            classe_prefixo = cell_proc.contents[0] if cell_proc.contents else ""
            if hasattr(classe_prefixo, 'strip'):
                classe_prefixo = classe_prefixo.strip()
            else:
                classe_prefixo = ""
            
            partes = texto_completo
            if texto_b_full:
                partes = partes.replace(texto_b_full, "").strip()
            if classe_prefixo:
                partes = partes.replace(classe_prefixo, "", 1).strip()
            # Limpar lixo visual
            partes = re.sub(r"\s+", " ", partes).strip()
            if partes.startswith("Ver detalhes do processo"):
                partes = partes.replace("Ver detalhes do processo", "").strip()

            # Coluna 2: Última movimentação
            ultima_mov = cells[2].get_text(strip=True) if len(cells) > 2 else ""

            if numero:
                resultados.append(ResumoProcessoFederal(
                    numero=numero,
                    classe=classe,
                    assunto=assunto,
                    partes=partes,
                    ultima_movimentacao=ultima_mov,
                    link_detalhe=link_detalhe,
                ))

        return resultados

    def detalhar_processo(self, link_detalhe: str) -> ProcessoDetalhadoFederal:
        """Extrai os dados completos da página de detalhes do processo no TRF1."""
        r = self._session.get(link_detalhe, verify=False, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Helper to extract text from a property block
        def get_prop(label_start):
            label = soup.find("label", string=re.compile(label_start, re.I))
            if label:
                parent_div = label.find_parent("div", class_="name")
                if parent_div:
                    val_div = parent_div.find_next_sibling("div", class_="value")
                    if val_div:
                        return val_div.get_text(" ", strip=True)
            return ""

        numero = get_prop("Número Processo")
        data_dist = get_prop("Data da Distribuição")
        classe = get_prop("Classe Judicial")
        assunto = get_prop("Assunto")
        jurisdicao = get_prop("Jurisdição")
        
        # Órgão julgador e endereço são um pouco mais complexos
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
                
        # Extrair partes
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
        
        # Extrair movimentações
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
            movimentacoes=movimentacoes
        )
