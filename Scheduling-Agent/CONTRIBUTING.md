# Contributing to Scheduling Agent

Thank you for your interest in contributing to this AB Talks Open Agent!

## How to Contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/my-improvement`)
3. **Commit** your changes (`git commit -m 'Add: my improvement'`)
4. **Push** to the branch (`git push origin feature/my-improvement`)
5. **Open** a Pull Request

## Development Setup

```bash
# Clone the repo
git clone https://github.com/ab-talks/scheduling-agent.git

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Fill in your Zoom OAuth and SMTP credentials

# Run the example
python example.py
```

## Code Style

- Python: Follow PEP 8
- Use type hints for all function signatures
- Add docstrings for all public methods
- Keep the agent class dependency-free (no SQLAlchemy, no FastAPI)

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce
- Include the Agent Decision Log output if applicable

## Architecture Rules

1. **The agent is pure intelligence** — it returns decisions, not side effects
2. **The router is the orchestrator** — it calls Zoom, Email, and DB
3. **Never import external services inside the agent class**

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
