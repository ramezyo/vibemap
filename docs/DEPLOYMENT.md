# Deployment Guide

Deploy Vibemap to production.

## Quick Deploy (Railway)

The easiest way to deploy Vibemap is via Railway:

1. **Fork this repository** to your GitHub account

2. **Create Railway account** at https://railway.app

3. **New Project** → **Deploy from GitHub repo** → Select `vibemap`

4. **Add PostgreSQL**: New → Database → Add PostgreSQL

5. **Configure environment variables**:
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   OPENWEATHER_API_KEY=your_key_here
   REDDIT_CLIENT_ID=your_id_here
   REDDIT_CLIENT_SECRET=your_secret_here
   GOOGLE_PLACES_API_KEY=your_key_here
   ```

6. **Deploy**: Railway will auto-deploy on every push to main

## Docker Deploy

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Local Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Docker

```bash
# Build production image
docker build -t vibemap:latest -f Dockerfile.prod .

# Run with environment
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e OPENWEATHER_API_KEY=... \
  vibemap:latest
```

## VPS Deploy (Ubuntu)

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx

# Enable PostGIS
sudo apt install -y postgresql-15-postgis-3
```

### 2. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE vibemap;
CREATE USER vibemap WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE vibemap TO vibemap;

# Enable PostGIS
\c vibemap
CREATE EXTENSION postgis;

# Exit
\q
```

### 3. Application Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/vibemap.git
cd vibemap

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://vibemap:your_password@localhost/vibemap"
export OPENWEATHER_API_KEY="your_key"
# ... other variables

# Run migrations
alembic upgrade head

# Start with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 4. Nginx Setup

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/vibemap
```

```nginx
server {
    listen 80;
    server_name vibemap.live www.vibemap.live;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/vibemap /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d vibemap.live -d www.vibemap.live
```

### 6. Systemd Service

```bash
sudo nano /etc/systemd/system/vibemap.service
```

```ini
[Unit]
Description=Vibemap API
After=network.target

[Service]
User=vibemap
Group=vibemap
WorkingDirectory=/home/vibemap/vibemap
Environment="PATH=/home/vibemap/vibemap/venv/bin"
Environment="DATABASE_URL=postgresql://..."
ExecStart=/home/vibemap/vibemap/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable vibemap
sudo systemctl start vibemap
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `OPENWEATHER_API_KEY` | No | Weather data (free tier available) |
| `REDDIT_CLIENT_ID` | No | Reddit sentiment (free) |
| `REDDIT_CLIENT_SECRET` | No | Reddit sentiment (free) |
| `GOOGLE_PLACES_API_KEY` | No | Venue data (free tier available) |
| `TWITTER_BEARER_TOKEN` | No | X sentiment ($100+/mo) |

## Health Checks

```bash
# Check API health
curl https://vibemap.live/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "genesis_anchor_active": true
}
```

## Monitoring

### Logs

```bash
# Docker
docker-compose logs -f

# Systemd
sudo journalctl -u vibemap -f
```

### Metrics

The `/health` endpoint provides basic metrics:
- Total anchors
- Total check-ins
- Database connectivity

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check PostGIS
psql $DATABASE_URL -c "SELECT PostGIS_Version()"
```

### API Not Responding

```bash
# Check if process is running
sudo systemctl status vibemap

# Check logs
sudo journalctl -u vibemap -n 100
```

### CORS Errors

Ensure `allow_origins` in `main.py` includes your domain:
```python
allow_origins=["https://vibemap.live", "https://www.vibemap.live"]
```

## Scaling

### Horizontal Scaling

Deploy multiple instances behind a load balancer:

```yaml
# docker-compose.yml
services:
  api-1:
    build: .
    environment:
      - DATABASE_URL=...
  
  api-2:
    build: .
    environment:
      - DATABASE_URL=...
  
  nginx:
    image: nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
```

### Database Scaling

For high traffic, consider:
- Read replicas for GET requests
- Connection pooling (PgBouncer)
- Redis for caching

## Security Checklist

- [ ] Use strong database passwords
- [ ] Enable SSL/TLS
- [ ] Set up rate limiting
- [ ] Rotate API keys regularly
- [ ] Keep dependencies updated
- [ ] Monitor for suspicious activity

## Support

For deployment issues:
- Open a GitHub Issue
- Check existing issues for solutions
- Tag with `deployment` label