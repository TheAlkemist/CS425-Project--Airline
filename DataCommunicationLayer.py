import psycopg2 as pg
from werkzeug.security import generate_password_hash
from User import User, salt
from FlightSearch import Flight, Airport

db_host = "localhost"
database = "airfare"
db_user = "postgres"
db_pwd = "airfare"


class Address:
    def __init__(self,building_no,direction, street,city, state,country,zipcode):
        self.building_no = building_no
        self.direction = direction
        self.street = street
        self.city = city
        self.state = state
        self.country = country
        self.zipcode = zipcode

    def get_address_string(self):
        return '%s %s %s, %s, %s %s %s' % (str(self.building_no),self.direction,self.street,self.city,self.state,self.country,self.zipcode)

    def list(self):
        return [self.building_no,self.direction,self.street,self.city,self.state,self.country,self.zipcode]

    def dictionary(self):
        return {'address':self.get_address_string()
                   ,'building_no':self.building_no
                   ,'direction':self.direction
                   ,'street':self.street
                   ,'city':self.city
                   ,'state':self.state
                   ,'country':self.country
                    ,'zipcode':self.zipcode}






class CreditCard:
    def __init__(self,card_no,address, exp_date,type, name_on_card):
        self.card_no = card_no
        self.address = address
        self.exp_date = exp_date
        self.type = type
        self.name_on_card = name_on_card

    def dictionary(self):
        return {'card_no':self.card_no
                   ,'address':self.address
                   ,'exp_date':self.exp_date.strftime('%Y-%m-%d')
                   ,'type':self.type
                   ,'name_on_card':self.name_on_card}

