# Quick Start Guide

Get up and running in **5 minutes**.

## Prerequisites

- Docker & Docker Compose (easiest), OR
- Python 3.11+ and Node.js 18+

## Step 1: Clone & Setup (2 minutes)

```bash
git clone <repo>
cd autonomous-sales-system
cp .env.example .env
```

## Step 2: Get API Keys (1 minute)

Get these free/cheap keys:
- **Claude API**: https://console.anthropic.com (free $5 credit)
- **Supabase**: https://supabase.com (free tier)
- **Hunter.io**: https://hunter.io (free: 25/month)
- **Apollo.io**: https://apollo.io (free: 100/month)

Add them to `.env`

## Step 3: Start System (2 minutes)

### With Docker (recommended)
```bash
docker-compose up
```

Visit:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Without Docker
```bash
# Terminal 1: Backend
python -m uvicorn backend.api:app --reload

# Terminal 2: Frontend
cd frontend && npm install && npm start
```

## Step 4: Generate Your First Leads

### Terminal 3:
```bash
# Test with 20 leads
python scrapers/multi_source_scraper.py --limit 20

# Or by ICP
python scrapers/multi_source_scraper.py --icp b2b_saas --limit 50

# Or from multiple sources
python scrapers/multi_source_scraper.py --sources yc,hunter,apollo --workers 10
```

Outputs: `leads.csv`

## Step 5: Import & Approve Drafts

1. Visit http://localhost:3000
2. Click "Import Leads" → select `leads.csv`
3. Select a lead
4. Click "Generate Draft"
5. Review → Click "Approve" to send

## Done! 🎉

You now have:
- ✅ 50-100 qualified leads
- ✅ AI-generated personalized messages
- ✅ Reply detection & classification
- ✅ Lead scoring & qualification
- ✅ Metrics dashboard

## Next Steps

1. **Define your ICP**: Edit `config/icp_profiles.json`
2. **Add more sources**: Uncomment in `multi_source_scraper.py`
3. **Setup Gmail**: Follow `docs/SETUP.md`
4. **Deploy**: See `docs/DEPLOYMENT.md`

## Available ICP Profiles

```bash
python scrapers/multi_source_scraper.py --list-icps

# Output:
# b2b_saas, fintech, ai_startups, healthcare, ecommerce, enterprise, logistics, edtech, realtech
```

## Commands Reference

```bash
# Scrape leads (all sources, unlimited)
python scrapers/multi_source_scraper.py

# Scrape with filters
python scrapers/multi_source_scraper.py --icp b2b_saas --limit 100 --workers 20

# Scrape specific sources only
python scrapers/multi_source_scraper.py --sources hunter,apollo

# List available ICPs
python scrapers/multi_source_scraper.py --list-icps

# Backend with debug
python -m uvicorn backend.api:app --reload --log-level debug

# Database shell
psql $DATABASE_URL

# View logs
docker-compose logs -f backend
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Port 8000 in use" | `lsof -ti:8000 \| xargs kill -9` |
| "Can't connect to database" | Check `.env` DATABASE_URL or SUPABASE_KEY |
| "Claude API rate limited" | Add spending limit in console, reduce --workers |
| "Gmail not working" | Download credentials JSON from Google Cloud Console |

## Cost Breakdown (First Month)

| Service | Cost | Notes |
|---------|------|-------|
| Claude API | $10-30 | 5-10M tokens |
| Supabase | $0 | Free tier (500MB) |
| Hunter.io | $0 | Free tier (25/month) |
| Apollo.io | $0 | Free tier (100/month) |
| Infrastructure | $0 | Local or free tier |
| **Total** | **$10-30** | Completely free to test |

## Documentation

- **Setup**: `docs/SETUP.md` - Detailed installation guide
- **API**: `docs/API.md` - Full API reference
- **Architecture**: `docs/ARCHITECTURE.md` - System design
- **Deployment**: `docs/DEPLOYMENT.md` - Production setup
- **Bottlenecks**: `docs/BOTTLENECKS.md` - Performance tips

## Support

- 📖 Read docs: `docs/` folder
- 🐛 Report bugs: GitHub Issues
- 💬 Discuss: GitHub Discussions
- 📧 Email: hello@autonomous-sales.com

---

**Questions? Start with: `docker-compose up` then visit http://localhost:3000**
