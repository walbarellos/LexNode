## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2024-10-25 - Use SoupStrainer for large JSF DOMs
**Learning:** Parsing the entirety of massive HTML payloads returned by JSF applications (like the TRF1 judicial system pages) is extremely slow and memory-intensive when using standard `BeautifulSoup`.
**Action:** When extracting a specific fragment from large HTML structures, use `bs4.SoupStrainer` with `BeautifulSoup(html, "lxml", parse_only=...)` to skip parsing irrelevant parts of the document, making memory footprint smaller and performance much better.
