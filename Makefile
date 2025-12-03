.PHONY: build install clean help

BACKEND_STATIC := backend/src/artframe/web/static/dist

# Default target
build:
	cd frontend && npm ci && npm run build
	rm -rf $(BACKEND_STATIC)
	cp -r frontend/dist $(BACKEND_STATIC)

# Install all dependencies
install:
	cd frontend && npm install
	cd backend && uv sync

# Clean build artifacts
clean:
	rm -rf frontend/dist
	rm -rf $(BACKEND_STATIC)
	rm -rf frontend/node_modules/.vite

help:
	@echo "Available targets:"
	@echo "  build   - Build frontend and copy to backend"
	@echo "  install - Install all dependencies"
	@echo "  clean   - Remove build artifacts"
