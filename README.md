
![logo](images/logo.png)

Objexplore is an interactive Python object explorer for the terminal. Use it while debugging, or exploring a new library, or whatever!

![cibuild](https://github.com/kylepollina/objexplore/actions/workflows/python-app.yml/badge.svg) [![pypi](https://img.shields.io/pypi/v/objexplore.svg)](https://pypi.org/project/objexplore/)


https://user-images.githubusercontent.com/13981456/133720490-7bd08dc6-4407-48f1-912a-329be6173619.mov


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

### Dictionary explorer

https://user-images.githubusercontent.com/13981456/133894806-c4dd6101-1e03-4b33-8c65-b6cca0a2c03f.mov


### List/tuple explorer

https://user-images.githubusercontent.com/13981456/133889219-0b80d1f4-697a-4532-aa4a-00898267eef5.mov

### Return the selected object

https://user-images.githubusercontent.com/13981456/133894047-b40aecb0-5e0a-48c8-8e4c-2bba89cdbe8f.mov


-----

Built with the amazing [rich](https://github.com/willmcgugan/rich) and [blessed](https://github.com/jquast/blessed) packages. Check them out!


## Contributing
Read [CONTRIBUTING.md](CONTRIBUTING.md)

------

[LICENSE](LICENSE)
