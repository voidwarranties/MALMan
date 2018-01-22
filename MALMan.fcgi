#!/usr/bin/python2
import sys
from os import path

activate_this = path.join(path.dirname(path.abspath( __file__ )), 'virtualenv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

from flup.server.fcgi import WSGIServer

sys.path.insert(0, path.dirname(path.abspath( __file__ )))

from MALMan import app

if __name__ == '__main__':
    WSGIServer(app).run()
