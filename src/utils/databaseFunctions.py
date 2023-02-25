import pandas as pd
import sqlalchemy
import pymongo
import json
from textwrap import wrap
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import os
from logger import logging

class mysql_data_helper:
    def __init__(self, host, port, user, password, database):
        try:
            logging.info("MySQL constructor created in database helper!")
            self.host = host
            self.port = port
            self.user = user
            self.password = password
            self.connection = None
            self.database = database  # dialect+driver://username:password@host:port/database.
            self.engine = sqlalchemy.create_engine(f"""mysql+mysqlconnector://{self.user}:{self.password}@
                                                    {self.host}:{self.port}/{self.database}""")
        except Exception as e:
            logging.error(f"{e} occurred in MySQL constructor!")

    def connect_todb(self):  
        try:
            self.connection = self.engine.connect()
            logging.info("MySQL connection created in database helper!")
            return self.connection
        except Exception as e:
            
            logging.error(f"{e} occurred in MySQL connection!")

    def custom_query(self, query):
        try:
            conn = self.connect_todb()
            results = conn.execute(query).fetchall()
            logging.info(f"Query executed successfully!")
            return results
        except Exception as e:
              
            logging.error(f"{e} occurred in custom query!")
            
    def retrive_dataset_from_table(self, table_name, download_path):
        try:
            conn = self.connect_todb()
            data_query = f"select * from {table_name}"
            schema_query = f"describe {table_name}"
            data = conn.execute(data_query).fetchall()
            schema = conn.execute(schema_query).fetchall()
            if conn is not None:
                conn.close()
            logging.info(f"Data and schema retrived from {table_name} table!")
            column_names = []
            for row in schema:
                column_names.append(row[0])
            try:
                dataframe = pd.DataFrame(data, columns=column_names).drop(columns='index')
                dataframe.to_csv(download_path, index=False)
                logging.info(f"Dataframe created and saved in {download_path}!")
                return 'Successful'
            except Exception as e:
                logging.error(f"{e} occurred in creating dataframe!")
                dataframe = pd.DataFrame(data, columns=column_names)
                dataframe.to_csv(download_path, index=False)
                return 'Successful'

        except Exception as e:
            logging.error(f"{e} occurred in retrive_dataset_from_table!")

    def push_file_to_table(self, file, table_name):
        try:
            if file.endswith(".csv"):
                dataframe = pd.read_csv(file)
                logging.info(f"{file}.csv pushed to {table_name}!")
            elif file.endswith(".tsv"):
                dataframe = pd.read_csv(file, sep="\t")
                logging.info(f"{file}.tsv pushed to {table_name}!")
            elif file.endswith(".json"):
                dataframe = pd.read_json(file)
                logging.info(f"{file}.json pushed to {table_name}!")
            else:
                logging.error(f"{file} is not a valid file!")
                return f"{file} is not supported!"

            try:
                dataframe.to_sql(con=self.engine, name=table_name, if_exists='replace', chunksize=1000)
                logging.info(f"Dataframe pushed to {table_name} table!")
                return "Successful"

            except Exception as e:
                logging.error(f"{e} occurred in pushing dataframe to {table_name} table!")
                return "Unsuccessful"

        except Exception as e:
            logging.error(f"{e} occurred in push_file_to_table!")
            return "Unsuccessful"

    def check_connection(self, table_name):

        table_list = []
        try:
            conn = self.connect_todb()
            query = 'SHOW TABLES'
            data = conn.execute(query).fetchall()
            if conn is not None:
                conn.close()
            for i in data:
                for table in i:
                    table_list.append(table)
            if table_name in table_list:
                logging.info(f"{table_name} table exists!")
                return "Successful"
            else:
                logging.error(f"{table_name} table does not exist!")
                return "table does not exist!!"

        except Exception as e:
            if 'Unknown database' in e.__str__():
                logging.error(f"{self.database} database not found!")
                return f"{self.database} database not found!"
            elif 'Access denied' in e.__str__():
                logging.error(f"Access denied for {self.user} user!")
                return "Incorrect Mysql User or Password!!"
            elif "Can't connect" in e.__str__():
                logging.error(f"Can't connect to {self.host} host!")
                return "Incorrect Host Given"
            else:
                logging.error(f"{e} occurred in check_connection!")
                return "OOPS something went wrong!!"

    def __str__(self):
        logging.info("MySQL object created!")
        return "mysql dataset helper"


