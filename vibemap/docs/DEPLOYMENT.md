# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Domain configured (vibemap.live)
- Server with at least 2GB RAM

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/vibemap/vibemap.git
cd vibemap
```

2. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your production values
```

3. Start services:
```bash
docker-compose up -d
```

4. Run migrations:
```bash
docker-compose exec api alembic upgrade head
```

5. Verify deployment:
```bash
curl http://localhost:8000/health
```

## Production Configuration

### Environment Variables

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/vibemap
REDIS_URL=redis://redis:6379/0
DEBUG=false
```

### SSL/TLS

Use Traefik or Nginx as a reverse proxy with Let's Encrypt:

```yaml
# docker-compose.prod.yml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@vibemap.live"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt

  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`vibemap.live`)"
      - "traefik.http.routers.api.tls=true"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
```

### Database Backups

```bash
# Backup
docker-compose exec db pg_dump -U postgres vibemap > backup.sql

# Restore
docker-compose exec -T db psql -U postgres vibemap < backup.sql
```

## Monitoring

- Health endpoint: `/health`
- Prometheus metrics: `/metrics` (Phase 2)
- Logs: `docker-compose logs -f api`

## Scaling

For high-throughput scenarios:

1. Use external managed PostgreSQL (RDS, Cloud SQL)
2. Use Redis Cluster for caching
3. Deploy multiple API instances behind a load balancer
4. Enable connection pooling with PgBouncer
