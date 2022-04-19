# Dev Notes <!-- omit in toc -->

This is an additional section for information, generally not relevant for the user but the developers. Here you will find some pitfalls and usefull information discovered during coding.

## TOC  <!-- omit in toc -->

- [Python Version](#python-version)
- [Program Schema](#program-schema)
- [Translating the UI](#translating-the-ui)
- [PyQt](#pyqt)
  - [Creating Styles](#creating-styles)
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

# Translating the UI

One contribution, that does not require any programming skill is the possibility to add a translation to your language.
The language file is found in `src/language.yaml` for CocktailBerry and in `dashboard/frontend/language.yaml` for the Dashboard. In the best szenario, both files get the according translation. You can use any of the existing language to translate into your own language, in most cases english will probably be the best to use. Please add for every existing option a translation, following the current YAML schema. Using a common **two letter code** for your country / language is desired.

# PyQt

All Topics related to PyQt (or Qt in general).

## Creating Styles

To manage the style, a qss (qt-css) file is used. [qtsass](https://github.com/spyder-ide/qtsass) is used to convert a sass file into the used qss file. For conversion run:

```bash
qtsass /src/ui/styles/stylname.scss -o /src/ui/styles/stylname.qss   
```

If you want to implement a new style, copy the default.scss file, rename the copy to your style name and plug your colors into the variables. After that, just compile the file. You got a new style setting. To be supported, the style name needs to be added to the `src.__init__` file into the SUPPORTED_STYLES list.

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

- [x] Extent RPi Controller API to be more generic for also other boards
  - [x] Introduce new config var to set board type
  - [x] Add list of supported board types to settings
  - [x] Extend documentation for pin names / numbers
  - [x] Check if setting is in list of supported types
  - [x] Refactor RPi to machine controller
  - [x] New board / pin controlller class for machine controller to inherit pin methods from
- [ ] Review microservice and its features
  - [ ] Email always is quite tricky, maybe get something more "working", or just remove it
  - [x] Review que logic for failed sending
  - [x] Add aditional logic for the new official endpoint + api key .env variable slot for example file
  - [x] Extend API for receiving as well as sending of language used and machine name
  - [ ] Generally review this logic, maybe extend it to make it work with other custom endpoints using keys are other header auth features
    - [ ] Make it to work with any amount of urls / header things
    - [x] Make it work with the official API
- [ ] Add progress bar to cleaning programm and possibility to cancel
- [ ] Add config management into maker UI
  - [ ] replace cleaning with option button
  - [ ] own window to have dedicated option settings
  - [ ] Get all needed configs from manager
  - [ ] Display with correct input option for user
  - [ ] Check values before change
- [ ] Add restart / reboot control into maker UI
- [ ] Switch from in file stylesheets to one central stylesheet
  - [ ] Create method to inject stylesheet into ui
  - [ ] Merge individual stylesheets into one central one
