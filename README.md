
![logo](images/logo.png)

Objexplore is an interactive Python object explorer for the terminal. Use it while debugging, or exploring a new library, or whatever!

![cibuild](https://github.com/kylepollina/objexplore/actions/workflows/python-app.yml/badge.svg) [![pypi](https://img.shields.io/pypi/v/objexplore.svg)](https://pypi.org/project/objexplore/)



https://user-images.githubusercontent.com/13981456/133946377-23444e20-61c9-4fac-85fa-f0f93674bc73.mov




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
import pandas
explore(pandas)
```

## Features


### Dictionary/list/tuple/set explorer


https://user-images.githubusercontent.com/13981456/133946740-7bbb2039-24ce-41a8-9589-0888918f9bd8.mov


### Filters

https://user-images.githubusercontent.com/13981456/133946565-ae2f9809-b724-4439-b5c5-13b77c3be8f6.mov


### Stack view

https://user-images.githubusercontent.com/13981456/133947144-dbed8d99-1ae8-4e50-a414-2a3b03311327.mov


### Explore and return the selected object


https://user-images.githubusercontent.com/13981456/133946981-3bf5cfda-6eac-4514-abb3-e073dd3fb6b2.mov



-----

Built with the amazing [rich](https://github.com/willmcgugan/rich) and [blessed](https://github.com/jquast/blessed) packages. Check them out!


## Contributing
Read [CONTRIBUTING.md](CONTRIBUTING.md)

------

[LICENSE](LICENSE)
