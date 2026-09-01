import re
import requests
from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler

class CrawlerJurisprudencia:
    def __init__(self):
        self.crawler = BaseCrawler()

    def buscar_jurisprudencia(self, termo: str) -> list:
        # First, initiate session
        self.crawler._session.get('https://esaj.tjac.jus.br/cjsg/consultaCompleta.do', verify=False, timeout=15)
        
        params = {
            'dados.buscaInteiroTeor': termo,
            'dados.pesquisarComSinonimos': 'S',
            'dados.origensSelecionadas': 'T',
            'tipoDecisaoSelecionados': 'A',
            'dados.ordenarPor': 'dtPublicacao'
        }
        
        r = self.crawler._session.post('https://esaj.tjac.jus.br/cjsg/resultadoCompleta.do', data=params, verify=False, timeout=15)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        resultados = []
        
        # Encontra todos os nós com texto Ementa:
        regex_ementa = re.compile(r'^\s*Ementa:', re.IGNORECASE)
        # O(1) lookup in tree without looping over tr
        ementas = soup.find_all(string=regex_ementa)
        tables_vistas = set()
        
        # Pre-compile regex patterns for metadata to avoid doing it inside the loop
        re_relator = re.compile(r'^\s*Relator\(a\):')
        re_orgao = re.compile(r'^\s*Órgão julgador:')
        re_data_julg = re.compile(r'^\s*Data do julgamento:')

        for em in ementas:
            table = em.find_parent('table')
            if not table or id(table) in tables_vistas:
                continue
            tables_vistas.add(id(table))
            
            # 1. Processo
            link_proc = table.find('a', class_='esajLinkLogin')
            if not link_proc:
                continue
            numero = link_proc.text.strip()
            
            # 2. Ementa
            link_ementa = table.find('a', class_='textoSemFormatacao')
            ementa_texto = link_ementa.text.strip() if link_ementa else ''
            
            # 3. Metadados
            def get_meta(regex_pattern):
                el = table.find(string=regex_pattern)
                if el:
                    td = el.find_parent('td')
                    if td:
                        return td.text.replace(el, '').strip()
                return ''
                
            relator = get_meta(re_relator)
            orgao = get_meta(re_orgao)
            data_julg = get_meta(re_data_julg)
            
            link_download = table.find('a', class_='downloadEmenta')
            cd_acordao = link_download.get('cdacordao', '') if link_download else ''

            resultados.append({
                'numero': numero,
                'cd_acordao': cd_acordao,
                'relator': relator,
                'orgao': orgao,
                'data': data_julg,
                'ementa': ementa_texto
            })
            
        return resultados
