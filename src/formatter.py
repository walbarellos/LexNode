import json
import re
import textwrap

try:
    from src.normalizer import ProcessoNormalizado
except ImportError:
    from normalizer import ProcessoNormalizado


class _Cor:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    MAGENTA = '\033[35m'
    BLUE = '\033[34m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    RED = '\033[31m'
    # Combinations
    BOLD_WHITE = '\033[1;97m'
    BOLD_CYAN = '\033[1;36m'
    BOLD_GREEN = '\033[1;32m'
    BOLD_YELLOW = '\033[1;33m'


def _remover_cores(texto: str) -> str:
    """Remove códigos ANSI de formatação do texto."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', texto)


def formatar_texto(processo: ProcessoNormalizado, colorido: bool = True) -> str:
    """
    Formata as informações de um processo de forma amigável para exibição no terminal.

    Args:
        processo: Objeto contendo os dados normalizados do processo.
        colorido: Se True, aplica cores ANSI. Se False, retorna texto simples.

    Returns:
        String formatada.
    """
    WIDTH = 67
    
    # Cores
    c_box = _Cor.DIM if colorido else ''
    c_num = _Cor.BOLD_CYAN if colorido else ''
    c_white = _Cor.BOLD_WHITE if colorido else ''
    c_gray = _Cor.GRAY if colorido else ''
    c_yellow = _Cor.BOLD_YELLOW if colorido else ''
    c_cyan = _Cor.CYAN if colorido else ''
    c_green = _Cor.GREEN if colorido else ''
    c_reset = _Cor.RESET if colorido else ''
    
    # Status cor
    situacao = processo.situacao or 'Desconhecida'
    situacao_lower = situacao.lower()
    if 'baixado' in situacao_lower or 'ativo' in situacao_lower or 'andamento' in situacao_lower:
        c_status = _Cor.BOLD_GREEN if colorido else ''
    elif 'suspenso' in situacao_lower or 'pendente' in situacao_lower:
        c_status = _Cor.BOLD_YELLOW if colorido else ''
    elif 'urgente' in situacao_lower or 'sigilo' in situacao_lower:
        c_status = _Cor.RED if colorido else ''
    else:
        c_status = _Cor.BOLD_WHITE if colorido else ''
        
    linhas = []
    
    # Cabeçalho (Caixa)
    linhas.append(f"{c_box}┌{'─' * 65}┐{c_reset}")
    
    # Número do processo
    numero = processo.numero_processo or 'Número não informado'
    pad_num = 65 - len(numero) - 2
    linhas.append(f"{c_box}│{c_reset}  {c_num}{numero}{c_reset}{' ' * pad_num}{c_box}│{c_reset}")
    
    # Classe, Vara, Foro
    partes_header = []
    if processo.classe: partes_header.append(processo.classe)
    if processo.vara: partes_header.append(processo.vara)
    if processo.foro: partes_header.append(processo.foro)
    header_text = ' · '.join(partes_header)
    
    if len(header_text) > 63:
        header_text = header_text[:60] + '...'
    pad_header = 65 - len(header_text) - 2
    linhas.append(f"{c_box}│{c_reset}  {c_white}{header_text}{c_reset}{' ' * pad_header}{c_box}│{c_reset}")
    
    # Situação
    sit_text = f"● {situacao}"
    pad_sit = 65 - len(sit_text) - 2
    linhas.append(f"{c_box}│{c_reset}  {c_status}{sit_text}{c_reset}{' ' * pad_sit}{c_box}│{c_reset}")
    
    linhas.append(f"{c_box}└{'─' * 65}┘{c_reset}")
    linhas.append("")
    
    # Campos detalhados
    def add_campo(label: str, valor: str):
        if valor:
            linhas.append(f"  {c_cyan}{label:<16}{c_reset}{c_green}{valor}{c_reset}")
            
    add_campo('Juiz', processo.juiz)
    add_campo('Área', processo.area)
    add_campo('Assunto', processo.assunto)
    add_campo('Valor', processo.valor_acao)
    add_campo('Distribuição', processo.distribuicao)
    add_campo('Controle', processo.numero_controle)
    
    linhas.append("")
    
    # Partes
    linhas.append(f" {c_box}───{c_reset} {c_yellow}PARTES{c_reset} {c_box}{'─' * 53}{c_reset}")
    linhas.append("")
    
    if not processo.partes:
        linhas.append(f"  {c_gray}(nenhuma parte encontrada){c_reset}")
    else:
        # Agrupa os advogados se for possível. Por enquanto, imprimimos o tipo e nome.
        # Caso seja advogado e queiramos o "└", poderíamos tratar.
        # Mas vamos exibir como "Tipo: Nome". Se o tipo contiver 'Advogad', indentamos
        for p in processo.partes:
            tipo = p.tipo or 'Parte'
            nome = p.nome or 'Nome não informado'
            
            if 'advogad' in tipo.lower() or 'defensor' in tipo.lower():
                linhas.append(f"                  {c_box}└{c_reset} {c_gray}{tipo}:{c_reset} {c_gray}{nome}{c_reset}")
            else:
                linhas.append(f"  {c_cyan}{tipo:<16}{c_reset}{c_white}{nome}{c_reset}")
                
    linhas.append("")
    
    # Movimentações
    linhas.append(f" {c_box}───{c_reset} {c_yellow}MOVIMENTAÇÕES{c_reset} {c_box}{'─' * 46}{c_reset}")
    linhas.append("")
    
    if not processo.movimentacoes:
        linhas.append(f"  {c_gray}(nenhuma movimentação encontrada){c_reset}")
    else:
        for m in processo.movimentacoes:
            data = m.data or ''
            descricao = m.descricao or ''
            
            linhas.append(f"  {c_cyan}{data:<16}{c_reset}{c_white}{descricao.split('\\n')[0]}{c_reset}")
            # Se houver mais texto na descrição, exibe em cinza e alinhado
            resto = '\\n'.join(descricao.split('\\n')[1:]).strip()
            if not resto and len(descricao) > 60:
                # Opcional: fazer o wrapping
                pass
            if resto:
                wrapped_linhas = textwrap.wrap(resto, width=47)
                for wl in wrapped_linhas:
                    linhas.append(f"                  {c_gray}{wl}{c_reset}")
                    
            linhas.append("")
            
    linhas.append(f" {c_box}{'─' * 64}{c_reset}")
    
    resultado = '\n'.join(linhas)
    if not colorido:
        resultado = _remover_cores(resultado)
        
    return resultado


def formatar_json(processo: ProcessoNormalizado, indent: int = 2) -> str:
    """
    Formata o processo como JSON.

    Args:
        processo: Objeto ProcessoNormalizado.
        indent: Nível de indentação do JSON.

    Returns:
        String JSON.
    """
    return json.dumps(processo.to_dict(), indent=indent, ensure_ascii=False)

def formatar_resumos_processos(resumos, colorido: bool = True) -> str:
    """Formata a lista de resultados da busca por nome de forma estruturada."""
    if not resumos:
        texto = "  (nenhum processo encontrado)\n"
        return texto if colorido else _remover_cores(texto)
        
    linhas = []
    linhas.append(f"\n  Processos encontrados ({len(resumos)}):\n")
    
    for i, p in enumerate(resumos, 1):
        if colorido:
            num = f"{_Cor.BOLD_CYAN}{p.numero}{_Cor.RESET}"
            cls_assunto = f"{_Cor.BOLD}{p.classe}{_Cor.RESET} · {_Cor.DIM}{p.assunto}{_Cor.RESET}"
            papel = f"{_Cor.CYAN}{p.participacao}:{_Cor.RESET} {p.nome_parte}"
            local = f"{_Cor.GREEN}{p.data_local}{_Cor.RESET}"
        else:
            num = p.numero
            cls_assunto = f"{p.classe} · {p.assunto}"
            papel = f"{p.participacao}: {p.nome_parte}"
            local = p.data_local
            
        linhas.append(f"    {i}.  {num}")
        linhas.append(f"        {cls_assunto}")
        linhas.append(f"        {papel}")
        linhas.append(f"        {local}\n")
        
    return "\n".join(linhas) + "\n"
