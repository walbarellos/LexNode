import re
from typing import List, Optional

try:
    from src.normalizer import ProcessoNormalizado, ResumoProcesso
except ImportError:
    from normalizer import ProcessoNormalizado, ResumoProcesso

def _gerar_estilo() -> str:
    return """
    :root {
        --primary-color: #1c3554;
        --primary-light: #e7eef5;
        --secondary-color: #f7f3ea;
        --text-main: #1b1916;
        --text-muted: #3e3a34;
        --border-color: #d4cbbd;
        --success-color: #14532d;
        --danger-color: #7f1d1d;
        --paper: #f3efe6;
        --sheet: #fffcf6;
        --serif: "Literata", Palatino, "Palatino Linotype", "Times New Roman", serif;
        --sans: "Source Sans 3", "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }

    body {
        margin: 0;
        background: var(--paper);
        color: var(--text-main);
        font-family: var(--sans);
        font-size: 1.0625rem;
        line-height: 1.55;
    }

    h1, h2, h3, h4 {
        font-family: var(--serif);
        font-weight: 650;
        color: var(--text-main);
        line-height: 1.25;
    }

    a { color: var(--primary-color); }
    a:hover { text-decoration-thickness: 2px; }

    :focus { outline: none; }
    :focus-visible {
        outline: 3px solid var(--primary-color);
        outline-offset: 3px;
    }

    .sr-only, .vh {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    .text-muted { color: var(--text-muted); }

    .header {
        background: var(--sheet);
        border-bottom: 3px solid var(--text-main);
        box-shadow: 0 1px 0 var(--text-main);
    }

    .container {
        max-width: 64rem;
        margin: 0 auto;
        padding: 0 1.25rem;
    }

    .header .container {
        display: flex;
        align-items: center;
        min-height: 4.25rem;
    }

    .brand {
        font-family: var(--serif);
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--text-main);
    }

    .main-grid {
        display: grid;
        grid-template-columns: 1fr 18rem;
        gap: 2rem;
        margin: 2rem 0 4rem;
    }

    @media (max-width: 768px) {
        .main-grid { grid-template-columns: 1fr; }
    }

    .card {
        background: var(--sheet);
        border: 1px solid var(--border-color);
        padding: 1.25rem 1.35rem;
        margin-bottom: 1.25rem;
    }

    .process-title {
        font-size: clamp(1.45rem, 3vw, 1.85rem);
        margin: 0 0 0.35rem;
        overflow-wrap: anywhere;
    }

    .process-subtitle {
        color: var(--text-muted);
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem 0.6rem;
        align-items: center;
        margin-bottom: 1.25rem;
    }

    .badge {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        font-family: var(--sans);
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .badge-status { background: var(--primary-light); color: var(--primary-color); }
    .badge-success { background: #e7f2ea; color: var(--success-color); }
    .badge-danger { background: #f8e8e6; color: var(--danger-color); }

    .parte-group {
        padding: 0.85rem 0;
        border-bottom: 1px solid var(--border-color);
    }

    .parte-group:last-child { border-bottom: 0; padding-bottom: 0; }

    .parte-role {
        font-size: 0.82rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 700;
    }

    .parte-name {
        font-weight: 700;
        color: var(--primary-color);
        margin-top: 0.15rem;
    }

    .parte-advogado {
        margin-top: 0.2rem;
        color: var(--text-muted);
    }

    .parte-advogado::before { content: "Advogado: "; font-weight: 700; }

    .timeline { margin: 0; }

    .timeline-item {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.15rem;
        padding: 0.85rem 0;
        border-bottom: 1px solid var(--border-color);
    }

    @media (min-width: 560px) {
        .timeline-item { grid-template-columns: 8.5rem 1fr; gap: 0.75rem; }
    }

    .timeline-marker { display: none; }

    .timeline-date {
        color: var(--text-muted);
        font-weight: 700;
    }

    .timeline-title { font-weight: 700; }

    .timeline-desc {
        margin-top: 0.35rem;
        white-space: pre-wrap;
        font-family: var(--serif);
    }

    .detail-list { list-style: none; margin: 0; padding: 0; }

    .detail-item { margin-bottom: 0.9rem; }

    .detail-label {
        font-size: 0.82rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 700;
    }

    .detail-value { margin-top: 0.12rem; overflow-wrap: anywhere; }

    @media (prefers-reduced-motion: reduce) {
        * { scroll-behavior: auto !important; transition: none !important; }
    }
    """


