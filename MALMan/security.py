from MALMan import app
import MALMan.database as DB
from flask_security import Security
from flask import session
from flask.ext.principal import Principal, RoleNeed, identity_loaded
from flask.ext.mail import Mail
from flask.ext.login import current_user

# configuration
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = app.config['SECURITY_PASSWORD_SALT']

app.config['DEFAULT_MAIL_SENDER'] = 'MALMan@voidwarranties.be'

# Setup mail extension
mail = Mail(app)

# Setup Flask-Security
from MALMan.forms import RegisterForm
security = Security(app, DB.user_datastore, confirm_register_form=RegisterForm )

# Setup Principal extension
principals = Principal(app)

@app.before_request
def before_request():
    # add the role and email variables to the session if they are missing but user is logged in.
    # this happens after a session is resumed from a cookie
    if session and ('user_id' in session) and (not 'email' in session):
    	user = DB.User.query.get(current_user.id)
        session['email'] = user.email
    	session['roles'] = [role.name for role in user.roles]

## I don't think we need this bit, the function is already defined by flask_security/core.py
# @identity_loaded.connect_via(app)
# def on_identity_loaded(sender, identity):
#     # Update the roles that a user can provide
#     if hasattr(identity, 'id'):
#         account = DB.User.query.filter_by(id=identity.id).first()
#         if account:
#             for role in account.roles:
#                 identity.provides.add(RoleNeed(role))
