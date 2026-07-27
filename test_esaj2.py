import requests

s = requests.Session()
s.headers.update({"User-Agent": "ProcessoLivreAC/0.1 (projeto civico sem fins lucrativos; contato: <preencher-email>)"})

# 1. Access open.do to get session cookies
r1 = s.get("https://esaj.tjac.jus.br/cpopg/open.do", timeout=15)
print("open.do status:", r1.status_code)

# 2. Access search.do
params = {
    "conversationId": "",
    "cbPesquisa": "NUMPROC",
    "dadosConsulta.tipoNuProcesso": "UNIFICADO",
    "numeroDigitoAnoUnificado": "0800224-44.2013",
    "foroNumeroUnificado": "0001",
    "dadosConsulta.valorConsultaNuUnificado": "0800224-44.2013.8.01.0001",
    "dadosConsulta.valorConsulta": "",
}
r2 = s.get("https://esaj.tjac.jus.br/cpopg/search.do", params=params, timeout=15)
print("search.do status:", r2.status_code)
print("Captcha in search:", "g-recaptcha" in r2.text.lower() or "vc-captcha" in r2.text.lower())
