#!/usr/bin/env python3
"""
inspecionar_html.py — ProcessoLivreAC

Script de inspeção manual para rodar LOCALMENTE na máquina com acesso
ao e-SAJ. Não faz parte do crawler em si — é uma ferramenta de
calibração para validar a estrutura real do HTML antes de implementar
os parsers.

Uso:
    # 1. Só inspecionar o formulário (nomes dos campos):
    python scripts/inspecionar_html.py --formulario

    # 2. Consultar um processo real e salvar o HTML:
    python scripts/inspecionar_html.py --processo "0700616-57.2024.8.01.0001"

    # 3. Analisar um HTML já salvo:
    python scripts/inspecionar_html.py --analisar saida/0700616-57_2024_8_01_0001.html

IMPORTANTE: Use apenas números de processos PÚBLICOS para teste.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ESAJ_BASE = "https://esaj.tjac.jus.br"
CPOPG_OPEN = f"{ESAJ_BASE}/cpopg/open.do"
CPOPG_SEARCH = f"{ESAJ_BASE}/cpopg/search.do"  # action real do form

USER_AGENT = (
    "ProcessoLivreAC/0.1-inspecao "
    "(script de calibracao manual; projeto civico sem fins lucrativos)"
)

SAIDA_DIR = Path(__file__).resolve().parent.parent / "saida"

# Marcadores de sigilo — mesmos do normalizer.py, replicados aqui pra
# este script ser independente
MARCADORES_SIGILO = (
    "segredo de justiça",
    "sigilo",
    "processo em segredo",
    "restrito",
    "acesso restrito",
)


def criar_sessao() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


# ---------------------------------------------------------------------------
# 1. Inspecionar formulário
# ---------------------------------------------------------------------------
def inspecionar_formulario(sessao: requests.Session) -> None:
    """Busca a página do formulário cpopg e lista todos os <input>/<select>."""
    print(f"\n{'='*60}")
    print(f"Buscando formulário: {CPOPG_OPEN}")
    print(f"{'='*60}\n")

    resp = sessao.get(CPOPG_OPEN, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Procurar todos os forms
    forms = soup.find_all("form")
    print(f"Total de <form> encontrados: {len(forms)}\n")

    for i, form in enumerate(forms):
        action = form.get("action", "(sem action)")
        method = form.get("method", "(sem method)")
        form_id = form.get("id", "(sem id)")
        print(f"--- Form #{i+1}: id={form_id}, action={action}, method={method} ---")

        # Inputs
        for inp in form.find_all("input"):
            inp_name = inp.get("name", "(sem name)")
            inp_type = inp.get("type", "text")
            inp_value = inp.get("value", "")
            inp_id = inp.get("id", "")
            print(f"  <input> name={inp_name!r}  type={inp_type!r}  "
                  f"id={inp_id!r}  value={inp_value!r}")

        # Selects
        for sel in form.find_all("select"):
            sel_name = sel.get("name", "(sem name)")
            sel_id = sel.get("id", "")
            options = sel.find_all("option")
            opt_preview = [
                f"{o.get('value','')}: {o.get_text(strip=True)}"
                for o in options[:5]
            ]
            print(f"  <select> name={sel_name!r}  id={sel_id!r}  "
                  f"options({len(options)}): {opt_preview}")

        print()

    # Salvar HTML do formulário pra referência
    form_path = SAIDA_DIR / "formulario_cpopg.html"
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    form_path.write_text(resp.text, encoding="utf-8")
    print(f"HTML do formulário salvo em: {form_path}")


# ---------------------------------------------------------------------------
# 2. Buscar por nome da parte
# ---------------------------------------------------------------------------
def buscar_por_nome(sessao: requests.Session, nome: str, foro: str = "0001") -> Path:
    """
    Busca processos por nome da parte e lista os resultados.
    Útil para encontrar números de processo reais para inspeção.

    O e-SAJ exige um foro/comarca para buscas por nome — sem ele,
    retorna 'muitos processos encontrados' e não lista nenhum.
    Foro padrão: 0001 = Rio Branco (capital).
    """
    params = {
        "conversationId": "",
        "cbPesquisa": "NMPARTE",
        "dadosConsulta.tipoNuProcesso": "UNIFICADO",
        "dadosConsulta.valorConsulta": nome,
        "cdForo": foro,
        "numeroDigitoAnoUnificado": "",
        "foroNumeroUnificado": "",
        "dadosConsulta.valorConsultaNuUnificado": "",
    }

    print(f"\n{'='*60}")
    print(f"Buscando por nome: {nome}  (foro: {foro})")
    print(f"{'='*60}\n")

    time.sleep(3)  # rate-limit
    resp = sessao.get(CPOPG_SEARCH, params=params, timeout=15)
    print(f"  Status: {resp.status_code}")
    print(f"  URL final: {resp.url}")
    print(f"  Tamanho HTML: {len(resp.text)} chars\n")

    # Salvar HTML da lista de resultados
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    nome_arquivo = re.sub(r"[^a-zA-Z0-9]", "_", nome)[:50]
    saida_path = SAIDA_DIR / f"busca_nome_{nome_arquivo}.html"
    saida_path.write_text(resp.text, encoding="utf-8")
    print(f"✓ HTML salvo em: {saida_path}\n")

    # Tentar extrair números de processo da lista de resultados
    soup = BeautifulSoup(resp.text, "html.parser")

    # Procurar links que pareçam números de processo CNJ
    cnj_pattern = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
    processos_encontrados = set()

    # Buscar em todo o texto da página
    for texto in soup.stripped_strings:
        matches = cnj_pattern.findall(texto)
        processos_encontrados.update(matches)

    # Buscar também em atributos href e value
    for tag in soup.find_all(["a", "input"]):
        for attr in ["href", "value", "title"]:
            val = tag.get(attr, "")
            matches = cnj_pattern.findall(str(val))
            processos_encontrados.update(matches)

    if processos_encontrados:
        print(f"📋 Processos encontrados ({len(processos_encontrados)}):")
        for i, num in enumerate(sorted(processos_encontrados), 1):
            print(f"  {i}. {num}")
        print(f"\n💡 Para inspecionar um deles:")
        primeiro = sorted(processos_encontrados)[0]
        print(f'   python scripts/inspecionar_html.py --processo "{primeiro}"')
    else:
        print("⚠️  Nenhum número de processo encontrado na resposta.")
        print("   Pode ser que a busca não retornou resultados,")
        print("   ou que o formato da lista é diferente do esperado.")
        print("   Verifique o HTML salvo manualmente.")

    # Verificar mensagens do e-SAJ
    texto_lower = resp.text.lower()
    if "não existem informações disponíveis" in texto_lower:
        print("\n⚠️  O e-SAJ retornou 'Não existem informações disponíveis'.")
    if "muitos processos" in texto_lower or "refine sua busca" in texto_lower:
        print("\n⚠️  O e-SAJ pediu para refinar a busca (muitos resultados).")
        print("   Tente um nome mais específico ou um foro diferente.")
        print("   Ex: --nome 'Fulano de Tal' --foro 0001")

    return saida_path


# ---------------------------------------------------------------------------
# 3. Consultar processo por número
# ---------------------------------------------------------------------------
def consultar_processo(sessao: requests.Session, numero: str, force_salvar: bool = False) -> Path:
    """
    Consulta um processo por número e salva o HTML cru em arquivo.

    Parâmetros de formulário CONFIRMADOS manualmente em 2026-07-27
    contra esaj.tjac.jus.br/cpopg/open.do (form#formConsulta).
    """
    # Extrair partes do número CNJ: NNNNNNN-DD.AAAA.J.TT.OOOO
    limpo = re.sub(r"[^0-9]", "", numero)

    if len(limpo) < 20:
        print(f"⚠️  Número de processo inválido (menos de 20 dígitos): {numero}")
        sys.exit(1)

    # Formato confirmado: NNNNNNN-DD.AAAA para numeroDigitoAnoUnificado
    digito_ano = f"{limpo[:7]}-{limpo[7:9]}.{limpo[9:13]}"
    foro = limpo[16:20]

    params = {
        "conversationId": "",
        "cbPesquisa": "NUMPROC",
        "dadosConsulta.tipoNuProcesso": "UNIFICADO",
        "numeroDigitoAnoUnificado": digito_ano,
        "foroNumeroUnificado": foro,
        "dadosConsulta.valorConsultaNuUnificado": numero,
        "dadosConsulta.valorConsulta": "",
    }

    print(f"\n{'='*60}")
    print(f"Consultando processo: {numero}")
    print(f"{'='*60}\n")

    # Parâmetros confirmados via formulário real
    print("Enviando consulta...")
    print(f"  Params: {params}\n")

    time.sleep(3)  # rate-limit
    resp = sessao.get(CPOPG_SEARCH, params=params, timeout=15)
    print(f"  Status: {resp.status_code}")
    print(f"  URL final: {resp.url}")
    print(f"  Tamanho HTML: {len(resp.text)} chars\n")

    # Verificar sigilo ANTES de salvar — análise DOM-aware
    # Remove elementos de UI (formulários, menus) que contêm 'segredo de
    # justiça' como label de dropdown, evitando falsos positivos.
    if not force_salvar:
        from copy import copy
        soup_check = BeautifulSoup(resp.text, "html.parser")
        for tag in soup_check.find_all(
            ["form", "select", "option", "nav", "aside",
             "header", "footer", "script", "style", "noscript"]
        ):
            tag.decompose()
        texto_conteudo = soup_check.get_text().lower()
        for marcador in MARCADORES_SIGILO:
            if marcador in texto_conteudo:
                print(f"⚠️  ATENÇÃO: Marcador de sigilo detectado ('{marcador}')!")
                print("   O HTML NÃO será salvo. Use outro número de processo.")
                print("   (Use --force-salvar para ignorar esta verificação.)")
                sys.exit(1)
    else:
        print("⚠️  --force-salvar ativo: verificação de sigilo IGNORADA.")
        print("   ATENÇÃO: confira manualmente se o processo é público!")

    # Salvar
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    nome_arquivo = numero.replace(".", "_").replace("-", "_").replace("/", "_")
    saida_path = SAIDA_DIR / f"{nome_arquivo}.html"
    saida_path.write_text(resp.text, encoding="utf-8")
    print(f"✓ HTML salvo em: {saida_path}")
    print(f"  Tamanho: {saida_path.stat().st_size:,} bytes")

    return saida_path


# ---------------------------------------------------------------------------
# 3. Analisar HTML salvo
# ---------------------------------------------------------------------------
def analisar_html(caminho: Path) -> None:
    """
    Analisa um HTML salvo e extrai IDs, classes, e estrutura relevante
    para calibrar o normalizer.py.
    """
    print(f"\n{'='*60}")
    print(f"Analisando: {caminho}")
    print(f"{'='*60}\n")

    html = caminho.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # IDs que esperamos encontrar (do normalizer.py)
    ids_esperados = [
        "classeProcesso",
        "assuntoProcesso",
        "varaProcesso",
        "tablePartesPrincipais",
        "tabelaTodasMovimentacoes",
    ]

    print("--- IDs esperados pelo normalizer.py ---")
    for eid in ids_esperados:
        el = soup.find(id=eid)
        if el:
            texto = el.get_text(strip=True)[:100]
            print(f"  ✓ #{eid} encontrado — tag: <{el.name}>, texto: {texto!r}")
        else:
            print(f"  ✗ #{eid} NÃO encontrado")

    # Listar TODOS os ids presentes pra descobrir os corretos
    print("\n--- Todos os IDs encontrados no HTML ---")
    todos_ids = []
    for el in soup.find_all(id=True):
        todos_ids.append((el.name, el["id"], el.get_text(strip=True)[:60]))

    todos_ids.sort(key=lambda x: x[1])
    for tag, eid, texto in todos_ids:
        print(f"  <{tag}> id={eid!r}  texto={texto!r}")

    # Listar classes únicas
    print(f"\n--- Classes CSS únicas (top 30) ---")
    classes = {}
    for el in soup.find_all(class_=True):
        for cls in el.get("class", []):
            classes[cls] = classes.get(cls, 0) + 1
    for cls, count in sorted(classes.items(), key=lambda x: -x[1])[:30]:
        print(f"  .{cls} ({count}x)")

    # Estrutura de tabelas
    print(f"\n--- Tabelas encontradas ---")
    for i, tabela in enumerate(soup.find_all("table")):
        tid = tabela.get("id", "(sem id)")
        tcls = " ".join(tabela.get("class", []))
        rows = len(tabela.find_all("tr"))
        print(f"  Tabela #{i+1}: id={tid!r} class={tcls!r} rows={rows}")

    # Verificar se há indicadores de "processo não encontrado"
    print(f"\n--- Verificações adicionais ---")
    texto_pagina = soup.get_text().lower()
    checks = [
        ("Processo não encontrado", "processo não encontrado" in texto_pagina),
        ("Captcha presente", "captcha" in texto_pagina or "recaptcha" in texto_pagina),
        ("Segredo de justiça", any(m in texto_pagina for m in MARCADORES_SIGILO)),
    ]
    for label, encontrado in checks:
        status = "⚠️  SIM" if encontrado else "✓ não"
        print(f"  {label}: {status}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspeção manual do e-SAJ para calibrar o ProcessoLivreAC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/inspecionar_html.py --formulario
  python scripts/inspecionar_html.py --nome "Francisca das Chagas Brito Gomes" --foro 0001
  python scripts/inspecionar_html.py --processo "0700616-57.2024.8.01.0001"
  python scripts/inspecionar_html.py --analisar saida/0700616_57_2024_8_01_0001.html
        """,
    )
    parser.add_argument(
        "--formulario",
        action="store_true",
        help="Busca o formulário cpopg e lista os campos",
    )
    parser.add_argument(
        "--nome",
        type=str,
        help="Nome da parte para buscar (retorna lista de processos)",
    )
    parser.add_argument(
        "--foro",
        type=str,
        default="0001",
        help="Código do foro/comarca (padrão: 0001 = Rio Branco)",
    )
    parser.add_argument(
        "--processo",
        type=str,
        help="Número do processo (formato CNJ) para consultar",
    )
    parser.add_argument(
        "--analisar",
        type=str,
        help="Caminho para um HTML já salvo para análise",
    )
    parser.add_argument(
        '--force-salvar',
        action='store_true',
        help='Ignora verificação de sigilo e salva o HTML (use com cuidado!)',
    )

    args = parser.parse_args()

    if not any([args.formulario, args.nome, args.processo, args.analisar]):
        parser.print_help()
        sys.exit(0)

    sessao = criar_sessao()

    if args.formulario:
        inspecionar_formulario(sessao)

    if args.nome:
        buscar_por_nome(sessao, args.nome, foro=args.foro)

    if args.processo:
        saida_path = consultar_processo(sessao, args.processo, force_salvar=args.force_salvar)
        print("\n📋 Rodando análise automática do HTML salvo...\n")
        analisar_html(saida_path)

    if args.analisar:
        analisar_html(Path(args.analisar))


if __name__ == "__main__":
    main()
