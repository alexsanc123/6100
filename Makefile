install:
	pip3 install .

develop:
	pip3 install -e .

uninstall:
	pip3 uninstall -y catsoop

test:
	pytest catsoop/test

.PHONY: install develop test uninstall
