import pyodbc
import traceback

class DataRetrievalDB():

    def __init__(self, request):
        self.req_obj = request  # reference to the current request object
        self.error = self.req_obj.error
        self.logger = self.req_obj.logger

        self.conf_process_entity = self.req_obj.conf_process_entity
        self.conf_main = self.req_obj.conf_main

        self.s_conn = ''
        self.conn = None

        self.init_specific_settings()

    def open_connection(self, conn_str = None):
        self.logger.info('Attempting to open connection to Metadata DB.')
        try:
            if conn_str:
                # overwrite the connection string with the one provided in the parameter, if present
                self.s_conn = conn_str
            self.conn = pyodbc.connect(self.s_conn, autocommit=True)
            self.logger.info('Successfully established the database connection.')
        except Exception as ex:
            # report unexpected error during openning DB connection
            _str = 'Unexpected Error "{}" occurred during an attempt to open connecton to database ({})\n{} ' \
                .format(ex, self.s_conn, traceback.format_exc())
            self.logger.error(_str)
            self.error.add_error(_str)

    def exec_sql_procedure_with_output(self, str_proc):
        rs_out = None
        str_error = ''

        self.logger.info('SQL Procedure call = {}'.format(str_proc))

        try:
            if not self.conn:
                # if connection was not set yet, open it
                self.open_connection()
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(str_proc)
                # returned recordsets
                rs_out = []
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))
                rs_out.extend(results)

        except Exception as ex:
            # report an error if DB call has failed.
            str_error = 'Error "{}" occurred while retrieving data from the database; ' \
                   'used SQL script "{}". Here is the traceback: \n{} '.format(
                ex, str_proc, traceback.format_exc())
            self.error.add_error(str_error)
            self.logger.error(str_error)

        return rs_out, str_error

