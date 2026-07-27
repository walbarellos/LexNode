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
    extrair_resumos_pesquisa,
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
        "--foro",
        default="0001",
        help="Código do foro/comarca para busca por nome (padrão: 0001 = Rio Branco)",
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

    if not args.processo and not args.nome:
        parser.print_help()
        sys.exit(1)

    if not args.json:
        print()
        print("  ProcessoLivreAC — Consulta pública de processos")
        print("  TJAC · 1º Grau · e-SAJ")
        print()

    crawler = BaseCrawler()

    try:
        if args.nome:
            if not args.json:
                print(f"Consultando por nome: {args.nome}...\n")
            
            params = {
                'conversationId': '',
                'cbPesquisa': 'NMPARTE',
                'dadosConsulta.tipoNuProcesso': 'UNIFICADO',
                'dadosConsulta.valorConsulta': args.nome,
                'cdForo': args.foro,
                'numeroDigitoAnoUnificado': '',
                'foroNumeroUnificado': '',
                'dadosConsulta.valorConsultaNuUnificado': '',
            }
            
            # Use crawler session to respect user-agent and potential future session handling
            crawler.iniciar_sessao()
            resp = crawler._session.get("https://esaj.tjac.jus.br/cpopg/search.do", params=params, timeout=15)
            resp.raise_for_status()
            
            texto_lower = resp.text.lower()
            if "muitos processos" in texto_lower or "refine sua busca" in texto_lower:
                print_warn("Foram encontrados muitos processos. Refine sua busca ou especifique o foro.")
                sys.exit(0)
            elif "não existem informações disponíveis" in texto_lower:
                print_warn("Não existem informações disponíveis para este nome/foro (nada encontrado).")
                sys.exit(0)
                
            resumos = extrair_resumos_pesquisa(resp.text)
            
            if not resumos:
                print_warn("Nenhum processo encontrado com este nome/foro.")
                sys.exit(0)
            
            if args.html:
                from src.html_generator import gerar_html_lista_busca, gerar_html_processo
                
                if args.detalhar:
                    print(f"Baixando detalhes de {len(resumos)} processos...")
                    for r in resumos:
                        try:
                            # Tentar não sobrecarregar o tribunal
                            time.sleep(1)
                            resp_proc = crawler.consultar_processo_1grau(r.numero)
                            proc_norm = normalizar_html_1grau(r.numero, resp_proc.html)
                            html_proc = gerar_html_processo(proc_norm)
                            
                            num_sanitizado = r.numero.replace(".", "_").replace("-", "_").replace("/", "_")
                            saida_dir = Path("saida")
                            saida_dir.mkdir(exist_ok=True)
                            (saida_dir / f"{num_sanitizado}.html").write_text(html_proc, encoding="utf-8")
                        except Exception as e:
                            print_warn(f"Erro ao baixar detalhes de {r.numero}: {e}")
                            
                saida_html = gerar_html_lista_busca(args.nome, resumos, link_local=args.detalhar)
                nome_arq = re.sub(r"[^a-zA-Z0-9]", "_", args.nome)[:50]
                saida_dir = Path("saida")
                saida_dir.mkdir(exist_ok=True)
                arquivo_saida = saida_dir / f"busca_{nome_arq}.html"
                arquivo_saida.write_text(saida_html, encoding="utf-8")
                print_succ(f"HTML gerado com sucesso em {arquivo_saida}")
                if args.detalhar:
                    print_succ("Detalhes de todos os processos também foram salvos como HTML na pasta 'saida/'.")
            elif args.json:
                saida = json.dumps({"nome": args.nome, "processos": [r.__dict__ for r in resumos]}, ensure_ascii=False, indent=2)
                print(saida)
            else:
                saida = formatar_resumos_processos(resumos, use_colors)
                print(saida)
                if not args.detalhar:
                    print("\n💡 Dica: Para ver o andamento e as partes completas de um processo, execute:")
                    print(f"   python consultar.py {resumos[0].numero} --html")
                
            if args.salvar and not args.html:
                nome_arq = re.sub(r"[^a-zA-Z0-9]", "_", args.nome)[:50]
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