def _campos_sidebar(processo: ProcessoNormalizado) -> list[tuple[str, str]]:
    """Retorna pares (label, valor) para a sidebar, adaptado ao grau."""
    campos = []
    if getattr(processo, 'grau', 1) == 2:
        campos.append(('Relator', processo.relator or '-'))
        campos.append(('Seção', processo.secao or '-'))
        campos.append(('Órgão Julgador', processo.orgao_julgador or '-'))
        campos.append(('Área', processo.area or '-'))
        campos.append(('Assunto', processo.assunto or '-'))
        campos.append(('Valor da Ação', processo.valor_acao or '-'))
        campos.append(('Volume / Apenso', processo.volume_apenso or '-'))
    else:
        campos.append(('Juiz', processo.juiz or '-'))
        campos.append(('Área', processo.area or '-'))
        campos.append(('Assunto', processo.assunto or '-'))
        campos.append(('Distribuição', processo.distribuicao or '-'))
        campos.append(('Valor da Ação', processo.valor_acao or '-'))
        campos.append(('Vara', processo.vara or '-'))
        campos.append(('Controle', processo.numero_controle or '-'))
    return campos

def gerar_html_processo(processo: ProcessoNormalizado) -> str:
    """Gera um HTML completo estilizado apresentando os dados do processo."""
    
    # Prepara Partes agrupadas
    if processo.partes:
        # Agrupa principais com seus advogados
        # No e-SAJ, geralmente vem [Parte Principal], [Advogado 1], [Advogado 2]...
        grupos = []
        grupo_atual = None
        for p in processo.partes:
            if p.tipo and ('advogad' in p.tipo.lower() or 'defensor' in p.tipo.lower()):
                if grupo_atual:
                    grupo_atual['advogados'].append(p)
                else:
                    # Advogado sem parte associada
                    grupos.append({'principal': p, 'advogados': []})
            else:
                if grupo_atual:
                    grupos.append(grupo_atual)
                grupo_atual = {'principal': p, 'advogados': []}
        if grupo_atual:
            grupos.append(grupo_atual)
            
        partes_list = []
        for g in grupos:
            prin = g['principal']
            advs = "".join([f'<div class="parte-advogado"><span class="sr-only">Advogado: </span>{a.nome}</div>' for a in g['advogados']])
            
            partes_list.append(f"""
            <div class="parte-group" role="group" aria-label="Participante do processo">
                <div class="parte-role">{prin.tipo}</div>
                <div class="parte-name">{prin.nome}</div>
                {advs}
            </div>
            """)
        partes_html = "".join(partes_list)
    else:
        partes_html = "<p class='text-muted'>Nenhuma parte encontrada.</p>"

    # Prepara Movimentações
    if processo.movimentacoes:
        movs_list = []
        for m in processo.movimentacoes:
            # Separa titulo e descricao da movimentacao se houver quebra de linha
            linhas = m.descricao.split('\n', 1) if m.descricao else ["", ""]
            titulo = linhas[0].strip()
            desc = linhas[1].strip() if len(linhas) > 1 else ""
            
            desc_html = f'<div class="timeline-desc">{desc}</div>' if desc else ""
            
            movs_list.append(f"""
            <div class="timeline-item">
                <div class="timeline-marker" aria-hidden="true"></div>
                <div class="timeline-date"><time>{m.data}</time></div>
                <div class="timeline-title">{titulo}</div>
                {desc_html}
            </div>
            """)
        movs_html = "".join(movs_list)
    else:
        movs_html = "<p class='text-muted'>Nenhuma movimentação encontrada.</p>"
        
    # Badge de Situação
    sit = processo.situacao or "Desconhecida"
    sit_lower = sit.lower()
    badge_class = "badge-status"
    if 'baixado' in sit_lower: badge_class = "badge-success"
    if 'urgente' in sit_lower or 'sigilo' in sit_lower: badge_class = "badge-danger"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Processo {processo.numero_processo} - LexNode</title>
    <meta name="description" content="Acompanhamento do processo {processo.numero_processo} - {processo.classe}">
    <link href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,600;7..72,700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        {_gerar_estilo()}
    </style>
