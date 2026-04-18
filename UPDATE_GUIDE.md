# VPS Update Guide

Use this guide when the application is already deployed and you only want to update it with the latest code.

## 1. SSH into the VPS

```bash
ssh root@your-vps-ip
```

## 2. Go to the project directory

```bash
cd /root/Ayush_Project
```

## 3. Run the update script

```bash
./update_app.sh
```

This script will:
- pull the latest code from GitHub
- copy `.env.prod` into `.env`
- rebuild and restart the containers
- show container status and recent web logs

## 4. Useful commands

Check container status:

```bash
docker-compose ps
```

See web logs:

```bash
docker-compose logs -f web
```

See database logs:

```bash
docker-compose logs -f db
```

Restart containers:

```bash
docker-compose restart
```

Stop containers:

```bash
docker-compose down
```

Start containers again:

```bash
docker-compose up -d
```
