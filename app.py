from flask import Flask
from flask import session
from flask import render_template
from flask import request
from flask.json import dumps
from log import setup_logging
from DataCommunicationLayer import DataCommunicationLayer


app = Flask(__name__)

async_mode = None
app.secret_key = "#$ALKJ34"

@app.route("/")
def landing_page():
    logger = setup_logging('logs/airfare_app')
    global comm_layer
    comm_layer = DataCommunicationLayer(logger)
    return render_template("LandingPage.html")

@app.route("/registration_page",methods = ["POST"])
def registration_page():
    return render_template("UserRegistration.html")

@app.route("/register_user",methods = ["POST"])
def register_user():
    email = request.form['email']
    name = request.form['name']
    home_airport = request.form['home_airport']
    if home_airport == '':
        comm_layer.register_user(email,name)
    else:
        comm_layer.register_user(email, name, home_airport)




if __name__ == '__main__':
    app.run(port=5000,debug=True)