import boto3
import pandas as pd
import os
from google.cloud import storage
from azure.storage.blob import BlobClient
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobServiceClient
from logger import logging

class aws_s3_helper:
    def __init__(self, region_name, aws_access_key_id, aws_secret_access_key):
        try:
            logging.info("Constructor created in Cloud Helper!")
            self.region_name = region_name
            self.aws_access_key_id = aws_access_key_id
            self.aws_secret_access_key = aws_secret_access_key
            self.s3 = boto3.resource(service_name='s3',
                                     region_name=self.region_name,
                                     aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key)
        except Exception as e:
            logging.error(f'{e} occurred during constructor creation in Cloud Helper!')

    def check_connection(self, bucket_name, file_name):
        bucket_list = []
        file_list = []
        try:
            for bucket in self.s3.buckets.all():
                bucket_list.append(bucket.name)
            if bucket_name in bucket_list:
                for obj in self.s3.Bucket(bucket_name).objects.all():
                    file_list.append(obj.key)
                if file_name in file_list:
                    return "Successful"
                else:
                    return "File does not exist!!"
            else:
                logging.info("S3 Bucket not found!")
                return "Bucket does not exist!!"

        except Exception as e:
            logging.error(f'{e} occurred in check connection to S3 bucket!')
            if 'InvalidAccessKeyId' in e.__str__():
                return 'aws access key id is not valid!!'
            elif 'SignatureDoesNotMatch' in e.__str__():
                return 'aws secret access key is not valid!!'
            elif 'endpoint' in e.__str__():
                return 'Given region is not valid!!'
            elif 'Not Found' in e.__str__():
                return 'Given bucket or file is not valid'
            else:
                return 'oops something went wrong!!'

    def check_available_buckets(self):
        bucket_list = []
        try:
            for bucket in self.s3.buckets.all():
                bucket_list.append(bucket.name)
            logging.info(f"Available buckets in S3 are {bucket_list}")
            return bucket_list

        except Exception as e:
            logging.error(f'{e} occurred in check available buckets in S3!')
            return False

    def show_files_in_bucket(self, bucket_name):
        file_list = []
        try:
            for obj in self.s3.Bucket(bucket_name).objects.all():
                file_list.append(obj.key)
            logging.info(f"Available files in S3 bucket {bucket_name} are {file_list}")
            return file_list
        except Exception as e:
            logging.error(f'{e} occurred in show files in S3 bucket!')
            return False

    def push_file_to_s3(self, bucket, file, user_project_name):
        try:
            self.s3.Bucket(bucket).upload_file(Filename=file, Key=user_project_name)
            print(f"{user_project_name} uploaded successfully to {bucket}")
            return 'Successful'
        except Exception as e:
            logging.error(f'{e} occurred in push file to S3 bucket!')
        logging.info(f"{file} pushed successfully to {bucket}")
        return f"{file} uploaded successfully to {bucket}"

    def read_file_from_s3(self, bucket, file):
        dataframe = None
        try:
            if file.endswith('.csv'):
                obj = self.s3.Bucket(bucket).Object(file).get()
                dataframe = pd.read_csv(obj['Body'], index_col=0)
                print(obj)
            elif file.endswith('.tsv'):
                obj = self.s3.Bucket(bucket).Object(file).get()
                dataframe = pd.read_tsv(obj['Body'], index_col=0)
            elif file.endswith('.json'):
                obj = self.s3.Bucket(bucket).Object(file).get()
                dataframe = pd.read_json(obj['Body'], index_col=0)
            else:
                pass
            logging.info(f"{file} read successfully from {bucket}")
            return dataframe
        except Exception as e:
            logging.error(f'{e} occurred in read file from S3 bucket!')
            
    def download_file_from_s3(self, bucket, file, download_filepath):
        try:
            self.s3.Bucket(bucket).download_file(Filename=download_filepath, Key=file)
            logging.info(f"{file} downloaded successfully to {download_filepath}")
            return 'Successful'

        except Exception as e:
            logging.error(f'{e} occurred in download file from S3 bucket!')