</head>
<body>
    <header class="header" role="banner">
        <div class="container">
            <div class="brand">LexNode</div>
        </div>
    </header>

    <main class="container" role="main">
        <div class="main-grid">
            <div class="content-column">
                <article>
                    <header style="margin-bottom: 2rem;">
                        <h1 class="process-title">{processo.numero_processo or 'Número indisponível'}</h1>
                        <div class="process-subtitle">
                            <span class="badge {badge_class}" aria-label="Situação do processo">{sit}</span>
                            <span>{processo.classe}</span>
                            <span aria-hidden="true">·</span>
                            <span>{processo.orgao_julgador or processo.foro or '-'}</span>
                        </div>
                    </header>

                    <section class="card" aria-labelledby="partes-heading">
                        <h2 id="partes-heading" style="margin-bottom: 1.5rem; font-size: 1.25rem;">Partes envolvidas</h2>
                        <div class="partes-list">
                            {partes_html}
                        </div>
                    </section>

                    <section class="card" aria-labelledby="movimentacoes-heading">
                        <h2 id="movimentacoes-heading" style="margin-bottom: 1.5rem; font-size: 1.25rem;">Movimentações</h2>
                        <div class="timeline">
                            {movs_html}
                        </div>
                    </section>
                </article>
            </div>
            
            <aside class="sidebar-column" aria-label="Detalhes do Processo">
                <div class="card" style="position: sticky; top: 80px;">
                    <h2 style="font-size: 1.1rem; margin-bottom: 1.25rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">Detalhes do Processo</h2>
                    <ul class="detail-list">
                        {''.join(f'''
                        <li class="detail-item">
                            <div class="detail-label">{label}</div>
                            <div class="detail-value">{valor}</div>
                        </li>''' for label, valor in _campos_sidebar(processo))}
                    </ul>
                </div>
            </aside>
        </div>
    </main>
</body>
</html>
"""
    return html

_NUMERO_TRANS_TABLE = str.maketrans(".-/", "___")

def gerar_html_lista_busca(nome: str, resumos: List[ResumoProcesso], link_local: bool = False) -> str:
    """Gera um HTML apresentando os resultados de busca por nome."""
    
    if resumos:
        itens_list = []
        for p in resumos:
            if link_local:
                num_sanitizado = p.numero.translate(_NUMERO_TRANS_TABLE)
                href = f"{num_sanitizado}.html"
                target = ""
                aria = f'aria-label="Ver detalhes locais do Processo {p.numero}"'
            else:
                href = f"https://esaj.tjac.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&dadosConsulta.valorConsultaNuUnificado={p.numero}"
                target = 'target="_blank"'
                aria = f'aria-label="Processo {p.numero} no site do tribunal"'
                
            itens_list.append(f"""
            <article class="card" style="margin-bottom: 1rem;">
                <h3 style="font-size: 1.2rem; margin-bottom: 0.25rem;">
                    <a href="{href}" {target} {aria}>
                        {p.numero}
                    </a>
                </h3>
                <div style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">
                    <strong>{p.classe}</strong> &middot; {p.assunto}
                </div>
                
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem; align-items: center; background-color: var(--secondary-color); padding: 0.75rem; border-radius: 4px;">
                    <div>
                        <span style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); font-weight: 600;">{p.participacao}:</span>
                        <span style="font-weight: 500;">{p.nome_parte}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: text-bottom; margin-right: 4px;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        {p.data_local}
                    </div>
                </div>
            </article>
            """)
        itens_html = "".join(itens_list)
    else:
        itens_html = "<div class='card'><p>Nenhum processo encontrado para este nome.</p></div>"
        
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Busca: {nome} - LexNode</title>
    <meta name="description" content="Resultados da busca de processos para {nome}">
    <link href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,600;7..72,700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        {_gerar_estilo()}
    </style>
</head>
<body>
    <header class="header" role="banner">
        <div class="container">
            <div class="brand">LexNode</div>
        </div>
    </header>

    <main class="container" role="main" style="max-width: 800px; padding-top: 2rem; padding-bottom: 4rem;">
        <header style="margin-bottom: 2rem;">
            <p style="color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.5px;">Resultados da busca</p>
            <h1 class="process-title" style="font-size: 1.8rem;">{nome}</h1>
            <p style="margin-top: 0.5rem; color: var(--text-muted);">{len(resumos)} processos encontrados no e-SAJ TJAC.</p>
        </header>

        <section aria-label="Lista de Processos">
            {itens_html}
        </section>
    </main>
</body>
</html>
"""
    return html
