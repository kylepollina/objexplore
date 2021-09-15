format-check:
	black --check .
format:
	black .
	flake8 .
publish:
	python3 setup.py sdist bdist_wheel
	twine upload --skip-existing dist/*
# test:
# 	pytest tests
