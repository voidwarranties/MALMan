"""Define the various forms used in MALMan"""

from wtforms import Form as wtforms_Form
from flask.ext.wtf import (Form, BooleanField, TextField, PasswordField, 
    DateField, IntegerField, SubmitField, SelectField, DecimalField, 
    validators, EqualTo)

def booleanfix(post, var):
    """returns a boolean indicating if a variable was in the received POST"""
    if var in post:
        return True
    else:
        return False

class NewMembers(Form):
    #some fields are added by the view
    submit = SubmitField("activate account(s)")

class LedenEditOwnAccount(Form):
    email = TextField('Email', [
        validators.Email(message='please enter a valid email address')])
    name = TextField('Name', [validators.Required()])
    geboortedatum = DateField('Date of birth (yyyy-mm-dd)', 
        [validators.Required(
            message='please enter a date using the specified formatting')])
    street = TextField('Street', [
        validators.Required()])
    number = IntegerField('Number', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')])
    bus = TextField('Bus (optional)', [
        validators.Optional()])
    postalcode = TextField('Postal code', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number'), 
        validators.Required()])
    gemeente = TextField('City', [
        validators.Required()])
    telephone = TextField('Telephone (0xx.xxx.xxx)', 
        [validators.Length(min=8, 
            message='entry is not long enough to be a valid phone number'), 
        validators.Required()])
    show_email = BooleanField('Display email address to other members')
    show_telephone = BooleanField('Display phone number to other members')
    submit = SubmitField("edit my account information")

class LedenEditPassword(Form):
    password = PasswordField("Password", [
        validators.Length(
            message="Password must be at least 6 characters long", min=6)])
    password_confirm = PasswordField("Retype Password", [
        EqualTo('password', message="Passwords do not match")])
    submit = SubmitField("change my password")

class LedenEditAccount(LedenEditOwnAccount):
    # some fields are added by the view
    actief_lid = BooleanField('Is an active member')
    membership_dues = IntegerField('Monthly dues (&euro;)', [
        validators.NumberRange(min=0, 
            message='please enter a positive number'),]) 
    submit = SubmitField("edit account information")

# this is used by flask_security to generate the register form
class NewFormFields(LedenEditOwnAccount):
    pass

# this is not used, check views.py for more info
class StockTellen(Form):
    # some fields are added by the view
    submit = SubmitField('ok!')

class StockLog(Form):
    revert = SubmitField('revert')

class StockToevoegen(Form):
    naam = TextField('Name', [validators.Required()])
    prijs = DecimalField('Price (e.g. 1.52)', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')],
        places=2)
    aanvullenTot = IntegerField('Stock maximum', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')])
    categorieID = SelectField('Category', coerce=int)
    josto = BooleanField('Josto')
    submit = SubmitField('add stock item')

class StockAanvullen(Form):
    # some fields are added by the view
    submit = SubmitField('ok!')

class StockAanpassenSingle(wtforms_Form):
    # some fields are added by the view
    naam = TextField('name', [validators.Required()])
    prijs = DecimalField('price (e.g. 1.52)', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')], places=2)
    aanvullenTot = IntegerField('Maximum stock', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')])
    categorieID = SelectField('category', coerce=int)
    josto = BooleanField('josto')

class StockAanpassen(Form):
    submit = SubmitField('add stock item')
