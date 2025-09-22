# --- Estágio 1: Builder ---
# Cria a build de produção otimizada
FROM node:20-slim AS builder
WORKDIR /app

# Copia os arquivos de definição de pacotes e instala as dependências
COPY frontend/package*.json ./
RUN npm ci

# Copia o restante do código do frontend
COPY frontend/ .

# Define a variável de ambiente pública ANTES da build
# O valor real será injetado pelo Docker Compose no estágio final
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Roda o script de build para gerar a aplicação otimizada
RUN npm run build

# --- Estágio 2: Runner ---
# Cria a imagem final, leve, para rodar a aplicação
FROM node:20-slim
WORKDIR /app

ENV NODE_ENV=production

# Copia os arquivos da build do estágio anterior
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Expõe a porta que o Next.js roda por padrão
EXPOSE 3000

# Comando para iniciar o servidor de produção do Next.js
CMD ["npm", "start"]
