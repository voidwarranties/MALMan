#!/usr/bin/python2
"""Define functions to be used by VWCR"""

from MALMan import app
from MALMan.database import db, BarLog, BarAccountLog, CashTransaction
from flask.ext.script import Manager
from datetime import datetime

manager = Manager(app)

def _record_purchase(item_id, amount, total_price, user_id):
    """add a purchase to the database and return the purchase id"""
    changes = BarLog(
        item_id = item_id,
        amount = - int(amount),
        total_price = total_price,
        user_id = user_id,
        transaction_type = "sale")
    db.session.add(changes)
    db.session.commit()
    return BarLog.query.order_by(BarLog.id.desc()).first().id

def _record_cash_transaction(purchase_id, amount, description):
    """add a cash transaction to the database"""
    changes = CashTransaction(
        amount = amount,
        description = description,
        datetime = datetime.now())
    db.session.add(changes)
    db.session.commit()

@manager.command
def donate(amount, description=None):
    """add a donation to the database"""
    string = "donation"
    if description:
        string += ": " + description
    _record_cash_transaction(None, amount, string)

@manager.command
def purchase(item_id, amount, total_price, user_id=None):
    """Register a purchase in the bar log.
    If a userID is passed also register the purchase in the user's bar BarAccountLog.
    If no userID is passed register it as a cash transaction.
    """
    purchase_id = _record_purchase(item_id, amount, total_price, user_id)
    if user_id == None:
        _record_cash_transaction(purchase_id, total_price, "purchase #" + str(purchase_id))
    else:
        change = BarAccountLog(
            user_id = user_id,
            purchase_id = purchase_id)
        db.session.add(change)
        db.session.commit()

if __name__ == "__main__":
    manager.run()
