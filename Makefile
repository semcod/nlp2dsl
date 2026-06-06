# =============================================================================
# NLP2DSL Makefile
# =============================================================================

.PHONY: help install install-dev update test build build-packages build-all clean \
        check-pypi-deps publish publish-packages publish-root setup-dev

PYTHON ?= $(shell if [ -x ./.venv/bin/python3 ]; then echo ./.venv/bin/python3; elif [ -x ./venv/bin/python3 ]; then echo ./venv/bin/python3; else echo python3; fi)

PACKAGES := \
	packages/pact-ir \
	packages/nlp2cmd-intent \
	packages/nlp2cmd-planner \
	packages/nlp2cmd-propact \
	packages/nlp2dsl-show

GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m

.DEFAULT_GOAL := help

help: ## Show this help
	@echo "$(BLUE)NLP2DSL — Makefile$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-22s$(NC) %s\n", $$1, $$2}'

install: ## Install root SDK (editable)
	$(PYTHON) -m pip install -e .

install-dev: setup-dev ## Install SDK + packages + optional nlp2cmd integration

setup-dev: ## Run scripts/setup-dev.sh
	@./scripts/setup-dev.sh

update: ## Reinstall all packages + SDK + nlp2cmd integration (editable, --upgrade)
	@echo "$(YELLOW)==> update integration stack$(NC)"
	@./scripts/setup-dev.sh

test: ## Run tests
	$(PYTHON) -m pytest tests/ -v

test-parallel: test ## Alias for goal/Makefile compatibility

check-pypi-deps: ## Verify build/twine are installed (auto-install if missing)
	@$(PYTHON) -c "import build, twine" 2>/dev/null || $(PYTHON) -m pip install build twine -q

clean: ## Remove build artifacts (root + packages)
	rm -rf dist/ build/ *.egg-info
	@for pkg in $(PACKAGES); do \
		rm -rf $$pkg/dist $$pkg/build $$pkg/src/*.egg-info 2>/dev/null || true; \
	done
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build: check-pypi-deps ## Build root nlp2dsl SDK wheel
	@echo "$(YELLOW)==> build root SDK$(NC)"
	$(PYTHON) -m build .

build-packages: check-pypi-deps ## Build all packages/ wheels (dependency order)
	@for pkg in $(PACKAGES); do \
		echo "$(YELLOW)==> build $$pkg$(NC)"; \
		$(PYTHON) -m build $$pkg; \
	done

build-all: build build-packages ## Build root SDK + all packages

publish-root: build ## Upload root SDK to PyPI
	@echo "$(YELLOW)==> twine upload root SDK$(NC)"
	$(PYTHON) -m twine upload dist/*

PYPI_UPLOAD_DELAY ?= 12

publish-packages: build-packages ## Upload all packages/ to PyPI
	@for pkg in $(PACKAGES); do \
		echo "$(YELLOW)==> twine upload $$pkg$(NC)"; \
		$(PYTHON) -m twine upload --skip-existing $$pkg/dist/* || exit 1; \
		sleep $(PYPI_UPLOAD_DELAY); \
	done

publish-package: check-pypi-deps ## Upload one package (PKG=packages/nlp2dsl-show)
	@test -n "$(PKG)" || (echo "Usage: make publish-package PKG=packages/nlp2dsl-show" && exit 1)
	@echo "$(YELLOW)==> build $(PKG)$(NC)"
	@$(PYTHON) -m build $(PKG)
	@echo "$(YELLOW)==> twine upload $(PKG)$(NC)"
	@$(PYTHON) -m twine upload --skip-existing $(PKG)/dist/*

publish: update build-all ## Update editable installs, build and publish to PyPI
	@echo "$(YELLOW)==> Publishing nlp2dsl + packages to PyPI$(NC)"
	$(PYTHON) -m twine upload dist/*
	@for pkg in $(PACKAGES); do \
		echo "$(YELLOW)==> twine upload $$pkg$(NC)"; \
		$(PYTHON) -m twine upload $$pkg/dist/*; \
	done
	@echo "$(GREEN)Done: nlp2dsl + $(words $(PACKAGES)) packages published$(NC)"

version: ## Show root SDK version
	@grep -m1 '^version = ' pyproject.toml | cut -d'"' -f2

package-versions: ## Show package versions
	@for pkg in $(PACKAGES); do \
		v=$$(grep -m1 '^version = ' $$pkg/pyproject.toml | cut -d'"' -f2); \
		echo "$$pkg: $$v"; \
	done
