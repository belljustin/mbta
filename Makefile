clean:
	rm -rf dist/*

build: clean
	python3 -m build

upload: build
	python3 -m twine upload --repository testpypi dist/*