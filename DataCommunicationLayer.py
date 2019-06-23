import psycopg2 as pg
from werkzeug.security import generate_password_hash
from User import User, salt

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


class Itinerary:
    def __init__(self,flight_no,code,dept_airport,arrival_airport,flight_date,dept_time,arrival_time,
                 first_class_capacity,economy_class_capacity):
        self.flight_no = flight_no
        self.code = code
        self.dept_airport = dept_airport
        self.arrival_airport = arrival_airport
        self.flight_date = flight_date
        self.dept_time = dept_time
        self.arrival_time = arrival_time
        self.first_class_capacity = first_class_capacity
        self.economy_class_capacity = economy_class_capacity


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

    def check_address(self,address_string):
        cursor = self._db_conn.cursor()
        sql = 'select * from Address where address = %(address)s'
        cursor.execute(sql, {'address': address_string})
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

    def searchFlight(self, dep_airport,des_airport,dep_flight_date):
        query = ""

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

    def is_address_assoc_with_cc(self,user_id,address_id):
        cursor = self._db_conn.cursor()
        sql = """
            select *
            from credit_card cc
            JOIN customer_credit_card ccc
	            ON cc.card_no = cc.card_no
            where address = %(address)s
            and email = %(email)s
        """
        try:
            cursor.execute(sql, {'address': address_id,'email': user_id})
            for row in cursor:
                return True
        except Exception as e:
            self._logger.error(e)
        finally:
            return False

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

            self._db_conn.commit()
        except Exception as e:
            self._logger.error(e)
            success = False
            msg = str(e)
        finally:
            return success,msg