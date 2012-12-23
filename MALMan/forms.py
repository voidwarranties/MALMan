from wtforms import Form as wtforms_Form
from flask.ext.wtf import Form, Required, FormField, BooleanField, TextField, PasswordField, HiddenField, DateField, IntegerField, SubmitField, SelectField, DecimalField, validators, EqualTo, ListWidget, Input
from wtforms.widgets import TextInput, CheckboxInput
from flask_security.forms import unique_user_email

def booleanfix(POST, var):
    '''returns a boolean indicating if a variable was in the received form fields'''
    if var in POST:
        return True
    else:
        return False

class new_members_form(Form):
    # some fields are added by the view
    submit = SubmitField("activate account(s)")

class leden_edit_own_account_form(Form):
    email = TextField('Email', [
        validators.Email(message='please enter a valid email address')])
    name = TextField('Name', [validators.Required()])
    geboortedatum = DateField('Date of birth (yyyy-mm-dd)', [
        validators.Required(message='please enter a date using the specified formatting')])
    street = TextField('Street', [
        validators.Required()])
    number = IntegerField('Number', [
        validators.NumberRange(min=0, message='please enter a positive number')])
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
         validators.Length(message="Password must be at least 6 characters long", min=6)])
     password_confirm = PasswordField("Retype Password", [
         EqualTo('password', message="Passwords do not match")])
     submit = SubmitField("change my password")

class leden_edit_account_form(leden_edit_own_account_form):
    # some fields are added by the view
    actief_lid = BooleanField('Is an active member')
    membership_dues = IntegerField('Monthly dues (&euro;)', [
        validators.NumberRange(min=0, message='please enter a positive number'),]) 
    submit = SubmitField("edit account information")

# this is used by flask_security to generate the register form
class NewFormFields(leden_edit_own_account_form):
    pass

# this is not used, check views.py for more info
class stock_tellen_form(Form):
    # some fields are added by the view
    submit = SubmitField('ok!')

class stock_log_form(Form):
    revert = SubmitField('revert')

class stock_toevoegen_form(Form):
    naam = TextField('name', [validators.Required()])
    prijs = DecimalField('price (e.g. 1.52)', [validators.NumberRange(min=0, message='please enter a positive number')], places=2)
    aanvullenTot = IntegerField('Maximum stock', [validators.NumberRange(min=0, message='please enter a positive number')])
    categorieID = SelectField('category', coerce=int)
    josto = BooleanField('josto')
    submit = SubmitField('add stock item')

class stock_aanvullen_form(Form):
    # some fields are added by the view
    submit = SubmitField('ok!')

class stock_aanpassen_form_single(wtforms_Form):
    # some fields are added by the view
    naam = TextField('name', [validators.Required()])
    prijs = DecimalField('price (e.g. 1.52)', [validators.NumberRange(min=0, message='please enter a positive number')], places=2)
    aanvullenTot = IntegerField('Maximum stock', [validators.NumberRange(min=0, message='please enter a positive number')])
    categorieID = SelectField('category', coerce=int)
    josto = BooleanField('josto')

class stock_aanpassen_form(Form):
    submit = SubmitField('add stock item')
