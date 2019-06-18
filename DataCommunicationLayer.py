import psycopg2 as pg



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

    def register_user(self,email,name,home_airport = None):
        cursor = self._db_conn.cursor()
        try:
            values = cursor.mogrify('(%s,%s,%s)'.format(email,name,home_airport))
            cursor.execute('insert into customer values ' + values)
            self._db_conn.commit()
            self._logger.info('Successfully inserted %s into the Database.' % email)
        except Exception as e:
            self._logger.info(e)
        finally:
            cursor.close()