class gcp_browser_storage:
    def __init__(self, credentials_file):
        try:
            self.storage_client = storage.Client.from_service_account_json(credentials_file)
            logging.info("Constructor created in GCP Cloud Helper!")
        except Exception as e:
            logging.error(f'{e} occurred during constructor creation in GCP Cloud Helper!')
            return 'Provide proper credentials file in json'

    # create a new bucket
    def create_bucket(self, bucket_name, project, storage_class, location):
        try:
            bucket = self.storage_client.bucket(bucket_name)
            bucket.storage_class = storage_class  # Archive | Nearline | Standard | Coldline
            bucket.location = location  # Taiwan
            bucket = self.storage_client.create_bucket(bucket)  # returns Bucket object
            logging.info(f"{bucket_name} created in GCP Cloud!")

        except Exception as e:
            logging.error(f'{e} occurred in create bucket in GCP Cloud!')

    def list_buckets(self):
        bucket_list = []
        try:
            for bucket in self.storage_client.list_buckets():
                bucket_list.append(bucket.name)
            logging.info(f"Available buckets in GCP are {bucket_list}")
            return bucket_list

        except Exception as e:
            logging.error(f'{e} occurred in list buckets in GCP!')
            return False
        
    def list_file_in_buckets(self, bucket_name):
        file_list = []
        try:
            for file in self.storage_client.list_blobs(bucket_name):
                file_list.append(file.name)
            logging.info(f"Available files in GCP bucket {bucket_name} are {file_list}")
            return file_list

        except Exception as e:
            logging.error(f'{e} occurred in list files in GCP bucket!')
            return False

    def upload_to_bucket(self, blob_name, file_path, bucket_name):
        """
            Upload file to a bucket
            : blob_name  (str) - object name
            : file_path (str)
            : bucket_name (str)
        """
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            print(f"{blob_name} was uploaded to {bucket_name}")
            return 'Successful'

        except Exception as e:
            print(f"{blob_name} was not uploaded to {bucket_name}")
            print(e)

    def download_file_from_bucket(self, blob_name, file_path, bucket_name):

        """
            download file from bucket
            : blob_name  (str) - object name
            : file_path (str)
            : bucket_name (str)
        """

        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            blob = bucket.blob(blob_name)
            with open(file_path, 'wb') as f:
                self.storage_client.download_blob_to_file(blob, f)
            logging.info(f"{blob_name} downloaded successfully to {file_path}")
            return 'Successful'

        except Exception as e:
            logging.error(f'{e} occurred in download file from bucket in GCP!')

    def check_connection(self, bucket_name, file_name):
        bucket_list = []
        file_list = []

        try:
            for bucket in self.storage_client.list_buckets():
                bucket_list.append(bucket.name)
            print(bucket_list, bucket_name)
            if bucket_name in bucket_list:
                for file in self.storage_client.list_blobs(bucket_name):
                    file_list.append(file.name)
                if file_name in file_list:
                    logging.info(f"{file_name} found in {bucket_name}!")
                    return 'Successful'
                else:
                    logging.info(f'The {file_name} does not exist {bucket_name} bucket!')
                    return 'File does not exist!!'
            else:
                return f'bucket:{bucket_name} does not exist!'
                logging.info(f'The {bucket_name} bucket does not exist!')

        except Exception as e:
            logging.error(f'{e} occurred in check connection in GCP!')


