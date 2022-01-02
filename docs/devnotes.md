# Dev Notes <!-- omit in toc -->

This is an additional section for information, generally not relevant for the user but the developers. Here you will find some pitfalls and usefull information discovered during coding.

## TOC  <!-- omit in toc -->

- [PyQt](#pyqt)
  - [Button clicked.connect behaviour](#button-clickedconnect-behaviour)

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