''' Initialise all neccecary global Values, which are passed
over several Modules in the Python Script.
Also assigns the values to them.
'''


def initialize():
    """ The Initialise Function for the global variables. """
    global startcheck
    global loopcheck
    global masterpassword
    global usedpins
    global pumpvolume

    startcheck = False
    loopcheck = True
    masterpassword = "1337"
    usedpins = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 20]
    pumpvolume = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
