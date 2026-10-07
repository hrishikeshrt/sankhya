#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 22:59:39 2020

@author: Hrishikesh Terdalkar
"""

import datetime
from flask import Flask, render_template  # , url_for, redirect
from flask_uploads import configure_uploads

# from utils.reverseproxied import ReverseProxied

from sankhya.katapayaadi.settings import app as katapayaadi_app
from sankhya.katapayaadi.webapp import texts
from sankhya.katapayaadi.webapp import webapp as katapayaadi_webapp

from sankhya.aaryabhatiya.webapp import webapp as aaryabhatiya_webapp

from sankhya.bhoota.webapp import webapp as bhoota_webapp

###############################################################################

webapp = Flask('Alpha-Syllabic Numeral Systems',
               template_folder='sankhya/templates',
               static_folder='static')
# webapp.wsgi_app = ReverseProxied(webapp.wsgi_app)
webapp.secret_key = '' # place your secret key here


@webapp.context_processor
def inject_global_constants():
    return {
        'now': datetime.datetime.utcnow(),
    }


@webapp.route("/")
def sankhya_home():
    return render_template("sankhya_main.html")


###############################################################################

webapp.register_blueprint(katapayaadi_webapp)
webapp.config['UPLOADED_TEXTS_DEST'] = katapayaadi_app.data_dir
configure_uploads(webapp, texts)

webapp.register_blueprint(aaryabhatiya_webapp)
webapp.register_blueprint(bhoota_webapp)

###############################################################################


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    port = 2490

    webapp.run(host=host, port=port, debug=True)