class DataCommunicationLayer:

    def __init__(self,logger):
        self._logger = logger
        self._db_conn = None

        try:
            self._db_conn = pg.connect(host = db_host,database = database,user=db_user,password=db_pwd)
            self._logger.info('Successfully connected to the Database!')
        except Exception as e:
            self._logger.info('Connecting to the Database Failed!')
            self._logger.error(e)
            Exception('Connecting to the Database Failed!')

    def register_user(self,email,password,first_name,last_name,home_airport,address):

        cursor = self._db_conn.cursor()
        success = True
        saltedhash = generate_password_hash(salt + password)
        home_airport = None if home_airport == '' else home_airport
        try:

            values = cursor.mogrify("(%s,%s,%s,%s)", (email,first_name,last_name,home_airport)).decode('utf-8')
            cursor.execute('insert into customer values ' + values)
            values = cursor.mogrify("(%s,%s)", (email, saltedhash)).decode('utf-8')
            cursor.execute('insert into registered_user values ' + values)
            success = self.add_address(email,address)
            self._db_conn.commit()
            self._logger.info('Successfully inserted %s into the Database.' % email)
        except Exception as e:
            self._logger.error(e)
            self._db_conn.rollback()
            success = False
        finally:
            cursor.close()
            return success

    def add_address(self,email,address):
        success = True
        cursor = self._db_conn.cursor()
        try:
            assert isinstance(address,Address)
            if not self.check_address(address.get_address_string()):
                values = cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", (address.get_address_string(), address.direction, address.street, address.city,address.country,address.state,address.building_no,address.zipcode)).decode('utf-8')
                cursor.execute('insert into address values ' + values)
            values = cursor.mogrify("(%s,%s)", (email,address.get_address_string())).decode('utf-8')
            cursor.execute('insert into customer_address values ' + values)
            self._db_conn.commit()
            self._logger.info('Successfully inserted address %s for email %s into the Database.' % (address.get_address_string(),email))
        except Exception as e:
            self._logger.error(e)
            self._db_conn.rollback()
            success = False
        finally:
            cursor.close()
            return success

    def add_cc(self,email,credit_card):
        success = True
        cursor = self._db_conn.cursor()
        try:
            assert isinstance(credit_card,CreditCard)
            if not self.check_cc(credit_card.card_no):
                values = cursor.mogrify("(%s,%s,%s,%s,%s)", (credit_card.card_no, credit_card.address, credit_card.exp_date, credit_card.type,credit_card.name_on_card)).decode('utf-8')
                cursor.execute('insert into credit_card values ' + values)
            values = cursor.mogrify("(%s,%s)", (email,credit_card.card_no)).decode('utf-8')
            cursor.execute('insert into customer_credit_card values ' + values)
            self._db_conn.commit()
            self._logger.info('Successfully inserted credit_card %s for email %s into the Database.' % (credit_card.card_no,email))
        except Exception as e:
            self._logger.error(e)
            self._db_conn.rollback()
            success = False
        finally:
            cursor.close()
            return success

    def check_address(self,address_string):
        cursor = self._db_conn.cursor()
        sql = 'select * from Address where address = %(address)s'
        cursor.execute(sql, {'address': address_string})
        rows = cursor.fetchall()
        if len(rows) == 0:
            return False
        else:
            return True

    def check_cc(self,card_no):
        cursor = self._db_conn.cursor()
        sql = 'select * from credit_card where card_no = %(card_no)s'
        cursor.execute(sql, {'card_no': card_no})
        rows = cursor.fetchall()
        if len(rows) == 0:
            return False
        else:
            return True

    def get_user_from_db(self,id):
        cursor = self._db_conn.cursor()
        sql = 'select * from registered_user where email = %(user_id)s'
        cursor.execute(sql,{'user_id':id})
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        else:
            return User(id,rows[0][1])

    def search_flight(self, dep_airport,dep_flight_date,des_airport,connections = None ,max_time = None, price = None):
        cursor = self._db_conn.cursor()
        query = """WITH RECURSIVE ITINERARY(flight_code,dep,dest,connects,price,flight_time,arrival) AS (
                   SELECT flight_date::text || code || flight_no::text AS flight_code,
                   dept_airport,
                   arrival_airport,
                   0 AS connects,
                   {} AS price,
                   (arrival_time-dept_time) AS flight_time,
                   arrival_time
                   FROM flight f0
                   WHERE dept_airport = %s AND flight_date = %s
                   UNION ALL
                   SELECT con.flight_code || '/' || f1.flight_date::text || f1.code || f1.flight_number::text  as flight
                   ,con.dep
                   ,f1.arrival_airport
                   ,con.connects + 1 AS connects
                   ,con.price + f1.{} AS price
                   ,(con.flight_time + f1.arrival_time - f1.dept_time)) AS total_flight_time
                   ,f1.arrival_time
                   FROM ITINERARY con
                    JOIN flight f1
                    on f1.dept_airport = con.dest AND flight_date = %s
                    AND f1.dept_time > con.arrival
                    )
                    SELECT *
                    FROM connections
                    WHERE dest = %s"""
        try:
            cursor.execute(query, (dep_airport, dep_flight_date, dep_flight_date,des_airport, connections,max_time,price ))
            flights = cursor.fetchall()
            flights = [x for x in flights if x[3] <= float(connections) and float(x[4]) <= float(price) and (x[5].seconds <= float(max_time)*3600)]

        except Exception as error:
            self._logger.error(error)

        if len(flights) == 0:
            self._logger.info("No flights found for given parameters.")
            return False

        self._logger.info("""\nDisplaying flight options in the following format:
        [i]: <# of connections>, $<airfare>, <total airtime> hrs 
        """)

        i, j = 0, 0
        for itin in flights:
            self._logger.info("        [{}]: {}, ${}, {:.3g} hrs".format(i, itin[3], float(itin[4]), (itin[5].seconds)/3600))
            i +=1
        return True

    def get_addresses_for_user(self,user_id):
        cursor = self._db_conn.cursor()
        sql = """select *
                from address ad
                JOIN customer_address ca
                    ON ad.address = ca.address
                where ca.email = %(user_id)s"""
        addresses = []
        try:
            cursor.execute(sql, {'user_id': user_id})
            for row in cursor:
                building_no = row[6]
                direction = row[1]
                street = row[2]
                city = row[3]
                state = row[5]
                country = row[4]
                zipcode = row[7]


                address = Address(building_no,direction, street,city, state,country,zipcode)
                addresses.append(address)
        except Exception as e:
            self._logger.error(e)
        finally:
            return addresses

    def get_credit_cards_for_user(self,user_id):
        cursor = self._db_conn.cursor()
        sql = """select *
                from credit_card cc
                JOIN customer_credit_card ccc
                    ON cc.card_no = ccc.card_no
                where ccc.email = %(user_id)s"""
        cards = []
        try:
            cursor.execute(sql, {'user_id': user_id})
            for row in cursor:
                card_no = row[6]
                address = row[1]
                exp_date = row[2]
                type = row[3]
                name_on_card = row[5]

                card = CreditCard(card_no,address, exp_date,type, name_on_card)
                cards.append(card)
        except Exception as e:
            self._logger.error(e)
        finally:
            return cards


    def is_address_assoc_with_cc(self,user_id,address_id):
        tmp = False
        cursor = self._db_conn.cursor()
        sql = """
            select *
            from credit_card cc
            JOIN customer_credit_card ccc
	            ON cc.card_no = ccc.card_no
            where address = %(address)s
            and email = %(email)s
        """
        print(cursor.mogrify(sql, {'address': address_id,'email': user_id}))
        try:
            cursor.execute(sql, {'address': address_id,'email': user_id})
            for row in cursor:
                tmp = True
        except Exception as e:
            self._logger.error(e)
        finally:
            return tmp

    def is_address_assoc_with_customer(self, address_id):
        tmp = False
        cursor = self._db_conn.cursor()
        sql = """
            select *
            from customer_address ad
            where address = %(address)s

        """
        try:
            cursor.execute(sql, {'address': address_id})
            for row in cursor:
                tmp = True
        except Exception as e:
            self._logger.error(e)
        finally:
            return tmp

    def is_cc_assoc_with_customer(self, card_no):
        tmp = False
        cursor = self._db_conn.cursor()
        sql = """
            select *
            from customer_credit_card ad
            where card_no = %(card_no)s

        """
        try:
            cursor.execute(sql, {'card_no': card_no})
            for row in cursor:
                tmp = True
        except Exception as e:
            self._logger.error(e)
        finally:
            return tmp

    def is_customers_only_address(self,user_id,address_id):
        cursor = self._db_conn.cursor()
        tmp = True
        sql = """
                    select *
                    from customer_address ad
                    where address != %(address)s
                    and email = %(email)s
                """

        try:
            cursor.execute(sql, {'address': address_id, 'email': user_id})
            for row in cursor:
                tmp = False
        except Exception as e:
            self._logger.error(e)
        finally:
            return tmp

    def remove_address(self,user_id,address_id):
        success = True
        msg = "Success"
        cursor = self._db_conn.cursor()

        if self.is_address_assoc_with_cc(user_id,address_id):
            return False,'Cannot remove a billing address!'

        if self.is_customers_only_address(user_id,address_id):
            return False, 'Customer must have at least one address!'

        sql1 = """delete from customer_address
                where address = %(address)s
                    and email = %(email)s"""

        sql2 = """delete from address
                        where address = %(address)s"""


        try:
            cursor.execute(sql1, {'email': user_id,'address': address_id})
            if not self.is_address_assoc_with_customer(address_id):
                cursor.execute(sql2, { 'address': address_id})
            self._db_conn.commit()
        except Exception as e:
            self._logger.error(e)
            msg = str(e)
            success = False
        finally:
            return success,msg


    def remove_cc(self,user_id,card_no):
        success = True
        msg = "Success"
        cursor = self._db_conn.cursor()

        sql1 = """delete from customer_credit_card
                where card_no = %(card_no)s
                    and email = %(email)s"""

        sql2 = """delete from credit_card
                        where card_no = %(card_no)s"""


        try:
            cursor.execute(sql1, {'email': user_id,'card_no': card_no})
            if not self.is_cc_assoc_with_customer(card_no):
                cursor.execute(sql2, { 'card_no': card_no})
            self._db_conn.commit()
        except Exception as e:
            self._logger.error(e)
            msg = str(e)
            success = False
        finally:
            return success,msg

    def address_exists(self,address_id):
        cursor = self._db_conn.cursor()
        sql = """
                            select *
                            from address ad
                            where address = %(address)s
                        """
        try:
            cursor.execute(sql, {'address': address_id})
            for row in cursor:
                return True
        except Exception as e:
            self._logger.error(e)
        finally:
            return False


    def modify_address(self,user_id,address,old_address_id):
        cursor = self._db_conn.cursor()
        success = True
        msg = "Success"


        sql2 = """delete from address
                                where address = %(address)s"""

        try:
            if not self.address_exists(address.get_address_string()):
                self.add_address(user_id,address)


            self.remove_address(user_id,old_address_id)
            if not self.is_address_assoc_with_customer(old_address_id):
                cursor.execute(sql2, { 'address': old_address_id})
            self.update_cards(user_id,old_address_id,address.get_address_string())
            self._db_conn.commit()
        except Exception as e:
            self._logger.error(e)
            success = False
            msg = str(e)
        finally:
            return success,msg

    def update_cards(self,user_id,old_address_id,new_address_id):
        cursor = self._db_conn.cursor()
        success = True
        msg = "Success"

        sql = """update credit_card
                            set address = %(new_address_id)s
                            where card_no in (select card_no from customer_credit_card where email = %(user_id)s
                            and address = %(old_address_id)s"""

        try:
            cursor.execute(sql, {'old_address_id': old_address_id,'user_id': user_id, 'new_address': new_address_id})

            self._db_conn.commit()
        except Exception as e:
            self._logger.error(e)
            success = False
            msg = str(e)
        finally:
            return success, msg

    def modify_credit_card(self,card_no,new_address):
        cursor = self._db_conn.cursor()
        success = True
        msg = "Success"

        sql = """update credit_card
                    set address = %(new_address)s

                    where card_no = %(card_no)s
                    """

        try:
            cursor.execute(sql, {'card_no': card_no,'new_address':new_address})

            self._db_conn.commit()
        except Exception as e:
            self._logger.error(e)
            success = False
            msg = str(e)
        finally:
            return success,msg

    def get_all_flights(self,flight_class,flight_date):
        sql = """
            select flight_no,code,dept_airport,arrival_airport,flight_date,dept_time,arrival_time,price
            from flights f
                JOIN price pr on f.flight_no = pr.flight_no
            where
            pr.flight_class = %(flight_class)s
            and pr.flight_date >= %(flight_date)s


        """
        cursor = self._db_conn.cursor()
        flights = []
        try:
            cursor.execute(sql, {'flight_class': flight_class,'flight_date':flight_date})
            for row in cursor:
                flight_no = row[0]
                code = row[1]
                dept_airport = row[2]
                arrival_airport = row[3]
                dept_time = row[5]
                arrival_time = row[6]
                price = row[7]
                flight = Flight(flight_no,code,dept_airport,arrival_airport,dept_time,arrival_time,price)
                flights.append(flight)

        except Exception as e:
            self._logger.error(e)
        finally:
            return flights

    def get_network_graph(self,flight_class,flight_date):
        flights = self.get_all_flights(flight_class,flight_date)
        network = {}

        for flight in flights:
            if flight.frm not in network:
                airport = Airport(flight.frm)
                network[flight.frm] = airport
            if flight.to not in network:
                airport = Airport(flight.to)
                network[flight.to] = airport
            network[flight.frm].add_flight(flight)

        return network
