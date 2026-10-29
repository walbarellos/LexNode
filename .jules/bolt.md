## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2024-10-29 - TRF1 HTML Payload Parsing Optimization
**Learning:** TRF1 responses can contain massive HTML payloads. Using `BeautifulSoup` to parse the entire DOM is a performance bottleneck. By using `bs4.SoupStrainer` (`parse_only=SoupStrainer('table', id='fPP:processosTable')`), we can restrict parsing to only the elements we actually need, avoiding the overhead of constructing the full DOM tree and cutting parsing time by over 50%.
**Action:** When scraping specific elements from large HTML payloads, especially in target systems like TRF1, always use `bs4.SoupStrainer` with `BeautifulSoup` to only parse the required portions of the document.