class cassandra_connector:
    """
    cassandra_connector class performs cassandra database operations,eg: connecting to database,
    creating table, inserting values into table, retriving dataset for allowed filetypes
    """

    def __init__(self, bundel_zip, client_id, client_secret, keyspace):
        try:
            self.cloud_config = {'secure_connect_bundle': bundel_zip}
            self.auth_provider = PlainTextAuthProvider(client_id, client_secret)
            self.cluster = Cluster(cloud=self.cloud_config, auth_provider=self.auth_provider)
            self.keyspace = keyspace
            logging.info("Cassandra constructor created in database helper!")
        except Exception as e:
            logging.error(f"{e} occurred in Cassandra constructor!")

    def connect_to_cluster(self):
        try:
            session = self.cluster.connect(self.keyspace)
            logging.info("Cassandra connection created in database helper!")
            return session
        except Exception as e:
            logging.error(f"{e} occurred in Cassandra connection!")

    def push_dataframe_to_table(self, dataframe, table_name):

        try:
            data = dataframe.to_json()
            data = wrap(data, 65000)

            create_query = f'create table {table_name}('
            logging.info(f"Query created for creating {table_name} table!")
            column_names = []

            for i in range(len(data)):  # creating create table query and collect column names
                if i == 0:
                    create_query += f'data{i * "1"} text primary key, '
                    column_names.append(f'data{i * "1"}')

                else:
                    create_query += f'd{i * "1"} text ,'
                    column_names.append(f'd{i * "1"}')

            create_query = create_query.strip(" ,") + ");"
            session = self.connect_to_cluster()
            session.execute(create_query, timeout=None)

            insert_query = f'insert into {table_name}({", ".join(column_names)}) values ({"? ," * len(column_names)}'.strip(", ") + ");"
            prepared_query = session.prepare(insert_query)
            session.execute(prepared_query, data, timeout=None)
            session.shutdown()
            logging.info(f"Dataframe pushed to {table_name} table!")
            logging.info("Cassandra session closed")
            return "Successful"

        except Exception as e:
            logging.error(f"{e} occurred in pushing dataframe to {table_name} table!")
            

    def custom_query(self, custom_query):
        try:
            session = self.cluster.connect(self.keyspace)
            data = session.execute(custom_query)
            logging.info(f"Custom query executed!")
            session.shutdown()
            print("Cassandra session closed")
            logging.info("Cassandra session closed")
            return data

        except Exception as e:
            
            logging.error(f"{e} occurred in custom_query!")

    def retrive_table(self, table_name, download_path):
        try:
            session = self.cluster.connect(self.keyspace)
            dataframe = pd.DataFrame(list(session.execute(f"select * from {table_name}")))
            logging.info(f"Dataframe created from {table_name} table!")
            session.shutdown()
            logging.info("Cassandra session closed")
            dataframe.to_csv(download_path, index=False)
            logging.info(f"Dataframe pushed to {download_path}!")
            return 'Successful'

        except Exception as e:
            
            logging.error(f"{e} occurred in retrive_table!")

    def retrive_uploded_dataset(self, table_name, download_path):
        try:
            session = self.cluster.connect(self.keyspace)
            data = session.execute("select * from neuro")
            dataset_string = ""
            for row in data:
                for chunks in row:
                    dataset_string += chunks
            dataset = json.loads(dataset_string)
            dataframe = pd.DataFrame(dataset)
            dataframe.to_csv(download_path, index=False)
            logging.info(f"Dataframe retrived from Cassandra DB!")
            session.shutdown()
            logging.info("Cassandra session closed")
            return 'Successful'

        except Exception as e:
            
            logging.error(f"{e} occurred in retrive_uploded_dataset!")

    def check_connection(self, table_name):
        table_list = []

        try:
            session = self.cluster.connect(self.keyspace)
            query = f"SELECT * FROM system_schema.tables WHERE keyspace_name = '{self.keyspace}';"
            data = session.execute(query)

            for table in data:
                table_list.append(table.table_name)
            if table_name in table_list:
                logging.info(f"{table_name} table exists in {self.keyspace} keyspace!")
                session.shutdown()
                return "Successful"
            else:
                session.shutdown()
                logging.error(f"{table_name} table not found in {self.keyspace} keyspace!")
                return "table does not exist!!"

        except Exception as e:
            if 'AuthenticationFailed' in e.__str__():
                logging.error(f"Incorrect Cassandra DB User or Password!!")
                return "Given client_id or client_secret is invalid"
            elif 'keyspace' in e.__str__():
                logging.error(f"Incorrect Cassandra DB keyspace!!")
                return f"Given {self.keyspace} keyspace does not exist!!"
            elif 'Unable to connect to any servers' in e.__str__():
                logging.error(f"Unable to connect to any servers!!")
                return "Unable to connect to any servers, please try again later!!"
            else:
                logging.error(f"{e} occurred in check_connection!")
                return "Provide valid bundel zip file!!"


