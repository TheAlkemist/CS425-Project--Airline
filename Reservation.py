import time
import datetime
import psycopg2
conn = psycopg2.connect("dbname='test' user='postgres' host='localhost' password='airfare'")
cursor = conn.cursor()

def customer_registration():
    print("Customer Registration")
    registered = False
    while not registered:
        print("Please enter your email, name and home airport when prompted")
        email = input("Enter Email: ")
        first_name = input("Enter first name: ")
        middle_name = input("Enter middle name: ")
        last_name = input("Enter last name: ")

        home = input("Enter your home airport: ")
        while home not in airports:
            print("Invalid Airport")
            home = input("Enter your home airport: ")
        registered = insert_customer("REG",email,first_name,middle_name,last_name, home)
    print("Thank you, Registration Has Been Completed")
    time.sleep(3)
    customer_login()

def customer_login():
    print( "Customer Login")
    user = False
    while not user:
        email = input("Enter Email: ")
        cursor.execute("SELECT * FROM customer WHERE email=%s",(email,))
        try:
            user = cursor.fetchall()[0]
        except:
             print(" Login Failed, Try Again")
             user = False
        if user:
            user = True
            print(" Login Successfull")
            print("Welcome" + user[1])
            menu(email)

def menu(user):
    user_menu="Please Select an Option"
    print(user_menu)
    while True:
        print(menu)
        selection=input("?")
        if selection == "1":
            address_modify(user)
        elif selection == "2":
            payment_modify(user)
        elif selection == "q":



def insert_customer(*args):
    cmd = "INSERT INTO Customer(Email, customer_first_name, customer_middle_name, customer_last_name, home_airport) VALUES (%s %s %s %s %s)"
    try:
        cursor.execute(cmd, (args[0], args[1], args[2], args[3], args[4]))
    except Exception as errormessage:
        print("Unable to register User")
        print(errormessage)
        return False
    return True

def insert_addr(*args):
    cmd = "INSERT INTO Address(Address, building_no, street, city, customer_state, country) VALUES (%s %s %s %s %s %s)"
    try:
        cursor.execute(cmd,(args[0],args[1],args[2],args[3],args[4],args[5]))
    except Exception as errormessage:
        print("Unable to update Address")
        print(errormessage)
        return False
    return True

def insert_pay(*args):
    cmd = "INSERT INTO Credit_Card(Card_no, address) VALUES (%s %s)"
    try:
        cursor.execute(cmd, (args[0], args[1]))
    except Exception as errormessage:
        print("Unable to update Payment Info")
        print(errormessage)
        return False
    return True

def insert_booking(*args):
    cmd = "INSERT INTO Booking(Booking_no, Email, Flight "


def del_addr(arg):
    cmd = "DELETE FROM Address WHERE address={}".format(arg)
    try:
        cursor.execute(cmd)
    except Exception as errormessage:
        print("Unable to delete Address")
        print(errormessage)

def del_pay(arg):
    cmd = "DELETE FROM Credit_Card WHERE card_no = %s"
    try:
        cursor.execute(cmd,(arg,))
    except Exception as errormessage:
        print("Unable to delete Payment Method")
        print(errormessage)

def del_booking(arg):
    cmd = "DELETE FROM Booking WHERE booking_no = %s"
    try:
        cursor.execute(cmd,(arg,))
    except Exception as errormessage:
        print("Unable to delete Booking")
        print(errormessage)

def address_modify(user):
    selection = input("Enter Selection: ")
    if selection.lower()=="I":
        street = input("Enter Street Name")
        city = input("Enter City")
        country = input("Enter Country Name")
        customer_state = input("Enter State")
        building_no = input("Enter Building Number")
        insert_addr("NULL", building_no, street, city, customer_state, country)

    elif selection.lower()=="D":
        try:
            cursor.execute("SELECT * FROM address WHERE user_='{}'".format(user[0]))
            addresses = cursor.fetchall()
            print("Please select the address to be removed\n")
            i = 0
            for addr in addresses:
        print("[{}]: {}, {}, {}, {}, {}".format(i, addr[1], addr[2], addr[3], addr[4], addr[5]))

def booking_modify(user):
    print("Your bookings are displayed below")
    cursor.execute("SELECT * FROM booking where user = %s",(user[0],))
    booking = cursor.fetchall()
    for booking in bookings:
        cursor.excecute("SELECT flight.flight_no, flight.code, flight.dept_airport, flight.arrival_airport, flight.flight_date, flight.dept_time, flight.arrival_time",(booking[0],))
        flights= cursor.fetchall()
        for flight in flights:
            print("\t" + str(flight[0]) +" " + str(flight[1]) + " on " + str(flight[2]))
            print("\t\tTakeoff at " + str(flight[5]) + " from " + flight[3])
            print("\t\tLanding at " + str(flight[6]) + " at " + flight[4])

def card_modify(user):
    cursor.excecute("SELECT card_no FROM Credit_Card WHERE user ")