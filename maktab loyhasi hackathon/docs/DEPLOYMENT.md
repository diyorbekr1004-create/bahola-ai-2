Deployment guide (minimal)

1) Local Docker Compose

- Build and run services:

```bash
docker-compose up --build
```

- Backend available: http://localhost:8000/docs
- Frontend: http://localhost:8501

2) Production checklist

- Use managed Postgres (Azure Database for PostgreSQL / Cloud SQL)
- Set `DATABASE_URL` env var to Postgres connection string
- Set `OPENAI_API_KEY` and `TEACHER_API_KEY` securely
- Use HTTPS (TLS termination)
- Configure backup and retention for DB
- Use secrets manager for API keys

3) Optional: Deploy to Azure App Service or container instances
- Build Docker images and push to registry
- Use orchestration (AKS) or App Service for containers

