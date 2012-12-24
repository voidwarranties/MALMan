"""Keep a log and send out email in case an error happens"""

from MALMan import app

if not app.debug:
    import logging
    from logging import Formatter
    from logging.handlers import RotatingFileHandler

    # send out error mails if run in production mode
    mail_handler.setFormatter(Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
    '''))
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(app.MAIL_SERVER,
                               'MALMan',
                               app.ADMINS,
                               'MALMan Failed',
                               credentials=(MAIL_USERNAME,MAIL_PASSWORD))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    # save logfiles
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
       '[in %(pathname)s:%(lineno)d]'
    ))
    file_handler = RotatingFileHandler('logs/MALMan.log', maxBytes=0, 
        backupCount=10 )
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
