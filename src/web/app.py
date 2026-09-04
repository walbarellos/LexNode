import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

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

app = FastAPI(title="JusBrasil API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Thread pool for concurrent synchronous crawler calls
executor = ThreadPoolExecutor(max_workers=10)
crawler_juris = CrawlerJurisprudencia()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/buscar/processo/{numero}")
async def buscar_processo(numero: str, grau: int = Query(1)):
    """Search for a specific process number."""
    
    # Check if TRF1 process (ends in .4.01.xxxx)
    is_trf1 = ".4.01." in numero
    
    def fetch_processo():
        if is_trf1:
            crawler = CrawlerTRF1()
            resumos = crawler.buscar_por_numero(numero)
            if resumos:
                # Convert the TRF1 resumo format to match the detailed TJAC format enough for the frontend
                r = resumos[0]
                return {
                    "numero_processo": r.numero,
                    "classe": r.classe,
                    "assunto": r.assunto,
                    "foro": "Justiça Federal (TRF1)",
                    "situacao": "Desconhecido",
                    "partes": [{"nome": r.partes, "tipo": "Partes"}],
                    "movimentacoes": [{"data": "Última", "descricao": r.ultima_movimentacao}],
                    "link_detalhe": r.link_detalhe,
                    "sistema": "TRF1"
                }
            raise ProcessoNaoEncontradoError()
        else:
            crawler = BaseCrawler()
            if grau == 2:
                resposta = crawler.consultar_processo_2grau(numero)
                processo = normalizar_html_2grau(numero, resposta.html)
            else:
                resposta = crawler.consultar_processo_1grau(numero)
                processo = normalizar_html_1grau(numero, resposta.html)
            
            res = processo.to_dict()
            res["sistema"] = "TJAC"
            return res

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

@app.get("/api/buscar/nome/{nome}")
async def buscar_nome(nome: str, foro: str = Query("-1"), doc: bool = Query(False)):
    """Search for processes by name or document (CPF/CNPJ) concurrently in TJAC and TRF1"""
    termo_busca = nome
    tipo_pesquisa = 'DOCPARTE' if doc else 'NMPARTE'
    
    if doc:
        termo_busca = re.sub(r'[^0-9]', '', termo_busca)

    def fetch_tjac(g: int):
        crawler = BaseCrawler()
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
        
        resp = crawler._session.get(search_url, params=params, timeout=15)
        resp.raise_for_status()
        
        texto_lower = resp.text.lower()
        if "muitos processos" in texto_lower or "refine sua busca" in texto_lower:
            return []
        elif "não existem informações disponíveis" in texto_lower:
            return []
            
        resumos = extrair_resumos_pesquisa_2grau(resp.text) if g == 2 else extrair_resumos_pesquisa(resp.text)
        formatted = []
        for r in resumos:
            d = asdict(r)
            d["sistema"] = "TJAC (1º Grau)" if g == 1 else "TJAC (2º Grau)"
            formatted.append(d)
        return formatted

    def fetch_trf1():
        crawler = CrawlerTRF1()
        if doc:
            resumos = crawler.buscar_por_documento(termo_busca)
        else:
            resumos = crawler.buscar_por_nome(termo_busca)
        
        formatted = []
        for r in resumos:
            # Map TRF1 fields to match TJAC ResumoProcesso where possible
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
    
    # Launch concurrent tasks
    tjac1 = loop.run_in_executor(executor, fetch_tjac, 1)
    tjac2 = loop.run_in_executor(executor, fetch_tjac, 2)
    trf1_task = loop.run_in_executor(executor, fetch_trf1)
    
    # Wait for all to finish
    results = await asyncio.gather(tjac1, tjac2, trf1_task, return_exceptions=True)
    
    todos_resumos = []
    for r in results:
        if isinstance(r, list):
            todos_resumos.extend(r)
        else:
            print(f"Erro em um dos crawlers: {r}")

    return JSONResponse(content={"resultados": todos_resumos})

@app.get("/api/buscar/jurisprudencia/{termo}")
async def buscar_jurisprudencia(termo: str):
    """Search for case law based on a term"""
    def fetch_juris():
        # Using a new instance for safety or sharing crawler_juris is fine since it's just one endpoint
        return crawler_juris.buscar_jurisprudencia(termo)
        
    loop = asyncio.get_running_loop()
    try:
        resultados = await loop.run_in_executor(executor, fetch_juris)
        return JSONResponse(content={"resultados": resultados})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
