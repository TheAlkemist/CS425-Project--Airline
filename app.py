from flask import Flask
from flask import session
from flask import render_template
from flask import request
from flask.json import dumps
from log import setup_logging
from DataCommunicationLayer import DataCommunicationLayer
import json

app = Flask(__name__)

async_mode = None
app.secret_key = "#$ALKJ34"

@app.route("/")
def landing_page():
    global comm_layer
    logger = setup_logging('logs/airfare_app')

    comm_layer = DataCommunicationLayer(logger)
    return render_template("LandingPage.html")

@app.route("/registration_page",methods = ["POST"])
def registration_page():
    return render_template("UserRegistration.html")

@app.route("/register_user",methods = ["POST"])
def register_user():

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))

    email = data['email']
    name = data['name']
    home_airport = data['home_airport']

    if email == '':
        return 'Email cannot be blank!'
    if name == '':
        return 'Name cannot be blank!'
    if home_airport == '':
        success = comm_layer.register_user(email,name)
    else:
        success = comm_layer.register_user(email, name, home_airport)
    return 'Successfully Added new User' if success else 'Failed to Add new User!'



if __name__ == '__main__':
    app.run(port=5000,debug=True)