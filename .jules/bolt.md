## 2024-06-11 - Use SoupStrainer for targeted parsing of large DOMs
**Learning:** Parsing massive judicial pages (like TRF1 results) with `BeautifulSoup` and loading the entire DOM into memory is a significant performance bottleneck.
**Action:** When only specific elements (e.g., a specific table or input field) are needed from a large HTML payload, use `bs4.SoupStrainer` (e.g., `parse_only=SoupStrainer('table', id='fPP:processosTable')`) to instruct `BeautifulSoup` to parse only those parts, dramatically reducing memory usage and parsing time.
