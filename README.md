
![logo](images/logo.png)

Objexplore is an interactive Python object explorer for the terminal. Use it while debugging, or exploring a new library, or whatever!

![cibuild](https://github.com/kylepollina/objexplore/actions/workflows/python-app.yml/badge.svg) [![pypi](https://img.shields.io/pypi/v/objexplore.svg)](https://pypi.org/project/objexplore/) [![downloads](https://img.shields.io/pypi/dm/objexplore)](https://img.shields.io/pypi/dm/objexplore)




https://user-images.githubusercontent.com/13981456/134781043-a2d2b375-12b6-4400-8b54-b59720b2f8b8.mov



## Install

```
pip install objexplore
```

or

```
pip install git+https://github.com/kylepollina/objexplore
```

## Usage

```python
from objexplore import explore
import rich
explore(rich)
```

## Features

- [Type filters](#type-filters)
- [Search filters](#search-filters)
- [Stack view](#stack-view)
- [Exploring and returning](#exploring-and-returning)
- [Open the source file in `$EDITOR`](#open-source-file-in-editor)


### Type Filters


https://user-images.githubusercontent.com/13981456/134781148-7068ff86-ba6f-4996-9a98-d7dc3adcdf54.mov



### Search Filters


https://user-images.githubusercontent.com/13981456/134781262-b8e38485-3346-4d81-bfd0-4ea318001ed8.mov


### Stack view


https://user-images.githubusercontent.com/13981456/134781375-f630647d-6fc2-4d13-9ba9-92b9f397e103.mov


### Exploring and returning


https://user-images.githubusercontent.com/13981456/133946981-3bf5cfda-6eac-4514-abb3-e073dd3fb6b2.mov


### Open source file in `$EDITOR`


https://user-images.githubusercontent.com/13981456/134768632-1d3d22a8-7554-4085-b25b-94fee2528df4.mov


-----

Built with the amazing [rich](https://github.com/willmcgugan/rich) and [blessed](https://github.com/jquast/blessed) packages. Check them out!


## Contributing
Read [CONTRIBUTING.md](CONTRIBUTING.md)

------

[LICENSE](LICENSE)
