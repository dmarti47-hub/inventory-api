# AWS EC2 Deployment

This deployment runs the React frontend, FastAPI backend, and PostgreSQL database on one EC2 instance. Nginx exposes only port 80 and proxies `/api` to FastAPI. The API and database ports are not published to the internet.

## Recommended EC2 configuration

- Region: `us-east-2` (Ohio)
- AMI: Ubuntu Server 24.04 LTS, 64-bit x86
- Instance: `t3.small`
- CPU credits: Standard
- Storage: 20 GiB `gp3`
- Security group inbound rules:
  - SSH (22) from **My IP** only
  - HTTP (80) from anywhere
  - HTTPS (443) from anywhere only after a domain and TLS proxy are configured

Do not open ports 5432, 8000, 8001, 5173, or 5433 in the EC2 security group.

## Initial server setup

Connect to the instance with SSH, then run:

```bash
git clone https://github.com/dmarti47-hub/inventory-api.git /tmp/inventory-api
sudo bash /tmp/inventory-api/deploy/ec2/bootstrap.sh
exit
```

Reconnect so the Docker group membership is active.

## Configure production secrets

```bash
cd /opt/inventory-api
cp .env.production.example .env.production
PASSWORD="$(openssl rand -hex 24)"
sed -i "s/replace_with_a_random_hex_password/${PASSWORD}/" .env.production
unset PASSWORD
chmod 600 .env.production
```

The generated `.env.production` file stays on EC2 and is ignored by Git.

## Deploy

```bash
cd /opt/inventory-api
./deploy/ec2/deploy.sh
```

Load the portfolio demonstration data once:

```bash
docker compose \
  --env-file .env.production \
  -f docker-compose.production.yml \
  exec api uv run python -m scripts.seed_demo_data
```

Open `http://EC2_PUBLIC_IP/` in a browser. API documentation is available at `http://EC2_PUBLIC_IP/api/docs`.

## Operations

Check service status:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

View logs:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml logs --tail=100
```

Deploy an update from `main`:

```bash
./deploy/ec2/deploy.sh
```

Back up PostgreSQL:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml \
  exec -T db pg_dump -U inventory_user inventory_db | gzip > "inventory-$(date +%F).sql.gz"
```

## HTTPS

An EC2 public IP or AWS-generated hostname is suitable for the initial demonstration. Before treating the deployment as production-like, attach a domain and add HTTPS using Caddy or an AWS load balancer and certificate. Do not expose authentication or sensitive data over plain HTTP.
