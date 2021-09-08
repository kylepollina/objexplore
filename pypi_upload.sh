# Script for uploading current package to pypi
python3 setup.py sdist bdist_wheel
twine upload --skip-existing dist/*
