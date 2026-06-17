# Usa imagem Python
FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Copia requirements primeiro (melhor para cache)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código
COPY . .

# Expõe a porta (ajuste conforme sua aplicação)
EXPOSE 5000

# Comando para iniciar (ajuste para seu arquivo principal)
CMD ["python", "bot.py"]
