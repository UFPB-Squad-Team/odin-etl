#!/usr/bin/env bash
# =============================================================
# ODIN-ETL — Script de deploy no servidor
#
# Uso:
#   ./scripts/deploy.sh           # deploy completo
#   ./scripts/deploy.sh --etl     # só reconstrói a imagem ETL
#   ./scripts/deploy.sh --status  # mostra status dos containers
# =============================================================

set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_DIR"

# ── Cores para output ─────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $*"; }
err()  { echo -e "${RED}[error]${NC} $*" >&2; exit 1; }

# ── Verificações pré-deploy ───────────────────────────────────
check_prerequisites() {
    command -v docker >/dev/null 2>&1 || err "Docker não encontrado."
    docker compose version >/dev/null 2>&1 || err "Docker Compose plugin não encontrado."

    [[ -f ".env.prod" ]]                  || err "Arquivo .env.prod não encontrado. Copie .env.example para .env.prod e preencha."
    [[ -f "secrets/mongo_password.txt" ]] || err "Arquivo secrets/mongo_password.txt não encontrado. Veja secrets/README.md."

    local pwd_size
    pwd_size=$(wc -c < secrets/mongo_password.txt)
    [[ "$pwd_size" -ge 16 ]] || warn "Senha do MongoDB parece curta (< 16 chars). Considere usar uma mais forte."
}

# ── Status ────────────────────────────────────────────────────
show_status() {
    log "Status dos containers:"
    $COMPOSE ps
}

# ── Deploy completo ───────────────────────────────────────────
deploy() {
    log "Iniciando deploy — $(date '+%Y-%m-%d %H:%M:%S')"

    check_prerequisites

    log "Fazendo pull das imagens base..."
    $COMPOSE pull mongo mongo-express 2>/dev/null || true

    log "Construindo imagem ETL (multi-stage)..."
    $COMPOSE build --no-cache etl

    log "Subindo MongoDB..."
    $COMPOSE up -d mongo

    log "Aguardando MongoDB ficar saudável..."
    local retries=0
    until $COMPOSE exec mongo mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; do
        retries=$((retries + 1))
        [[ $retries -ge 30 ]] && err "MongoDB não respondeu após 30 tentativas."
        echo -n "."
        sleep 2
    done
    echo ""
    log "MongoDB saudável."

    log "Deploy concluído."
    show_status
}

# ── Só reconstrói ETL ─────────────────────────────────────────
deploy_etl_only() {
    check_prerequisites
    log "Reconstruindo imagem ETL..."
    $COMPOSE build etl
    log "Imagem ETL atualizada. Use 'make run-socioeconomico' para executar."
}

# ── Entry point ───────────────────────────────────────────────
case "${1:-}" in
    --status)  show_status ;;
    --etl)     deploy_etl_only ;;
    "")        deploy ;;
    *)         err "Argumento desconhecido: $1. Use --status, --etl ou sem argumentos." ;;
esac
