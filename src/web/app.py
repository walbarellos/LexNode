import os
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import re
from dataclasses import asdict

from src.base_crawler import BaseCrawler, ProcessoNaoEncontradoError, ConsultaFalhouError
from src.normalizer import (
    normalizar_html_1grau, 
    normalizar_html_2grau, 
    ProcessoSigilosoError,
    extrair_resumos_pesquisa,
    extrair_resumos_pesquisa_2grau
)
from src.crawler_jurisprudencia import CrawlerJurisprudencia

app = FastAPI(title="LexNode API")

# Set up templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Keep a singleton instance of BaseCrawler and CrawlerJurisprudencia
crawler = BaseCrawler()
crawler_juris = CrawlerJurisprudencia()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/buscar/processo/{numero}")
async def buscar_processo(numero: str, grau: int = Query(1)):
    """Search for a specific process number in 1st or 2nd degree"""
    try:
        if grau == 2:
            resposta = crawler.consultar_processo_2grau(numero)
            processo = normalizar_html_2grau(numero, resposta.html)
        else:
            resposta = crawler.consultar_processo_1grau(numero)
            processo = normalizar_html_1grau(numero, resposta.html)
            
        return JSONResponse(content=processo.to_dict())
    
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
    """Search for processes by name or document (CPF/CNPJ)"""
    termo_busca = nome
    tipo_pesquisa = 'DOCPARTE' if doc else 'NMPARTE'
    
    if doc:
        termo_busca = re.sub(r'[^0-9]', '', termo_busca)
        
    resumos = []
    
    try:
        for g in [1, 2]:
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
                continue
            elif "não existem informações disponíveis" in texto_lower:
                continue
                
            novos_resumos = extrair_resumos_pesquisa_2grau(resp.text) if g == 2 else extrair_resumos_pesquisa(resp.text)
            if novos_resumos:
                resumos.extend(novos_resumos)
                
        # Format list to dicts
        resultados_dict = [asdict(r) for r in resumos]
        return JSONResponse(content={"resultados": resultados_dict})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/buscar/jurisprudencia/{termo}")
async def buscar_jurisprudencia(termo: str):
    """Search for case law based on a term"""
    try:
        resultados = crawler_juris.buscar_jurisprudencia(termo)
        return JSONResponse(content={"resultados": resultados})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
