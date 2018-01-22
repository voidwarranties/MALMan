"""Keep a log and send out email in case an error happens"""

from MALMan import app

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(app.config['LOGPATH'], maxBytes=1024*1024, backupCount=5)
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
