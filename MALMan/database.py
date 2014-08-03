"""Connect to the database and define the database table models"""

from MALMan import app
from flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin
try:
    from flask.ext.sqlalchemy import SQLAlchemy
except ImportError:
    from flask_sqlalchemy import SQLAlchemy
import datetime

from sqlalchemy import and_, or_
from sqlalchemy.ext.hybrid import hybrid_property

def _date_to_datetime(date):
    '''Convert a date object to a datetime object

    The time is set to 00:00:00
    '''
    midnight = datetime.time(0, 0, 0)
    return datetime.datetime.combine(date, midnight)


db = SQLAlchemy(app)

roles_users = db.Table('members_roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('members.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('members_roles.id')))


class Role(db.Model, RoleMixin):
    """Define the Role database table"""
    __tablename__ = 'members_roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return self.name


class User(db.Model, UserMixin):
    """Define the User database table"""
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    street = db.Column(db.String(255))
    number = db.Column(db.Integer)
    bus = db.Column(db.String(255))
    postalcode = db.Column(db.Integer)
    city = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date())
    telephone = db.Column(db.String(255))
    membership_start = db.Column(db.Date())
    membership_end = db.Column(db.Date())
    membership_dues = db.Column(db.Numeric(5, 2), default=0)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    show_telephone = db.Column(db.Boolean())
    show_email = db.Column(db.Boolean())
    motivation = db.Column(db.Text())
    confirmed_at = db.Column(db.Date())
    roles = db.relationship('Role', secondary=roles_users,
        backref=db.backref('Roleusers', lazy='dynamic'))

    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)

    @property
    def bar_account_balance(self):
        total = 0
        for item in self.bar_account_log:
            if item.purchase_id:
                total -= item.purchase.price
            else:
                total += item.transaction.amount
        return total

    @property
    def membership_due(self):
    	for item in self.Membership_Fee:
    	    #This will only be excecuted once, but this replaces a complicated if-construction
            return item.until
        return "0000-00-00"

    @hybrid_property
    def active_member(self):
        '''Whether the user is a member at the moment.
        This function is used when the propery is called through User.active_member'''
        start = self.membership_start
        end = self.membership_end
        if start:
            if end and start < end:
                return False
            if start <= datetime.date.today():
                return True
        return False

    @active_member.expression
    def active_member_sql(member):
        '''Whether the user is a member at the moment.
        This function is used when the propery is called by sqlalchemy functions such as filter()'''
        start = member.membership_start
        end = member.membership_end
        is_member = and_(
            start != None,
            start <= datetime.date.today(),
            or_(
                end == None,
                end < start
            )
        )
        return is_member

user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class MembershipFee(db.Model):
    """Define the members_fees database table"""
    __tablename__ = 'members_fees'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    user = db.relationship('User', backref=db.backref("Membership_Fee", order_by="desc(MembershipFee.until)"), lazy="joined")
    transaction_id = db.Column(db.Integer, db.ForeignKey('accounting_transactions.id'))
    transaction = db.relationship('Transaction')
    until = db.Column(db.Date())


class StockItem(db.Model):
    """Define the StockItem database table"""
    __tablename__ = 'bar_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    stock_max = db.Column(db.Integer)
    price = db.Column(db.Numeric(5, 2))
    category_id = db.Column(db.Integer, db.ForeignKey('bar_categories.id'))
    category = db.relationship("StockCategory", backref="dranken", lazy="joined")
    josto = db.Column(db.Boolean())
    purchases = db.relationship("BarLog", backref="Drank")
    active = db.Column(db.Boolean())

    @property
    def stock(self):
        # this might be improved
        return sum(item.amount for item in self.purchases)

    @property
    def stockup(self):
        return (self.stock_max - self.stock)

    def __repr__(self):
        return '<Bar item %r>' % self.name


class StockCategory(db.Model):
    """Define the StockCategory database table"""
    __tablename__ = 'bar_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __repr__(self):
        return '<Category %r>' % self.name


class BarLog(db.Model):
    """Define the BarLog database table"""
    __tablename__ = 'bar_log'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('bar_items.id'))
    item = db.relationship("StockItem", backref="BarLog", lazy="joined")
    amount = db.Column(db.Integer)
    price = db.Column(db.Numeric(5, 2), default=0)
    datetime = db.Column(db.DateTime())
    user_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    user = db.relationship('User')
    transaction_type = db.Column(db.String(50))

    def __repr__(self):
        return '<id %r>' % self.id


