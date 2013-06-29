from MALMan import app
import MALMan.database as DB
import MALMan.forms as forms
from MALMan.view_utils import add_confirmation, return_flash, accounting_categories, permission_required, membership_required, Pagination

from flask import render_template, request, redirect, flash, abort, url_for
from flask.ext.login import current_user
from flask.ext.wtf import (Form, SubmitField, FormField, BooleanField,
    IntegerField, validators)

@app.route("/bar")
@membership_required()
def bar():
    items = DB.StockItem.query.filter_by(active=True).order_by(DB.StockItem.name.asc()).all()
    return render_template('bar/list_items.html', items=items)

@app.route("/bar/activate_stockitems", methods=['GET', 'POST'])
@permission_required('bar')
def bar_activate_stockitems():
    stockitems = DB.StockItem.query.filter_by(active=False).all()
    for stockitem in stockitems:
        setattr(forms.BarActivateItem, 'activate_' + str(stockitem.id),
            BooleanField('activate item'))
    form = forms.BarActivateItem()

    if form.validate_on_submit():
        confirmation = 'the following stockitem\'s status were set to "active": '
        for stockitem in stockitems:
            new_value = 'activate_' + str(stockitem.id) in request.form
            if new_value != stockitem.active:
                stockitem.active = True
                confirmation = confirmation + stockitem.name + ", "
        DB.db.session.commit()
        return_flash(confirmation)
        return redirect(request.url)

    return render_template('bar/activate_stockitems.html', stockitems=stockitems, form=form)

@app.route("/bar/remove_<int:item_id>", methods=['GET', 'POST'])
@permission_required('bar')
def bar_remove_item(item_id):
    stockitem = DB.StockItem.query.get(item_id)
    form = forms.BarRemoveItem()
    if form.validate_on_submit():
        new_value = 'activate_' + str(stockitem.id) in request.form
        if new_value != stockitem.active:
            stockitem.active = False
            DB.db.session.commit()
            flash('The item "' + stockitem.name + '" status was set to "inactive"', 'confirmation')
        return redirect(url_for('bar'))
    return render_template('bar/remove_item.html', stockitem=stockitem, form=form)


@app.route("/bar/edit_item_amounts", methods=['GET', 'POST'])
@permission_required('bar')
def bar_edit_item_amounts():
    items = DB.StockItem.query.filter_by(active=True).order_by(DB.StockItem.name.asc()).all()
    for item in items:
        setattr(forms.BarEditAmounts, 'amount_' + str(item.id),
            IntegerField(item.name, [validators.NumberRange(min=0,
                message='please enter a positive number')],
            default=item.stock))
    form = forms.BarEditAmounts()
    if form.validate_on_submit():
        confirmation = app.config['CHANGE_MSG']
        for item in items:
            if int(request.form["amount_" + str(item.id)]) != int(item.stock):
                changes = DB.BarLog(
                    item_id = item.id,
                    amount = int(request.form["amount_" + str(item.id)]) - int(item.stock),
                    user_id = current_user.id,
                    transaction_type = "correction")
                DB.db.session.add(changes)
                DB.db.session.commit()
                confirmation = add_confirmation(confirmation, "stock " +
                    item.name + " = " + request.form["amount_" +
                    str(item.id)])
        return_flash(confirmation)
        return redirect(request.url)
    return render_template('bar/edit_amounts.html', form=form)


@app.route("/bar/edit_items", methods=['GET', 'POST'])
@permission_required('bar')
def bar_edit_items():
    items = DB.StockItem.query.filter_by(active=True).order_by(DB.StockItem.name.asc()).all()
    categories = DB.StockCategory.query.all()
    for item in items:
        setattr(forms.BarEdit, str(item.id),
            FormField(forms.BarEditItem, default=item, separator='_'))
    form = forms.BarEdit()
    for item in form:
        if item.name != 'csrf_token' and item.name != 'submit':
            item.category_id.choices = [(category.id, category.name) for category in categories]
    if form.validate_on_submit():
        confirmation = app.config['CHANGE_MSG']
        for item in items:
            # only write to DB and display a confirmation if the value given in the POST does not equal the value in the DB
            atributes = ['name' , 'price' , 'stock_max', 'category_id', 'josto']
            for atribute in atributes:
                old_value = getattr(item, atribute)
                if atribute == 'josto':
                    new_value = str(item.id) + '_josto' in request.form
                else:
                    new_value = request.form[str(item.id) + '_' + atribute]
                if str(old_value) != str(new_value):
                    setattr(item, atribute, new_value)
                    DB.db.session.commit()
                    if atribute == "name":
                        confirmation = add_confirmation(confirmation,
                            old_value + " => " + new_value)
                    elif atribute == "category_id":
                        newcat = DB.StockCategory.query.get(new_value).name
                        oldcat = DB.StockCategory.query.get(old_value).name
                        confirmation = add_confirmation(confirmation,
                            "category" + " " + item.name + " = \"" + newcat +
                            "\" (was \"" + oldcat + "\")")
                    else:
                        confirmation = add_confirmation(confirmation,
                            atribute + " " + item.name + " = " +
                            str(new_value) + " (was " + str(old_value) + ")")
        return_flash(confirmation)
        return redirect(request.url)
    return render_template('bar/edit_items.html', form=form)


