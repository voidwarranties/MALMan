from MALMan import app
import MALMan.database as DB

from flask import Response, request
from flask_security.utils import verify_and_update_password
from flask.ext.basicauth import BasicAuth

import json
from datetime import datetime

api_auth = BasicAuth(app)

@app.route("/api/stock")
@api_auth.required
def list_stock():
    stock = DB.StockItem.query.filter_by(active=True).all()
    items = [ {
        'id': str(item.id),
        'name': str(item.name),
        'price': str(item.price),
        'category': str(item.category.name)} for item in stock ]
    return Response(json.dumps(items), mimetype='application/json')


@app.route("/api/user")
@api_auth.required
def list_users():
    users = DB.User.query.filter(DB.User.bar_account_balance > 0 and DB.User.active_member == 1).order_by(DB.User.name).all()
    userlist = [ {
        'id': str(user.id),
        'name': str(user.name)} for user in users ]
    return Response(json.dumps(userlist), mimetype='application/json')


@app.route("/api/user/<int:user_id>")
@api_auth.required
def authenticate_user(user_id):
    """Return the user's account balance if user and password match, return False otherwise"""
    user = DB.User.query.get(user_id)
    if not user:
        return str(False)
    if verify_and_update_password(request.args['password'], user):
        return str(user.bar_account_balance)
    return str(False)

        
@app.route("/api/purchase", methods=['POST'])
@api_auth.required
def purchase():
    """Register a purchase in the bar log.
    If a userID is passed also register the purchase in the user's bar BarAccountLog.
    If no userID is passed register it as a cash transaction.
    """
    if not 'item_id' in request.form:
        return str(False)
    item_id = int(request.form['item_id'])
    item = DB.StockItem.query.get(item_id)
    if not item:
        return str(False)
    if 'user_id' in request.form:
        user_id = int(request.form['user_id'])
        user = DB.User.query.get(user_id)
        if not user: 
            return str(False)
    else: 
        user_id = None
         
    purchase = DB.BarLog(
        item_id = item.id,
        amount = -1,
        price = item.price,
        user_id = user_id,
        transaction_type = "sale")
    DB.db.session.add(purchase)
    DB.db.session.commit()

    if user_id != None:
        transaction = DB.BarAccountLog(
            user_id = user.id,
            purchase_id = purchase.id)
        DB.db.session.add(transaction)
        DB.db.session.commit()
    else:
        transaction = DB.CashTransaction(
            purchase_id = purchase.id,
            is_revenue = True,
            amount = item.price,
            description = "purchase",
            datetime = datetime.now())
        DB.db.session.add(transaction)
        DB.db.session.commit()
    
    return str(True)

