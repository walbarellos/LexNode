## 2024-05-24 - HTML Parser Optimization
**Learning:** The application uses BeautifulSoup with the default 'html.parser' in several places. Since the application performs heavy web scraping of large judicial HTML pages, switching to 'lxml' provides a significant performance boost (up to 35-50% faster parsing times) without losing functionality. Also found an unused BeautifulSoup parsing in the fallback regex extraction.
**Action:** Replace 'html.parser' with 'lxml' where BeautifulSoup is used. Add 'lxml' to requirements.txt. Remove the unnecessary BeautifulSoup instantiation in `extrair_resumos_pesquisa_2grau` since it extracts via regex anyway.

## 2023-10-28 - Optimizing BeautifulSoup parsing with SoupStrainer
**Learning:** For optimal HTML scraping performance, especially against large payloads like TRF1 judicial pages, parsing the entire massive DOM with BeautifulSoup is inefficient. We can use `bs4.SoupStrainer` (e.g., `parse_only=SoupStrainer('table', id='target')`) to extract only the required elements, avoiding the creation of unnecessary DOM structures and speeding up parsing.
**Action:** Always use `SoupStrainer` when extracting specific elements (like hidden inputs or tables) from large HTML responses to improve performance.
