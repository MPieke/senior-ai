# Senior AI

A calm, local-first assistant for helping people understand everyday messages
and documents. It runs with deterministic demo responses by default; add an
OpenAI key only when you want live analysis.

## Run it

1. Install Docker Desktop.
2. Optionally copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
3. Run `make up`.
4. Open [http://localhost:4173](http://localhost:4173).

Use `make status` to see service health, `make logs` to follow both services,
`make logs-api` or `make logs-web` to focus on one service, and `make down` to
stop the application. Analyses and retained uploaded documents live in the
`senior-ai-data` Docker volume and survive `make down`.

## Commands

Run `make help` for the complete command list.

```sh
make test       # runtime interface + backend + frontend unit tests
make test-e2e   # browser tests; install Chromium once with:
npx --prefix frontend playwright install chromium
make smoke      # after make up, check API and web HTTP responses
```

Never commit `.env`; it may contain your OpenAI API key.
