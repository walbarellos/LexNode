## 2024-10-25 - Removing useless BeautifulSoup parsing
**Learning:** Found an unnecessary `BeautifulSoup` parsing call in the `extrair_resumos_pesquisa_2grau` fallback path in `src/normalizer.py`. It parses the entire HTML string into a BeautifulSoup object, only to completely ignore it and use standard library `re.findall` on the raw `html` string.
**Action:** Remove unused variable and object creation to avoid the significant parsing overhead of `BeautifulSoup` when it's not even used.
