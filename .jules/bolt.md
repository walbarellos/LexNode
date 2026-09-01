## 2024-05-18 - BeautifulSoup nested search optimization
**Learning:** In BeautifulSoup, using a nested `find_all` loops (e.g., finding `tr` then finding text inside each `tr`) is significantly slower than searching the entire document directly and navigating from the found node up (`find_parent`). The nested loop for parsing search results in `crawler_jurisprudencia.py` was O(n).
**Action:** Always prefer single document-wide queries or targeted selector queries over manual subtree traversal loops in BeautifulSoup parsing.
