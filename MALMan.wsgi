activate_this = '/srv/MALMan/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/srv/MALMan')

from MALMan import app as application

