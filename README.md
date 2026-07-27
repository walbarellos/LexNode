# LexNode (ProcessoLivreAC)

Ferramenta em Python focada em OSINT e levantamento de alvos a partir de processos públicos do Tribunal de Justiça do Acre (TJAC). O sistema faz varreduras exaustivas nos sistemas e-SAJ de 1º e 2º Grau de forma invisível.

## O que temos (Funcionalidades)
* **Busca Exaustiva Automática:** Pesquisa simultânea e automática em todos os foros e instâncias (1º e 2º Grau) para garantir que a ficha completa do alvo seja levantada.
* **OSINT por CPF/CNPJ e Nome:** Busca de alvos através do parâmetro nativo de documento ou nome da parte. A ferramenta sanitiza CPFs sujos automaticamente.
* **Extração Direta (CNJ):** Puxa dezenas de metadados processuais (relator, juiz, classe, assunto, valores) e a linha do tempo completa de movimentações.
* **Segurança e Privacidade (Fail-Closed):** Identifica falsos positivos no DOM e bloqueia estritamente vazamentos de processos em Segredo de Justiça.
* **Exportação Múltipla:** Resultados em CLI limpo, arquivos JSON estruturados para ingestão em outras ferramentas, ou relatórios finais estáticos em formato HTML (estilo Jusbrasil).

## O que falta (Próximos Passos)
* **Download de Documentos (PDFs):** Fazer login automatizado e baixar a íntegra de peças públicas (sentenças, despachos, acórdãos).
* **Banco de Dados / Cache:** Salvar as requisições em um SQLite/PostgreSQL para construir histórico próprio, não depender do e-SAJ online e gerar alertas de novas movimentações.
* **Interface Web API / Frontend:** Embrulhar tudo num backend FastAPI e criar um frontend que consuma a base sem precisar do terminal.
* **Integração com IA (Tradutor Jurídico):** Passar as movimentações processuais brutas por um LLM para gerar resumos explicativos simples das decisões judiciais.

<img width="1219" height="561" alt="image" src="https://github.com/user-attachments/assets/ade240d7-db03-46dd-b821-1d0f91775779" />


## Tutorial de Uso

### Instalação
```bash
# Clone o repositório
git clone https://github.com/walbarellos/LexNode.git
cd LexNode

# Crie e ative um ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### Como buscar (Exemplos)



<img width="1303" height="607" alt="image" src="https://github.com/user-attachments/assets/f377681c-3237-4512-b72f-2245ebf78506" />

```bash
# 1. Buscar um alvo por CPF (busca estado inteiro + 1º e 2º grau)
python consultar.py --doc 00000000000

# 2. Buscar por CNPJ e baixar os detalhes HTML de TUDO que for achado
python consultar.py --doc 11669325000188 --html --detalhar

# 3. Buscar alvo por Nome
python consultar.py --nome "João da Silva"

# 4. Pesquisar um processo específico (CNJ) e gerar o relatório HTML
python consultar.py 0701300-79.2019.8.01.0003 --html

# 5. Exportar a ficha do alvo em JSON estruturado
python consultar.py --doc 11669325000188 --json > alvo.json
```

## Créditos
* Willian Albarello
