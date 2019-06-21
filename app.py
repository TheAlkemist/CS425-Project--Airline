from flask import Flask
from flask import session
from flask_login import current_user, login_user, LoginManager, logout_user
from User import User
from flask import render_template
from flask import request
import wtforms
from flask import redirect, url_for
from flask.json import dumps
from log import setup_logging
from DataCommunicationLayer import DataCommunicationLayer
import json

app = Flask(__name__)

async_mode = None
app.secret_key = "#$ALKJ34"

login_manager = LoginManager()
login_manager.init_app(app)

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
    password = data['password']
    name = data['name']
    home_airport = data['home_airport']

    if email == '':
        return 'Email cannot be blank!'
    if name == '':
        return 'Name cannot be blank!'
    if home_airport == '':
        success = comm_layer.register_user(email,password,name)
    else:
        success = comm_layer.register_user(email,password, name, home_airport)
    return 'Successfully Added new User' if success else 'Failed to Add new User!'

@login_manager.user_loader
def load_user(user_id):
    return comm_layer.get_user_from_db(user_id)


@app.route('/login_page', methods=['POST'])
def login_page():
    if current_user.is_authenticated:
        return 'User id already logged in!'
    return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))
    email = data['email']
    pwd = data['password']

    user = comm_layer.get_user_from_db(email)
    if user is None or not user.check_password(pwd):
        return 'Invalid username or password'
        #return redirect(url_for('login'))
    login_user(user)
    return 'Successfully Logged In!'

@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return 'Successfully Logged Out!'

if __name__ == '__main__':
    app.run(port=5000,debug=True)


