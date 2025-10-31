# ----------------------------------------------------------------
# Name:		Libs/WGU-OSMT
# Purpose:	Build WGU OSMT
# ----------------------------------------------------------------

install:
	poetry lock
	poetry check
	poetry update
	poetry install

test:
	poetry run pytest --disable-pytest-warnings

build:
	make install
	make test
	poetry build

freeze:
	poetry run pip freeze > requirements.txt
	poetry run python -m pip install --upgrade pip

all:
	make build
	make freeze
