PY ?= $(shell command -v python3 >/dev/null 2>&1 && echo python3 || echo python)

.PHONY: check prober web hygiene budget

check:
	$(PY) scripts/check.py

prober:
	cd prober && uv run ruff check . ../scripts
	cd prober && uv run mypy src tests ../scripts
	cd prober && uv run pytest
	cd prober && uv run lint-imports

web:
	cd web && pnpm typecheck
	cd web && pnpm lint
	cd web && pnpm test
	cd web && pnpm arch

hygiene:
	$(PY) scripts/repo_hygiene.py

budget:
	cd prober && uv run python ../scripts/request_budget.py
