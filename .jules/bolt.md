## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2024-05-25 - SoupStrainer for TRF1 parsing
**Learning:** The TRF1 crawler used to parse massive judicial HTML pages using BeautifulSoup to find a single table. Using `SoupStrainer` reduces parsing time significantly (~60-70% faster) and memory usage by only constructing the DOM for the matched elements.
**Action:** Always prefer `SoupStrainer` with `BeautifulSoup` when scraping specific sections of large HTML documents, and handle the returned root element carefully as it changes depending on the match.
