import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger("processolivre.pdf")

# Carrega variáveis do arquivo .env
load_dotenv()

def baixar_acordao(cd_acordao: str, caminho_saida: str) -> bool:
    """
    Baixa o PDF de um Acórdão do 2º Grau usando injeção de cookie.
    Retorna True se o download foi bem sucedido, False caso contrário.
    """
    cookie = os.getenv("ESAJ_COOKIE")
    if not cookie:
        logger.error("ESAJ_COOKIE não encontrado no .env. Configure o cookie para baixar PDFs.")
        return False
        
    url = f"https://esaj.tjac.jus.br/cjsg/getArquivo.do?cdAcordao={cd_acordao}&cdForo=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": cookie
    }
    
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=20)
        
        # Verifica se retornou PDF ou se foi bloqueado/deslogado (retornando HTML)
        content_type = r.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower():
            logger.error("Download falhou: Servidor não retornou um PDF. Verifique se o seu Cookie está expirado.")
            return False
            
        saida_dir = Path(caminho_saida).parent
        saida_dir.mkdir(parents=True, exist_ok=True)
        
        with open(caminho_saida, "wb") as f:
            f.write(r.content)
            
        return True
    except Exception as e:
        logger.error(f"Erro ao baixar PDF: {e}")
        return False
