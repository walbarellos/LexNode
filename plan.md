1. **Optimize `_iniciar_sessao` in `src/crawler_trf1.py`**:
   - The method parses the entire HTML to find the `javax.faces.ViewState` input field using BeautifulSoup. Since we only need an `input` tag with a specific name, using `SoupStrainer("input", {"name": "javax.faces.ViewState"})` will dramatically speed up parsing of large pages.

2. **Optimize `_parsear_resultados` in `src/crawler_trf1.py`**:
   - The method looks for a `table` with id `fPP:processosTable`. Since the HTML snippet returned from the AJAX response might be large, parsing only this table with `SoupStrainer("table", id="fPP:processosTable")` will improve performance.

3. **Verify tests and linting**:
   - Ensure `pnpm test` / `pnpm lint` or equivalent Python test/linting (`pytest` and `ruff`) runs and passes before pushing the changes. I will measure the impact and document it in the `.jules/bolt.md` journal.

4. **Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.**
   - Run the necessary pre commit instructions tools.

5. **Submit the PR**:
   - Commit and submit with the title format `⚡ Bolt: [performance improvement]`.