class mongo_data_helper:

    def __init__(self, mongo_db_url):
        try:
            logging.info("Mongo constructor created in database helper!")
            self.mongo_db_uri = mongo_db_url
        except Exception as e:
            
            logging.error(f"{e} occurred in Mongo constructor!")
            
    def connect_to_mongo(self):
        try:
            client_cloud = pymongo.MongoClient(self.mongo_db_uri)
            return client_cloud
        except Exception as e:
            
            logging.error(f"{e} occurred in Mongo connection!")
            
    def close_connection(self, client_cloud):
        try:
            logging.info("Mongo connection closed!")
            client_cloud.close()
            print("Mongo db connection closed")
        except Exception as e:
            logging.error(f"{e} occurred in Mongo connection!")

    def retrive_dataset(self, database_name, collection_name, download_path):
        try:
            client_cloud = self.connect_to_mongo()
            database = client_cloud[database_name]
            collection = database[collection_name]
            dataframe = pd.DataFrame(list(collection.find())).drop(columns='_id')
            dataframe.to_csv(download_path, index=False)
            logging.info(f"Dataframe retrived from Mongo DB!")
            self.close_connection(client_cloud)
            logging.info("Mongo connection closed!")
            return "Successful"

        except Exception as e:
            logging.error(f"{e} occurred in retrive_dataset!")

    def push_dataset(self, database_name, collection_name, file):
        try:
            if file.endswith('.csv'):
                dataframe = pd.read_csv(file)
                logging.info(f"{file}.csv pushed to {collection_name} collection in {database_name} database!")
            elif file.endswith('.tsv'):
                logging.info(f"{file}.tsv pushed to {collection_name} collection in {database_name} database!")
                dataframe = pd.read_csv(file, sep='\t')
            elif file.endswith('.json'):
                dataframe = pd.read_json(file)
                logging.info(f"{file}.json pushed to {collection_name} collection in {database_name} database!")
            else:
                logging.error(f"{file} is not supported file format!")
                return "given file is not supported"

            data = dataframe.to_dict('record')

            client_cloud = self.connect_to_mongo()
            database = client_cloud[database_name]
            collection = database[collection_name]
            collection.delete_many({})
            logging.info(f"{collection_name} collection in {database_name} database deleted!")
            print(f"cleaned {collection_name} collection")
            collection.insert_many(data)
            logging.info(f"{collection_name} collection in {database_name} database inserted!")
            self.close_connection(client_cloud)
            logging.info("Mongo connection closed!")
            return 'Successful'

        except Exception as e:
            logging.error(f"{e} occurred in push_dataset!")

    def check_connection(self, database_name, collection_name):
        try:
            client_cloud = self.connect_to_mongo()
            DBlist = client_cloud.list_database_names()

            if database_name in DBlist:
                database = client_cloud[database_name]
                collection_list = database.list_collection_names()
                
                if collection_name in collection_list:
                    self.close_connection(client_cloud)
                    return "Successful"
                else:
                    self.close_connection(client_cloud)
                    return "collection does not exits!!"
            else:
                self.close_connection(client_cloud)
                return f"Given {database_name} database does not exist!!"

        except Exception as e:
            logging.error(f"{e} occurred in check_connection!")
            if "Authentication failed" in e.__str__():
                return "Provide valid Mongo DB URL"
            else:
                return "OOPS something went wrong!!"
              