class azure_data_helper:
    def __init__(self, connection_string):
        try:
            self.connection_string = connection_string
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        except Exception as e:
            print(e)

    def create_container(self, container_name):
        try:
            self.blob_service_client.create_container(container_name)
            logging.info(f"{container_name} created in Azure!")
            print(f"{container_name} container created!!")
            return 'Successful'

        except Exception as e:
            logging.error(f'{e} occurred in create container in Azure!')
            if 'Server failed to authenticate' or 'blank or malformed' in e.__str__():
                logging.error('Provide valid azure connection string')
                return 'Provide valid azure connection string'
            else:
                logging.error('OOPS something went wrong!!')
                return 'OOPS something went wrong!!'

    def delete_container(self, container_name):
        try:
            self.blob_service_client.delete_container(container_name)
            logging.info(f"{container_name} deleted in Azure!")
            print(f"{container_name} container deleted!!")
            return 'Successful'

        except Exception as e:
            logging.error(f'{e} occurred in delete container in Azure!')
            if 'Server failed to authenticate' or 'blank or malformed' in e.__str__():
                logging.error('Provide valid azure connection string')
                return 'Provide valid azure connection string'
            else:
                logging.error('OOPS something went wrong!!')
                return 'OOPS something went wrong!!'

    def upload_file(self, file_path, container_name, user_file_name):
        try:
            blob = BlobClient.from_connection_string(conn_str=self.connection_string, container_name=container_name,
                                                     blob_name=user_file_name)
            with open(file_path, "rb") as data:
                blob.upload_blob(data)
            logging.info(f"{user_file_name} uploaded successfully to {container_name}")
            print(f"{user_file_name} is uploded to {container_name} container")
            return 'Successful'

        except Exception as e:
            if 'Server failed to authenticate' or 'blank or malformed' in e.__str__():
                logging.error('Provide valid azure connection string')
                return 'Provide valid azure connection string'
            else:
                logging.error('OOPS something went wrong!!')
                return 'OOPS something went wrong!!'

    def download_file(self, container_name, file_name, download_file_path):
        try:
            blob = BlobClient.from_connection_string(conn_str=self.connection_string, container_name=container_name,
                                                     blob_name=file_name)
            with open(download_file_path, "wb") as my_blob:
                blob_data = blob.download_blob()
                blob_data.readinto(my_blob)
            logging.info(f"{file_name} downloaded successfully to {download_file_path}")
            print(f"{file_name} downloaded from {container_name} container to {download_file_path}")
            return 'Successful'

        except Exception as e:
            if 'Server failed to authenticate' or 'blank or malformed' in e.__str__():
                logging.error('Provide valid azure connection string')
                return 'Provide valid azure connection string'
            else:
                logging.error('OOPS something went wrong!!')
                return 'OOPS something went wrong!!'

    def list_containers(self):
        container_list = []
        try:
            for container in self.blob_service_client.list_containers():
                container_list.append(container.name)
            logging.info(f"{container_list} listed in Azure!")
            return container_list

        except Exception as e:
            if 'Server failed to authenticate' or 'blank or malformed' in e.__str__():
                logging.error('Provide valid azure connection string')
                return 'Provide valid azure connection string'
            else:
                logging.error('OOPS something went wrong!!')
                return 'OOPS something went wrong!!'

    def list_blobs(self, container_name):
        my_blob_list = []
        try:
            container = ContainerClient.from_connection_string(conn_str=self.connection_string,
                                                               container_name=container_name)
            blob_list = container.list_blobs()
            for blob in blob_list:
                my_blob_list.append(blob.name)
            logging.info(f"{my_blob_list} listed in Azure!")
            return my_blob_list

        except Exception as e:
            if 'Server failed to authenticate' or 'blank or malformed' in e.__str__():
                logging.error('Provide valid azure connection string')
                return 'Provide valid azure connection string'
            else:
                logging.error('OOPS something went wrong!!')
                return 'OOPS something went wrong!!'

    def check_connection(self, container_name, file_name):
        try:
            containers = self.list_containers()

            if type(containers) != list:
                return containers
            elif container_name in containers:
                blobs = self.list_blobs(container_name)
                if file_name in blobs:
                    logging.info(f"{file_name} found in {container_name}!")
                    return 'Successful'
                else:
                    logging.info(f"{file_name} does not exist in {container_name}!")
                    return "File does not exist!!"
            else:
                logging.info(f"{container_name} does not exist in Azure!")
                return f"{container_name} container does not exist!!"

        except Exception as e:
            if 'Server failed to authenticate' or 'blank or malformed' in e.__str__():
                logging.error('Provide valid azure connection string')
                return 'Provide valid azure connection string'
            else:
                logging.error('OOPS something went wrong!!')
                return 'OOPS something went wrong!!'