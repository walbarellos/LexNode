## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2026-07-27 - Cache JSF ViewState & Retry Pattern
**Learning:** TRF1's architecture utilizes JavaServer Faces (JSF), demanding a `javax.faces.ViewState` paired with `JSESSIONID` to run subsequent searches. Getting these parameters required a dedicated GET request initially done before *each* search request. However, `ViewState` values persist for a limited time on the server.
**Action:** When scraping JSF-based targets (like TRF1), cache the `javax.faces.ViewState` across instances to bypass redundant GET requests. To counter server-side `ViewExpiredException` side effects, implement a catch-and-retry strategy mapping `requests.HTTPError` on subsequent POSTs to cleanly force a ViewState refresh and reattempt.
