from flask import Flask, render_template, request
app = Flask(__name__)

error = "errors are not implemented yet!"

@app.route("/aanvullen", methods=['GET', 'POST'])
def stock_aanvullen():
	confirmation = ""
	if request.method == 'POST': #hier moet normaal gezien even OK komen bij confirmation of zo, dit is maar om te testen.
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


@app.route("/controleren", methods=['GET', 'POST'])
def stock_aanpassen():
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
	return render_template('stock_aanpassen.html', lijst=cust, confirmation=confirmation, error=error)

if __name__ == '__main__':
    app.debug = True
    app.run()