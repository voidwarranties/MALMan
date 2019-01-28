Installation [![Build Status](https://travis-ci.org/voidwarranties/MALMan.svg?branch=master)](https://travis-ci.org/voidwarranties/MALMan) [![Requirements Status](https://requires.io/github/voidwarranties/MALMan/requirements.png?branch=master)](https://requires.io/github/voidwarranties/MALMan/requirements/?branch=master)
============

## Setting up a development environment using vagrant and ansible.

Get the source code.

    git clone git://github.com/voidwarranties/MALMan.git

Install vagrant, virtualbox and ansible.
You can now create a development environment in a virtual machine by executing `vagrant up`.

    cd MALMan
    vagrant up

Add an entry for the VM to /etc/hosts so you don't have to access the vm by it's IP address

    echo "172.16.12.2  malman-dev" | sudo tee -a /etc/hosts

The different components of the development environment should now be accessible:

- MALMan: http://malman-dev/ (runs as a WSGI app in production mode under apache, u:admin@example.com p:secret)
- PHPMyAdmin: http://malman-dev/phpmyadmin  (u:MALMan p:CLUBMATE2010)
- Maildev: http://malman-dev:1080/ (displays sent emails)

### Debug mode

To run the app in debug mode you need to log in to the VM and start the app manually:

    $ vagrant ssh
    $ cd /var/www/MALMan
    $ export WERKZEUG_DEBUG_PIN=off; virtualenv/bin/python commands.py rundebug

A debug version of MALMan should now be available at http://malman-dev:5000/.
In debug mode the app will auto-reload when source files change and an interactive stack trace will be displayed in the browser if an error occurs.

---

** Warning: the rest of this README file might not be up to date anymore. **

## Setting up a development environment manually

### Getting the code

Create a directory to contain the program and get the source code:

    git clone git://github.com/voidwarranties/MALMan.git /var/www/MALMan

From here on on I will assume you are located in the directory you installed MALMan in,
so move into this directory.

    cd /var/www/MALMan

### Setting up the virtualenv and getting dependencies

You will need to have version 2 of python, pip and virtualenv installed on your system.
On debian-based systems these are provided by the packages python, python-pip and python-virtualenv.
If installing on Arch linux you will need the packages python2, python2-pip and python2-virtualenv
and will have to substitute 'virtualenv-2' for 'virtualenv' in the following command.

Set up a isolated Python environment in the directory 'virtualenv'.

    virtualenv virtualenv

Fetch the latest version of distribute, which is needed to fetch some of the dependencies:

    virtualenv/bin/pip install distribute --upgrade


Install the required python packages into the enviroment.

    virtualenv/bin/pip install -r requirements.txt

### Setting up the database

If you want to use sqlite skip this step.

If you want to use mysql create a new database with your favorite mysql client.
For mysql you also have to install one more requirement:

    virtualenv/bin/pip install MySQL-python==1.2.5

### Configuration

Copy MALMan.cfg.template to MALMan.cfg and fill in the database, SMTP and security parameters.

    cp MALMan/MALMan.cfg{.template,}

For development purposes you might want to use Python's SMTP debugging server:

    python -m smtpd -n -c DebuggingServer localhost:1025

This will start an SMTP server on port 1025 of localhost.
All mails sent will be displayed in the console output.

### Before the first run

Test the database connection create the tables we need:

    virtualenv/bin/python commands.py init_database

### Running in debug mode

You should now be able to run MALMan in development mode. This isn't suitable for production use.

    virtualenv/bin/python commands.py runserver

MALMan should be running locally on 0.0.0.0:5000.

Specify a host to make it accessible to other devices on the network:

    virtualenv/bin/python commands.py runserver --host ::

### Activating the first account

After registering a user's membership request will have to be accepted by an
active member with member management permissions. With no one to activate the
first user we will have to do this outside of MALMan:

    virtualenv/bin/python commands.py confirm_email user@example.org
    virtualenv/bin/python commands.py activate_member user@example.org
    virtualenv/bin/python commands.py give_perm user@example.org members

This will accept the membership request of your first user and grant her
membership management permissions, so further request can be handled through
MALMan.

### Running in production mode

Be sure to disable the DEBUG mode in MALMan/MALMan.cfg when running in production.

MALMan can run as a WSGI app under Apache or as a fastcgi app under various other web servers.
A runner is provided for both (MALMan.wsgi and MALMan.fcgi).

#### Using apache

Include this in /etc/httpd/conf/httpd.conf:

    LoadModule wsgi_module modules/mod_wsgi.so
    WSGIScriptAlias /MALMan /var/www/MALMan/MALMan.wsgi
    <Directory /var/www/MALMan/MALMan>
        Order deny,allow
        Allow from all
        WSGIScriptReloading On
    </Directory>

This tells apache to load the wsgi module at /var/www/MALMan/MALMan.wsgi
and serve it under /MALMan.

#### Using Lighttpd

1. enable fastcgi:

    lighttpd-enable-mod fastcgi

2. make a new file /etc/lighttpd/conf-available/15-fastcgi-MALMan.conf with this content:

    fastcgi.server += (
        "/MALMan" =>
        ((
            "socket" => "/tmp/MALMan-fcgi.sock",
               "bin-path" => "/var/www/MALMan/MALMan.fcgi",
            "check-local" => "disable",
            "max-procs" => 1
        ))
    )

3. enable the new config:

    lighttpd-enable-mod fastcgi-MALMan

4. change owner of the files to www-data:

    chown www-data:www-data /var/www/MALMan/MALMan -R

4. restart lighttpd:

    service lighttpd restart

5. you can find your website at http://localhost/MALMan.fcgi
(or using the ip / a linked domain if hosted remotely)
