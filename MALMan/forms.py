"""Define the various forms used in MALMan"""

from MALMan import app
from wtforms import Form as wtforms_Form
from flask.ext.wtf import (Form, BooleanField, TextField, PasswordField, 
    DateField, IntegerField, SubmitField, SelectField, DecimalField, 
    TextAreaField, FileField, validators, EqualTo)
from flask.ext.uploads import UploadSet, configure_uploads

attachments = UploadSet(name='attachments')
configure_uploads(app, attachments)

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


from flask_security.forms import ConfirmRegisterForm, unique_user_email
class RegisterForm(MembersEditOwnAccount, ConfirmRegisterForm):
    '''The register form'''
    motivation = TextAreaField('My motivation to become a member:', 
        [validators.Required()])
    email = TextField('Email', [unique_user_email, 
        validators.Email(message='please enter a valid email address')])
    submit = SubmitField("create my account")

    def to_dict(self):
        return dict(
            email = self.email.data,
            password = self.password.data,
            name = self.name.data,
            street = self.street.data,
            number = self.number.data,
            bus = self.bus.data,
            postalcode = self.postalcode.data,
            city = self.city.data,
            date_of_birth = self.date_of_birth.data,
            telephone = self.telephone.data,
            show_telephone = self.show_telephone.data,
            show_email = self.show_email.data,
            motivation = self.motivation)


## check if a name is alreasy in use
# from MALMan.database import StockItem
# def _unique_item_name(form, field):
#    if StockItem.query.filter_by(name=field.data) is not None:
#        raise ValidationError(field.data + ' is already a stock item')

class BarRemoveItem(Form):
    submit = SubmitField('remove stock item')


class BarActivateItem(Form):
    #some fields are added by the view
    submit = SubmitField("activate stock item(s)")


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
    facturation_date = DateField('facturation date (optional, yyyy-mm-dd)', 
        [validators.Optional()])
    is_revenue = SelectField('type', 
        choices = [(1, "revenue"), (0, "expense")], coerce=int)
    amount = DecimalField('amount (e.g. 1.52)', 
        [validators.NumberRange(message='please enter a positive or negative number')], places=2)
    description = TextField('description', [validators.Required()])
    bank_id = SelectField('bank', coerce=int)
    to_from = TextField('to/from', [validators.Required()])
    category_id = SelectField('category')
    bank_statement_number = IntegerField('bank statement number (optional)', 
        [validators.Optional(), validators.NumberRange(min=0, 
            message='please enter a positive number')])
    attachment = FileField("add attachment", 
        [validators.file_allowed(attachments, "This filetype is not whitelisted")])
    submit = SubmitField('file transaction')


class TopUpBarAccount(Form):
    user_id = SelectField('user', coerce=int)
    submit = SubmitField('top up')


class FileMembershipFee(Form):
    user_id = SelectField('Member', coerce=int)
    until = DateField("This settles this member's membership dues until (yyyy-mm-dd)", 
        [validators.Required(
            message='please enter a date using the specified formatting')])
    submit = SubmitField('file payment of membership fee')


class EditTransaction(AddTransaction):
    attachment = FileField("add attachment", 
        [validators.file_allowed(attachments, "This filetype is not whitelisted")])
    submit = SubmitField('edit transaction')


class RequestReimbursement(Form):
    advance_date = DateField('date of advance (yyyy-mm-dd)',
        [validators.Required(
            message='please enter a date using the specified formatting')])
    amount = DecimalField('amount advanced (e.g. 1.52)', 
        [validators.NumberRange(min=0, message='please enter a positive number')], places=2)
    description = TextField('description', [validators.Required()])
    attachment = FileField("add attachment", 
        [validators.file_allowed(attachments, "This filetype is not whitelisted")])
    submit = SubmitField('request reimbursement')


class Remove_Attachment(Form):
    cancel = SubmitField('cancel')
    submit = SubmitField('remove attachment')


class ApproveReimbursement(AddTransaction):
    date = DateField('date of reimbursement (yyyy-mm-dd)',
        [validators.Required(
            message='please enter a date using the specified formatting')])


class FilterTransaction(Form):
    is_revenue = SelectField('type', 
        choices = [("","filter by type"), ("1", "revenues"), ("0", "expenses")])
    category_id = SelectField('category_id')
    bank_id = SelectField('bank')
    submit = SubmitField('filter')


class FilterMembershipFees(Form):
    user = SelectField('user')
    user.choices = [("0","filter by user")]
    submit = SubmitField('filter')


class FilterCashbook(Form):
    year = SelectField('year')
    bank_id = SelectField('bank')
    submit = SubmitField('go')
