"""Define the various forms used in MALMan"""

from wtforms import Form as wtforms_Form
from flask.ext.wtf import (Form, BooleanField, TextField, PasswordField, 
    DateField, IntegerField, SubmitField, SelectField, DecimalField, 
    TextAreaField, validators, EqualTo)

def booleanfix(post, var):
    """returns a boolean indicating if a variable was in the received POST"""
    if var in post:
        return True
    else:
        return False

class NewMembers(Form):
    #some fields are added by the view
    submit = SubmitField("activate account(s)")


class MembersEditOwnAccount(Form):
    email = TextField('Email', [
        validators.Email(message='please enter a valid email address')])
    name = TextField('Name', [validators.Required()])
    date_of_birth = DateField('Date of birth (yyyy-mm-dd)', 
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
    city = TextField('City', [
        validators.Required()])
    telephone = TextField('Telephone (0xx.xxx.xxx)', 
        [validators.Length(min=8, 
            message='entry is not long enough to be a valid phone number'), 
        validators.Required()])
    show_email = BooleanField('Display email address to other members')
    show_telephone = BooleanField('Display phone number to other members')
    submit = SubmitField("edit my account information")


class MembersEditAccount(MembersEditOwnAccount):
    # some fields are added by the view
    active_member = BooleanField('Is an active member')
    membership_dues = IntegerField('Monthly dues (&euro;)', [
        validators.NumberRange(min=0, 
            message='please enter a positive number'),]) 
    submit = SubmitField("edit account information")


class MembersEditPassword(Form):
    password = PasswordField("Password", [
        validators.Length(
            message="Password must be at least 6 characters long", min=6)])
    password_confirm = PasswordField("Retype Password", [
        EqualTo('password', message="Passwords do not match")])
    submit = SubmitField("change my password")


# this is used by flask_security to generate the register form
class NewFormFields(MembersEditOwnAccount):
    motivation = TextAreaField('My motivation to become a member:', 
        [validators.Required()])


## check if a name is alreasy in use
# from MALMan.database import StockItems
# def _unique_item_name(form, field):
#    if StockItems.query.filter_by(name=field.data) is not None:
#        raise ValidationError(field.data + ' is already a stock item')

class BarRemoveItem(Form):
    submit = SubmitField('remove stock item')


# this is not used, check views.py for more info
class BarEditAmounts(Form):
    # some fields are added by the view
    submit = SubmitField('ok!')


class BarEditItem(wtforms_Form):
    # some fields are added by the view
    name = TextField('name', [validators.Required()])
    price = DecimalField('price (e.g. 1.52)', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')], places=2)
    stock_max = IntegerField('Maximum stock', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')])
    category_id = SelectField('category', coerce=int)
    josto = BooleanField('josto')


class BarEdit(Form):
    # the view adds a BarEditItem form for each stock item
    submit = SubmitField('add stock item')


# this is not used, check views.py for more info
class BarStockup(Form):
    # some fields are added by the view
    submit = SubmitField('ok!')


class BarLog(Form):
    revert = SubmitField('revert')


class BarAddItem(Form):
    name = TextField('Name', [validators.Required()])
    price = DecimalField('Price (e.g. 1.52)', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')],
        places=2)
    stock_max = IntegerField('Stock maximum', 
        [validators.NumberRange(min=0, 
            message='please enter a positive number')])
    category_id = SelectField('Category', coerce=int)
    josto = BooleanField('Josto')
    submit = SubmitField('add stock item')


class AddTransaction(Form):
    date = DateField('date (yyyy-mm-dd)', 
        [validators.Required(
            message='please enter a date using the specified formatting')])
    amount = DecimalField('amount (e.g. 1.52)', 
        [validators.NumberRange(message='please enter a positive or negative number')], places=2)
    description = TextField('description', [validators.Required()])
    bank_id = SelectField('bank', coerce=int)
    to_from = TextField('to/from', [validators.Required()])
    category_id = SelectField('category', coerce=int)
    bank_statement_number = IntegerField('bank statement number (optional)', 
        [validators.Optional(), validators.NumberRange(min=0, 
            message='please enter a positive number')])
    submit = SubmitField('file transaction')


class EditTransaction(AddTransaction):
    submit = SubmitField('edit transaction')


class RequestReimbursement(AddTransaction):
    date = DateField('date of advance (yyyy-mm-dd)', 
        [validators.Required(
            message='please enter a date using the specified formatting')])
    amount = DecimalField('amount advanced (e.g. 1.52)', 
        [validators.NumberRange(min=0, message='please enter a positive number')], places=2)
    submit = SubmitField('request reimbursement')


class ApproveReimbursement(AddTransaction):
    date = DateField('date of reimbursement (yyyy-mm-dd), (optional)', [validators.Optional()]) 


class FilterTransaction(Form):
    amount = SelectField('type', [validators.Optional()])
    category_id = SelectField('category_id', [validators.Optional()])
    bank_id = SelectField('bank', [validators.Optional()])
    submit = SubmitField('filter')
