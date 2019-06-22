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