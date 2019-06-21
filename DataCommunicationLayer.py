import psycopg2 as pg
from werkzeug.security import generate_password_hash
from User import User, salt

db_host = "localhost"
database = "test"
db_user = "postgres"
db_pwd = "airfare"

class DataCommunicationLayer:

    def __init__(self,logger):
        self._logger = logger
        self._db_conn = None

        try:
            self._db_conn = pg.connect(host = db_host,database = database,user=db_user,password=db_pwd)
            self._logger.info('Successfully connected to the Database!')
        except Exception as e:
            self._logger.info('Connecting to the Database Failed!')
            self._logger.info(e)
            Exception('Connecting to the Database Failed!')

    def register_user(self,email,password,name,home_airport = None):
        cursor = self._db_conn.cursor()
        success = True
        saltedhash = generate_password_hash(salt + password)
        try:
            values = cursor.mogrify("(%s,%s,%s)", (email,name,home_airport)).decode('utf-8')
            cursor.execute('insert into customer values ' + values)
            values = cursor.mogrify("(%s,%s)", (email, saltedhash)).decode('utf-8')
            cursor.execute('insert into registered_user values ' + values)
            self._db_conn.commit()
            self._logger.info('Successfully inserted %s into the Database.' % email)
        except Exception as e:
            self._logger.info(e)
            success = False
        finally:
            cursor.close()
            return success

    def get_user_from_db(self,id):
        cursor = self._db_conn.cursor()
        sql = 'select * from registered_user where email = %(user_id)s'
        cursor.execute(sql,{'user_id':id})
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        else:
            return User(id,rows[0][1])