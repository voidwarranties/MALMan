"""MALMan stands for Members, Accounting and Library Managment

This file wil initialize, configure and run the application.
"""

import sys
from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('MALMan.cfg')
app.secret_key = app.config['SECRET_KEY']
app.CHANGE_MSG = app.config['CHANGE_MSG']
app.ITEMS_PER_PAGE = app.config['ITEMS_PER_PAGE']

CSRF_ENABLED = True

from MALMan import security

from MALMan import views_members, views_bar, views_accounting, views_errors

#enable logging if we are not running in debug mode
if not app.debug:
    from MALMan import logging
