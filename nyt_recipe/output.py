import logging

# Initialize DEBUG variable
DEBUG = False

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Create console handler and set level based on DEBUG flag
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(levelname)s: %(message)s')
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)

def toggle_debug(enabled):
    global DEBUG
    DEBUG = enabled
    if enabled:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)

def error(text):
    logger.error(text)

def warn(text):
    logger.warning(text)

def debug(text):
    logger.debug(text)
