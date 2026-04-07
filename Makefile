# =============================================================================
# Finance Analytics API — Developer Makefile
# =============================================================================

.PHONY: help install run seed test test-cov lint docker-up docker-down docker-logs clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Local Development ---

install:  ## Install all dependencies into active venv
	pip install -r requirements.txt

run:  ## Run the API server with hot reload
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

seed:  ## Seed the database with sample data
	python seed.py

# --- Testing ---

test:  ## Run all tests
	pytest tests/ -v

test-cov:  ## Run tests with coverage report
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# --- Code Quality ---

lint:  ## Run linting (requires ruff: pip install ruff)
	ruff check app/ tests/

format:  ## Format code (requires ruff)
	ruff format app/ tests/

# --- Docker ---

docker-up:  ## Start the full stack (app + postgres) in detached mode
	docker-compose up --build -d

docker-down:  ## Stop and remove all containers
	docker-compose down

docker-logs:  ## Follow application logs
	docker-compose logs -f app

docker-seed:  ## Run seed script inside the running container
	docker-compose exec app python seed.py

# --- Maintenance ---

clean:  ## Remove Python cache files and test artifacts
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -f .coverage coverage.xml

migrate:  ## Run Alembic database migrations
	alembic upgrade head

migration:  ## Create a new Alembic migration (usage: make migration MSG="your message")
	alembic revision --autogenerate -m "$(MSG)"
