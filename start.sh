#!/bin/bash
# start.sh - Inicia o servidor Web do LexNode

echo "🚀 Iniciando o LexNode Web Server..."

if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado. Por favor, rode ./install.sh primeiro."
    exit 1
fi

source venv/bin/activate

# Inicia o servidor FastAPI usando Uvicorn (escutando em todas as interfaces de rede)
echo "🌐 Acesse no seu navegador: http://localhost:8000"
uvicorn src.web.app:app --host 0.0.0.0 --port 8000 --reload
