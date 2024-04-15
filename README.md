# libxgecu
Reference code to talk to stock xgecu firmware (T48, T56, etc)

## Usage:

### Setup virtual env
```
poetry install # Download locked dependencies to virtual env
```

### Enter the virtual env
```
poetry shell
```

### Call package entry points in virtual env
```
poetry run t48_update
poetry run t48_verstion
```

### Build sdist and wheel
```
poetry build
```

### Publish to PyPI
```
poetry publish
```

### To update the locked dependencies
```
poetry update
```
