# LexNode (ProcessoLivreAC)

O LexNode é uma arquitetura de software desenvolvida em Python orientada à coleta de inteligência de fontes abertas (OSINT) e raspagem de dados estruturados em sistemas judiciais estaduais (especificamente o e-SAJ do TJAC). O sistema realiza web scraping avançado, contornando limitações de UI para fornecer extração exaustiva em 1º e 2º graus de jurisdição.

## 🚀 Arquitetura e Funcionalidades

* **Crawler Exaustivo Bidirecional:** Mecanismo de busca simultânea que varre todas as comarcas (1º grau) e câmaras isoladas (2º grau), consolidando o grafo processual do alvo em uma única requisição.
* **Parser de Jurisprudência (`--juris`):** Motor de indexação focado em Acórdãos, capaz de realizar busca de texto-livre em decisões colegiadas, extraindo ementas, relatores e datas de julgamento.
* **Extração Direta e Normalização (Padrão CNJ):** O `normalizer.py` mapeia o DOM caótico do e-SAJ para um schema unificado, extraindo metadados críticos (relator, magistrado, classe, assunto, valor da causa) e a cronologia completa de movimentações.
* **Bypass de Autenticação para PDFs (`--baixar-pdfs`):** Implementação de injeção de cookies via `.env` para autenticação de sessão, permitindo a extração automatizada de peças processuais originais (PDFs) burlando restrições nativas do servidor.
* **Painel Web Analítico (FastAPI + Tailwind):** Além da CLI, o sistema embarca um servidor assíncrono (`uvicorn`) provendo uma API RESTful completa e um dashboard de inteligência em Glassmorphism responsivo.
* **Privacy by Design (Fail-Closed):** O sanitizador de HTML implementa uma heurística estrita para detectar flags de "Segredo de Justiça". Em caso de ambiguidade, o pipeline descarta a payload para garantir o compliance com a LGPD e evitar a exposição de dados sensíveis.

## 🛠️ Roadmap e Melhorias Futuras

* **Persistência Relacional:** Implementar `SQLAlchemy` (SQLite/PostgreSQL) para armazenamento em cache local, permitindo investigações offline e versionamento de linha do tempo processual (alertas de movimentação).
* **Processamento de Linguagem Natural (LLM):** Integração com APIs de LLM para processar a base de movimentações, resumindo o mérito das decisões judiciais de forma autônoma.
* **Automação Headless Avançada:** Migração parcial da engine de requisições de `requests` para `Playwright` com `stealth plugins`, mitigando de forma definitiva os desafios de *Cloudflare Turnstile* e captchas dinâmicos.

<img width="1219" height="561" alt="image" src="https://github.com/user-attachments/assets/ade240d7-db03-46dd-b821-1d0f91775779" />

## ⚙️ Guia de Implantação (Deployment)

### Instalação Automatizada (Linux/macOS):
O projeto conta com *shell scripts* para provisionamento automático do *virtual environment* e das dependências.

```bash
# Clone o repositório
git clone https://github.com/walbarellos/LexNode.git
cd LexNode

# Conceda permissão de execução aos scripts
chmod +x install.sh start.sh

# Execute o provisionamento e inicie o backend
./install.sh
./start.sh
```

### Instalação Manual (Qualquer SO):

```bash
python3 -m venv venv
source venv/bin/activate
# No Windows: venv\Scripts\activate

pip install -r requirements.txt
```

<img width="1311" height="705" alt="image" src="https://github.com/user-attachments/assets/d5b82610-bf1c-4b82-85ac-b62ad1efd9c1" />

<img width="1299" height="269" alt="image" src="https://github.com/user-attachments/assets/4f28fe73-6ae7-4b42-b856-38b59f031414" />

## 💻 Interface de Linha de Comando (CLI)

O script principal `consultar.py` aceita os seguintes parâmetros de execução. *Screenshots da CLI e da interface Web:*

<img width="1920" height="557" alt="image" src="https://github.com/user-attachments/assets/80fd9f02-3a11-4091-b701-f06da5344f8d" />

<img width="1303" height="607" alt="image" src="https://github.com/user-attachments/assets/f377681c-3237-4512-b72f-2245ebf78506" />

<img width="1817" height="911" alt="image" src="https://github.com/user-attachments/assets/a7dc531d-67db-4129-abc0-e5f8e2acb1db" />

```bash
# 1. Varredura por CPF/CNPJ (Busca global em 1º e 2º grau)
python consultar.py --doc 00000000000

# 2. Pesquisa livre de Jurisprudência e extração automática dos Acórdãos (PDF)
python consultar.py --juris "atraso voo gol" --baixar-pdfs

# 3. Varredura nominal com dump completo de HTML e detalhamento estrutural
python consultar.py --nome "João da Silva" --html --detalhar

# 4. Parsing isolado de processo unificado (CNJ) com exportação HTML
python consultar.py 0701300-79.2019.8.01.0003 --html

# 5. Serialização de output em JSON para datalakes
python consultar.py --doc 11669325000188 --json > alvo.json
```

## 🔐 Configuração de Variáveis de Ambiente (.env)

Para extrair PDFs oficiais (via `--baixar-pdfs`), é necessário injetar o cookie de uma sessão autenticada.
Crie um arquivo `.env` na raiz do projeto (baseie-se no `.env.example`):
```env
ESAJ_COOKIE="JSESSIONID=AECB13860D...; outro_cookie=valor"
```

## Créditos
* Arquitetura e Desenvolvimento: Willian Albarello
