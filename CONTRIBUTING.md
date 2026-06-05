# Contributing to Ghostrace

Thank you for your interest in contributing to **Ghostrace** — an AI agent observability platform.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Suraj-kummar/Ghostrace.git
cd Ghostrace

# 2. Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Run the backend
uvicorn app.main:app --reload --port 8000

# 4. Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev
```

### Running Tests

```bash
# From the repo root:
cd backend
pytest
```

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable production-ready code |
| `feat/*` | New features |
| `fix/*` | Bug fixes |
| `chore/*` | Tooling, dependency, config changes |
| `docs/*` | Documentation only |

---

## Commit Convention

We follow **Conventional Commits**:

```
<type>(<scope>): <short description>

Types: feat, fix, chore, docs, test, refactor, style, perf, ci
```

Examples:
```
feat(sessions): add export endpoint
fix(auth): handle expired JWT gracefully
test(analytics): add coverage for weekly trends
```

---

## Pull Request Guidelines

1. **One concern per PR** — keep PRs focused and reviewable.
2. **Add tests** for every new feature or bug fix.
3. **Update docs** if you add or change public APIs.
4. **Link to issue** in the PR description if one exists.
5. All CI checks must pass before merge.

---

## Code Style

- **Python**: Follow PEP 8. We use `ruff` for linting.
- **TypeScript**: ESLint + Prettier. Run `npm run lint` before committing.
- Keep functions small and well-documented.
- Use type hints in Python everywhere.

---

## Reporting Issues

Open an issue with:
- A clear title and description
- Steps to reproduce
- Expected vs. actual behaviour
- Your OS and Python/Node versions

---

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
