import mysql.connector as connector
from logger import logging

class MySql:
    conn_obj=None
    def __init__(self,host,port,user,password,database):
        self.host=host
        self.port=port
        self.user=user
        self.password=password
        self.database=database
        self.IsConnected=False
        self.connection=None

    def connect_database(self):
        self.connection=connector.connect(host=self.host, port=self.port,user=self.user, password=self.password, database=self.database,ssl_ca="DigiCertGlobalRootCA.crt.pem",ssl_disabled=False)
        self.IsConnected=True
        return self.connection

    def close(self,conn,cursor):
        if conn is not None:
            conn.close()
        if cursor is not None:
            cursor.close()

    def fetch_all(self,query):
        cursor=None
        conn=None
        try:
            conn= self.connect_database()
            cursor=conn.cursor()
            cursor.execute(query)
            data=cursor.fetchall()
            return data
        except connector.Error as e:
            logging.info(f"Error occured: {e}")

     
    def fetch_one(self,query,*args):
        cursor=None
        conn=None
        try:
            conn= self.connect_database()
            cursor=conn.cursor()
            cursor.execute(query,*args)
            data=cursor.fetchone()
            return data
        except connector.Error as e:
            logging.info(f"Error occured: {e}")


    def delete_records(self,query):
        cursor=None
        conn=None
        try:
            conn= self.connect_database()
            cursor=conn.cursor()
            cursor.execute(query)
            rowcount=cursor.rowcount
            conn.commit()
            self.close(conn,cursor)
            return rowcount
        except connector.Error as e:
            logging.info(f"Error occured: {e}")




    def update_records(self, query):
        conn = None
        cursor = None
        try:
            conn= self.connect_database()
            cursor = conn.cursor()
            cursor.execute(query)
            rowcount = cursor.rowcount
            return rowcount

        except connector.Error as e:
            logging.error("Error: {}".format(e))

        finally:
            conn.commit()
            self.close(conn, cursor)


    def insert_records(self,query):
        cursor=None
        conn=None
        try:
            conn= self.connect_database()
            cursor=conn.cursor()
            cursor.execute(query)
            rowcount=cursor.rowcount
            conn.commit()
            return rowcount
        except connector.Error as e:
            logging.info(f"Error occured: {e}")


        finally:
            self.close(conn, cursor)
