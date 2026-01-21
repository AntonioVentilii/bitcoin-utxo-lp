format:
	poetry run black .
	poetry run ruff format .
	poetry run toml-sort --in-place pyproject.toml

lint:
	poetry run ruff check .

typecheck:
	poetry run mypy .

test:
	pytest

all: format lint typecheck test
