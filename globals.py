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
    global decoactivate

    # Only checkvariables for code and multimodule Communication
    startcheck = False
    loopcheck = True
    # set this to true if you want to log and supress errors while running the App
    # only recommended for the Maker on a Party, but not for debugging und you machine
    decoactivate = True
    # here you can define your individual Password
    # there is a tochwindow for numbers, so if you want to isert the Password
    # without any Keybord, only Numbers is the way to go
    # Can also be an empty String, then no PW is needed (will only work if the PW is empty)
    masterpassword = "1337"
    # The Pins of the RPi, where Pump 1-10 (original there were 12) is connected
    usedpins = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 20]
    # The according Volumeflow in ml/s for each Pump
    # Each Pump can be Measured individually and adjusted
    pumpvolume = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
