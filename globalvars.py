""" Initialise all neccecary global Values, which are passed
over several Modules in the Python Script.
Also assigns the values to them.
"""


def initialize():
    """ The Initialise Function for the global variables. """
    global cocktail_started
    global make_cocktail
    global SUPPRESS_ERROR
    global old_ingredient

    cocktail_started = False
    make_cocktail = True
    SUPPRESS_ERROR = False
    old_ingredient = []
