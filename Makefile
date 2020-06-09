install:
	pip3 install .

develop: uninstall
	python3 setup.py develop

uninstall:
	pip3 uninstall -y catsoop

test:
	python3 -m unittest -v catsoop/test/*test*.py

.PHONY: install develop test uninstall
