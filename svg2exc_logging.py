import logging

def getLogger(name, filename=None, level=logging.DEBUG):

    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter ('%(asctime)s:%(levelname)s:%(name)s:%(funcName)s:%(message)s')
    log_file = filename if filename else '{}.log'.format(name)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
