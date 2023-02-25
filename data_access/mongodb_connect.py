import os,sys,time
from logger import logging
import pymongo
import pandas as pd
from src.utils.basicFunctions import check_file_exists
from dataIngestion.models import upload_Dataset

class MongoDBClient:
    
    client=None
    def __init__(self,key):
        try:
            if MongoDBClient.client is None:
                self.mongo_db_uri=key
                
            
            else:
                return "client is not none"

            logging.info("Mongodb Connection Established")
        except Exception as e:
            logging.error(f"Error with Mongodb Connection: {e} ")
    
    def connect_to_mongodb(self):
        try:
            conn_client=pymongo.MongoClient(self.mongo_db_uri)
            return conn_client
        except Exception as e:
            logging.error(f"Error:{e}")


    def check_conn(self,database_name,collection_name):
        try:
            client_conn= self.connect_to_mongodb()
            if database_name in (client_conn.list_database_names()):
                DataBase= client_conn[database_name]
                if collection_name in (DataBase.list_collection_names()):
                    self.close_connect_mongodb()
                    return "Sucessfully connected to mongo"
                else:
                    self.close_connect_mongodb()
                    return "No such collection: {} exists in mongodb".format(collection_name)
            else:
                self.close_connect_mongodb()
                return "No such database: {} exists in mongodb".format(database_name)
        except Exception as e:
            logging.error(f"Error:{e}")


    def close_connect_mongodb(self,conn_client):
        try:
            conn_client.close()
        except Exception as e:
            logging.error(f"Error:{e}")



    def send_dataframe_to_mongodb(self,database_name:str,collection_name,dataset_file:str):
        try:
            if dataset_file.endswith('.csv'):
                df=pd.read_csv(dataset_file,sep=',')
                
            elif dataset_file.endswith('.tsv'):
                df=pd.read_csv(dataset_file,sep="\t")

            elif (dataset_file.endswith('.xlsx')) or (dataset_file.endswith('.xls')):
                df=pd.read_excel(dataset_file)
            
            elif dataset_file.endswith('.json'):
                df = pd.read_json(dataset_file)

            else:
                return "given file format is not supported"
            
            DataFrame=df.to_dict('records')  # inserting our file into mongodb collections
            
            conn_client=self.connect_to_mongodb()
        
            if database_name is not None:
                Collection=conn_client[database_name][collection_name]

            else:
                Collection=conn_client.database[collection_name]

            start_time=time.time()
            Collection.insert_many(DataFrame)
            end_time=time.time()
            logging.info(f"Your data is sucessfully uploaded. Total time taken: {end_time-start_time} seconds.")

            status="Successful"
            self.close_connect_mongodb(conn_client)
            return status,Collection
        
        except Exception as e:
            return e,None

    def get_dataframe(self,collection_name):
        df=pd.DataFrame(list(collection_name.find())).drop(columns=['_id'],axis=1)
        return df

    def delete_collection_data(self, database_name:str,collection_name):
        """[summary]
        Delete Collection Data
        Args:
            collection_name ([type]): [description]
        """
        try:
            conn_client=self.connect_to_mongodb()
            start_time=time.time()
            collection = conn_client[database_name][collection_name]
            collection.delete_many({})
            end_time=time.time()
            logging.info(f"All records deleted. Total time taken: {end_time-start_time} seconds.")
        except Exception as e:
            logging.error(f"Error:{e}")

   
        
    def download_collection_data(self,database_name,project_id, file_type):
        try:
            Project_details= upload_Dataset.objects.get(id=project_id)
            urls=Project_details.file_upload.url
            urls=urls[1:]
            file_name=urls.split(".")[0].split("/")[-1]
            path = os.path.join(os.path.join('media', 'uploads'), f"{file_name}.{file_type}")
                    

            if check_file_exists(urls)[0]:
                print('Exists')
                logging.info("User File Exist!!")
                df = check_file_exists(urls)[1]
                try:
                    df.drop(columns=['_id'], inplace=True)
                except Exception as e:
                    logging.info(e)

            else:
                conn_client=self.connect_to_mongodb()
        
                

                start_time=time.time()
                collection = conn_client[database_name][project_id]
                df = pd.DataFrame(list(collection.find()))
                df.drop(columns=['_id'], inplace=True)
                end_time= time.time()
                logging.info(f"Downloded {project_id} collection data from database. Total time taken: {end_time - start_time} seconds.")

            if file_type == 'csv':
                df.to_csv(path, index=False)
            elif file_type == 'tsv':
                df.to_csv(path, sep='\t', index=False)
            elif file_type == 'json':
                df.to_json(path)
            elif file_type == 'xlsx':
                df.to_excel(path)
            download_status = 'Successful'
            return download_status, path

        except Exception as e:
            download_status = "Unsuccessful"
            logging.error(f"{download_status}--> Error:{e}")
            return download_status, path
