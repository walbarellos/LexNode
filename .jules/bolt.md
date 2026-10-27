## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2024-05-19 - BS4 Parsing Optimization
**Learning:** Parsing the entire massive DOM returned by TRF1/PJe judicial systems is a significant performance bottleneck.
**Action:** Use `bs4.SoupStrainer` with `BeautifulSoup` (e.g., `parse_only=SoupStrainer('table', id='target')`) when scraping large payloads to only parse the required elements, saving time and memory.
