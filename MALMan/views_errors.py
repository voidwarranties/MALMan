from MALMan import app
from flask import render_template, request


@app.errorhandler(401)
def error_401(error):
    message = "You need to login to access this page"
    lastpage = request.referrer
    return render_template('error.html', error=error, message=message, lastpage=lastpage), 401


@app.errorhandler(403)
def error_403(error):
    message = "You are lacking permissions necessary to access this page"
    lastpage = request.referrer
    return render_template('error.html', error=error, message=message, lastpage=lastpage), 403


@app.errorhandler(404)
def error_404(error):
    message = "We can't find the page you were looking for."
    lastpage = request.referrer
    return render_template('error.html', error=error, message=message, lastpage=lastpage), 404


@app.errorhandler(413)
def error_413(error):
    message = "You probably tried to send a file larger than we allow."
    lastpage = request.referrer
    return render_template('error.html', error=error, message=message, lastpage=lastpage), 413


@app.errorhandler(500)
def error_500(error):
    error = '500 Internal Server Error'
    message = "An unexpected error has occurred. The administrator has been notified. Sorry for the inconvenience!"
    lastpage = request.referrer
    return render_template('error.html', error=error, message=message, lastpage=lastpage), 500
