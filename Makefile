# Frist24 — thin wrappers around docker compose. Every target has a plain-compose
# equivalent in README.md for machines without make.
.PHONY: up down demo logs reset test-api test-web

up:            ## Build and start web, api, db, ollama (+ model pull) in the background
	docker compose up -d --build
	@echo "web  -> http://localhost:3000"
	@echo "api  -> http://localhost:8000/docs"

down:          ## Stop everything, keep volumes (DB + pulled model)
	docker compose down

demo:          ## Seed products + SBOMs, sync KEV/EPSS/OSV, open incidents (step 5+)
	docker compose exec api python -m app.cli demo

logs:          ## Follow logs of all services
	docker compose logs -f --tail=100

reset:         ## Drop DB data and re-seed (keeps the pulled model)
	docker compose down -v --remove-orphans
	docker volume create frist24_ollama >/dev/null 2>&1 || true
	docker compose up -d --build

test-api:
	docker compose exec api pytest -q

test-web:
	docker compose exec web npm test --silent
