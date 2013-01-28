from MALMan import app
import MALMan.database as DB
import MALMan.forms as forms
from MALMan.view_utils import add_confirmation, return_flash, accounting_categories, permission_required, Pagination

from flask import render_template, request, redirect, flash, abort, url_for, send_from_directory
from flask.ext.login import current_user
from flask.ext.uploads import UploadSet, configure_uploads, patch_request_class

from werkzeug import secure_filename
from datetime import date


attachments = UploadSet(name='attachments')
configure_uploads(app, attachments)
patch_request_class(app, 5 * 1024 * 1024) # limit max upload size to 5 megabytes

CHANGE_MSG = "These values were updated: "

ITEMS_PER_PAGE = 10


@app.route("/accounting")
@permission_required('membership')
def accounting():
    banks = DB.Banks.query.all()
    running_account = DB.CashTransaction.query.all()
    running_acount_balance = sum(transaction.amount for transaction in running_account)
    return render_template('accounting.html', banks=banks, running_acount_balance=running_acount_balance)


@app.route("/accounting/log", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/accounting/log/page/<int:page>', methods=['GET', 'POST'])
@permission_required('membership')
def accounting_log(page):
    log = DB.Transactions.query.filter(DB.Transactions.date_filed != None).order_by(DB.Transactions.id.desc())
    banks = DB.Banks.query.all()

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
                    log = log.filter(DB.Transactions.amount > 0)
                else:
                    log = log.filter(DB.Transactions.amount < 0)
            else:
                args = {filter[0]: filter[1]}
                log = log.filter_by(**args)
            setattr(form[filter[0]], 'data', filter[1])
    
    item_count = len(log.all())
    log = log.paginate(page, ITEMS_PER_PAGE, False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, ITEMS_PER_PAGE, item_count)

    if form.validate_on_submit():   
        url = '/accounting/log?filters='
        fields = ["bank_id", "category_id", "amount"]
        for field in fields:
            if request.form[field] != '0':
                url += field + ':' + request.form[field] + ","
        return redirect(url)
    return render_template('accounting_log.html', log=log, form=form, pagination=pagination)


@app.route("/accounting/cashlog", defaults={'page': 1})
@app.route('/accounting/cashlog/page/<int:page>')
@permission_required('membership', 'finances')
def accounting_cashlog(page):
    log = DB.CashTransaction.query.order_by(DB.CashTransaction.id.desc())
    
    item_count = len(log.all())
    log = log.paginate(page, ITEMS_PER_PAGE, False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, ITEMS_PER_PAGE, item_count)
   
    return render_template('accounting_cashlog.html', log=log, pagination=pagination)


@app.route("/accounting/request_reimbursement", methods=['GET', 'POST'])
@permission_required('membership')
def accounting_request_reimbursement():
    form = forms.RequestReimbursement()
    del form.bank_id, form.to_from, form.category_id
    if form.validate_on_submit():
        transaction = DB.Transactions(
            advance_date = request.form["date"], 
            amount = "-" + request.form["amount"],
            description = request.form["description"],
            to_from = current_user.name)
        DB.db.session.add(transaction)
        DB.db.session.commit()

        attachment = request.files['attachment']
        if attachment:
            # upload the attachment
            transaction = DB.Transactions.query.order_by(DB.Transactions.id.desc()).first() #we can do better than this
            filename = secure_filename(attachment.filename)
            url = attachments.save(attachment, 
                folder = str(transaction.id), #minimizes the chance of a file existing with the same name
                name = filename)
        
            # add the attachment to the accounting_attachments DB table
            attachment = DB.AccountingAttachment(
                filename = filename,
                transaction_id = transaction.id)
            DB.db.session.add(attachment)

            # link the attachment to the transaction
            setattr(transaction, 'attachments', [attachment])

            # write changes to DB
            DB.db.session.commit()

        flash("the request for reimbursement was filed", "confirmation")
        return redirect(request.path)
    return render_template('accounting_request_reimbursement.html', form=form)


@app.route('/accounting/attachments/<transaction>/<filename>')
def uploaded_file(transaction, filename):
    directory = app.config['UPLOADED_ATTACHMENTS_DEST'] + '/' + transaction + '/'
    return send_from_directory(directory, filename)


@app.route("/accounting/approve_reimbursements")
@permission_required('membership', 'finances')
def accounting_approve_reimbursements():
    requests = DB.Transactions.query.filter_by(date_filed=None)
    return render_template('accounting_approve_reimbursements.html', requests=requests)


@app.route("/accounting/approve_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def accounting_approve_reimbursement(transaction_id):
    banks = DB.Banks.query.all()
    transaction = DB.Transactions.query.get(transaction_id)
    form = forms.ApproveReimbursement(obj=transaction)
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories(IN=False)
    if form.validate_on_submit():
        transaction.date = request.form["date"]
        transaction.amount = request.form["amount"]
        transaction.to_from = request.form["to_from"]
        transaction.description = request.form["description"]
        transaction.category_id = request.form["category_id"]
        transaction.bank_id = request.form["bank_id"]
        transaction.bank_statement_number = request.form["bank_statement_number"]
        transaction.date_filed = date.today()
        transaction.filed_by_id = current_user.id
        DB.db.session.commit()
        flash("the transaction was filed", "confirmation")
        return redirect(request.path)
    return render_template('accounting_approve_reimbursement.html', form=form)


@app.route("/accounting/add_transaction", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def accounting_add_transaction():
    banks = DB.Banks.query.all()
    form = forms.AddTransaction()
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories()
    if form.validate_on_submit():
        transaction = DB.Transactions(
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
        flash("the transaction was filed", "confirmation")

        if request.form["category_id"] == '6':
            id = DB.Transactions.query.order_by(DB.Transactions.id.desc()).first()
            return redirect(url_for('topup_bar_account', transaction_id=id.id))
        elif request.form["category_id"] == '8':
            id = DB.Transactions.query.order_by(DB.Transactions.id.desc()).first()
            return redirect(url_for('file_membershipfee', transaction_id=id.id))
        return redirect('/accounting/log')
    return render_template('accounting_add_transaction.html', form=form)

@app.route("/accounting/topup_bar_account_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def topup_bar_account(transaction_id):
    users = DB.User.query
    form = forms.TopUpBarAccount()
    form.user_id.choices = [(user.id, user.name) for user in users.all()]
    transaction = DB.Transactions.query.get(transaction_id)
    if form.validate_on_submit():
        item = DB.BarAccountLog(
            user_id = request.form["user_id"],
            transaction_id = transaction_id)
        DB.db.session.add(item)
        DB.db.session.commit()
        user = users.get(request.form["user_id"])
        flash(u"\u20AC" + str(transaction.amount) + " was added to " + user.name + "'s bar account", "confirmation")
        return redirect('/accounting/log')
    return render_template('accounting_topup_bar_account.html', form=form, transaction=transaction)


@app.route("/accounting/edit_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def accounting_edit_transaction(transaction_id):
    banks = DB.Banks.query.all()
    transaction = DB.Transactions.query.get(transaction_id)
    form = forms.EditTransaction(obj=transaction)
    form.bank_id.choices = [(bank.id, bank.name) for bank in banks]
    form.category_id.choices = accounting_categories()
    if form.validate_on_submit():
        confirmation = CHANGE_MSG
        for atribute in ['date', 'amount', 'to_from', 'description', 'category_id', 'bank_id', 'bank_statement_number']:
            old_value = getattr(transaction, str(atribute))
            new_value = request.form.get(atribute)
            if str(new_value) != str(old_value):
                setattr(transaction, atribute, new_value)
                confirmation = add_confirmation(confirmation, str(atribute) + 
                    " = " + str(new_value) + " (was " + str(old_value) + ")")
                DB.db.session.commit()
        return_flash(confirmation)
        return redirect(request.path)
    return render_template('accounting_edit_transaction.html', form=form)

@app.route("/accounting/membershipfees", defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/accounting/membershipfees/page/<int:page>')
@permission_required('membership', 'finances')
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
    log = log.paginate(page, ITEMS_PER_PAGE, False).items
    if not log and page != 1:
        abort(404)
    pagination = Pagination(page, ITEMS_PER_PAGE, item_count)

    if form.validate_on_submit():   
        url = '/accounting/membershipfees?filters='
        if request.form['user'] != '0':
            url += 'user' + ':' + request.form['user']
        return redirect(url)
   
    return render_template('accounting_membershipfees.html', log=log, pagination=pagination, form=form)


@app.route("/accounting/file_membershipfee_<int:transaction_id>", methods=['GET', 'POST'])
@permission_required('membership', 'finances')
def file_membershipfee(transaction_id):
    users = DB.User.query
    form = forms.FileMembershipFee()
    form.user_id.choices = [(user.id, user.name) for user in users.all()]
    transaction = DB.Transactions.query.get(transaction_id)

    if form.validate_on_submit():
        item = DB.MembershipFee(
            user_id = request.form["user_id"],
            transaction_id = transaction_id,
            until = request.form["until"])
        DB.db.session.add(item)
        DB.db.session.commit()
        user = users.get(request.form["user_id"])
        flash(user.name + "'s membership dues are payed until " + request.form["until"], "confirmation")
        return redirect('/accounting/log')
    
    return render_template('accounting_file_membershipfee.html', form=form, transaction=transaction)
