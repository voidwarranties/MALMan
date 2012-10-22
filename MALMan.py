from flask import Flask, render_template, request
from flaskext.sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config.from_pyfile('MALMan.cfg')
db = SQLAlchemy(app)


class Dranken(db.Model):
    __tablename__ = 'Dranken'
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(50))
    aanvullenTot = db.Column(db.Integer)
    prijs = db.Column(db.Numeric(5, 2))
    categorieID = db.Column(db.Integer, db.ForeignKey('Drankcat.id'))
    categorie = db.relationship("Drankcat", backref="dranken", lazy="joined")
    josto = db.Column(db.Boolean)
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

class Dranklog(db.Model):
    __tablename__ = 'Dranklog'
    id = db.Column(db.Integer, primary_key=True)
    drankID = db.Column(db.Integer, db.ForeignKey('Dranken.id'))
    aantal = db.Column(db.Integer)
    totaalprijs = db.Column(db.Numeric(5, 2))
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

aanpassing = "Deze waarden werden aangepast: "

@app.route("/")
def account():
    user = "testuser"
    drankrekening = "0"
    lidgeld = "Februari 2012"
    return render_template('account.html', user=user, drankrekening=drankrekening, lidgeld=lidgeld)

@app.route("/leden")
def ledenlijst():
    return render_template('ledenlijst.html')

@app.route("/stock")
def stock():
    dranken = Dranken.query.all()
    return render_template('stock.html', lijst=dranken, error=error)

@app.route("/stock_tellen", methods=['GET', 'POST'])
def stock_tellen():
    confirmation = ""
    error = ""
    dranken = Dranken.query.all()
    if request.method == 'POST':
        confirmation = aanpassing
        for ind in request.form.getlist('check[]'):
            drankopbject = Dranken.query.filter_by(id=ind).first()
            # only write to DB and display a confirmation for ids for which the amount_id we received in the POST does not equal the value in the DB 
            if int(request.form["amount_" + ind]) != int(drankopbject.stock):
                changes = Dranklog(ind, (int(request.form["amount_" + ind]) - int(drankopbject.stock)), 0, 0, "aanpassen") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += "stock " + drankopbject.naam + " = " + request.form["amount_" + ind]
        if confirmation == aanpassing:
            confirmation = ""
            error = "Er zijn geen veranderingen door te voeren "
    return render_template('stock_tellen.html', lijst=dranken, confirmation=confirmation, error=error)

@app.route("/stock_aanpassen", methods=['GET', 'POST'])
def stock_aanpassen():
    confirmation = ""
    dranken = Dranken.query.all()
    drankcats = Drankcat.query.all()
    if request.method == 'POST':
        for ind in request.form.getlist('ind[]'):
            drankopbject = Dranken.query.filter_by(id=ind).first()
            if (int(request.form["amount_" + ind]) - int(drankopbject.stock)) != 0:
                changes = Dranklog(ind, (int(request.form["amount_" + ind]) - int(drankopbject.stock)), 0, 0, "correctie") #userID moet nog worden ingevuld naar de user die de correctie doet
                db.session.add(changes)
                db.session.commit()
                confirmation = "aangepast"
    return render_template('stock_aanpassen.html', lijst=dranken, categorieen=drankcats, confirmation=confirmation, error=error)

@app.route("/stock_aanvullen", methods=['GET', 'POST'])
def stock_aanvullen():
    confirmation = ""
    error = ""
    dranken = Dranken.query.filter_by(josto=True).all()
    if request.method == 'POST': 
        confirmation = aanpassing
        for ind in request.form.getlist('check[]'):
            drankopbject = Dranken.query.filter_by(id=ind).first()
            if int(request.form["amount_" + ind]) != 0:
                changes = Dranklog(ind, request.form["amount_" + ind], 0, 0, "aanvullen") #userID moet nog worden ingevuld naar de user die dit toevoegt
                db.session.add(changes)
                db.session.commit()
                if confirmation != aanpassing:
                    confirmation += ", "
                confirmation += "stock " + drankopbject.naam + " = +" + request.form["amount_" + ind]
        if confirmation == aanpassing:
            confirmation = ""
            error += "Er zijn geen veranderingen door te voeren "
    return render_template('stock_aanvullen.html', lijst=dranken, confirmation=confirmation, error=error)

@app.route("/stock_toevoegen", methods=['GET', 'POST'])
def stock_toevoegen():
    drankcats = Drankcat.query.all()
    return render_template('stock_toevoegen.html', categorieen=drankcats, error=error)

@app.route("/boekhouding")
def boekhouding():
    return render_template('boekhouding.html')

if __name__ == '__main__':
    app.run()
