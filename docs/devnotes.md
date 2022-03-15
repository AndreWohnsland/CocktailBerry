# Dev Notes <!-- omit in toc -->

This is an additional section for information, generally not relevant for the user but the developers. Here you will find some pitfalls and usefull information discovered during coding.

## TOC  <!-- omit in toc -->

- [Python Version](#python-version)
- [Program Schema](#program-schema)
- [PyQt](#pyqt)
  - [Button clicked.connect behaviour](#button-clickedconnect-behaviour)
- [ToDos](#todos)


# Python Version

Currently used version:

```
Python Version 3.7.x
```

In the past, there were some issues due to not using the same Python version during development (PC) and at production (RPi). To prevent those issues, the same Python version (up to minor) like the current one shipped with the RPi system should be used. This will prevent making errors like using `list` instead of `List` for type hints (only works at Python 3.9+) and other features not yet available in the default RPi Python. Please use an according Python version for your local development.

# Program Schema

In the following diagram, the schema and Classes / Containers are displayed in a simplified version.

![ProgramSchema](diagrams/out/ProgramSchema.svg)

# PyQt

All Topics related to PyQt (or Qt in general).

## Button clicked.connect behaviour

One issue, which is not clear on the first view, is that there are two signatures for this function. See [this issue on StackOverflow](https://stackoverflow.com/questions/53110309/qpushbutton-clicked-fires-twice-when-autowired-using-ui-form/53110495#53110495) for more details. When using the error logging wrapper and just passing the wrapped function into the connect function, PyQt will also emmit the `False` argument into the wrapper. This will result in a crash of the programm in case the wrapped function got no arguments. In this case it is better to use a lambda to explicitly tell PyQt the function got no arguments.

```Python
# Wrapped function without arguments
@logerror
def some_function():
  print("Doing Stuff")

# Good
yourbutton.clicked.connect(lambda: some_function())

# Will crash because the wrapper got *args=(False,)
# and will call some_function(False)
yourbutton.clicked.connect(some_function)
```


# ToDos

Here are some todos, for now or later versions:

- Add validation of countrycode and only use supported codes
  - add supported codes paramter as a list to the src.init file
- Add new config parameter for machine name
  - Using `CocktailBerry (#RandomLongNumber)` as default (uuid?)
  - Add validation of the length for the name, limit it by reasonable length (something like 30-50 chars?)
- Review microservice and its features
  - Email always is quite tricky, maybe get something more "working", or just remove it
  - Review que logic for failed sending
  - Add aditional logic for the new official endpoint + api key .env variable slot for example file
  - Extend API for receiving as well as sending of language used and machine name
  - Generally review this logic, maybe extend it to make it work with other custom endpoints using keys are other header auth features
