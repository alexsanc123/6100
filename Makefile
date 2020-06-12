install:
	pip3 install .

develop: uninstall
	python3 setup.py develop

uninstall:
	pip3 uninstall -y catsoop

test:
	pytest catsoop/test

.PHONY: install develop test uninstall
