format-check:
	black --check .
format:
	black .
	flake8 .
# test:
# 	pytest tests
