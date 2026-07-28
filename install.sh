#!/bin/bash
# install.sh - Instala as dependencias do LexNode

echo "🚀 Iniciando a instalação do LexNode..."

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado! Por favor, instale o Python3."
    exit 1
fi

echo "📦 Criando ambiente virtual (venv)..."
python3 -m venv venv

echo "📦 Ativando o ambiente virtual e instalando dependências do Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Instalação concluída com sucesso!"
echo "➡️  Para iniciar o sistema, rode: ./start.sh"
