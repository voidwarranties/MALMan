from MALMan import app
import MALMan.database as DB
import MALMan.forms as forms
from MALMan.view_utils import add_confirmation, return_flash, accounting_categories, permission_required, Pagination

from flask import render_template, request, redirect, flash, abort, url_for
from flask.ext.login import current_user
from flask.ext.wtf import (Form, SubmitField, FormField, BooleanField, 
    IntegerField, validators)

@app.route("/bar")
@permission_required('membership')
def bar():
    items = DB.StockItem.query.all()
    return render_template('bar/list_items.html', items=items)


@app.route("/bar_remove_<int:item_id>", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def bar_remove(item_id):
    item = DB.StockItem.query.get(item_id)
    form = forms.BarRemoveItem()
    if form.validate_on_submit():
        DB.StockItem.remove(item)
        flash('The item was removed', 'confirmation')
        return redirect(url_for('bar'))
    return render_template('bar/remove_item.html', item=item, form=form)


@app.route("/bar/edit_item_amounts", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def edit_item_amounts():
    items = DB.StockItem.query.all()
    for item in items:
        setattr(forms.BarEditAmounts, 'amount_' + str(item.id), 
            IntegerField(item.name, [validators.NumberRange(min=0, 
                message='please enter a positive number')], 
            default=item.stock))
    form = forms.BarEditAmounts()
    if form.validate_on_submit():
        confirmation = app.CHANGE_MSG
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
        return redirect(request.path)
    return render_template('bar/edit_amounts.html', form=form)


@app.route("/bar/edit_items", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def edit_items():
    items = DB.StockItem.query.all()
    categories = DB.StockCategory.query.all()
    for item in items:
        setattr(forms.BarEdit, str(item.id), 
            FormField(forms.BarEditItem, default=item, separator='_'))
    form = forms.BarEdit()
    for item in form:
        if item.name != 'csrf_token' and item.name != 'submit':
            item.category_id.choices = [(category.id, category.name) for category in categories]
    if form.validate_on_submit():
        confirmation = app.CHANGE_MSG
        for item in items:
            # only write to DB and display a confirmation if the value given in the POST does not equal the value in the DB 
            atributes = ['name' , 'price' , 'stock_max', 'category_id', 'josto']
            for atribute in atributes:
                if atribute == 'josto':
                    old_value = formatbool(getattr(item, atribute))
                    new_value = forms.booleanfix(request.form, str(item.id) + '_josto')
                else: 
                    old_value = getattr(item, atribute)
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
        return redirect(request.path)
    return render_template('bar/edit_items.html', form=form)


@app.route("/bar/stockup", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def stockup():
    # get all stock items from josto
    items = DB.StockItem.query.filter_by(josto=True).all()
    # we need to redefine this everytime the view gets called, otherwise the setattr's are caried over
    class StockupForm(Form):
        submit = SubmitField('ok!')
    for item in items:
        if item.stockup > 0:
            setattr(StockupForm, 'amount_' + str(item.id), 
                IntegerField(item.name, [validators.NumberRange(min=0, 
                    message='please enter a positive number')], 
                default=item.stockup))
            setattr(StockupForm, 'check_' + str(item.id), 
                BooleanField(item.name))
    form = StockupForm()
    if form.validate_on_submit():
        confirmation = app.CHANGE_MSG
        for item in items:
            checked = forms.booleanfix(request.form, 'check_' + str(item.id))
            if checked: 
                if int(request.form["amount_" + str(item.id)]) != 0:
                    changes = DB.BarLog(
                        item_id = item.id,
                        amount = request.form["amount_" + str(item.id)],
                        user_id = current_user.id,
                        transaction_type = "stock up")
                    DB.db.session.add(changes)
                    DB.db.session.commit()
                    confirmation = add_confirmation(confirmation, "stock " + 
                        item.name + " = +" + 
                        request.form["amount_" + str(item.id)])
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('bar/stockup.html', form=form)


@app.route("/bar/log", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route("/bar/log/page/<int:page>", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def bar_log(page):
    log = DB.BarLog.query.order_by(DB.BarLog.datetime.desc())
    item_count = len(log.all())
    log = log.paginate(page, app.ITEMS_PER_PAGE, False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, app.ITEMS_PER_PAGE, item_count)
    form = forms.BarLog()
    if form.validate_on_submit():
        changes = DB.BarLog.query.get(request.form["revert"])
        DB.BarLog.remove(changes)
        flash('The change was reverted', 'confirmation')
        return redirect(request.path)
    return render_template('bar/log.html', log=log, pagination=pagination, form=form)


@app.route("/bar/add_item", methods=['GET', 'POST'])
@permission_required('membership', 'bar')
def add_item():
    categories = DB.StockCategory.query.all()
    form = forms.BarAddItem()
    form.category_id.choices = [(category.id, category.name) for category in categories]
    
    if form.validate_on_submit():
        josto = forms.booleanfix(request.form, 'josto')
        item = DB.StockItem(
            name = request.form["name"],
            stock_max = request.form["stock_max"], 
            price = request.form["price"], 
            category_id = request.form["category_id"], 
            josto = josto)
        DB.db.session.add(item)
        DB.db.session.commit()
        flash("added stock item: " + request.form["name"], "confirmation")
        return redirect(request.path)
    
    return render_template('bar/add_item.html', form=form)
