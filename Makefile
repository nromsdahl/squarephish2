run:
	python -m squarephish --config config.json -v

lint:
	ruff check .

install:
	pip install -e .
