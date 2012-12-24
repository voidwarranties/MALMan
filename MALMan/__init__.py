"""MALMan stands for Members, Accounting and Library Managment

This file wil initialize, configure and run the application.
"""

import sys
from flask import Flask
from flask.ext.mail import Mail
from MALMan.flask_security import Security
from flask.ext.login import current_user, login_required
from flask.ext.principal import Principal, RoleNeed, identity_loaded

app = Flask(__name__)

from MALMan.database import User, user_datastore

app.config.from_pyfile('MALMan.cfg')
app.secret_key = app.config['SECRET_KEY']
CSRF_ENABLED = True

# configuration
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = 'MALMan'
app.config['DEFAULT_MAIL_SENDER'] = 'MALMan@voidwarranties.be'

# Setup mail extension
mail = Mail(app)

# Setup Flask-Security
security = Security(app, user_datastore)

# Setup Principal extension
principals = Principal(app)

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Get the user information from the db
    account = User.query.filter_by(id=identity.name).first()
    # Update the roles that a user can provide
    if account:
        for role in account.roles:
            identity.provides.add(RoleNeed(role))

from MALMan import views

#enable logging if we are not running in debug mode
if not app.debug:
    from MALMan import logging
