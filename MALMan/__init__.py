import sys
from flask import Flask, render_template, request, flash, session, redirect
from flask.ext.mail import Mail
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask.ext.login import current_user, login_required
from flask.ext.principal import Principal, Permission, RoleNeed, identity_loaded, UserNeed, Need

try:
    from flaskext.sqlalchemy import SQLAlchemy
except ImportError:
    from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('MALMan.cfg')
CSRF_ENABLED = True
app.secret_key = app.config['SECRET_KEY']
db = SQLAlchemy(app)

#from flask_debugtoolbar import DebugToolbarExtension
#toolbar = DebugToolbarExtension(app)

## begin of User Managment
# configuration
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = 'MALMan'
app.config['DEFAULT_MAIL_SENDER'] = 'MALMan@voidwarranties.be'

# error logging
if not app.debug:
    import logging
    # send out error mails if run in production mode
    from logging import Formatter
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
    from logging import Formatter
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
       '[in %(pathname)s:%(lineno)d]'
    ))
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('logs/MALMan.log', maxBytes=0, backupCount=10 )
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

# Setup mail extension
mail = Mail(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return self.name

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    street = db.Column(db.String(255))
    number = db.Column(db.Integer)
    bus = db.Column(db.String(255))
    postalcode = db.Column(db.Integer)
    gemeente = db.Column(db.String(255))
    geboortedatum = db.Column(db.DateTime())
    telephone = db.Column(db.String(255))
    actief_lid = db.Column(db.Boolean(), default=False)
    member_since = db.Column(db.DateTime(), default="0000-00-00")
    membership_dues = db.Column(db.Integer, default="0")
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    show_telephone = db.Column(db.Boolean())
    show_email = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


#load principal extension
principals = Principal(app)

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Get the user information from the db
    account = User.query.filter_by(id=identity.name).first()
    # Update the roles that a user can provide
    if account:
        for role in account.roles:
            identity.provides.add(RoleNeed(role))
## end of User Managment

class Dranken(db.Model):
    __tablename__ = 'Dranken'
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(50))
    aanvullenTot = db.Column(db.Integer)
    prijs = db.Column(db.Numeric(5, 2))
    categorieID = db.Column(db.Integer, db.ForeignKey('Drankcat.id'))
    categorie = db.relationship("Drankcat", backref="dranken", lazy="joined")
    josto = db.Column(db.Integer, db.ForeignKey('stock_oorsprong.id'))
    oorsprong = db.relationship("stock_oorsprong", backref="dranken", lazy="joined")
    aankopen = db.relationship("Dranklog", backref="Drank")

    @property
    def stock(self): 
        return sum(item.aantal for item in self.aankopen) #dit kan waarschijnlijk beter, maar op deze manier werkt het

    @property
    def aanvullen(self):
        return (self.aanvullenTot - self.stock)

    def __init__(self, naam, aanvullenTot, prijs, categorieID, josto):
        self.naam = naam
        self.aanvullenTot = aanvullenTot
        self.prijs = prijs
        self.categorieID = categorieID
        self.josto = josto

    def __repr__(self):
        return '<Drank %r>' % self.naam


class Drankcat(db.Model):
    __tablename__ = 'Drankcat'
    id = db.Column(db.Integer, primary_key=True)
    beschrijving = db.Column(db.String(50))

    def __repr__(self):
        return '<Category %r>' % self.beschrijving

class stock_oorsprong(db.Model):
    __tablename__ = 'stock_oorsprong'
    id = db.Column(db.Integer, primary_key=True)
    beschrijving = db.Column(db.String(50))

    def __repr__(self):
        return '<Category %r>' % self.beschrijving

class Dranklog(db.Model):
    __tablename__ = 'Dranklog'
    id = db.Column(db.Integer, primary_key=True)
    drankID = db.Column(db.Integer, db.ForeignKey('Dranken.id'))
    stock_naam = db.relationship("Dranken", backref="Dranklog", lazy="joined")
    aantal = db.Column(db.Integer)
    totaalprijs = db.Column(db.Numeric(5, 2))
    datetime = db.Column(db.String(120))
    gebruikerID = db.Column(db.Integer)
    beschrijving = db.Column(db.String(50))

    def __init__(self, drankID, aantal, totaalprijs, gebruikerID, beschrijving):
        self.drankID = drankID
        self.aantal = aantal
        self.totaalprijs = totaalprijs
        self.gebruikerID = gebruikerID
        self.beschrijving = beschrijving

    def __repr__(self):
        return '<id %r>' % self.id

    def remove(entry):
        db.session.delete(entry)
        db.session.commit()

# create missing tables in db
# should only be run once, remove this when db is stable
#db.create_all()

from MALMan import views