# TODO: Próximos Passos e Melhorias Futuras

Abaixo está o roadmap sugerido de evolução para o **ProcessoLivreAC**, partindo de uma ferramenta de CLI e web scraping de linha de comando para uma possível solução escalável e completa.

## 1. ~~Suporte ao 2º Grau (Tribunal de Justiça)~~ [CONCLUÍDO]
Atualmente, o script consulta e extrai dados tanto do `cpopg` (1º Grau) quanto do `cposg5` (2º Grau) de forma automática e unificada, incluindo busca exaustiva por CPF/CNPJ.

## 2. Download de Documentos (Peças Processuais)
Nós conseguimos ler a *linha do tempo*, mas as peças (PDFs) não são baixadas.
**Objetivo:** Identificar links e senhas nos movimentos (para o que for público, como sentenças, acórdãos e despachos) e permitir que o usuário baixe diretamente o documento PDF gerado pelo sistema.

## 3. Gestão Anti-Ban e Tratamento de Captchas
Ao executar rotinas com `--detalhar` para uma busca muito vasta, o e-SAJ pode interromper a extração através de rate limits ou Captchas.
**Objetivo:** Incorporar sessão persistente via arquivos de Cookies (aproveitando sessão real do navegador logado do usuário), ou evoluir o scraper para automação *headless* moderna, como o `Playwright`, com a finalidade de lidar com desafios Cloudflare e captchas complexos do TJ.

## 4. Banco de Dados / Camada de Cache
Bater no Tribunal para cada consulta é ineficiente e arrisca bans. 
**Objetivo:** Adicionar uma camada de persistência com `SQLite` ou `PostgreSQL` usando um ORM como o SQLAlchemy. Isso permitirá salvar resultados num cache local e construir uma base histórica robusta (sempre respeitando as exclusões do Segredo de Justiça).

## 5. Interface Web API Completa (Backend/Frontend)
A atual exportação para HTML estático resolve a visualização, mas a interação exige o uso do Terminal.
**Objetivo:** Embrulhar a aplicação em um framework web (`FastAPI` ou `Flask`). 
Assim, cria-se um site local ou em nuvem onde o usuário digita a busca em um campo web e consome uma API que faz o trabalho por baixo dos panos, renderizando os processos num frontend React/Next.js (ou templates do lado do servidor) verdadeiramente análogo ao "JusBrasil".

## 6. Busca Fonética Flexível (Fuzzy Search)
**Objetivo:** Atualmente a busca usa a mecânica base do e-SAJ. É possível implementar e repassar *flags* (como `chNmCompleto`) na URL ou construir algoritmos baseados em fonética e divergência de caracteres ao iterar pelos resultados devolvidos, para melhorar a taxa de acertos ao procurar partes.

## 7. Motor de Jurisprudência (Text-Search de Decisões)
**Objetivo:** Criar um módulo independente (`crawler_jurisprudencia.py` e flag `--juris` no CLI) capaz de fazer buscar por texto-livre nos acórdãos e ementas do 2º Grau.
*   **Motivação:** Diferente dos processos de 1º grau que buscam por nome/documento da parte, a jurisprudência permite buscar qualquer palavra-chave (nomes de empresas, bairros, produtos, infrações). 
*   **Entrega:** Permitir ao usuário rodar `python consultar.py --juris "atraso voo gol"` e receber um HTML rico com a média de condenações e o histórico da corte para aquele tema, criando uma ferramenta de OSINT contextual valiosíssima.
