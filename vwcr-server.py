#!/usr/bin/env python

import SimpleXMLRPCServer
from datetime import datetime
from MALMan import app
from MALMan.database import db, User, StockItem, BarLog, BarAccountLog, CashTransaction
from flask_security.utils import verify_password

__title__ = "VWCR"
__version__ = "0.3"
__author__ = "the VoidWarranties All-Stars"

def authenticate(user_id, password):
    user = User.query.get(user_id)
    with app.app_context():
        if verify_password(password, user.password):
            return 'true'
        else:
            return 'false'

def check_balance(user_id, price):
    with app.app_context():
        user = User.query.get(user_id)
        if user.bar_account_balance >= price:
            return 'true'
        else:
            return 'false'

def _record_purchase(item_id, price, user_id):
    """add a purchase to the database and return the purchase id"""
    changes = BarLog(
        item_id = item_id,
        amount = -1,
        price = price,
        user_id = user_id,
        transaction_type = "sale")
    db.session.add(changes)
    db.session.commit()
    return BarLog.query.order_by(BarLog.id.desc()).first().id

def _record_cash_transaction(amount, description, purchase_id=None):
    """add a cash transaction to the database"""
    changes = CashTransaction(
        purchase_id = purchase_id,
        amount = amount,
        description = description,
        datetime = datetime.now())
    db.session.add(changes)
    db.session.commit()

def _record_bar_account_transaction(user_id, purchase_id):
    """add bar account transaction to the database"""
    change = BarAccountLog(
        user_id = user_id,
        purchase_id = purchase_id)
    db.session.add(change)
    db.session.commit()

def purchase(item_id, price, user_id=None):
    """Register a purchase in the bar log.
    If a userID is passed also register the purchase in the user's bar BarAccountLog.
    If no userID is passed register it as a cash transaction.
    """
    purchase_id = _record_purchase(item_id, price, user_id)
    if user_id == None:
        _record_cash_transaction(price, "purchase", purchase_id)
    else:
        _record_bar_account_transaction(user_id, purchase_id)

def donate(amount, description=None):
    """add a donation to the database"""
    string = "donation"
    if description:
        string += ": " + description
    _record_cash_transaction(amount, string)

def SellDrink(Drink, User):
    if User[0] == 'Cash':
        purchase(Drink['id'], Drink['price'])
    else:
        user_id = User[0]
        purchase(Drink['id'], Drink['price'], user_id)
    return "done"
    
def GetStockList():
    items = StockItem.query\
        .order_by(StockItem.category_id)\
        .order_by(StockItem.name).all()
    # make a tuple of tuple from the db object
    stock = (( item.id, 
                item.name.encode('ascii','ignore'),
                item.stock_max,
                item.price,
                item.category_id,
                int(item.josto)
            ) for item in items)
    stock = tuple(stock)
    return stock

def GetUserList():
    users = User.query\
        .filter_by(active_member='1')\
        .order_by(User.name).all()
    # make a tuple of tuple from the db object
    members = (( user.id, user.name.encode('ascii','ignore')) for user in users )
    members = tuple(members)
    return members

def VerifyBuyer(firstname, lastname,  price,  password):
    if verify_password(user, password) and bar_account_balance >= str(price):
        return user

# VWCR_Server
adres = ("0.0.0.0",  9000)
server = SimpleXMLRPCServer.SimpleXMLRPCServer(adres)
server.register_function(authenticate)
server.register_function(check_balance)
server.register_function(GetStockList)
server.register_function(SellDrink)
server.register_function(GetUserList)
server.register_function(VerifyBuyer)
server.register_introspection_functions()
server.serve_forever()
