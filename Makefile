install:
	poetry lock
	poetry check
	poetry update
	poetry install

build:
	make install
	poetry build

test:
	poetry run pytest -q -k test_fetch_wgu -m network
	poetry run pytest -q tests/test_fetch_wgu.py::test_fetch_single_skill_json_only -m network
	poetry run pytest -q tests/test_reports_prereqs.py

freeze:
	poetry run pip freeze > requirements.txt
	poetry run python -m pip install --upgrade pip

all:
	make build
	make test
	make freeze

fetch:
	poetry run python -m wgu_osmt_builder.common.cli fetch --dir wgu_osmt_builder/data/sources

build_ttl:
	poetry run python -m wgu_osmt_builder.common.cli build

validate:
	poetry run python -m wgu_osmt_builder.common.cli validate
