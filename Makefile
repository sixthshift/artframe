.PHONY: build build-frontend install dev dev-backend dev-frontend test lint clean help

BACKEND_STATIC := backend/src/artframe/web/static/dist

# Default target
build: build-frontend
	rm -rf $(BACKEND_STATIC)
	cp -r frontend/dist $(BACKEND_STATIC)

# Build frontend (outputs to frontend/dist)
build-frontend:
	cd frontend && npm install && npm run build

# Install all dependencies
install:
	cd frontend && npm install
	cd backend && uv sync

# Run backend server (requires frontend to be built)
dev:
	cd backend && uv run artframe

# Run backend only (for development with separate frontend)
dev-backend:
	cd backend && uv run artframe

# Run frontend dev server (proxies API to backend)
dev-frontend:
	cd frontend && npm run dev

# Run backend tests
test:
	cd backend && uv run pytest

# Run linting
lint:
	cd backend && uv run black src tests
	cd backend && uv run isort src tests
	cd backend && uv run mypy src

# Clean build artifacts
clean:
	rm -rf frontend/dist
	rm -rf $(BACKEND_STATIC)
	rm -rf frontend/node_modules/.vite

help:
	@echo "Available targets:"
	@echo "  build          - Build frontend for production"
	@echo "  install        - Install all dependencies"
	@echo "  dev            - Run backend server"
	@echo "  dev-backend    - Run backend server"
	@echo "  dev-frontend   - Run frontend dev server with hot reload"
	@echo "  test           - Run backend tests"
	@echo "  lint           - Run linters (black, isort, mypy)"
	@echo "  clean          - Remove build artifacts"
