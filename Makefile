# Car Repair, in Plain English — developer tasks
# (No dependencies beyond Python 3.9+ and the `markdown` package.)

PY ?= python3

.PHONY: build test serve clean check

build:
	$(PY) tools/build.py

test:
	$(PY) -m unittest discover -s tests -v

serve: build
	@echo "Serving site/ at http://localhost:8000 (Ctrl+C to stop)"
	$(PY) -m http.server 8000 --directory site

check: build test

clean:
	rm -rf site
