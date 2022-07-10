help:
	@echo 'make install:          Install package, hook, notebooks and gdslib'
	@echo 'make test:             Run tests with pytest'
	@echo 'make test-force:       Rebuilds regression test'

install:
	cp -r klayout_pyxs  ~/.klayout/python/
	cp pymacros/pyxs.lym  ~/.klayout/pymacros/
	# ln -s $(PWD)/klayout_pyxs  ~/.klayout/python/


release:
	git push
	git push origin --tags

upload-twine: build
	pip install twine
	twine upload dist/*

lint:
	flake8

pylint:
	pylint --rcfile .pylintrc klayout_pyxs/

lintdocs:
	flake8 --select RST

pydocstyle:
	pydocstyle klayout_pyxs

doc8:
	doc8 docs/

autopep8:
	autopep8 --in-place --aggressive --aggressive **/*.py

codestyle:
	pycodestyle --max-line-length=88
