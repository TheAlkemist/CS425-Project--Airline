from flask import Flask
from flask import session
from flask_login import current_user, login_user, LoginManager, logout_user
from User import User
from flask import render_template
from flask import request
from flask import redirect, url_for
from flask.json import dumps
from log import setup_logging
from DataCommunicationLayer import DataCommunicationLayer, Address, CreditCard
import json
from datetime import datetime, timedelta

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

    success = False
    msg = ''

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))

    home_airport = data['home_airport']
    password = data['password']
    password_check = data['password_check']

    del data['home_airport']
    del data['password_check']

    for key, value in data.items():
        if value == '':
            return '%s cannot be blank!' % key

    if password != password_check:
        return 'Password does not match!'

    address = Address(data['building_number'],data['direction'],data['street'],data['city'],data['state'],data['country'],data['zipcode'])

    success = comm_layer.register_user(data['email'],password,data['first_name'],data['last_name'],home_airport,address)

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
        return 'Already Logged In!'

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))
    email = data['email']
    pwd = data['password']

    user = comm_layer.get_user_from_db(email)
    if user is None or not user.check_password(pwd):
        return 'Invalid username or password'
    login_user(user)
    return 'Successfully Logged In!'

@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return 'Successfully Logged Out!'

@app.route('/manage_account', methods=['POST'])
def manage_account():
    if not current_user.is_authenticated:
        return 'You must be logged in to manage your account!'
    return render_template("ManageAccount.html")

@app.route('/manage_bookings', methods=['POST'])
def manage_bookings():
    if not current_user.is_authenticated:
        return 'You must be logged in to manage your bookings!'
    return render_template("ManageBookings.html")

@app.route('/flights', methods=['POST'])
def flights():
    return render_template("Flights.html")

@app.route('/get_addresses', methods=['GET'])
def user_addresses():
    if not current_user.is_authenticated:
        return

    addresses = comm_layer.get_addresses_for_user(current_user.get_id())

    tmp = {}
    for a in addresses:
        tmp[a.get_address_string()] = a.dictionary()

    return json.dumps(tmp)

@app.route('/add_address', methods=['POST'])
def add_address():
    if not current_user.is_authenticated:
        return 'Must Be logged in the add an address!'
    data = json.loads(request.data.decode('utf-8').replace("'", '"'))

    for key, value in data.items():
        if value == '':
            return '%s cannot be blank!' % key

    address = Address(data['building_number'], data['direction'], data['street'], data['city'], data['state'],
                      data['country'], data['zipcode'])



    success = comm_layer.add_address(current_user.get_id(),address)

    if success:
        return "Address added successfully!"
    else:
        return 'Failed to Add Address'

@app.route('/remove_address', methods=['POST'])
def remove_address():
    if not current_user.is_authenticated:
        return 'Must Be logged in to remove an address!'

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))
    address_id = data['address_id']
    success,msg = comm_layer.remove_address( current_user.get_id(),address_id)

    if success:
        return "Address removed successfully!"
    else:
        return msg

@app.route('/modify_address', methods=['POST'])
def modify_address():
    if not current_user.is_authenticated:
        return 'Must Be logged in to modify an address!'

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))
    address = Address(data['building_number'], data['direction'], data['street'], data['city'], data['state'],
                      data['country'], data['zipcode'])
    old_address_id = data['old_address']
    success,msg = comm_layer.modify_address(current_user.get_id(), address,old_address_id)

    if success:
        return "Address modified successfully!"
    else:
        return msg


@app.route('/get_credit_cards', methods=['GET'])
def user_cards():
    if not current_user.is_authenticated:
        return

    cards = comm_layer.get_credit_cards_for_user(current_user.get_id())

    tmp = {}
    for a in cards:
        tmp[a.card_no] = a.dictionary()

    return json.dumps(tmp)

@app.route('/add_credit_card', methods=['POST'])
def add_credit_card():
    if not current_user.is_authenticated:
        return 'Must Be logged in to add a credit card!'
    data = json.loads(request.data.decode('utf-8').replace("'", '"'))

    for key, value in data.items():
        if value == '':
            return '%s cannot be blank!' % key

    card = CreditCard(data['card_no'], data['address'], data['exp_date'], data['type'], data['name_on_card'])
    success = comm_layer.add_cc(current_user.get_id(),card)

    if success:
        return "Credit card added successfully!"
    else:
        return 'Failed to Add Credit Card'

