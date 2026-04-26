# Setup Guide - Autonomous Sales System

Complete step-by-step instructions to get the system running locally and in production.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ or Supabase account
- Git

## Local Development Setup (10 minutes)

### 1. Clone Repository

```bash
git clone <repo-url>
cd autonomous-sales-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 5a. Option A: Docker (Recommended for full stack)

```bash
docker-compose up
# Starts: PostgreSQL, Redis, Backend, Frontend scaffold
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 5b. Option B: Manual Setup

#### Database Setup

```bash
# If using PostgreSQL locally
createdb autonomous_sales

# Run migrations
psql autonomous_sales < migrations/001_initial_schema.sql

# Or with Supabase (recommended)
psql $SUPABASE_CONNECTION_STRING < migrations/001_initial_schema.sql
```

#### Start Backend

```bash
python -m uvicorn backend.api:app --reload --port 8000
```

The backend supports two modes:

- With `SUPABASE_URL` and `SUPABASE_KEY`, it uses Supabase tables.
- Without them, it falls back to an in-memory store for local development and tests.

#### Start Frontend

```bash
cd frontend
npm install
npm start
```

The frontend now ships with an operator console, though the backend is still the most production-ready part of the repo today.

The current UI is an operator console that expects `REACT_APP_API_URL` to point at the FastAPI server.

## Production Deployment

### Option 1: Railway + Vercel (Easiest)

#### Backend on Railway

1. Sign up at https://railway.app
2. Connect GitHub repo
3. Create new project
4. Add PostgreSQL plugin
5. Set environment variables (from .env)
6. Deploy

```bash
# Or deploy from CLI
railway login
railway link
railway up
```

#### Frontend on Vercel

```bash
cd frontend
npm install -g vercel
vercel --prod
```

### Option 2: Self-Hosted (AWS/GCP/DigitalOcean)

#### 1. Create Server (Ubuntu 22.04)

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
```

#### 2. Clone & Setup

```bash
git clone <repo> /opt/autonomous-sales
cd /opt/autonomous-sales

# Create .env from template
cp .env.example .env
# Edit .env with production values
```

#### 3. Create Systemd Service

```bash
cat > /etc/systemd/system/autonomous-sales.service << EOF
[Unit]
Description=Autonomous Sales System
After=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/autonomous-sales
ExecStart=/usr/bin/docker-compose up
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable autonomous-sales
systemctl start autonomous-sales
```

#### 4. Setup Reverse Proxy (Nginx)

```bash
apt-get install nginx

cat > /etc/nginx/sites-available/autonomous-sales << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
    }
}
EOF

ln -s /etc/nginx/sites-available/autonomous-sales /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### 5. SSL Certificate (Let's Encrypt)

```bash
apt-get install certbot python3-certbot-nginx
certbot certonly --nginx -d your-domain.com
```

## API Keys Setup

### 1. Anthropic (Claude)

1. Go to https://console.anthropic.com/account/keys
2. Create new API key
3. Add to `.env`: `CLAUDE_API_KEY=sk-...`

### 2. Supabase (Database)

1. Go to https://supabase.com
2. Create new project
3. Go to Settings → API → Copy URL & anon key
4. Add to `.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=eyJ...
   ```

### 3. Hunter.io (Email Enrichment)

1. Go to https://hunter.io/signup
2. Create account (free tier: 25 searches/month)
3. Get API key from dashboard
4. Add to `.env`: `HUNTER_API_KEY=...`

### 4. Apollo.io (B2B Leads)

1. Go to https://apollo.io
2. Sign up (free tier: 100 searches/month)
3. Get API key from settings
4. Add to `.env`: `APOLLO_API_KEY=...`

### 5. Google Gmail API

1. Go to https://console.cloud.google.com
2. Create new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download JSON file
6. Save as `google_credentials.json`
7. Add to `.env`: `GMAIL_CREDENTIALS_JSON=/path/to/google_credentials.json`

### 6. Calendly

1. Go to https://calendly.com/integrations
2. Find API in settings
3. Create API key
4. Add to `.env`: `CALENDLY_API_KEY=...`

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/test_api.py

# Integration tests
pytest tests/test_scrapers.py

# All tests
pytest
```

### Manual Testing

```bash
# Test scraper
python scrapers/multi_source_scraper.py --limit 20

# Test backend
curl http://localhost:8000/health

# Test frontend
open http://localhost:3000
```

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python -m uvicorn backend.api:app --port 8001
```

### Database Connection Error

```bash
# Check Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Claude API Rate Limited

```bash
# Check API usage
curl https://api.anthropic.com/v1/account/usage \
  -H "x-api-key: $CLAUDE_API_KEY"

# Reduce batch size
python scrapers/multi_source_scraper.py --workers 2
```

### Docker Issues

```bash
# Check logs
docker-compose logs -f backend

# Rebuild containers
docker-compose build --no-cache
docker-compose up
```

## Monitoring & Logs

### Backend Logs

```bash
# With Docker
docker-compose logs -f backend

# With systemd
journalctl -u autonomous-sales -f

# Application logs
tail -f logs/backend.log
```

### Database Monitoring

```bash
# Supabase Studio (web)
# https://supabase.com/dashboard

# Local PostgreSQL
psql autonomous_sales

# Check table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname != 'pg_catalog'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Performance Optimization

### Database Indexing

```bash
# Check missing indexes
SELECT schemaname, tablename FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY tablename;

# Add custom indexes
psql autonomous_sales < migrations/002_add_indexes.sql
```

### Caching

- Template caching: Enabled in `backend/api.py`
- Hit rate target: 80-90%
- Monitor in logs: "Cache hit rate: X%"

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/locustfile.py --host=http://localhost:8000
```

## Backup & Recovery

### Supabase Backups

Automatic daily backups included. Point-in-time recovery available.

### Manual Backup

```bash
# PostgreSQL
pg_dump autonomous_sales > backup_$(date +%Y%m%d).sql

# Restore
psql autonomous_sales < backup_20240101.sql
```

## Next Steps

1. **Configure ICP profiles** - Edit `config/icp_profiles.json`
2. **Run first scrape** - `python scrapers/multi_source_scraper.py --limit 20`
3. **Generate drafts** - Visit http://localhost:3000
4. **Monitor metrics** - Check dashboard for funnel

## Support & Resources

- API Docs: http://localhost:8000/docs
- GitHub Issues: Report bugs
- Discussions: Ask questions
- Email: hello@autonomous-sales.com

---

**You're all set! Start with: `docker-compose up`**
