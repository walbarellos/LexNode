## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2024-05-14 - SoupStrainer for Partial DOM Parsing in BeautifulSoup
**Learning:** When scraping large, complex judicial pages (like TRF1/JSF) using `BeautifulSoup`, loading the entire HTML into the DOM is a massive performance bottleneck. `SoupStrainer` allows parsing only specific elements (e.g., `parse_only=SoupStrainer('table', id='target')`), which skips building the parse tree for the rest of the document, drastically reducing memory usage and execution time.
**Action:** Use `SoupStrainer` with `BeautifulSoup` whenever extracting specific, known elements (like `javax.faces.ViewState` inputs or specific data tables) from large HTML payloads, rather than parsing the entire page.
