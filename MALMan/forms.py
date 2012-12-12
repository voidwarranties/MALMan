from flask.ext.wtf import Form, FormField, BooleanField, TextField, PasswordField, HiddenField, validators, TableWidget

# This form starts up empty, and is filled up with field by the view
class new_members_form(Form):
	pass

class leden_edit_own_acount_form(Form):
	name = TextField('name')
	geboortedatum = TextField('date of birth')
	email = TextField('email')
	telephone = TextField('telephone')
	street = TextField('street')
	number = TextField('number')
	bus = TextField('bus')
	postalcode = TextField('postalcode')
	gemeente = TextField('gemeente')
	show_email = BooleanField('show email')
	show_telephone = BooleanField('show telephone')