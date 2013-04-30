from MALMan import app
import MALMan.database as DB
import MALMan.forms as forms
from MALMan.view_utils import (add_confirmation, return_flash, accounting_categories, 
    permission_required, membership_required, Pagination, upload_attachments)

from flask import render_template, request, redirect, flash, abort, url_for, send_from_directory
from flask.ext.login import current_user
from flask.ext.uploads import UploadSet, configure_uploads, patch_request_class
from flask.ext.wtf import file_allowed

from werkzeug import secure_filename
from datetime import date

attachments = UploadSet(name='attachments')
configure_uploads(app, attachments)

@app.route("/accounting")
@membership_required()
def accounting():
    banks = DB.Bank.query.all()
    running_account = DB.CashTransaction.query.all()
    running_acount_balance = sum(transaction.amount for transaction in running_account)
    return render_template('accounting/balance.html', banks=banks, running_acount_balance=running_acount_balance)


@app.route("/accounting/log", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/accounting/log/page/<int:page>', methods=['GET', 'POST'])
@membership_required()
def accounting_log(page):
    log = DB.Transaction.query.filter(DB.Transaction.date_filed != None).order_by(DB.Transaction.id.desc())
    banks = DB.Bank.query.all()

    form = forms.FilterTransaction()
    form.bank_id.choices = [("0","filter by bank")]
    form.bank_id.choices.extend([(str(bank.id), bank.name) for bank in banks])
    form.category_id.choices = [("0","filter by category")]
    form.category_id.choices.extend(accounting_categories())

    filters = request.args.get('filters', '').split(",")
    for filter in filters:
        filter = filter.split(":")
        if len(filter) > 1: #split() seems to return empty lists, don't run on those
            if filter[0] == "amount":
                if filter[1] == '1':
                    log = log.filter(DB.Transaction.amount > 0)
                else:
                    log = log.filter(DB.Transaction.amount < 0)
            else:
                args = {filter[0]: filter[1]}
                log = log.filter_by(**args)
            setattr(form[filter[0]], 'data', filter[1])
    
    item_count = len(log.all())
    log = log.paginate(page, app.config['ITEMS_PER_PAGE'], False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, app.config['ITEMS_PER_PAGE'], item_count)

    if form.validate_on_submit():   
        url = '/accounting/log?filters='
        fields = ["bank_id", "category_id", "amount"]
        for field in fields:
            if request.form[field] != '0':
                url += field + ':' + request.form[field] + ","
        return redirect(url)
    return render_template('accounting/log.html', log=log, form=form, pagination=pagination)

@app.route("/accounting/accounting/remove_attachment_<transaction_id>_<attachment_id>", methods=['GET', 'POST'])
@permission_required('finances')
def accounting_remove_attachment(transaction_id, attachment_id):
    if 'cancel' in request.form:
        flash("removing the attachment was canceled", "confirmation")
        return redirect(url_for('accounting_log'))
    
    transaction = DB.Transaction.query.get(transaction_id)
    form = forms.Remove_Attachment()
    
    if form.validate_on_submit():
        new_attachments = []
        for attachment in transaction.attachments:
            if str(attachment.id) != str(attachment_id):
                new_attachments.append(attachment)
        setattr(transaction, 'attachments', new_attachments)
        DB.db.session.commit()
        flash("the attachment was removed", "confirmation")
        return redirect(url_for('accounting_edit_transaction', transaction_id=transaction.id))
    
    return render_template('accounting/remove_attachment.html', form=form)


@app.route("/accounting/cashlog", defaults={'page': 1})
@app.route('/accounting/cashlog/page/<int:page>')
@permission_required('finances')
def accounting_cashlog(page):
    log = DB.CashTransaction.query.order_by(DB.CashTransaction.id.desc())
    
    item_count = len(log.all())
    log = log.paginate(page, app.config['ITEMS_PER_PAGE'], False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, app.config['ITEMS_PER_PAGE'], item_count)
   
    return render_template('accounting/cashlog.html', log=log, pagination=pagination)


@app.route("/accounting/request_reimbursement", methods=['GET', 'POST'])
@membership_required()
def accounting_request_reimbursement():
    form = forms.RequestReimbursement()
    del form.bank_id, form.to_from, form.category_id
   
    if form.validate_on_submit():
        transaction = DB.Transaction(
            date = request.form["date"], 
            amount = "-" + request.form["amount"],
            description = request.form["description"],
            to_from = current_user.name)
        DB.db.session.add(transaction)
        DB.db.session.commit()

        upload_attachments(request, attachments, transaction, DB)

        flash("the request for reimbursement was filed", "confirmation")
        return redirect(request.url)
    return render_template('accounting/request_reimbursement.html', form=form)


@app.route('/accounting/attachments/<transaction>/<filename>')
def accounting_attachment(transaction, filename):
    directory = app.config['UPLOADED_ATTACHMENTS_DEST'] + '/' + transaction + '/'
    return send_from_directory(directory, filename)


@app.route("/accounting/approve_reimbursements")
@permission_required('finances')
def accounting_approve_reimbursements():
    requests = DB.Transaction.query.filter_by(date_filed=None)
    return render_template('accounting/list_reimbursements.html', requests=requests)


@app.route("/accounting/approve_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('finances')
def accounting_approve_reimbursement(transaction_id):
    banks = DB.Bank.query.all()
    transaction = DB.Transaction.query.get(transaction_id)
    form = forms.ApproveReimbursement(obj=transaction)
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories(IN=False)
    if form.validate_on_submit():
        transaction.reimbursement_date = request.form["reimbursement_date"] or "0001-01-01"
        transaction.amount = request.form["amount"]
        transaction.to_from = request.form["to_from"]
        transaction.description = request.form["description"]
        transaction.category_id = request.form["category_id"]
        transaction.bank_id = request.form["bank_id"]
        transaction.bank_statement_number = request.form["bank_statement_number"]
        transaction.date_filed = date.today()
        transaction.filed_by_id = current_user.id
        DB.db.session.commit()

        upload_attachments(request, attachments, transaction, DB)

        flash("the transaction was filed", "confirmation")
        return redirect(url_for('accounting_approve_reimbursements'))
    return render_template('accounting/approve_reimbursement.html', form=form, transaction=transaction )


@app.route("/accounting/add_transaction", methods=['GET', 'POST'])
@permission_required('finances')
def accounting_add_transaction():
    banks = DB.Bank.query.all()
    form = forms.AddTransaction()
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories()
    if form.validate_on_submit():
        transaction = DB.Transaction(
            date = request.form["date"],
            amount = request.form["amount"],
            to_from = request.form["to_from"], 
            description = request.form["description"],
            category_id = request.form["category_id"],
            bank_id = request.form["bank_id"],
            date_filed = date.today(),
            filed_by_id = current_user.id
            )
        DB.db.session.add(transaction)
        DB.db.session.commit()

        upload_attachments(request, attachments, transaction, DB)
        
        if request.form["category_id"] == '6':
            id = DB.Transaction.query.order_by(DB.Transaction.id.desc()).first()
            return redirect(url_for('topup_bar_account', transaction_id=id.id))
        elif request.form["category_id"] == '8':
            id = DB.Transaction.query.order_by(DB.Transaction.id.desc()).first()
            return redirect(url_for('file_membershipfee', transaction_id=id.id))
        return redirect(url_for('accounting_log'))

        flash("the transaction was filed", "confirmation")
    return render_template('accounting/add_transaction.html', form=form)

@app.route("/accounting/topup_bar_account_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('finances')
def topup_bar_account(transaction_id):
    users = DB.User.query
    form = forms.TopUpBarAccount()
    form.user_id.choices = [(user.id, user.name) for user in users.all()]
    transaction = DB.Transaction.query.get(transaction_id)
    if form.validate_on_submit():
        item = DB.BarAccountLog(
            user_id = request.form["user_id"],
            transaction_id = transaction_id)
        DB.db.session.add(item)
        DB.db.session.commit()
        user = users.get(request.form["user_id"])
        flash(u"\u20AC" + str(transaction.amount) + " was added to " + user.name + "'s bar account", "confirmation")
        return redirect(url_for('accounting_log'))
    return render_template('accounting/topup_bar_account.html', form=form, transaction=transaction)


@app.route("/accounting/edit_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('finances')
def accounting_edit_transaction(transaction_id):
    banks = DB.Bank.query.all()
    transaction = DB.Transaction.query.get(transaction_id)
    form = forms.EditTransaction(obj=transaction)
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories()
    if form.validate_on_submit():
        confirmation = app.config['CHANGE_MSG']
        atributes = ['date', 'amount', 'to_from', 'description', 
            'category_id', 'bank_id']
        for atribute in atributes:
            old_value = getattr(transaction, str(atribute))
            new_value = request.form.get(atribute)
            if str(new_value) != str(old_value):
                setattr(transaction, atribute, new_value)
                confirmation = add_confirmation(confirmation, str(atribute) + 
                    " = " + str(new_value) + " (was " + str(old_value) + ")")
            transaction.date_filed
        DB.db.session.commit()

        uploadconfirmation = upload_attachments(request, attachments, transaction, DB)
        
        confirmation = add_confirmation(confirmation, uploadconfirmation)
        return_flash(confirmation)
        return redirect(request.url)
    return render_template('accounting/edit_transaction.html', form=form, transaction=transaction)

@app.route("/accounting/membershipfees", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/accounting/membershipfees/page/<int:page>')
@permission_required('finances')
def accounting_membershipfees(page):
    log = DB.MembershipFee.query
    users = DB.User.query

    form = forms.FilterMembershipFees()
    form.user.choices = [("0","filter by user")]
    form.user.choices.extend([(str(user.id), user.name) for user in users])

    filter = request.args.get('filters', '').split(":")
    if len(filter) > 1: #split() seems to return empty lists, don't run on those
        log = log.filter_by(user_id=filter[1])
        setattr(form[filter[0]], 'data', filter[1])
    
    item_count = len(log.all())
    log = log.paginate(page, app.config['ITEMS_PER_PAGE'], False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, app.config['ITEMS_PER_PAGE'], item_count)

    if form.validate_on_submit():   
        url = '/accounting/membershipfees?filters='
        if request.form['user'] != '0':
            url += 'user' + ':' + request.form['user']
        return redirect(url)
   
    return render_template('accounting/membershipfees.html', log=log, pagination=pagination, form=form)


@app.route("/accounting/file_membershipfee_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('finances')
def file_membershipfee(transaction_id):
    users = DB.User.query
    form = forms.FileMembershipFee()
    form.user_id.choices = [(user.id, user.name) for user in users.all()]
    transaction = DB.Transaction.query.get(transaction_id)

    if form.validate_on_submit():
        item = DB.MembershipFee(
            user_id = request.form["user_id"],
            transaction_id = transaction_id,
            until = request.form["until"])
        DB.db.session.add(item)
        DB.db.session.commit()
        user = users.get(request.form["user_id"])
        flash(user.name + "'s membership dues are payed until " + request.form["until"], "confirmation")
        return redirect(url_for('accounting_log'))
    
    return render_template('accounting/file_membershipfee.html', form=form, transaction=transaction)
