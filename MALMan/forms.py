from flask.ext.wtf import Form, Required, FormField, BooleanField, TextField, PasswordField, HiddenField, DateField, IntegerField, SubmitField, validators, EqualTo
from flask_security.forms import unique_user_email

# This form starts up empty, and is filled up with field by the view
class new_members_form(Form):
	submit = SubmitField("activate account(s)")

class leden_edit_own_account_form(Form):
	email = TextField('Email', [
		validators.Email(message='please enter a valid email address'),
		unique_user_email])
	name = TextField('Name', [validators.Required()])
	geboortedatum = DateField('Date of birth (yyyy-mm-dd)', [
		validators.Required(message='please enter a date using the specified formatting')])
	street = TextField('Street', [
		validators.Required()])
	number = IntegerField('Number', [
		validators.NumberRange(min=0, message='please enter a positive number'),])
	bus = TextField('Bus (optional)', [
		validators.Optional()])
	postalcode = TextField('Postal code', [
		validators.NumberRange(min=0, message='please enter a positive number'), validators.Required()])
	gemeente = TextField('City', [
		validators.Required()])
	telephone = TextField('Telephone (0xx.xxx.xxx)', [
		validators.Length(min=8, message='entry is not long enough to be a valid phone number'), 
		validators.Required()])
	show_email = BooleanField('Display email address to other members')
	show_telephone = BooleanField('Display phone number to other members')
	submit = SubmitField("edit my account information")

class leden_edit_password_form(Form):
	password = PasswordField("Password", [
    	validators.Length(message="Password must be at least 6 characters long", min=6, max=128)])
	password_confirm = PasswordField("Retype Password", [
        EqualTo('password', message="Passwords do not match")])
	submit = SubmitField("change my password")


class leden_edit_account_form(leden_edit_own_account_form):
	actief_lid = BooleanField('Is an active member')
	membership_dues = IntegerField('Monthly dues (&euro;)', [
		validators.NumberRange(min=0, message='please enter a positive number'),]) 
	submit = SubmitField("edit account information")

# this is used by flask_security to generate the register form
class NewFormFields(leden_edit_own_account_form):
	pass