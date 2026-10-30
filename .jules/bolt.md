## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2024-05-19 - Use SoupStrainer to optimize BeautifulSoup HTML parsing
**Learning:** When parsing very large HTML payloads like those from JSF applications (e.g. TRF1 responses), using `bs4.BeautifulSoup(html, "lxml")` loads the entire massive DOM tree into memory. This degrades performance significantly and unnecessarily when you only need a small subsection of the page.
**Action:** Use `bs4.SoupStrainer` (e.g. `parse_only=SoupStrainer("table", id="fPP:processosTable")`) during initialization of `BeautifulSoup` to ignore irrelevant parts of the document, dramatically speeding up parsing and reducing memory consumption.
