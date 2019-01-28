from MALMan import app
import MALMan.database as DB

from flask.ext.script import Manager
from flask_security.utils import encrypt_password

from datetime import date

manager = Manager(app)


@manager.command
def activate_member(email):
    """Makes the user corresponding to the email adress an active member"""

    user = DB.User.query.filter_by(email=email).first()
    if not user:
        return 'There is no registered user with this email adress'
    if user.active_member:
        return "%s is already an active member" % email
    setattr(user, 'membership_start', date.today())
    DB.db.session.commit()
    return "%s was made an active member" % email


@manager.command
def give_perm(email, permission):
    """Grants a permission to the user corresponding to the email adress"""

    user = DB.User.query.filter_by(email=email).first()
    role = DB.Role.query.filter_by(name=permission).first()
    if not user:
        return 'There is no registered user with this email adress'
    if not role:
        return 'The role %s does not exist' % permission
    if role in user.roles:
        return "%s already has the permission %s" % (email, permission)
    DB.user_datastore.add_role_to_user(user, role)
    DB.db.session.commit()
    return "%s was granted the permission %s" % (email, permission)


@manager.command
def confirm_email(email):
    """Manually confirm an email adress"""

    user = DB.User.query.filter_by(email=email).first()
    if not user:
        return 'There is no registered user with this email adress'
    if user.confirmed_at:
        return "%s is already confirmed" % email
    setattr(user, 'confirmed_at', date.today())
    DB.db.session.commit()
    return "%s has been confirmed and can login now" % email

@manager.command
def test():
    """Test the build, without starting a web service"""
    app.config['TESTING'] = True
    app.config['CSRF_ENABLED'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as c:
        resp = c.post('/login', data={'email': "doesnotexists", 'password': "pass",
                                      'submit': "Login", 'next': " ",
                                      'csrf_token': " "}, follow_redirects=True)
        assert '200 OK' in resp.status
        assert 'Specified user does not exist' in resp.data


@manager.command
def init_database():
    """Adds all tables and default data to the database"""
    from MALMan.database import db
    db.create_all()
    # check if StockCategory is empty, and if so put default values in database
    if not DB.StockCategory.query.first():
        DB.db.session.add(DB.StockCategory(name="food"))
        DB.db.session.add(DB.StockCategory(name="alcoholic drink"))
        DB.db.session.add(DB.StockCategory(name="non-alcoholic drink"))
        DB.db.session.add(DB.Bank(id=1, name="bank 1"))
        DB.db.session.add(DB.Bank(id=2, name="bank 2"))
        DB.db.session.add(DB.Bank(id=99, name="cash"))
        DB.db.session.add(DB.AccountingCategory(name='vaste kosten',
                                                legal_category='Diverse Goederen en Diensten',
                                                is_revenue=0))
        DB.db.session.add(DB.AccountingCategory(name='Aankopen diverse goederen en diensten',
                                                legal_category='Diverse Goederen en Diensten',
                                                is_revenue=0))
        DB.db.session.add(DB.AccountingCategory(name='investeringen',
                                                legal_category='Diverse Goederen en Diensten',
                                                is_revenue=0))
        DB.db.session.add(DB.AccountingCategory(name='aankopen verbruiksgoederen',
                                                legal_category='Goederen en Diensten',
                                                is_revenue=0))
        DB.db.session.add(DB.AccountingCategory(name='verkoop verbruiksgoederen',
                                                legal_category='Verkopen Handelsgoederen',
                                                is_revenue=1))
        DB.db.session.add(DB.AccountingCategory(name='Aanvullen drankrekening',
                                                legal_category='Verkopen Handelsgoederen',
                                                is_revenue=1))
        DB.db.session.add(DB.AccountingCategory(name='Transfer',
                                                legal_category='Transfer',
                                                is_revenue=1))
        DB.db.session.add(DB.AccountingCategory(name='Lidgelden',
                                                legal_category='Bijdragen',
                                                is_revenue=1))
        DB.db.session.add(DB.AccountingCategory(name='Deelname workshops',
                                                legal_category='Giften',
                                                is_revenue=1))
        DB.db.session.add(DB.AccountingCategory(name='feed the hackers',
                                                legal_category='Giften',
                                                is_revenue=1))
        DB.db.session.add(DB.AccountingCategory(name='Geld donaties',
                                                legal_category='Giften',
                                                is_revenue=1))
        DB.db.session.add(DB.AccountingCategory(name='Bankkosten',
                                                legal_category='Overige',
                                                is_revenue=0))
        DB.db.session.add(DB.AccountingCategory(name='Transfer',
                                                legal_category='Transfer',
                                                is_revenue=0))
        DB.db.session.add(DB.Role(name="bar", description="Manage bar stock"))
        DB.db.session.add(DB.Role(name="members", description="membership management"))
        DB.db.session.add(DB.Role(name="finances", description="edit accounting information"))
        DB.db.session.commit()


@manager.command
def seed_dummy_data():
    """Adds dummy data to the database so all features can be tested"""
    users = [('admin@example.com', 'secret', ['members', 'bar', 'finances']),
             ('user@example.com', 'secret', [])]
    for u in users:
        DB.user_datastore.create_user(email=u[0], password=encrypt_password(u[1]), roles=u[2], active=True)
        DB.db.session.commit()
        confirm_email(u[0])
        activate_member(u[0])


@manager.command
def rundebug():
    app.debug = True
    app.run(host='0.0.0.0', debug=True)


if __name__ == "__main__":
    manager.run()
