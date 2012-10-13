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
    prijs = db.Column(db.Numeric(5,2))
    categorieID = db.Column(db.Integer, db.ForeignKey('Drankcat.id'))
    categorie = db.relationship("Drankcat", backref="dranken")
    josto = db.Column(db.Boolean)

    def __repr__(self):
        return '<Drank %r>' % self.categorie.beschrijving


class Drankcat(db.Model):
    __tablename__ = 'Drankcat'
    id = db.Column(db.Integer, primary_key=True)
    beschrijving = db.Column(db.String(50))

    def __repr__(self):
        return '<Category %r>' % self.beschrijving


error = "errors are not implemented yet!"
test = Dranken.query.first()
print test.categorie.beschrijving

@app.route("/account", methods=['GET'])
def account():
	user = "testuser"
	drankrekening = "0"
	lidgeld="Februari 2012"
	return render_template('account.html', user=user, drankrekening=drankrekening, lidgeld=lidgeld)

@app.route("/boekhouding", methods=['GET'])
def boekhouding():
	return render_template('boekhouding.html')

@app.route("/ledenlijst", methods=['GET'])
def ledenlijst():
	return render_template('ledenlijst.html')


@app.route("/stock_aanvullen", methods=['GET', 'POST'])
def stock_aanvullen():
	confirmation = ""
	if request.method == 'POST': 
		for ind in request.form.getlist('check[]'):
			confirmation += ind
			confirmation += "="
			confirmation += request.form["amount_" + ind]
			confirmation += ", "

	#dit moet uiteraard dynamisch worden
	cust= [	{"id":1,"name":u"name 1","aantal":5},
		{"id":2,"name":u"name 2","aantal":3},
		{"id":3,"name":u"name 3","aantal":7},
		{"id":4,"name":u"name 4","aantal":6}
  	      ]
	return render_template('stock_aanvullen.html', lijst=cust, confirmation=confirmation, error=error)


@app.route("/stock", methods=['GET', 'POST'])
def stock():
	confirmation = ""
	if request.method == 'POST':
		for ind in request.form.getlist('ind[]'):
			confirmation += ind
			confirmation += "="
			confirmation += request.form["amount_" + ind]
			confirmation += ", "

	#dit moet uiteraard dynamisch worden
	cust= [	{"id":1,"name":u"name 1","aantal":5},
		{"id":2,"name":u"name 2","aantal":3},
		{"id":3,"name":u"name 3","aantal":-7},
		{"id":4,"name":u"name 4","aantal":6}
  	      ]
	return render_template('stock.html', lijst=cust, confirmation=confirmation, error=error)

if __name__ == '__main__':
    app.run()
