# ProcessoLivreAC

Ferramenta em Python para consulta, extração e estruturação de processos públicos do Tribunal de Justiça do Acre (TJAC), especificamente do sistema e-SAJ de 1º Grau.

O **ProcessoLivreAC** funciona como um "JusBrasil local", permitindo buscar processos por nome da parte ou pelo número CNJ, extraindo os metadados processuais (partes, juízo, classe, assunto) e as movimentações, com uma premissa técnica de *privacy-by-design* (fail-closed para processos sigilosos). 

A ferramenta exporta os dados em formato JSON, em TXT puro, ou gera uma interface **HTML completa e acessível**, desenhada para apresentar uma leitura clara, profissional e rápida do processo.

## Funcionalidades
* Busca de processos por Nome da Parte.
* Extração rica e completa por número do Processo (CNJ).
* Validação DOM-aware estrita de marcadores de segredo de justiça.
* Exportação elegante em linha de comando (CLI).
* Geração de páginas HTML independentes de alta usabilidade e estilo moderno (com `--html`).
* Opção de varredura profunda: listagem de processos atrelada à extração completa automática (com `--detalhar`).

## Instalação
```bash
# Clone o repositório
git clone https://github.com/walbarellos/JuyceAC.git
cd JuyceAC

# Crie e ative um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

## Como usar
```bash
# Pesquisar um processo específico e gerar um lindo HTML
python consultar.py 0800224-44.2013.8.01.0001 --html

# Buscar processos pelo nome da parte (lista no terminal)
python consultar.py --nome "Roberto Duarte Júnior"

# Buscar processos por nome e gerar a visualização completa de todos eles em HTML
python consultar.py --nome "Roberto Duarte Júnior" --html --detalhar
```

## Próximos Passos
Veja o [TODO.md](TODO.md) para o cronograma (roadmap) do que ainda pode ser implementado no sistema.
