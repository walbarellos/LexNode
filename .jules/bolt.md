## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2024-05-24 - SoupStrainer for Large Payloads
**Learning:** When scraping specific JSF-based targets like TRF1, the judicial pages contain massive DOM structures. Using `BeautifulSoup(html, "lxml")` loads the entire HTML. `bs4.SoupStrainer` allows parsing only specific elements (e.g., `parse_only=SoupStrainer('table', id='fPP:processosTable')`).
**Action:** Use `bs4.SoupStrainer` together with `BeautifulSoup` to avoid parsing unnecessary DOM structures, drastically improving HTML parsing speed.
