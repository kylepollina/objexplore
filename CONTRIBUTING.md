# Contributing

## Running the [makefile](https://github.com/kylepollina/objexplore/blob/main/Makefile)

### `make pytest`
Runs the pytests for this package. Make sure to install the dev requirements in `dev-requirements.txt`

### `make check`
Running `make check` will run [mypy](http://mypy-lang.org/) and [flake8](https://flake8.pycqa.org/en/latest/) to check the code is typed correctly and to make sure it follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) guidelines.

### `make format`
Running `make format` will run the [black](https://pypi.org/project/black/) code formatter to automatically format the code.

### `make test`
Running `make test` will open up objexplore and explore the `rich` package for testing.