class Bank(db.Model):
    """Define the acounting_banks database table"""
    __tablename__ = 'accounting_banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    transactions = db.relationship("Transaction")

    @property
    def balance(self):
        calculated_balance = 0
        for transaction in self.transactions:
            if transaction.is_revenue:
                calculated_balance += transaction.amount
            else:
                calculated_balance -= transaction.amount
        return calculated_balance


class CashTransaction(db.Model):
    """Define the acounting_cashregister database table"""
    __tablename__ = 'accounting_cashregister'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('bar_log.id'))
    purchase = db.relationship('BarLog', backref="cash_transaction", lazy="joined")
    is_revenue = db.Column(db.Boolean())
    amount = db.Column(db.Numeric(10, 2))
    description = db.Column(db.Text())
    datetime = db.Column(db.DateTime())


class AccountingCategory(db.Model):
    """Define the accounting_categories database table"""
    __tablename__ = 'accounting_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    legal_category = db.Column(db.String(256))
    is_revenue = db.Column(db.Boolean())


class AccountingAttachment(db.Model):
    """Define the accounting_attachments database table"""
    __tablename__ = 'accounting_attachments'
    id = db.Column(db.Integer, primary_key=True)
    extension = db.Column(db.String(50))

    @property
    def filename(self):
        return str(self.id) + '.' + self.extension


attachments_transactions = db.Table('accounting_attachments_transactions',
        db.Column('attachment_id', db.Integer(), db.ForeignKey('accounting_attachments.id')),
        db.Column('transaction_id', db.Integer(), db.ForeignKey('accounting_transactions.id')))


class Transaction(db.Model):
    """Define the transactions database table"""
    __tablename__ = 'accounting_transactions'
    id = db.Column(db.Integer, primary_key=True)
        # Could be used to tag (paper, or scanned) receipts to transactions.
    date = db.Column(db.Date())
        # date the bank transaction took place
    advance_date = db.Column(db.Date())
        # only applicable if the money was advanced
    facturation_date = db.Column(db.Date())
        # same as 'date' if there is no invoice
    is_revenue = db.Column(db.Boolean())
    amount = db.Column(db.Numeric(11, 2))
        # positive is it is a revenue, negative if it's an expense
    to_from = db.Column(db.String(256))
        # the second party involved in the transaction
    category_id = db.Column(db.Integer, db.ForeignKey('accounting_categories.id'))
        # which kind of revenue or expense the transaction is
    category = db.relationship("AccountingCategory")
    description = db.Column(db.Text)
    bank_id = db.Column(db.Integer, db.ForeignKey('accounting_banks.id'))
        # the bankaccount involved. cash transactions are considered an account too (id=99)
    bank = db.relationship("Bank", backref="Transaction", lazy="joined")
    bank_statement_number = db.Column(db.Integer)
        # number in the bank's account statements
    date_filed = db.Column(db.Date())
        # if it is a reimbursement this is the date the request was approved
    filed_by_id = db.Column(db.Integer, db.ForeignKey('members.id'))
        # if it is a reimbursement this is the user that approved the request
    filed_by = db.relationship('User')
    reimbursement_comments = db.Column(db.Text)
    attachments = db.relationship('AccountingAttachment', secondary=attachments_transactions,
        backref=db.backref('transactions', lazy='dynamic'))


class BarAccountLog(db.Model):
    """Define the bar_accounts database table"""
    __tablename__ = 'bar_accounts_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    user = db.relationship('User', backref="bar_account_log", lazy="joined")
    purchase_id = db.Column(db.Integer, db.ForeignKey('bar_log.id'))
    purchase = db.relationship('BarLog', backref="bar_account_transaction", lazy="joined")
    transaction_id = db.Column(db.Integer, db.ForeignKey('accounting_transactions.id'))
    transaction = db.relationship('Transaction')

    @property
    def datetime(self):
        '''Return the datetime of either the transaction or the purchase'''
        if self.purchase_id:
            return self.purchase.datetime
        else:
            return _date_to_datetime(self.transaction.date)
