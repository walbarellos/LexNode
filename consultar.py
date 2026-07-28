#!/usr/bin/env python3
"""
consultar.py — ProcessoLivreAC

Consulta processos públicos do 1º grau no e-SAJ do TJAC e exibe os
resultados de forma organizada no terminal.

Uso:
    python consultar.py <numero-processo>
    python consultar.py --nome <nome-da-parte> [--foro <codigo-foro>]
    python consultar.py <numero-processo> --json
    python consultar.py <numero-processo> --salvar
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

from src.base_crawler import (
    BaseCrawler,
    ConsultaFalhouError,
    ProcessoNaoEncontradoError,
)
from src.normalizer import (
    ProcessoNormalizado,
    ProcessoSigilosoError,
    normalizar_html_1grau,
    normalizar_html_2grau,
    extrair_resumos_pesquisa,
    extrair_resumos_pesquisa_2grau,
)
from src.formatter import formatar_texto, formatar_json, formatar_resumos_processos

def main():
    parser = argparse.ArgumentParser(
        description="ProcessoLivreAC — Consulta pública de processos (TJAC · 1º Grau · e-SAJ)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python consultar.py 0800224-44.2013.8.01.0001
  python consultar.py --nome "Ministério Público" --foro 0001
  python consultar.py 0800224-44.2013.8.01.0001 --json
  python consultar.py 0800224-44.2013.8.01.0001 --salvar
  python consultar.py 0800224-44.2013.8.01.0001 --sem-cor
"""
    )
    parser.add_argument(
        "processo",
        nargs="?",
        help="Número do processo (formato CNJ) para consultar",
    )
    parser.add_argument(
        "--nome",
        help="Nome da parte para buscar (retorna lista de processos)",
    )
    parser.add_argument(
        "--doc",
        help="CPF ou CNPJ da parte para buscar (apenas números ou com máscara)",
    )
    parser.add_argument(
        "--juris",
        help="Termo para busca livre em Jurisprudência (acórdãos do 2º Grau)",
    )
    parser.add_argument(
        "--foro",
        default="-1",
        help="Código do foro/comarca para busca por nome/doc (padrão: -1 = Todos os foros do Estado)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime o resultado em formato JSON em vez de texto",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Salva e gera o resultado em uma página HTML estilo JusBrasil",
    )
    parser.add_argument(
        "--detalhar",
        action="store_true",
        help="Ao buscar por nome, baixa também os detalhes de todos os processos encontrados",
    )
    parser.add_argument(
        "--salvar",
        action="store_true",
        help="Salva o resultado em um arquivo na pasta 'saida'",
    )
    parser.add_argument(
        "--sem-cor",
        action="store_true",
        help="Desativa a formatação com cores no terminal",
    )
    parser.add_argument(
        "--grau",
        type=int,
        choices=[1, 2],
        default=1,
        help="Grau de jurisdição: 1 = 1º Grau (cpopg, padrão), 2 = 2º Grau (cposg5, Tribunal)",
    )

    args = parser.parse_args()

    use_colors = not args.sem_cor and sys.stdout.isatty()

    def print_err(msg):
        if use_colors:
            print(f"\033[31m✗ {msg}\033[0m", file=sys.stderr)
        else:
            print(f"✗ {msg}", file=sys.stderr)

    def print_warn(msg):
        if use_colors:
            print(f"\033[33m⚠ {msg}\033[0m", file=sys.stderr)
        else:
            print(f"⚠ {msg}", file=sys.stderr)
            
    def print_succ(msg):
        if use_colors:
            print(f"\033[32m✓ {msg}\033[0m", file=sys.stderr)
        else:
            print(f"✓ {msg}", file=sys.stderr)

    if not args.processo and not args.nome and not args.doc and not args.juris:
        parser.print_help()
        sys.exit(1)

    if not args.json:
        grau_label = "2º Grau (Tribunal)" if args.grau == 2 else "1º Grau"
        print()
        print("  ProcessoLivreAC — Consulta pública de processos")
        print(f"  TJAC · {grau_label} · e-SAJ")
        print()

    crawler = BaseCrawler()

    try:
        if args.juris:
            from src.crawler_jurisprudencia import CrawlerJurisprudencia
            cj = CrawlerJurisprudencia()
            if not args.json:
                print(f"Consultando jurisprudência por: '{args.juris}'...\n")
            
            resumos = cj.buscar_jurisprudencia(args.juris)
            
            if not resumos:
                print_warn("Nenhuma jurisprudência encontrada para este termo.")
                sys.exit(0)
                
            if args.json:
                saida = json.dumps({"termo": args.juris, "jurisprudencia": resumos}, ensure_ascii=False, indent=2)
                print(saida)
            elif args.html:
                # Basic HTML for jurisprudence
                linhas_html = []
                for r in resumos:
                    linhas_html.append(f'''
                    <div style="border-bottom: 1px solid #ccc; padding: 15px 0;">
                        <h3><a href="https://esaj.tjac.jus.br/cjsg/resultadoCompleta.do" target="_blank">{r['numero']}</a></h3>
                        <p><strong>Relator:</strong> {r['relator']} | <strong>Órgão:</strong> {r['orgao']} | <strong>Data:</strong> {r['data']}</p>
                        <p style="color: #555;">{r['ementa'].replace(chr(10), '<br>')}</p>
                    </div>''')
                html = f"<html><body style='font-family:sans-serif; max-width:800px; margin:0 auto; padding:20px;'><h2>Jurisprudência: {args.juris}</h2>{''.join(linhas_html)}</body></html>"
                nome_arq = re.sub(r"[^a-zA-Z0-9]", "_", args.juris)[:50]
                saida_dir = Path("saida")
                saida_dir.mkdir(exist_ok=True)
                arquivo_saida = saida_dir / f"juris_{nome_arq}.html"
                arquivo_saida.write_text(html, encoding="utf-8")
                print_succ(f"HTML de jurisprudência gerado em {arquivo_saida}")
            else:
                use_c = "\033[1;36m" if use_colors else ""
                end_c = "\033[0m" if use_colors else ""
                print(f"  Decisões encontradas ({len(resumos)}):")
                for i, r in enumerate(resumos, 1):
                    print(f"\n    {i}.  {use_c}{r['numero']}{end_c}")
                    print(f"        Relator(a): {r['relator']} · Julgamento: {r['data']} · {r['orgao']}")
                    em_curta = r['ementa'][:300].replace(chr(10), ' ') + ('...' if len(r['ementa'])>300 else '')
                    print(f"        Ementa: {em_curta}")
            
            if args.salvar and not args.html:
                nome_arq = re.sub(r"[^a-zA-Z0-9]", "_", args.juris)[:50]
                ext = "json" if args.json else "txt"
                saida_dir = Path("saida")
                saida_dir.mkdir(exist_ok=True)
                arquivo_saida = saida_dir / f"juris_{nome_arq}.{ext}"
                arquivo_saida.write_text(saida if args.json else json.dumps(resumos, ensure_ascii=False, indent=2), encoding="utf-8")
                if not args.json: print_succ(f"Salvo em {arquivo_saida}")
                
            sys.exit(0)

        elif args.nome or args.doc:
            termo_busca = args.nome or args.doc
            tipo_pesquisa = 'NMPARTE' if args.nome else 'DOCPARTE'
            
            if args.doc:
                # Sanitiza CPF/CNPJ mantendo apenas números
                termo_busca = re.sub(r'[^0-9]', '', termo_busca)
                
            if not args.json:
                tipo_lbl = "nome" if args.nome else "documento"
                print(f"Consultando por {tipo_lbl}: {termo_busca}...\n")
            
            resumos = []
            for g in [1, 2]:
                if not args.json:
                    print(f"  Buscando no {g}º Grau...")
                
                if g == 2:
                    params = {
                        'conversationId': '',
                        'paginaConsulta': '0',
                        'cbPesquisa': tipo_pesquisa,
                        'tipoNuProcesso': 'UNIFICADO',
                        'dePesquisa': termo_busca,
                        'dePesquisaNuUnificado': '',
                        'numeroDigitoAnoUnificado': '',
                        'foroNumeroUnificado': '',
                    }
                    search_url = "https://esaj.tjac.jus.br/cposg5/search.do"
                    crawler.iniciar_sessao(grau=2)
                else:
                    params = {
                        'conversationId': '',
                        'cbPesquisa': tipo_pesquisa,
                        'dadosConsulta.tipoNuProcesso': 'UNIFICADO',
                        'dadosConsulta.valorConsulta': termo_busca,
                        'cdForo': args.foro,
                        'numeroDigitoAnoUnificado': '',
                        'foroNumeroUnificado': '',
                        'dadosConsulta.valorConsultaNuUnificado': '',
                    }
                    search_url = "https://esaj.tjac.jus.br/cpopg/search.do"
                    crawler.iniciar_sessao()
                
                # Use crawler session to respect user-agent and potential future session handling
                resp = crawler._session.get(search_url, params=params, timeout=15)
                resp.raise_for_status()
                
                texto_lower = resp.text.lower()
                if "muitos processos" in texto_lower or "refine sua busca" in texto_lower:
                    if not args.json: print_warn(f"Muitos processos no {g}º Grau. Refine a busca.")
                    continue
                elif "não existem informações disponíveis" in texto_lower:
                    continue
                    
                novos_resumos = extrair_resumos_pesquisa_2grau(resp.text) if g == 2 else extrair_resumos_pesquisa(resp.text)
                if novos_resumos:
                    resumos.extend(novos_resumos)
            
            if not resumos:
                print_warn("Nenhum processo encontrado com este nome/documento em nenhum dos graus.")
                sys.exit(0)
            
            if args.html:
                from src.html_generator import gerar_html_lista_busca, gerar_html_processo
                
                if args.detalhar:
                    print(f"Baixando detalhes de {len(resumos)} processos...")
                    for r in resumos:
                        try:
                            # Tentar não sobrecarregar o tribunal
                            time.sleep(1)
                            try:
                                resp_proc = crawler.consultar_processo_1grau(r.numero)
                                proc_norm = normalizar_html_1grau(r.numero, resp_proc.html)
                            except ProcessoNaoEncontradoError:
                                resp_proc = crawler.consultar_processo_2grau(r.numero)
                                proc_norm = normalizar_html_2grau(r.numero, resp_proc.html)
                            html_proc = gerar_html_processo(proc_norm)
                            
                            num_sanitizado = r.numero.replace(".", "_").replace("-", "_").replace("/", "_")
                            saida_dir = Path("saida")
                            saida_dir.mkdir(exist_ok=True)
                            (saida_dir / f"{num_sanitizado}.html").write_text(html_proc, encoding="utf-8")
                        except Exception as e:
                            print_warn(f"Erro ao baixar detalhes de {r.numero}: {e}")
                            
                saida_html = gerar_html_lista_busca(termo_busca, resumos, link_local=args.detalhar)
                nome_arq = re.sub(r"[^a-zA-Z0-9]", "_", termo_busca)[:50]
                saida_dir = Path("saida")
                saida_dir.mkdir(exist_ok=True)
                arquivo_saida = saida_dir / f"busca_{nome_arq}.html"
                arquivo_saida.write_text(saida_html, encoding="utf-8")
                print_succ(f"HTML gerado com sucesso em {arquivo_saida}")
                if args.detalhar:
                    print_succ("Detalhes de todos os processos também foram salvos como HTML na pasta 'saida/'.")
            elif args.json:
                chave_json = "nome" if args.nome else "documento"
                saida = json.dumps({chave_json: termo_busca, "processos": [r.__dict__ for r in resumos]}, ensure_ascii=False, indent=2)
                print(saida)
            else:
                saida = formatar_resumos_processos(resumos, use_colors)
                print(saida)
                if not args.detalhar:
                    print("\n💡 Dica: Para ver o andamento e as partes completas de um processo, execute:")
                    print(f"   python consultar.py {resumos[0].numero} --html")
                
            if args.salvar and not args.html:
                nome_arq = re.sub(r"[^a-zA-Z0-9]", "_", termo_busca)[:50]
                ext = "json" if args.json else "txt"
                saida_dir = Path("saida")
                saida_dir.mkdir(exist_ok=True)
                arquivo_saida = saida_dir / f"busca_{nome_arq}.{ext}"
                arquivo_saida.write_text(saida, encoding="utf-8")
                if not args.json:
                    print()
                    print_succ(f"Resultado salvo em {arquivo_saida}")
                
        elif args.processo:
            if not args.json:
                print("Consultando...")
                
            if args.grau == 2:
                resposta = crawler.consultar_processo_2grau(args.processo)
                processo_normalizado = normalizar_html_2grau(args.processo, resposta.html)
            else:
                resposta = crawler.consultar_processo_1grau(args.processo)
                processo_normalizado = normalizar_html_1grau(args.processo, resposta.html)
            
            if args.html:
                from src.html_generator import gerar_html_processo
                saida_html = gerar_html_processo(processo_normalizado)
                numero_sanitizado = args.processo.replace(".", "_").replace("-", "_").replace("/", "_")
                saida_dir = Path("saida")
                saida_dir.mkdir(exist_ok=True)
                arquivo_saida = saida_dir / f"{numero_sanitizado}.html"
                arquivo_saida.write_text(saida_html, encoding="utf-8")
                print_succ(f"HTML gerado com sucesso em {arquivo_saida}")
            elif args.json:
                saida = formatar_json(processo_normalizado)
                print(saida)
            else:
                saida = formatar_texto(processo_normalizado, use_colors)
                print(saida)
                
            if args.salvar and not args.html:
                numero_sanitizado = args.processo.replace(".", "_").replace("-", "_").replace("/", "_")
                ext = "json" if args.json else "txt"
                saida_dir = Path("saida")
                saida_dir.mkdir(exist_ok=True)
                arquivo_saida = saida_dir / f"{numero_sanitizado}.{ext}"
                arquivo_saida.write_text(saida, encoding="utf-8")
                if not args.json:
                    print()
                    print_succ(f"Resultado salvo em {arquivo_saida}")

    except ProcessoNaoEncontradoError:
        print_err("Processo não encontrado no e-SAJ.")
        sys.exit(1)
    except ProcessoSigilosoError:
        print_err("Processo sob segredo de justiça. Não é possível exibir.")
        sys.exit(1)
    except ConsultaFalhouError:
        print_err("Falha na consulta. Verifique sua conexão ou tente novamente.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário.", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print_err(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
