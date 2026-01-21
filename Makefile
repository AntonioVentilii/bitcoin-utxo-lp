POETRY := poetry run

format:
	$(POETRY)  black .
	$(POETRY)  ruff format .
	$(POETRY)  toml-sort --in-place pyproject.toml

lint:
	$(POETRY)  ruff check . --fix

typecheck:
	$(POETRY)  mypy .

test:
	pytest

all: format lint typecheck test