@app.route("/bar/stockup_josto", methods=['GET', 'POST'])
@permission_required('bar')
def bar_stockup_josto():
    # get all active stock items from josto that need stocking up
    items = DB.StockItem.query.filter_by(active=True, josto=True).order_by(DB.StockItem.name.asc()).all()
    items = [item for item in items if item.stockup > 0]

    # we need to redefine this form everytime the view gets called,
    # otherwise the setattr's are caried over
    class StockupForm(Form):
        submit = SubmitField('stockup!')
    for item in items:
        setattr(StockupForm,
                str(item.id),
                FormField(forms.StockupJostoFormMixin,
                          label=item.name,
                          default={'amount':item.stockup}))
    form = StockupForm()

    if form.validate_on_submit():
        confirmation = app.config['CHANGE_MSG']
        for item in items:
            checked = str(item.id) + '-check'  in request.form
            if checked:
                amount = int(request.form[str(item.id) + "-amount" ])
                if amount != 0:
                    changes = DB.BarLog(
                        item_id = item.id,
                        amount = amount,
                        user_id = current_user.id,
                        transaction_type = "stock up")
                    DB.db.session.add(changes)
                    DB.db.session.commit()
                    confirmation = add_confirmation(confirmation, "stock " +
                        item.name + " = +" + str(amount))
        return_flash(confirmation)
        return redirect(request.url)
    return render_template('bar/stockup_josto.html', form=form)


@app.route("/bar/stockup_own", methods=['GET', 'POST'])
@permission_required('bar')
def bar_stockup_own():
    # get all active stock items that are not from josto
    items = DB.StockItem.query.filter_by(active=True, josto=False).order_by(DB.StockItem.name.asc()).all()

    # we need to redefine this form everytime the view gets called,
    # otherwise the setattr's are caried over
    class StockupForm(Form):
        submit = SubmitField('stockup!')
    for item in items:
        setattr(StockupForm,
                "amount-" + str(item.id),
                IntegerField(item.name,
                             [validators.NumberRange(min=0, message='Please enter a positive number.')],
                             default=0))
    form = StockupForm()

    if form.validate_on_submit():
        item_confirmation = []
        confirmation = "These stockitems were stocked up: "
        for item in items:
            amount = int(request.form["amount-" + str(item.id)])
            if amount != 0:
                changes = DB.BarLog(
                    item_id = item.id,
                    amount = amount,
                    user_id = current_user.id,
                    transaction_type = "stock up")
                DB.db.session.add(changes)
                confirmation_string = "%s (+%i)" % (item.name, amount)
                item_confirmation.append(confirmation_string)
        DB.db.session.commit()
        if item_confirmation:
            confirmation = "These stockitems were stocked up: "
            confirmation += ", ".join(item_confirmation)
            flash(confirmation, 'confirmation')
        else:
            flash("No items to stock up.", "error")
        return redirect(request.url)
    return render_template('bar/stockup_own.html', form=form)


@app.route("/bar/log", defaults={'page': 1})
@app.route("/bar/log/page/<int:page>")
@permission_required('bar')
def bar_log(page):
    log = DB.BarLog.query.order_by(DB.BarLog.datetime.desc())
    item_count = len(log.all())
    log = log.paginate(page, app.config['ITEMS_PER_PAGE'], False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, app.config['ITEMS_PER_PAGE'], item_count)
    return render_template('bar/log.html', log=log, pagination=pagination)


@app.route("/bar/reverse_<int:item_id>", methods=['GET'])
@permission_required('bar')
def bar_reverse(item_id):
    barlog_entry = DB.BarLog.query.get(item_id)
    # barlog_entry.bar_account_entry and barlog_entry.cash_transaction are lists, not elements
    [DB.db.session.delete(transaction) for transaction in barlog_entry.bar_account_transaction]
    [DB.db.session.delete(transaction) for transaction in barlog_entry.cash_transaction]
    DB.db.session.delete(barlog_entry)
    DB.db.session.commit()
    flash('The change was reverted', 'confirmation')
    prev = request.args.get('prev')
    if prev:
        return redirect(prev)
    return redirect(url_for('bar_log'))


@app.route("/bar/add_item", methods=['GET', 'POST'])
@permission_required('bar')
def bar_add_item():
    categories = DB.StockCategory.query.all()
    form = forms.BarAddItem()
    form.category_id.choices = [(category.id, category.name) for category in categories]

    if form.validate_on_submit():
        josto = 'josto' in request.form
        item = DB.StockItem(
            name = request.form["name"],
            stock_max = request.form["stock_max"],
            price = request.form["price"],
            category_id = request.form["category_id"],
            josto = josto,
            active = 1)
        DB.db.session.add(item)
        DB.db.session.commit()
        flash("added stock item: " + request.form["name"], "confirmation")
        return redirect(url_for('bar'))

    return render_template('bar/add_item.html', form=form)
