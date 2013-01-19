#!/usr/bin/python2
"""Define functions to be used by VWCR"""

from MALMan import app
from MALMan.database import db, BarLog
from flask.ext.script import Manager

manager = Manager(app)

@manager.command
def record_purchase(item_id, amount, total_price, user_id=99):
    """add a purchase to the database"""
    changes = BarLog(
        item_id = item_id,
        amount = - int(amount),
        total_price = total_price,
        user_id = user_id,
        transaction_type = "sale")
    db.session.add(changes)
    db.session.commit()

@manager.command
def record_donation(amount):
	"""add a donation to the database"""
	#add a transation to the cash register
	pass

if __name__ == "__main__":
    manager.run()
