import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import threading
from src.base_crawler import BaseCrawler, ProcessoNaoEncontradoError, ConsultaFalhouError
from src.normalizer import (
    normalizar_html_1grau, 
    normalizar_html_2grau, 
    ProcessoSigilosoError,
    extrair_resumos_pesquisa,
    extrair_resumos_pesquisa_2grau
)
from src.crawler_jurisprudencia import CrawlerJurisprudencia
from src.crawler_trf1 import CrawlerTRF1

app = FastAPI(title="LexNode")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

executor = ThreadPoolExecutor(max_workers=10)

thread_local = threading.local()

def get_base_crawler():
    if not hasattr(thread_local, 'base_crawler'):
        thread_local.base_crawler = BaseCrawler()
    return thread_local.base_crawler

def get_crawler_trf1():
    if not hasattr(thread_local, 'crawler_trf1'):
        thread_local.crawler_trf1 = CrawlerTRF1()
    return thread_local.crawler_trf1

crawler_juris = CrawlerJurisprudencia()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/buscar/processo/{numero}")
async def buscar_processo(numero: str, grau: int = Query(1)):
    is_trf1 = ".4.01." in numero

    def fetch_processo():
        if is_trf1:
            crawler = get_crawler_trf1()
            resumos = crawler.buscar_por_numero(numero)
            if resumos:
                detalhe = crawler.detalhar_processo(resumos[0].link_detalhe)
                return {
                    "numero_processo": detalhe.numero or resumos[0].numero,
                    "sistema": "TRF1",
                    "classe": detalhe.classe or resumos[0].classe,
                    "assunto": detalhe.assunto or resumos[0].assunto,
                    "situacao": "Consulta pública",
                    "juiz": None,
                    "relator": None,
                    "vara": detalhe.orgao_julgador,
                    "orgao_julgador": detalhe.orgao_julgador,
                    "foro": detalhe.jurisdicao,
                    "distribuicao": detalhe.data_distribuicao,
                    "partes": {
                        "ativo": detalhe.polo_ativo,
                        "passivo": detalhe.polo_passivo,
                    },
                    "movimentacoes": detalhe.movimentacoes,
                }
            raise ProcessoNaoEncontradoError("Processo não encontrado no TRF1")

        crawler = get_base_crawler()
        if grau == 2:
            resp = crawler.consultar_processo_2grau(numero)
            dados = normalizar_html_2grau(resp.html)
        else:
            resp = crawler.consultar_processo_1grau(numero)
            dados = normalizar_html_1grau(resp.html)
        d = asdict(dados) if hasattr(dados, '__dataclass_fields__') else dados
        if isinstance(d, dict):
            d["sistema"] = "TJAC (2º Grau)" if grau == 2 else "TJAC (1º Grau)"
        return d

    loop = asyncio.get_running_loop()
    try:
        resultado = await loop.run_in_executor(executor, fetch_processo)
        return JSONResponse(content=resultado)
    except ProcessoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    except ProcessoSigilosoError:
        raise HTTPException(status_code=403, detail="Processo sob segredo de justiça")
    except ConsultaFalhouError:
        raise HTTPException(status_code=502, detail="Falha na consulta ao tribunal")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/buscar/nome")
async def buscar_nome(q: str = Query(..., min_length=1), foro: str = Query("-1"), doc: bool = Query(False)):
    # Query string evita 404 com CNPJ (barras) e nomes com caracteres especiais.
    termo_busca = q
    tipo_pesquisa = 'DOCPARTE' if doc else 'NMPARTE'

    if doc:
        termo_busca = re.sub(r'[^0-9]', '', termo_busca)

    def fetch_tjac(g: int):
        label = "TJAC (1º Grau)" if g == 1 else "TJAC (2º Grau)"
        crawler = get_base_crawler()
        if g == 2:
            params = {
                'conversationId': '',
                'paginaConsulta': '0',
                'cbPesquisa': tipo_pesquisa,
                'tipoNuProcesso': 'UNIFICADO',
                'dePesquisa': termo_busca,
                'dePesquisaNuUnificado': '',
                'numeroDigitoAnoUnificado': '',
                'foroNumeroUnificado': '',
            }
            search_url = "https://esaj.tjac.jus.br/cposg5/search.do"
            crawler.iniciar_sessao(grau=2)
        else:
            params = {
                'conversationId': '',
                'cbPesquisa': tipo_pesquisa,
                'dadosConsulta.tipoNuProcesso': 'UNIFICADO',
                'dadosConsulta.valorConsulta': termo_busca,
                'cdForo': foro,
                'numeroDigitoAnoUnificado': '',
                'foroNumeroUnificado': '',
                'dadosConsulta.valorConsultaNuUnificado': '',
            }
            search_url = "https://esaj.tjac.jus.br/cpopg/search.do"
            crawler.iniciar_sessao()

        resp = crawler._session.get(search_url, params=params, timeout=25)
        resp.raise_for_status()

        texto_lower = resp.text.lower()
        if "muitos processos" in texto_lower or "refine sua busca" in texto_lower:
            return []
        if "não existem informações disponíveis" in texto_lower:
            return []

        resumos = extrair_resumos_pesquisa_2grau(resp.text) if g == 2 else extrair_resumos_pesquisa(resp.text)
        formatted = []
        for r in resumos:
            d = asdict(r)
            d["sistema"] = label
            formatted.append(d)
        return formatted

    def fetch_trf1():
        crawler = get_crawler_trf1()
        if doc:
            resumos = crawler.buscar_por_documento(termo_busca)
        else:
            resumos = crawler.buscar_por_nome(termo_busca)

        formatted = []
        for r in resumos:
            formatted.append({
                "numero": r.numero,
                "classe": r.classe,
                "assunto": r.assunto,
                "data_local": r.ultima_movimentacao,
                "participacao": r.partes,
                "sistema": "TRF1"
            })
        return formatted

    loop = asyncio.get_running_loop()

    fontes = [
        ("TJAC (1º Grau)", loop.run_in_executor(executor, fetch_tjac, 1)),
        ("TJAC (2º Grau)", loop.run_in_executor(executor, fetch_tjac, 2)),
        ("TRF1", loop.run_in_executor(executor, fetch_trf1)),
    ]

    results = await asyncio.gather(*(t for _, t in fontes), return_exceptions=True)

    todos_resumos = []
    avisos = []
    for (fonte, _), r in zip(fontes, results):
        if isinstance(r, list):
            todos_resumos.extend(r)
        else:
            msg = str(r)
            if "timed out" in msg.lower() or "timeout" in msg.lower():
                aviso = f"{fonte}: o tribunal não respondeu a tempo. Tente novamente em instantes."
            else:
                aviso = f"{fonte}: falha na consulta ({type(r).__name__})."
            avisos.append(aviso)
            print(f"Erro em {fonte}: {r}")

    return JSONResponse(content={"resultados": todos_resumos, "avisos": avisos})

@app.get("/api/buscar/jurisprudencia")
async def buscar_jurisprudencia(q: str = Query(..., min_length=1)):
    def fetch_juris():
        return crawler_juris.buscar_jurisprudencia(q)

    loop = asyncio.get_running_loop()
    try:
        resultados = await loop.run_in_executor(executor, fetch_juris)
        return JSONResponse(content={"resultados": resultados})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
