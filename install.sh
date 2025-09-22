#!/bin/bash

# --- Guia de Instalação e Deploy Completo para IaAndData em Ubuntu Virgem ---

# Este script automatiza a preparação do servidor.
# Execute-o como root ou com sudo.

echo "--- [PASSO 1 de 5] Atualizando o sistema ---"
apt-get update && apt-get upgrade -y

echo "--- [PASSO 2 de 5] Instalando dependências (Git, Curl, etc.) ---"
apt-get install -y git curl ca-certificates gnupg

echo "--- [PASSO 3 de 5] Instalando Docker Engine ---"
# Adiciona a chave GPG oficial do Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Adiciona o repositório do Docker ao Apt
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update

# Instala os pacotes do Docker
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "--- [PASSO 4 de 5] Verificando a instalação do Docker ---"
# Testa se o Docker está rodando
docker run hello-world

if [ $? -eq 0 ]; then
  echo ">>> Docker instalado com sucesso!"
else
  echo ">>> ERRO: Falha na instalação do Docker. Verifique os logs."
  exit 1
fi

echo "--- [PASSO 5 de 5] Preparação do servidor concluída! ---"
echo ""
echo "--- PRÓXIMOS PASSOS (MANUAIS) ---"
echo "1. Clone o seu repositório do projeto:"
echo "   git clone <URL_DO_SEU_REPOSITORIO>"
echo "   cd <NOME_DO_SEU_REPOSITORIO>"
echo ""
echo "2. Crie e configure o arquivo de ambiente:"
echo "   nano .env"
echo "   (Cole o conteúdo abaixo e salve com Ctrl+X, Y, Enter)"
echo ""
echo "   # --- Conteúdo para o arquivo .env ---"
echo "   # Credenciais do Supabase e OpenAI"
echo "   SUPABASE_URL=https://wrfoouidopjirqzxqvee.supabase.co"
echo "   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndyZm9vdWlkb3BqaXJxenhxdmVlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg0MTE2ODksImV4cCI6MjA3Mzk4NzY4OX0.Ox6lEDjLqFoyxxmVfyOFsG92BkLnXUcA9YhJEzDTwv4"
echo "   OPENAI_API_KEY=SUA_CHAVE_DA_OPENAI_AQUI"
echo ""
echo "   # URLs públicas para o frontend e backend (substitua pelos seus domínios)"
echo "   NEXT_PUBLIC_API_URL=https://api.seusite.com"
echo ""
echo "3. Edite o Caddyfile com seus domínios reais:"
echo "   nano Caddyfile"
echo ""
echo "4. Inicie toda a aplicação com um único comando:"
echo "   docker compose up --build -d"
echo ""
echo "5. Configure os registros DNS dos seus domínios (api.seusite.com e app.seusite.com) para apontar para o IP deste servidor."
echo ""
echo ">>> O deploy estará completo após o DNS propagar. Use 'docker compose logs -f' para ver os logs."
