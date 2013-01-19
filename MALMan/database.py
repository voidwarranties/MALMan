"""Connect to the database and define the database table models"""

from MALMan import app
from MALMan.flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin
try:
    from flask.ext.sqlalchemy import SQLAlchemy
except ImportError:
    from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('roles.id')))


class Role(db.Model, RoleMixin):
    """Define the Role database table"""
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return self.name


class User(db.Model, UserMixin):
    """Define the User database table"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    street = db.Column(db.String(255))
    number = db.Column(db.Integer)
    bus = db.Column(db.String(255))
    postalcode = db.Column(db.Integer)
    city = db.Column(db.String(255))
    date_of_birth = db.Column(db.DateTime())
    telephone = db.Column(db.String(255))
    active_member = db.Column(db.Boolean(), default=False)
    member_since = db.Column(db.DateTime(), default="0000-00-00")
    membership_dues = db.Column(db.Integer, default="0")
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    show_telephone = db.Column(db.Boolean())
    show_email = db.Column(db.Boolean())
    motivation = db.Column(db.String())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users, 
        backref=db.backref('Roleusers', lazy='dynamic'))

    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)

    @property
    def bar_account_balance(self):
        total = 0
        for item in self.bar_account_log:
            if item.purchase_id:
                total -= item.purchase.total_price
            else:
                total += item.transaction.amount
        return total


user_datastore = SQLAlchemyUserDatastore(db, User, Role)

class StockItems(db.Model):
    """Define the StockItems database table"""
    __tablename__ = 'bar_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    stock_max = db.Column(db.Integer)
    price = db.Column(db.Numeric(5, 2))
    category_id = db.Column(db.Integer, db.ForeignKey('bar_categories.id'))
    category = db.relationship("StockCategories", backref="dranken", lazy="joined")
    josto = db.Column(db.Boolean())
    purchases = db.relationship("BarLog", backref="Drank")

    @property
    def stock(self):
        # this might be improved
        return sum(item.amount for item in self.purchases) 

    @property
    def stockup(self):
        return (self.stock_max - self.stock)

    def __init__(self, name, stock_max, price, category_id, josto):
        self.name = name
        self.stock_max = stock_max
        self.price = price
        self.category_id = category_id
        self.josto = josto

    def __repr__(self):
        return '<Bar item %r>' % self.name

    def remove(entry):
        """remove entry from StockItems table"""
        db.session.delete(entry)
        db.session.commit()


class StockCategories(db.Model):
    """Define the StockCategories database table"""
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
    stock_name = db.relationship("StockItems", backref="BarLog", lazy="joined")
    amount = db.Column(db.Integer)
    total_price = db.Column(db.Numeric(5, 2))
    datetime = db.Column(db.DateTime())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User')
    transaction_type = db.Column(db.String(50))

    def __repr__(self):
        return '<id %r>' % self.id

    def remove(entry):
        """remove entry from BarLog table"""
        db.session.delete(entry)
        db.session.commit()


class Banks(db.Model):
    """Define the acounting_banks database table"""
    __tablename__ = 'accounting_banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    transactions = db.relationship("Transactions")

    @property
    def balance(self):
        return sum(item.amount for item in self.transactions) 


class AccountingCategories(db.Model):
    """Define the accounting_categories database table"""
    __tablename__ = 'accounting_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    legal_category = db.Column(db.String)
    is_revenue = db.Column(db.Boolean())


class Transactions(db.Model):
    """Define the transactions database table"""
    __tablename__ = 'accounting_transactions'
    id = db.Column(db.Integer, primary_key=True)
        # Could be used to tag (paper, or scanned) receipts to transactions.
    date = db.Column(db.DateTime())
        # date the transaction took place.
    amount = db.Column(db.Integer)
        # positive is it is a revenue, negative if it's an expense
    to_from = db.Column(db.String)
        # the second party involved in the transaction
    category_id = db.Column(db.Integer, db.ForeignKey('accounting_categories.id'))
        # which kind of revenue or expense the transaction is
    category = db.relationship("AccountingCategories")
    description = db.Column(db.String)
    bank_id = db.Column(db.Integer, db.ForeignKey('accounting_banks.id'))
        # the bankaccount involved. cash transactions are considered an account too (id=99)
    bank = db.relationship("Banks", backref="Transactions", lazy="joined")
    bank_statement_number = db.Column(db.Integer)
        # number in the bank's account statements 
    advance_date = db.Column(db.DateTime())
        # only applicable if it is a reimbursement request; the date the money was advanced
    date_filed = db.Column(db.DateTime())
        # if it is a reimbursement this is the date the request was approved
    filed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
        # if it is a reimbursement this is the user that approved the request
    filed_by = db.relationship('User')

class BarAccountLog(db.Model):
    """Define the bar_accounts database table"""
    __tablename__ = 'bar_accounts_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref="bar_account_log", lazy="joined")
    purchase_id = db.Column(db.Integer, db.ForeignKey('bar_log.id'))
    purchase = db.relationship('BarLog')
    transaction_id = db.Column(db.Integer, db.ForeignKey('accounting_transactions.id'))
    transaction = db.relationship('Transactions')

    @property
    def datetime(self):
        if self.purchase_id:
            return self.purchase.datetime
        else:
            return self.transaction.date
        

# create missing tables in db
# should only be run once, remove this when db is stable
#db.create_all()