# Artframe Development Container

This devcontainer provides a complete Python development environment for Artframe without requiring Python to be installed on your host machine.

## Quick Start

### Prerequisites
- [VS Code](https://code.visualstudio.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for VS Code

### Getting Started

1. **Clone and Open Project**:
   ```bash
   git clone <your-repo-url>
   cd artframe
   code .
   ```

2. **Open in Container**:
   - VS Code will prompt: "Reopen in Container" → Click **Reopen in Container**
   - Or use Command Palette (`Ctrl+Shift+P`): "Dev Containers: Reopen in Container"

3. **Wait for Setup**:
   - First time takes 5-10 minutes (downloads Python, installs dependencies)
   - Subsequent opens are much faster

4. **Start Developing**:
   - Environment is fully configured with Python 3.11, all dependencies, and tools
   - Terminal is ready to use with all Artframe commands

## What's Included

### Development Tools
- **Python 3.11** with pip, setuptools, wheel
- **Code Formatting**: black, autopep8, isort
- **Linting**: flake8, pylint, mypy
- **Testing**: pytest, pytest-cov, pytest-mock
- **Development**: IPython, Jupyter notebooks
- **Security**: bandit for security scanning

### VS Code Extensions (Auto-installed)
- Python language support
- Testing integration
- Git integration (GitLens)
- YAML/JSON editing
- Code spell checking
- Remote SSH (for Pi deployment)

### Pre-configured Features
- **Python path**: Automatically set to `src/`
- **Testing**: pytest discovery and running
- **Formatting**: Black on save
- **Type checking**: mypy integration
- **Git hooks**: Pre-commit formatting
- **Debug configs**: Ready-to-use launch configurations

## Directory Structure

```
.devcontainer/
├── devcontainer.json       # Main container configuration
├── Dockerfile             # Python environment setup
├── docker-compose.yml     # Multi-service setup (optional)
├── post-create.sh         # Setup script run after container creation
└── .env.template          # Environment variables template
```

## Development Workflow

### 1. Environment Setup (One-time)
```bash
# Container automatically runs post-create.sh which:
# - Installs Artframe in development mode
# - Creates .env from template
# - Sets up directories and git hooks
# - Runs basic tests

# Edit your API keys
code .env
```

### 2. Daily Development
```bash
# All commands work immediately in the container terminal:

# Run tests
pytest tests/ -v

# Format code
black src/ tests/

# Type check
mypy src/artframe

# Test locally with mock display
python examples/simple_test.py

# Test Artframe commands
python -m artframe.main --config config/artframe-dev.yaml test
python -m artframe.main --config config/artframe-dev.yaml update
```

### 3. Deploy to Raspberry Pi
```bash
# Deploy code to Pi (from container)
./scripts/deploy.sh pi@192.168.1.100

# Quick test on Pi
./scripts/quick_test.sh pi@192.168.1.100
```

## VS Code Integration

### Debug Configurations (F5)
- **Test Connection**: Debug API connections
- **Manual Update**: Debug photo update workflow
- **Show Status**: Debug status reporting
- **Run Scheduler**: Debug scheduling loop
- **Simple Test**: Debug basic functionality

### Tasks (Ctrl+Shift+P → "Tasks: Run Task")
- **Run Tests**: Execute pytest
- **Format Code**: Run black formatter
- **Type Check**: Run mypy
- **Deploy to Pi**: Deploy to Raspberry Pi
- **Generate Coverage**: Coverage report

### Useful Shortcuts
- `Ctrl+Shift+P`: Command palette
- `Ctrl+`` : Open terminal
- `F5`: Start debugging
- `Ctrl+Shift+I`: Format document
- `Ctrl+Shift+M`: Show problems panel

## Configuration Files

### .env (API Keys)
```bash
# Copy from template and fill in your values
cp .env.example .env
code .env
```

### SSH Keys for Pi Deployment
```bash
# Your host SSH keys are mounted read-only at ~/.ssh
# To add new keys or configure SSH for Pi access:
mkdir -p .devcontainer/ssh
cp ~/.ssh/id_rsa .devcontainer/ssh/
cp ~/.ssh/id_rsa.pub .devcontainer/ssh/
```

## Troubleshooting

### Container Won't Start
- Ensure Docker Desktop is running
- Check Docker has enough memory (4GB+ recommended)
- Try: "Dev Containers: Rebuild Container"

### Python Import Errors
- PYTHONPATH is pre-configured to include `src/`
- If issues persist: `pip install -e .`

### Permission Issues with Pi Deployment
```bash
# Fix SSH permissions in container
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Add Pi to known hosts
ssh-keyscan -H pi@192.168.1.100 >> ~/.ssh/known_hosts
```

### Port Conflicts
- Container exposes ports 8000, 8080, 5000
- If conflicts occur, modify `devcontainer.json` ports section

## Advanced Usage

### Multiple Containers
```bash
# Use docker-compose for additional services
docker-compose -f .devcontainer/docker-compose.yml up -d
```

### Persist Data
- Python packages persist in named volume `artframe-python`
- Bash history persists in `artframe-bashhistory`
- SSH keys mounted from host or `.devcontainer/ssh/`

### Custom Configuration
Edit `.devcontainer/devcontainer.json` to:
- Add more VS Code extensions
- Change Python version
- Add additional tools
- Modify environment variables

### Remote Debugging
```bash
# Install remote debugger in your code
pip install debugpy

# Add to your Python code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()

# Use "Python: Remote Attach" debug configuration
```

## Performance Tips

- **First build**: Takes 5-10 minutes
- **Rebuilds**: Use "Rebuild Container" sparingly
- **Dependencies**: Changes to requirements.txt trigger reinstall
- **File watching**: Large directories excluded via .dockerignore

## Container Lifecycle

1. **Build**: Downloads Python, installs system packages
2. **Create**: Runs post-create.sh setup script
3. **Start**: Ready for development
4. **Stop**: Preserves volumes and settings
5. **Rebuild**: Full rebuild when Dockerfile changes

---

Happy coding in your containerized Python environment! 🐍📦