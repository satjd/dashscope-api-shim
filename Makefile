.PHONY: help install install-dev test test-cov lint format clean run docker-build docker-run

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PROJECT_NAME := dashscope-api-shim
DOCKER_IMAGE := $(PROJECT_NAME):latest

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt
	pre-commit install

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=dashscope_api_shim --cov-report=html --cov-report=term

lint: ## Run linters
	ruff check dashscope_api_shim tests
	mypy dashscope_api_shim

format: ## Format code with black
	black dashscope_api_shim tests
	ruff check --fix dashscope_api_shim tests

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info

run: ## Run the development server
	uvicorn dashscope_api_shim.main:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Run Docker container
	docker run -d \
		-p 8000:8000 \
		-e DASHSCOPE_API_KEY=$${DASHSCOPE_API_KEY} \
		--name $(PROJECT_NAME) \
		$(DOCKER_IMAGE)

docker-stop: ## Stop Docker container
	docker stop $(PROJECT_NAME) || true
	docker rm $(PROJECT_NAME) || true

docker-logs: ## Show Docker container logs
	docker logs -f $(PROJECT_NAME)

setup-env: ## Create .env file from example
	cp .env.example .env
	@echo "Please edit .env file and add your API keys"