class ConfigManager:
    """Manager for all static configuration of the machine """

    MASTERPASSWORD = "1337"
    USEDPINS = [14, 15, 18, 23, 24, 25, 8, 7, 17, 27, 22, 20]
    PUMP_VOLUMEFLOW = [30, 30, 25, 30, 30, 30, 25, 30, 30, 23, 30, 30]
    NUMBER_BOTTLES = 10
    CLEAN_TIME = 20
    SLEEP_TIME = 0.05
    PARTYMODE = False
    LOGGERNAME = "cocktaillogger"
    LOGGERNAME_DEBUG = "debuglogger"
    USE_MICROSERVICE = True
    MICROSERVICE_BASE_URL = "http://127.0.0.1:5000"
    DEVENVIRONMENT = True
