format-check:
	black --check .
format:
	black .
	flake8 .
publish:
	python3 setup.py sdist bdist_wheel
	twine upload --skip-existing dist/*
test:
	python3 -c "import objexplore; import rich; objexplore.explore(rich)"
# test:
# 	pytest tests
