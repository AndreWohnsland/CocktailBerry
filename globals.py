""" Initialise all neccecary global Values, which are passed
over several Modules in the Python Script.
Also assigns the values to them.
"""


def initialize():
    """ The Initialise Function for the global variables. """
    global startcheck
    global loopcheck
    global SUPPRESS_ERROR
    global old_ingredient

    startcheck = False
    loopcheck = True
    SUPPRESS_ERROR = False
    old_ingredient = []
