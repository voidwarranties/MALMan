"""Connect to the database and define the database table models"""

from MALMan.flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin
try:
    from flask.ext.sqlalchemy import SQLAlchemy
except ImportError:
    from flask_sqlalchemy import SQLAlchemy
from MALMan import app

db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    """Define the Role database table"""
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return self.name


class User(db.Model, UserMixin):
    """Define the User database table"""
    __tablename__ = 'user'
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
    roles = db.relationship('Role', secondary=roles_users, 
        backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)


user_datastore = SQLAlchemyUserDatastore(db, User, Role)

class Dranken(db.Model):
    """Define the Dranken database table"""
    __tablename__ = 'Dranken'
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(50))
    aanvullenTot = db.Column(db.Integer)
    prijs = db.Column(db.Numeric(5, 2))
    categorieID = db.Column(db.Integer, db.ForeignKey('Drankcat.id'))
    categorie = db.relationship("Drankcat", backref="dranken", lazy="joined")
    josto = db.Column(db.Boolean())
    aankopen = db.relationship("Dranklog", backref="Drank")

    @property
    def stock(self):
        # this might be improved
        return sum(item.aantal for item in self.aankopen) 

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
    """Define the Drancat database table"""
    __tablename__ = 'Drankcat'
    id = db.Column(db.Integer, primary_key=True)
    beschrijving = db.Column(db.String(50))

    def __repr__(self):
        return '<Category %r>' % self.beschrijving


class Dranklog(db.Model):
    """Define the Dranklog database table"""
    __tablename__ = 'Dranklog'
    id = db.Column(db.Integer, primary_key=True)
    drankID = db.Column(db.Integer, db.ForeignKey('Dranken.id'))
    stock_naam = db.relationship("Dranken", backref="Dranklog", lazy="joined")
    aantal = db.Column(db.Integer)
    totaalprijs = db.Column(db.Numeric(5, 2))
    datetime = db.Column(db.String(120))
    gebruikerID = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
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
        """remove entry from Dranklog table"""
        db.session.delete(entry)
        db.session.commit()

# create missing tables in db
# should only be run once, remove this when db is stable
#db.create_all()