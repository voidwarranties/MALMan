from MALMan import app
import MALMan.database as DB

from flask.ext.script import Manager

from textwrap import dedent
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
def test():
    """Test the build, without starting a web service"""
    app.config['TESTING'] = True
    app.config['CSRF_ENABLED'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as c:
        resp = c.post('/login', data={'email':"doesnotexists", 'password':"pass", 'submit':"Login", 'next':" ", 'csrf_token':" "}, follow_redirects=True)
        assert '200 OK' in resp.status
        assert 'Specified user does not exist' in resp.data

if __name__ == "__main__":
    manager.run()
