# Production Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repo-url>
cd Dept-Dashboard

# Copy and edit production environment
cp .env.prod.example .env.prod

# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output to SECRET_KEY in .env.prod
```

### 2. Configure Environment Variables

Edit `.env.prod`:

```env
DEBUG=false
SECRET_KEY=<your-generated-key>
DB_PASSWORD=<strong-database-password>
CAS_USE_MOCK=false
CAS_SERVICE_URL=https://your-domain.fr/api/auth/cas/callback
FRONTEND_URL=https://your-domain.fr
CORS_ORIGINS=["https://your-domain.fr"]
```

### 3. SSL Certificates

#### Option A: Let's Encrypt (Recommended)

```bash
# Create directories
mkdir -p nginx/ssl certbot/www

# Start nginx temporarily for certificate validation
docker-compose -f docker-compose.prod.yml up -d nginx

# Get certificate
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d your-domain.fr \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Update nginx.prod.conf with your domain
sed -i 's/your-domain.fr/YOUR_ACTUAL_DOMAIN/g' nginx/nginx.prod.conf
```

#### Option B: Self-Signed (Testing Only)

```bash
mkdir -p nginx/ssl/live/your-domain.fr

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/live/your-domain.fr/privkey.pem \
  -out nginx/ssl/live/your-domain.fr/fullchain.pem \
  -subj "/CN=your-domain.fr"
```

### 4. Deploy

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend alembic upgrade head
```

### 6. Seed Demo Data (Optional)

Populate the database with demo users, budget data, and recruitment data:

```bash
# Via CLI
docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m app.seeds

# Or via API (after services are running)
curl -X POST "http://localhost:8000/api/admin/seed"

# To reseed (deletes existing data)
docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m app.seeds --force
```

**Demo accounts created:**

| Login | Role |
|-------|------|
| `admin` | Superadmin (all permissions) |
| `chef_rt` | RT department admin |
| `chef_geii` | GEII department admin |
| `enseignant_rt` | RT teacher (view scolarite/edt only) |
| `secretaire` | Secretary (scolarite/recrutement for RT & GEII) |
| `pending_user` | Inactive account (pending validation) |

**Demo data includes:**
- 3 years of budget data per department (6 departments)
- 4 years of Parcoursup/recruitment data per department
- Sample expenses and candidates

### 7. Create Admin User (Production)

For production without demo data, connect via CAS then set superadmin:

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod exec db psql -U dashboard -d dept_dashboard

# In psql:
UPDATE "user" SET is_superadmin = true, is_active = true WHERE cas_login = 'your_cas_login';
\q
```

## Maintenance

### Backup Database

```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump -U dashboard dept_dashboard > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U dashboard dept_dashboard
```

### Update Application

```bash
git pull
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Renew SSL Certificate

```bash
docker-compose -f docker-compose.prod.yml --profile ssl up -d certbot
```

## Troubleshooting

### Backend not starting

```bash
docker-compose -f docker-compose.prod.yml logs backend
```

Common issues:
- `SECRET_KEY must be changed in production` - Set a proper secret key
- `CAS_USE_MOCK must be False` - Set `CAS_USE_MOCK=false`
- Database connection failed - Check DB_PASSWORD and DATABASE_URL

### 502 Bad Gateway

- Backend might still be starting: `docker-compose logs -f backend`
- Check if backend is healthy: `docker-compose ps`

### CAS Redirect Issues

- Ensure `CAS_SERVICE_URL` matches your domain exactly
- Check CORS_ORIGINS includes your frontend URL
