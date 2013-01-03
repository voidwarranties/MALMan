from MALMan import app
from MALMan.database import User, user_datastore
from MALMan.flask_security import Security
from flask.ext.principal import Principal, RoleNeed, identity_loaded
from flask.ext.mail import Mail


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
