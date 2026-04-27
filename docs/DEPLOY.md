# Deploy no Servidor da Faculdade

Guia completo para colocar o ODIN-ETL em produção num servidor Linux.

---

## Pré-requisitos no servidor

```bash
# Docker Engine (não Docker Desktop)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # adiciona seu usuário ao grupo docker
newgrp docker                   # aplica sem precisar fazer logout

# Verifica
docker --version
docker compose version
```

---

## Primeiro deploy

```bash
# 1. Clonar o repositório
git clone <url-do-repo> /opt/odin
cd /opt/odin

# 2. Criar o arquivo de variáveis de produção
cp .env.example .env.prod
nano .env.prod   # preencha MONGO_DB_NAME, LOG_LEVEL, etc.

# 3. Gerar senha forte para o MongoDB
mkdir -p secrets
openssl rand -base64 32 > secrets/mongo_password.txt
chmod 600 secrets/mongo_password.txt

# 4. Deploy
./scripts/deploy.sh
```

---

## Executar os pipelines

```bash
# Módulo educação
make prod-run-education

# Módulo socioeconômico
make prod-run-socioeconomico

# Validar dados
make prod-validar

# Ou diretamente:
docker compose -f docker-compose.prod.yml run --rm etl \
    python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.main
```

---

## Agendar execução automática (cron)

```bash
sudo crontab -e
```

Adicione:

```cron
# ODIN-ETL — roda todo domingo às 2h da manhã
0 2 * * 0  cd /opt/odin && make prod-run-socioeconomico >> /var/log/odin-etl.log 2>&1
```

---

## Acessar o MongoDB via UI (Mongo Express)

O Mongo Express fica disponível apenas internamente. Para acessar remotamente:

```bash
# No seu computador local, crie um SSH tunnel:
ssh -L 8081:localhost:8081 usuario@ip-do-servidor

# Suba o Mongo Express no servidor:
make prod-mongo-ui

# Acesse no browser: http://localhost:8081
```

---

## Atualizar o código

```bash
cd /opt/odin
git pull
./scripts/deploy.sh --etl   # só reconstrói a imagem ETL, não mexe no banco
```

---

## Backup do MongoDB

```bash
# Backup manual
docker compose -f docker-compose.prod.yml exec mongo \
    mongodump --username odin_admin \
              --password $(cat secrets/mongo_password.txt) \
              --authenticationDatabase admin \
              --db odin \
              --out /tmp/backup

docker cp odin-mongo:/tmp/backup ./backup-$(date +%Y%m%d)

# Restaurar
docker cp ./backup-20260426 odin-mongo:/tmp/restore
docker compose -f docker-compose.prod.yml exec mongo \
    mongorestore --username odin_admin \
                 --password $(cat secrets/mongo_password.txt) \
                 --authenticationDatabase admin \
                 /tmp/restore
```

---

## Monitoramento básico

```bash
# Status dos containers
make prod-status

# Logs em tempo real
make prod-logs

# Uso de recursos
docker stats odin-mongo

# Espaço em disco dos volumes
docker system df
```

---

## Estrutura de arquivos no servidor

```
/opt/odin/
├── src/                    ← código fonte
├── config/                 ← configurações YAML
├── data/                   ← dados (volume Docker, não no git)
├── secrets/
│   └── mongo_password.txt  ← senha do MongoDB (chmod 600)
├── .env.prod               ← variáveis de produção (não no git)
├── docker-compose.prod.yml
└── Makefile
```

---

## Troubleshooting

**MongoDB não sobe:**

```bash
docker compose -f docker-compose.prod.yml logs mongo
# Verifique se o arquivo secrets/mongo_password.txt existe e tem conteúdo
```

**ETL falha com erro de conexão:**

```bash
# Verifique se o MongoDB está saudável
make prod-status
# O MONGO_URI no .env.prod deve usar o nome do service: mongo
# MONGO_URI=mongodb://odin_user:<senha>@mongo:27017/odin?authSource=odin
```

**Sem espaço em disco:**

```bash
docker system prune -f          # remove imagens e containers não usados
docker volume ls                # lista volumes
```
