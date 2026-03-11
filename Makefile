SPHINXAPIDOC = venv/bin/sphinx-apidoc
SPHINXBUILD   = venv/bin/sphinx-build

.PHONY: docs

docs:
	find docs/source -name 'pytoolbox*.rst' -delete
	$(SPHINXAPIDOC) --force --module-first --separate -o docs/source pytoolbox
	rm -rf docs/build/html
	$(MAKE) -C docs html SPHINXBUILD=../$(SPHINXBUILD)
