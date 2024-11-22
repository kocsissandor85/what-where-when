import logging


def setup_logger():
    logger_instance = logging.getLogger("ParserLogger")
    logger_instance.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = logging.FileHandler("parsers/parser.log")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    logger_instance.addHandler(console_handler)
    logger_instance.addHandler(file_handler)

    return logger_instance


logger = setup_logger()