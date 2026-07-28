# TODO: Próximos Passos e Melhorias Futuras

Abaixo está o roadmap sugerido de evolução para o **LexNode**, partindo de uma ferramenta de CLI e web scraping de linha de comando para uma solução escalável de OSINT e inteligência processual.

## Funcionalidades Implementadas (Concluídas)
* ~~**1. Suporte ao 2º Grau (Tribunal de Justiça)**~~ [CONCLUÍDO]
* ~~**2. Motor de Jurisprudência (Text-Search de Decisões)**~~ [CONCLUÍDO]
* ~~**3. Download de Documentos (Peças Processuais Originais)**~~ [CONCLUÍDO via Cookie Injection]
* ~~**4. Interface Web API Completa (Backend/Frontend)**~~ [CONCLUÍDO via FastAPI + Tailwind]

## Próximos Passos

### 5. Integração com Banco Nacional de Mandados de Prisão (BNMP - CNJ)
**Objetivo:** Permitir que o LexNode descubra se o alvo tem mandado de prisão em aberto no Brasil inteiro.
*   **Alvo:** API JSON oficial do CNJ (`https://portalbnmp.cnj.jus.br/`)
*   **Abordagem:** Não precisa parsear HTML. O BNMP moderno é uma SPA em React e tem uma API REST por trás. Faremos requisições POST diretas para a API de pesquisa pública.

### 6. Integração com a Justiça Federal (TRF1 - PJe)
**Objetivo:** Capturar crimes federais (contrabando, fraudes ao INSS, corrupção, Receita Federal) no Estado do Acre, que rodam inteiramente fora do e-SAJ.
*   **Alvo:** Sistema PJe do TRF1 (`https://pje1g.trf1.jus.br/consultapublica/ConsultaPublica/listView.seam`)
*   **Abordagem:** O PJe usa JavaServer Faces (JSF). Precisamos fazer um Crawler PJe que capture o token oculto `javax.faces.ViewState` e envie via POST para extrair os resultados e a linha do tempo.

### 7. Integração com a Justiça do Trabalho (TRT14 - PJe Trabalhista)
**Objetivo:** Encontrar passivos trabalhistas, fraudes a credores, laranjas e histórico corporativo do alvo (Acre e Rondônia).
*   **Alvo:** Sistema PJe do TRT14 (`https://pje.trt14.jus.br/consultapublica/ConsultaPublica/listView.seam`)
*   **Abordagem:** Mesma mecânica do TRF1. O PJe trabalhista segue o mesmo padrão arquitetural JSF do CNJ. 

### 8. Banco de Dados / Camada de Cache (SQLite)
**Objetivo:** Adicionar uma camada de persistência com `SQLite` usando um ORM como o SQLAlchemy. Bater nos Tribunais para cada consulta é ineficiente. Isso permitirá salvar resultados num cache local e construir uma base histórica offline permanente.

### 9. Automação Headless Avançada (Playwright)
**Objetivo:** Migrar o bypass de PDFs (que hoje depende de injeção manual de cookie no `.env`) para um navegador *headless* automatizado que consiga resolver os desafios Cloudflare Turnstile nativamente e realizar login de forma invisível.
