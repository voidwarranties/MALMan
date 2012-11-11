import sys
from flask import Flask, render_template, request, flash, session, redirect
from flask.ext.mail import Mail
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask.ext.login import current_user, login_required

try:
    from flaskext.sqlalchemy import SQLAlchemy
except ImportError:
    from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('MALMan.cfg')
app.secret_key = 'some_secret'
db = SQLAlchemy(app)

## begin of User Managment
# configuration
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'sha512_crypt'
app.config['SECURITY_PASSWORD_SALT'] = 'MALMan'
app.config['DEFAULT_MAIL_SENDER'] = 'MALMan@voidwarranties.be'

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

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
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

# create missing tables in db
# should only be run once, remove this when db is stable
db.create_all()

aanpassing = "Deze waarden werden aangepast: "
error = ""

@app.route("/")
def index():
    if current_user.is_active() == True:
        user = current_user.email
        return render_template('account.html', user=user)
    else:
        return redirect('login')

@app.route("/leden")
@login_required
def ledenlijst():
    user = current_user.email
    return render_template('ledenlijst.html', user=user)

@app.route("/stock")
@login_required
def stock():
    user = current_user.email
    dranken = Dranken.query.all()
    return render_template('stock.html', lijst=dranken, user=user)

@app.route("/stock_tellen", methods=['GET', 'POST'])
@login_required
def stock_tellen():
    user = current_user.email
    dranken = Dranken.query.all()
    if request.method == 'POST':
        confirmation = aanpassing
        for ind in request.form.getlist('check[]'):
            drankobject = Dranken.query.filter_by(id=ind).first()
            # only write to DB and display a confirmation for ids for which the amount_id we received in the POST does not equal the value in the DB 
            if int(request.form["amount_" + ind]) != int(drankobject.stock):
                changes = Dranklog(ind, (int(request.form["amount_" + ind]) - int(drankobject.stock)), 0, 0, "correctie") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += "stock " + drankobject.naam + " = " + request.form["amount_" + ind]
        if confirmation == aanpassing:
            flash("Er zijn geen veranderingen door te voeren", "error")
        else:
            flash(confirmation, "confirmation")
    return render_template('stock_tellen.html', lijst=dranken, user=user)

@app.route("/stock_aanpassen", methods=['GET', 'POST'])
@login_required
def stock_aanpassen():
    user = current_user.email
    dranken = Dranken.query.all()
    drankcats = Drankcat.query.all()
    oorsprongen = stock_oorsprong.query.all()
    if request.method == 'POST':
        confirmation = aanpassing
        for ind in request.form.getlist('ind[]'):
            drankobject = Dranken.query.filter_by(id=ind).first()
            # only write to DB and display a confirmation if the value given in the POST does not equal the value in the DB 
            atributes = ['naam', 'prijs', 'aanvullenTot', 'categorieID'] #josto is not implemented jet
            for atribute in atributes:
                if str(request.form[atribute + "_" + ind]) != str(getattr(drankobject, atribute)):
                    oudewaarde = str(getattr(drankobject, atribute))
                    obj = Dranken.query.get(ind)
                    setattr(obj, atribute, request.form[atribute + "_" + ind])
                    db.session.commit()
                    if confirmation != aanpassing:
                        confirmation += ", "
                    if atribute == "naam":
                        confirmation += oudewaarde + " => " + request.form["naam_" + ind]
                    elif atribute == "categorieID":
                        newcat = Drankcat.query.filter_by(id=request.form[atribute + "_" + ind]).first().beschrijving
                        oldcat = Drankcat.query.filter_by(id=oudewaarde).first().beschrijving
                        confirmation += "categorie" + " " + drankobject.naam + " = \"" + newcat + "\" (was \"" + oldcat + "\")"
                    else:
                        confirmation += atribute + " " + drankobject.naam + " = " + request.form[atribute + "_" + ind] + " (was " + oudewaarde + ")"
        if confirmation == aanpassing:
            flash("Er zijn geen veranderingen door te voeren", "error")
        else: 
            flash(confirmation, "confirmation")
    return render_template('stock_aanpassen.html', lijst=dranken, categorieen=drankcats, oorsprongen=oorsprongen, user=user)

@app.route("/stock_aanvullen", methods=['GET', 'POST'])
@login_required
def stock_aanvullen():
    user = current_user.email
    dranken = Dranken.query.filter_by(josto=True).all()
    if request.method == 'POST': 
        confirmation = aanpassing
        for ind in request.form.getlist('check[]'):
            drankopbject = Dranken.query.filter_by(id=ind).first()
            if int(request.form["amount_" + ind]) != 0:
                changes = Dranklog(ind, request.form["amount_" + ind], 0, 0, "aanvulling") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += "stock " + drankopbject.naam + " = +" + request.form["amount_" + ind]
        if confirmation == aanpassing:
            flash('Er zijn geen veranderingen door te voeren', 'error')
        else:
            flash(confirmation, 'confirmation')
    return render_template('stock_aanvullen.html', lijst=dranken, user=user)

@app.route("/stock_log", methods=['GET', 'POST'])
@login_required
def stock_log():
    user = current_user.email
    if request.method == 'POST': 
        changes = Dranklog.query.filter_by(id=request.form["revert"]).first()
        db.session.delete(changes)
        db.session.commit()
    log = Dranklog.query.all()
    return render_template('stock_log.html', log=log, user=user)

@app.route("/stock_toevoegen", methods=['GET', 'POST'])
@login_required
def stock_toevoegen():
    user = current_user.email
    drankcats = Drankcat.query.all()
    oorsprongen = stock_oorsprong.query.all()
    if request.method == 'POST': 
        changes = Dranken(request.form["naam"], request.form["aanvullenTot"], request.form["prijs"], request.form["categorieID"], request.form["josto"])
        db.session.add(changes)
        db.session.commit()
        flash("stockitem toegevoegd: " + request.form["naam"], "confirmation")
    return render_template('stock_toevoegen.html', categorieen=drankcats, oorsprongen=oorsprongen, user=user)

@app.route("/boekhouding")
@login_required
def boekhouding():
    user = current_user.email
    return render_template('boekhouding.html', user=user)

if __name__ == '__main__':
    app.run()