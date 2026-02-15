.PHONY: docs deploy depoly

DEPTH ?= 2

docs:
	python scripts/gen_mkdocs.py --depth $(DEPTH)

deploy: docs
	mkdocs gh-deploy

depoly: deploy
