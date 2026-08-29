# TODO: Próximos Passos e Melhorias Futuras

Abaixo está o roadmap sugerido de evolução para o **JusBrasil**, partindo de uma ferramenta de CLI e web scraping de linha de comando para uma solução escalável de OSINT e inteligência processual.

## Funcionalidades Implementadas (Concluídas)
* ~~**1. Suporte ao 2º Grau (Tribunal de Justiça)**~~ [CONCLUÍDO]
* ~~**2. Motor de Jurisprudência (Text-Search de Decisões)**~~ [CONCLUÍDO]
* ~~**3. Download de Documentos (Peças Processuais Originais)**~~ [CONCLUÍDO via Cookie Injection]
* ~~**4. Interface Web API Completa (Backend/Frontend)**~~ [CONCLUÍDO via FastAPI + Tailwind]
* ~~**5. Integração com a Justiça Federal (TRF1 - PJe)**~~ [CONCLUÍDO via JSF ViewState Parsing]

## Próximos Passos

### 6. Integração com Banco Nacional de Mandados de Prisão (BNMP - CNJ)
**Objetivo:** Permitir que o JusBrasil descubra se o alvo tem mandado de prisão em aberto no Brasil inteiro.
*   **Alvo:** API JSON oficial do CNJ (`https://portalbnmp.cnj.jus.br/`)
*   **Abordagem:** Não precisa parsear HTML. O BNMP moderno é uma SPA em React e tem uma API REST por trás. Faremos requisições POST diretas para a API de pesquisa pública.

### 7. Integração com a Justiça do Trabalho (TRT14 - PJe Trabalhista)
**Objetivo:** Encontrar passivos trabalhistas, fraudes a credores, laranjas e histórico corporativo do alvo (Acre e Rondônia).
*   **Alvo:** Sistema PJe do TRT14 (`https://pje.trt14.jus.br/consultapublica/ConsultaPublica/listView.seam`)
*   **Abordagem:** Mesma mecânica do TRF1. O PJe trabalhista segue o mesmo padrão arquitetural JSF do CNJ. 

### 8. Banco de Dados / Camada de Cache (SQLite)
**Objetivo:** Adicionar uma camada de persistência com `SQLite` usando um ORM como o SQLAlchemy. Bater nos Tribunais para cada consulta é ineficiente. Isso permitirá salvar resultados num cache local e construir uma base histórica offline permanente.

### 9. Automação Headless Avançada (Playwright)
**Objetivo:** Migrar o bypass de PDFs (que hoje depende de injeção manual de cookie no `.env`) para um navegador *headless* automatizado que consiga resolver os desafios Cloudflare Turnstile nativamente e realizar login de forma invisível.
