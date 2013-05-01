"""Keep a log and send out email in case an error happens"""

from MALMan import app
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('MALMan.log', maxBytes=1024*1024, backupCount=5)
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
