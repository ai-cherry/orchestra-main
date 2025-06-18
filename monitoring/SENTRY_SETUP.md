# Sentry Error Tracking

This project supports optional self-hosted Sentry for error monitoring.

## Quick Start

1. Set the `SENTRY_DSN` environment variable in your `.env` file.
2. Run Sentry using Docker Compose:

```bash
docker run -d --name sentry -p 9000:9000 \
  -e SENTRY_SECRET_KEY=generate_your_key \
  -e SENTRY_POSTGRES_HOST=postgres \
  sentry self-hosted
```

3. Access the Sentry UI at `http://localhost:9000` and create a project to obtain your DSN.
4. Restart the API so it can send errors to Sentry.

Errors from `main_api.py` and other services will now be captured automatically.
