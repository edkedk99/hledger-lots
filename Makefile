remote_server := phl
remote_wheel_dir=/shared/wheels

get_value = $(shell sed -n "s/\($1 \?= \?\"\)\(.*\)\(\"\)/\2/p" pyproject.toml)
pkg_name := $(call get_value,name)
version := $(call get_value,version)
vermin := 3.8
wheel := $(pkg_name)-$(version)-py3-none-any.whl

test_docs := pytest --cov=hledger_fifo tests/ --cov-report=html:docs/test_coverage && \
	mkdir -p docs/unit_tests && \
	pytest --html=docs/unit_tests/index.html

.PHONY: local
local:
	make build && \
	pip3 uninstall -y $(pkg_name) && \
	pip3 install dist/$(wheel)


.PHONY: build
build:
	make fix && python -m build



.PHONY: fix
fix:
	source venv/bin/activate && \
	pyright $(pkg_name) && \
	pycln $(pkg_name) && \
	isort --profile black $(pkg_name) && \
	black $(pkg_name) && \
	vermin -t=$(vermin) \
		--eval-annotations \
		--backport dataclasses \
		--backport typing \
		--no-parse-comments "$(pkg_name)" && \
	pytest

.PHONY: serve-docs
serve-docs:
	source venv/bin/activate && \
	$(test_docs) && \
	PYTHONPATH="$(CURDIR)" mkdocs serve

.PHONY: gh-deploy
gh-deploy:
	source venv/bin/activate && \
	$(test_docs) && \
	PYTHONPATH="$(CURDIR)" mkdocs gh-deploy


.PHONY: version
version:
	vermin -t=$(vermin) \
		--eval-annotations \
		--backport dataclasses \
		--backport typing \
		--no-parse-comments "$(pkg_name)"
