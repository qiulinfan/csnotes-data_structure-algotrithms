.PHONY: docs deploy depoly

DEPTH ?= 3

docs:
	python scripts/gen_mkdocs.py --depth $(DEPTH)

deploy: docs
	mkdocs gh-deploy

depoly: deploy
