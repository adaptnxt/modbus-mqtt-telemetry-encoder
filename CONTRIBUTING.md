# Contributing to AdaptNXT Telemetry & Edge Buffer

Thank you for your interest in contributing to the AdaptNXT open-source ecosystem! We welcome bug reports, documentation enhancements, feature proposals, and pull requests.

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat everyone with respect and kindness.

---

## Development Workflow

### 1. Fork & Clone
Fork the repository on GitHub and clone your fork locally:
```bash
git clone https://github.com/<your-username>/modbus-mqtt-telemetry-encoder.git
cd modbus-mqtt-telemetry-encoder
```

### 2. Environment Setup
We recommend using Python 3.10+ in a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e .[dev]
```

### 3. Running Tests
Ensure all unit tests pass before submitting code:
```bash
pytest tests/ -v
```

### 4. Code Standards
- **Typing**: Use standard Python type annotations on all public functions and methods.
- **Docstrings**: Include descriptive docstrings detailing arguments, returns, and raised exceptions.
- **Error Handling**: Use the custom exception hierarchy in `src/adaptnxt_telemetry/exceptions.py`.

---

## Submitting Pull Requests

1. Create a descriptive branch: `git checkout -b feature/sparkplug-b-support` or `git checkout -b fix/sqlite-lock-timeout`.
2. Commit your changes with conventional commit messages (`feat:`, `fix:`, `docs:`, `test:`).
3. Push to your fork and open a Pull Request against `main`.
4. Fill out the PR template completely. Maintainers from [AdaptNXT](https://www.adaptnxt.com) review PRs promptly.

---

## Questions & Support

For architecture questions, commercial support, or edge hardware integration consulting, reach out to the engineering team at [queries@adaptnxt.com](mailto:queries@adaptnxt.com).
