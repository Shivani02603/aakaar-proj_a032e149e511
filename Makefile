.PHONY: install dev build test docker-up docker-down clean

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	./scripts/dev.sh

build:
	docker-compose build

test:
	cd backend && python -m pytest

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf frontend/.next
	rm -rf frontend/node_modules