@app.route('/remove_credit_card', methods=['POST'])
def remove_credit_card():
    if not current_user.is_authenticated:
        return 'Must Be logged in to remove a credit card!'

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))
    card_no = data['card_no']
    success,msg = comm_layer.remove_cc( current_user.get_id(),card_no)

    if success:
        return "Credit Card removed successfully!"
    else:
        return msg

@app.route('/modify_credit_card', methods=['POST'])
def modify_credit_card():
    if not current_user.is_authenticated:
        return 'Must Be logged in to modify a credit card!'

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))
    card_no = data['card_no']
    new_address = data['new_address']
    success,msg = comm_layer.modify_credit_card( card_no,new_address)

    if success:
        return "Credit Card address changed successfully!"
    else:
        return msg

@app.route('/add_booking', methods=['POST'])
def add_booking():
    if not current_user.is_authenticated:
        return 'Must Be logged in to book flights!'

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))
    card_no = data['card_no']
    flight_class = data['flight_class']
    flights = data['to_flights'] + data['from_flights']
    flight_ids = [f['flight_no'] for f in flights]

    success = comm_layer.add_booking(current_user.get_id(),flight_class, card_no,flight_ids)

    if success:
        return "Flights successfully booked!"
    else:
        return "Failed to book flights!"

@app.route('/get_bookings', methods=['GET'])
def get_bookings():
    if not current_user.is_authenticated:
        return

    bookings = comm_layer.get_bookings(current_user.get_id())
    return json.dumps(bookings)


@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if not current_user.is_authenticated:
        return
    data = json.loads(request.data.decode('utf-8').replace("'", '"'))
    booking_no = data['booking_no']
    success = comm_layer.remove_booking(booking_no)
    if success:
        return "Booking successfully cancelled!"
    else:
        return "Failed to cancel booking!"

@app.route('/search_flights', methods=['POST','GET'])
def search_flights():

    msg = {'to_itins': [], 'from_itins': [], 'msg': '','success':True}

    data = json.loads(request.data.decode('utf-8').replace("'", '"'))

    to_iata = data['to']
    from_iata = data['from']

    if to_iata == '' or from_iata == '':
        msg['success'] = False
        msg['msg'] = 'To and From must not be blank!'
        return json.dumps(msg)

    dept_date = data['depart']
    return_date = data['return_dt'] if data['rtrn'] else None

    if dept_date == '' or return_date == '':
        msg['success'] = False
        msg['msg'] = 'Dept and Arrival dates must not be blank!'
        return json.dumps(msg)

    dept_date = datetime.strptime(dept_date,'%Y-%m-%d')
    if data['rtrn']:
        return_date = datetime.strptime(return_date,'%Y-%m-%d')

    sort_by = data['sort']

    flight_class = data['flight_class']

    max_duration = None if data['max_dur'] == '' else timedelta(hours = int(data['max_dur']))
    max_connections = None if data['max_con'] == '' else int(data['max_con'])
    max_price = None if data['max_price'] == '' else float(data['max_price'])

    skyline = data['skyline']

    to_itins, from_itins = comm_layer.get_itineraries(flight_class,dept_date,from_iata,to_iata,return_date
                             ,max_duration = max_duration,max_connections=max_connections,max_price=max_price,skyline =skyline)

    if sort_by == 'price':
        to_itins.sort(key = lambda var:var.total_price)
        from_itins.sort(key=lambda var: var.total_price)
    else:
        to_itins.sort(key=lambda var: var.duration)
        from_itins.sort(key=lambda var: var.duration)



    for i, itin in enumerate(to_itins):
        msg['to_itins'].append(itin.to_dict())

    for i, itin in enumerate(from_itins):
        msg['from_itins'].append(itin.to_dict())

    if len(to_itins) == 0 and len(from_itins) == 0:
        msg['msg'] = 'No itineraries were found!'
    elif len(to_itins) == 0:
        msg['msg'] = 'No to itineraries were found!'
    elif len(from_itins) == 0 and return_date is not None:
        msg['msg'] = 'No return itineraries were found!'
    else:
        msg['msg'] = 'Successfully found itineraries'

    return json.dumps(msg)

if __name__ == '__main__':
    app.run(port=5000,debug=True)


