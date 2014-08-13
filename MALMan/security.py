from MALMan import app
import MALMan.database as DB
from flask_security import Security
from flask import session
from flask.ext.principal import Principal
from flask.ext.mail import Mail
from flask.ext.login import current_user

# configuration
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = app.config['SECURITY_PASSWORD_SALT']

app.config['SECURITY_POST_LOGIN_VIEW'] = 'index'
app.config['SECURITY_POST_LOGOUT_VIEW'] = 'index'

app.config['DEFAULT_MAIL_SENDER'] = 'MALMan@voidwarranties.be'

# Setup mail extension
mail = Mail(app)

# Setup Flask-Security
from MALMan.forms import RegisterForm
security = Security(app, DB.user_datastore, confirm_register_form=RegisterForm)

# Setup Principal extension
principals = Principal(app)


@app.before_request
def before_request():
    # add the role and email variables to the session if they are missing but user is logged in.
    # this happens after a session is resumed from a cookie
    if session and ('user_id' in session) and ('email' not in session):
        user = DB.User.query.get(current_user.id)
        session['email'] = user.email
        session['roles'] = [role.name for role in user.roles]
