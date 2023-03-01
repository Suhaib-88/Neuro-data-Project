from django.shortcuts import render,redirect
from django.views import View
from dataIngestion.models import upload_Dataset
from data_access.mongodb_connect import MongoDBClient
from data_access.mysql_connect import MySql
from constants.database import DATABASE_NAME
from src.utils.basicFunctions import read_configure_file, delete_temporary_file, check_file_exists
from FeatureEngineering.functions_FE.fe_operations import FE
# from .forms import *
from .models import export_Data,exportSources
from django.http import HttpResponse
from django.contrib import messages
import pandas as pd
from src.utils.cloudFunctions import aws_s3_helper,gcp_browser_storage, azure_data_helper
from src.utils.databaseFunctions import mysql_data_helper, mongo_data_helper
from src.utils.databaseFunctions import cassandra_connector
from src.utils.basicFunctions import handle_uploaded_file, update_data,absoluteFilePaths
from src.utils.projectReports import ProjectReports
from src.utils.plotlyFunctions import Plotly_agent
from src.constants.const import PROJECT_ACTIONS

import time
import os,glob
import numpy as np
from logger import logging
from logger import logging
import pathlib
import io
import zipfile
import ast

config_args= read_configure_file("config.yaml")
mongodb = MongoDBClient(key=config_args['confidential_info']['mongo_db_key'])
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)

class Project(View):
    """
    This class provides the post() and fetch() methods to handle post requests and data fetching respectively.
    """

    def post(self, request, id):
        """
        This method handles the post request to the specified project with the given id.

        It inserts the project id to get_project_id sql table. Then it inserts the project information and initializes
        the project action report using the "ProjectReports" class. 

        Next, it queries the project module URL from the "projects_info" table in the database. If it exists, it redirects
        to the URL. If it doesn't exist, it renders the "dataProcessing/home.html" template with the project details in
        the context.

        Args:
        - request: the HTTP request
        - id: the id of the project to be processed

        Returns:
        - A redirect to the project module URL, if it exists
        - A render of the "dataProcessing/home.html" template with the project details in the context
        """
        # Get the project details based on the given id
        Project_details = upload_Dataset.objects.get(id=id)

        # Insert the project information and initialize the project action report
        ProjectReports.insert_project_info(
            Project_details.id,
            Project_details.problem_statement_type,
            Project_details.problem_statement_name,
            1
        )

        
        # insert the project id to an sql table "get_project_id"
        sql_obj.insert_records(f"""INSERT INTO get_project_id (project_id) VALUES ({Project_details.id});""")


        ProjectReports.insert_project_action_report(Project_details.id,PROJECT_ACTIONS.get("INITIALIZATION"))

        # Query the project module URL from the "projects_info" table
        query = sql_obj.fetch_one(f"SELECT ModuleUrl FROM projects_info WHERE Projectid={id}")[0]

        # If the project module URL exists, redirect to it
        if query != "None":
            return redirect(query)

        # If the project module URL doesn't exist, render the "dataProcessing/home.html" template with the project details
        return render(request, 'dataProcessing/home.html', context={"Projects": Project_details})

    def fetch(self,id):
        """
        This method fetches the data of the specified project with the given id.

        It tries to get the project details based on the given id. If the project data is stored in a file from resources,
        it sends the data to the MongoDB database and returns the data as a dataframe. If the project data is stored as a
        file upload, it sends the file to the MongoDB database and returns the data as a dataframe. If the project doesn't
        exist, it returns a message "Does not exists".

        Args:
        - id: the id of the project to be fetched

        Returns:
        - The data of the project as a dataframe, if it exists
        - The status of the data fetching process (e.g. "Successful", "Error")
        - A message "Does not exists" if the file url is not present. 
        """
        try:
            # Get the project details from the upload_Dataset model
            Project_details = upload_Dataset.objects.get(id=int(id))

            # If the project data is stored as a file upload
            if Project_details.file_from_resources is None:
                # Get the URL of the project data
                self.url = Project_details.file_upload.url
                full_path=os.path.join(next(absoluteFilePaths('media')),'uploads',os.path.basename(self.url))
                # Connect to MongoDB
                self.mongodb = MongoDBClient(key=config_args['confidential_info']['mongo_db_key'])
                self.client = self.mongodb.connect_to_mongodb()

                # Delete existing data for the project in the MongoDB collection
                self.mongodb.delete_collection_data(DATABASE_NAME, str(id))

                # Send the data to the MongoDB collection and get the status of the operation
                status,self.Collection=self.mongodb.send_dataframe_to_mongodb(DATABASE_NAME,str(id),str(full_path))
                
                # If the data was sent successfully, get the data as a dataframe and return it
                if status=="Successful":
                    self.df=self.mongodb.get_dataframe(self.Collection)        
                    return self.df
                else:
                    # If there was an error, return the status
                    return status
            
            # Check if the project data is stored in a file from resources
            if Project_details.file_from_resources is not None:
                # Get the URL of the project data
                self.url = Project_details.file_from_resources
                full_path=os.path.join(next(absoluteFilePaths('media')),os.path.basename(self.url))
                
                # Connect to MongoDB
                self.mongodb = MongoDBClient(key=config_args['confidential_info']['mongo_db_key'])
                self.client = self.mongodb.connect_to_mongodb()

                # Delete existing data for the project in the MongoDB collection
                self.mongodb.delete_collection_data(DATABASE_NAME, str(id))

                # Send the data to the MongoDB collection and get the status of the operation
                status, self.Collection = self.mongodb.send_dataframe_to_mongodb(DATABASE_NAME, str(id), str(full_path))

                # If the data was sent successfully, get the data as a dataframe and return it
                if status == "Successful":
                    self.df = self.mongodb.get_dataframe(self.Collection)        
                    return self.df
                # If there was an error, return the status
                else:
                    return status



            else:
                msg="Does not exists"
                return msg
        
        except Exception as e:
            logging.error(e)

class Set_Target(View):
    """
    This class provides the get() and post() methods to set the target column for a project.
    """

    def get(self, request, id):
        """
        This method handles the GET request for setting the target column for a project.

        It fetches the data of the specified project based on the given id, and returns a list of columns in the dataframe to
        the user. If the project is a Clustering problem, a message is displayed to the user that there is no target column to be
        set.

        Args:
        - request: the GET request to set the target column
        - id: the id of the project to set the target column

        Returns:
        - A list of columns in the dataframe, if the problem statement is not a Clustering problem
        - A message "No target column to be set in Clustering Problem", if the problem statement is a Clustering problem
        """
        proj1 = Project()
        df = proj1.fetch(id=id)    

        Project_details = upload_Dataset.objects.get(id=id)

        if Project_details.problem_statement_type != "Clustering":
            list_of_cols = list(df.columns)
            return render(request, 'dataProcessing/target_col.html', {"cols": list_of_cols, "Projects": Project_details})
        else:
            message = "No target column to be set in Clustering Problem"
            return render(request, 'dataProcessing/welcome.html', {'data': df, "Projects": Project_details, 'msg': message})

    def post(self, request, id):
        """
        This method handles the POST request for setting the target column for a project.

        It updates the target column for the specified project based on the given id. The target column is obtained from the
        POST request, and the status of the update operation is returned to the user.

        Args:
        - request: the POST request to set the target column
        - id: the id of the project to set the target column

        Returns:
        - A message "unsuccessful", if the target column is not set
        - A message "successful", if the target column is set successfully
        """
        status = "unsuccessful"
        target_column = request.POST.get('set-target-col')
        
        query_ = f"UPDATE projects_info set SetTarget='{target_column}' where Projectid= {id}"
        sql_obj.update_records(query_)
            
        if target_column:
            status = "successful"
        return render(request, 'dataProcessing/welcome.html', {'set_status': status, "target_column": target_column})



def generate_project_Reports(request):
    id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

    records = ProjectReports.retrive_project_reports(project_id=int(id_))
    graphJSON = ""
    pie_graphJSON = ""
    df = pd.DataFrame(records)

    if not df.empty:
        df_counts = pd.DataFrame(df.groupby('ModuleName').count()).reset_index(level=0)
        y = list(pd.DataFrame(df.groupby('ModuleName').count()).reset_index(level=0).columns)[-1]
        df_counts['Total Actions'] = df_counts[y]
        graphJSON = Plotly_agent.plot_barplot(df_counts,x='ModuleName', y='Total Actions')
        pie_graphJSON = Plotly_agent.plot_pieplot(df_counts, names='ModuleName', values='Total Actions', title='')
        return render(request,'dataProcessing/project-reports.html', {"records":records.to_html(), "graphJSON":graphJSON, "pie_graphJSON":pie_graphJSON})
    
    else:
        return render(request,'dataProcessing/project-reports.html', {"msg":"The Reccords are Empty"})




def project_action_history(request):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        all_actions_data = sql_obj.fetch_all(f''' select project_actions.ProjectActionId,project_actions.current_datetime,projectreports.Input,projectreports.ModuleName from projectreports join project_actions on project_actions.Projectid=projectreports.Projectid where project_actions.ProjectId ={int(id_)}
        ''')
        data = ""
        if len(all_actions_data) > 0:
            df = pd.DataFrame(np.array(all_actions_data), columns=['ProjectActionID','Current_date','Input','Module Name'])
            data = df.to_html()
        return render(request,'dataProcessing/actions-history.html', {'status':"success", "data":data})
    except Exception as e:
        return render(request,'dataProcessing/actions-history.html', {"status":"error", "msg":str(e)})




def export_helper(request):    
    source_=request.GET.get('export-data-source')

    source_type=export_Data.objects.filter(export_sources=source_)
    return render(request,'partials/export-choices.html',{"choices":source_type})


def export_data(request):
    '''
    The function fetches all data from the "exportSources" model and retrieves the project details from the 
    'upload_Dataset' model based on the ID stored in the get_project_id table. It then checks if the request method 
    is a POST request and retrieves the selected export format from the request data. The dataset is 
    then retrieved from mongodb and exported to selected sources

    '''
    # Fetch all data from the 'exportSources' model
    Source = exportSources.objects.all()
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        # Retrieve the project details from the 'upload_Dataset' model based on the ID stored in the get_project_id table
        Project_details = upload_Dataset.objects.get(id=int(id_))
        proj1 = Project()
        df = proj1.fetch(id=int(id_))

        # Initialize the download status
        download_status = None
        # Check if the request method is a POST request
        if request.method == "POST":
            # Retrieve the selected export format from the request data
            source_type = request.POST.get('export-data-source')

            # If source_type==1 then Export to file 
            if source_type == '1':
                # Log the start of the export process
                logging.info('Export File in Process')
                # Retrieve the selected export format
                fileID = request.POST.get('get-source', '')
                
                # Check if a format has been selected
                if fileID != "":
                    # Log the creation of a temporary file
                    logging.info(f'Temporary File Created!!, {Project_details.problem_statement_name}.csv')
                    # Get the URL of the file
                    urls = Project_details.file_upload.url
                    # Remove the first character of the URL
                    urls = urls[1:]
                    # Get the file name without the extension
                    file_name = os.path.basename(urls).split('.')[0]
                    # Check if the URL is None
                    if urls is None:
                        # Return an error message
                        render(request,'dataProcessing/export-file.html', {"msg": "OOPS something went wrong!!"})

                # Check if the selected format is CSV
                if fileID == "1":
                    # Check if the file exists
                    status, content = check_file_exists(urls)
                    # Log the successful export to CSV
                    logging.info(f'{status}:Exported to CSV Sucessful')
                    # Return the content as a CSV file
                    response = HttpResponse(content.to_csv(index=False), content_type="text/csv",)
                    response["Content-Disposition"] = f"attachment; filename={file_name}.csv"
                    return response

                # Check if the selected format is TSV
                elif fileID == '2':
                    # Check if the file exists
                    status, content = check_file_exists(urls)
                    # Log the successful export to TSV
                    logging.info(f'{status}: Exported to TSV Sucessful')
                    # Return the content as a TSV file
                    response = HttpResponse(content.to_csv(sep='\t', index=False), content_type="text/tsv",)
                    response["Content-Disposition"] = f"attachment; filename={file_name}.tsv"
                    return response

                # Check if the selected format is JSON
                elif fileID == '3':
                    # Check if the file exists
                    status, content = check_file_exists(urls)

                    # Log the successful export to JSOn
                    logging.info(f'{status}: Exported to JSON Sucessful')
                    # Return the content as a JSON file
                    response= HttpResponse(content.to_json(), content_type="text/json")
                    response["Content-Disposition"]=f"attachment; filename={file_name}.json"
                    return response
                    
                # Check if the selected format is XLSX
                elif fileID == '4':
                    # check if file exists and return its content
                    status,content = check_file_exists(urls)

                    # log the successful export to XLSX
                    logging.info(f'{status}:Exported to XLSX Sucessful')

                    # create a new ExcelWriter object
                    writer= pd.ExcelWriter(f"{file_name}.xlsx")

                    # write the data to the XLSX file
                    df.to_excel(writer, index=False, header=True)

                    # save the file
                    writer.save()

                    # create a response object with the content of the exported file
                    response= HttpResponse(content.to_excel(writer), content_type="application/xlsx",)

                    # set the filename of the exported file in the response header
                    response["Content-Disposition"]=f"attachment; filename={file_name}.xlsx"

                    # return the response to the user
                    return response


            # else If source_type==2 then Export to database 
            elif source_type=="2":
                fileID = request.POST.get('get-source','')

                # check if selected database is MySql
                if fileID == "5":
                    # Get the user input for the MySQL database details
                    host = request.POST.get('host')
                    port = request.POST.get('port')
                    user = request.POST.get('user')
                    password = request.POST.get('password')
                    database = request.POST.get('database')

                    # Connect to the MySQL database using the user input
                    mysql_data = mysql_data_helper(host, port, user, password, database)
                    
                    logging.info("Validating User Mysql Credentials")
                    # Check the connection to the MySQL database
                    conn_msg = mysql_data.check_connection('none')
                    
                    # If the connection is unsuccessful, render the error message
                    if conn_msg != "table does not exist!!":
                        logging.info(f"Users Mysql Connection Not Successful!! {conn_msg}")
                        return render(request,'dataProcessing/export-file.html',{"msg":conn_msg})
                    logging.info("Users Mysql Connection Successful!!")
                    # Download the data from the MongoDB collection
                    download_status, file_path = mongodb.download_collection_data(DATABASE_NAME, Project_details.id, "csv")
                    
                    # If the download is unsuccessful, render an error message
                    if download_status != "Successful":
                        logging.warning(f"Status: download {download_status}")
                        render(request,'dataProcessing/export-file.html',{"msg":"OOPS something went wrong!!"})
                    # Get the current time in milliseconds
                    timestamp = round(time.time() * 1000)
                    
                    # Upload the data to the MySQL table
                    upload_status = mysql_data.push_file_to_table(file_path, f'{Project_details.problem_statement_name}_{timestamp}')
                    
                    # If either the download or upload was unsuccessful, render an error message
                    if download_status != 'Successful' or upload_status != 'Successful':
                        logging.warning(f"Status: upload {upload_status} & download {download_status}")
                        return render(request,'dataProcessing/export-file.html',{"msg":upload_status})
                    
                    # Return the success message
                    message = f'{file_name}_{timestamp} table created in {database} database'
                    logging.info(message)
                    return render(request,'dataProcessing/export-file.html', {"msg":message})

                # check if selected database is CassandraDB
                elif fileID == "6":
                    # Get the secure connect bundle file from the request
                    secure_connect_bundle = request.FILES['secure_connect_bundle']
                    # Get the client ID and client secret from the request
                    client_id = request.POST.get('client_id')
                    client_secret = request.POST.get('client_secret')
                    # Get the keyspace from the request
                    keyspace = request.POST.get('keyspace')
                    # Create a file path for the secure connect bundle
                    secure_connect_bundle_file_path = os.path.join('media/uploads',secure_connect_bundle.name)
                    # Call the handle_uploaded_file function to save the secure connect bundle to disk
                    handle_uploaded_file(secure_connect_bundle,secure_connect_bundle_file_path)
                    
                    # Connect to Cassandra using the secure connect bundle, client ID, client secret, and keyspace
                    cassandra_db = cassandra_connector(secure_connect_bundle_file_path, client_id, client_secret, keyspace)

                    # Log that the user's Cassandra credentials are being validated
                    logging.info("Validating User Cassandra Credentials")
                    # Check the connection to Cassandra
                    conn_msg = cassandra_db.check_connection('none')
                    # Delete the secure connect bundle file
                    delete_temporary_file([secure_connect_bundle_file_path])
                    # If the connection to Cassandra was not successful, log a warning and render an error message
                    if conn_msg != 'table does not exist!!':
                        logging.warning(f"Users Cassandra Connection Not Successful!! {conn_msg}")
                        render(request,'dataProcessing/export-file.html',{"msg":conn_msg})
                    # Log that the connection to Cassandra was successful
                    logging.info("Users Cassandra Connection Successful!!")
                    # Get the URL of the uploaded file
                    url=Project_details.file_upload.url
                    # Replace forward slashes with backslashes and remove the first character
                    url=url.replace('/',"\\")[1:]
                    # Send the data from the uploaded file to MongoDB
                    download_status, getCollection = mongodb.send_dataframe_to_mongodb(DATABASE_NAME,str(Project_details.id),url)
                    # Get the data from MongoDB as a pandas dataframe
                    df=mongodb.get_dataframe(getCollection)
                    # If the data was not sent to MongoDB successfully, render an error message
                    if download_status != "Successful":
                        render(request,'dataProcessing/export-file.html',{"msg":"OOPS something went wrong!!"})

                    # Get the current timestamp in milliseconds
                    timestamp = round(time.time() * 1000)
                    # Push the data from the pandas dataframe to Cassandra
                    upload_status = cassandra_db.push_dataframe_to_table(df,f'{Project_details.problem_statement_name}_{timestamp}')
                    delete_temporary_file([file_path])
                                    
                    # If either the download or upload was unsuccessful, render an error message
                    if download_status != 'Successful' or upload_status != 'Successful':
                            logging.warning(f"Status: upload {upload_status} & download {download_status}")
                            return render(request,'dataProcessing/export-file.html',{"msg":f'{upload_status}'})
                    # else successfully create table in keyspace
                    message = f'{Project_details.problem_statement_name}_{timestamp} table created in {keyspace} keyspace'
                    logging.info(message)
                    return render(request,'dataProcessing/export-file.html',{"msg":message})

                # check if selected database is Mongodb
                elif fileID == "7":
                    # Get the MongoDB URL and database name from the user request
                    mongo_db_url = request.POST.get('mongo_db_url')
                    mongo_database = request.POST.get('mongo_database')

                    # Create a helper object for interacting with the MongoDB database
                    mongo_helper = mongo_data_helper(mongo_db_url)

                    # Check the connection to the MongoDB database
                    conn_msg = mongo_helper.check_connection(mongo_database, 'none')
                    logging.info("Validating User MongoDB Credentials")
                    if conn_msg != "collection does not exits!!":
                        logging.warning(f"Users MongoDB Connection Not Successful!! {conn_msg}")
                        return render(request,'dataProcessing/export-file.html',{"msg":conn_msg})
                    logging.info("Users MongoDB Connection Successful!!")

                    # Download the data from the existing MongoDB database
                    download_status, file_path = mongodb.download_collection_data(DATABASE_NAME,Project_details.id, "csv")
                    if download_status != "Successful":
                        logging.warning(f"Couldnt Download The File!! {download_status}")
                        render(request,'dataProcessing/export-file.html',{"msg":"OOPS something went wrong!!"})
                    logging.info("Looking For User File!!")

                    # Generate a timestamp for the new collection name
                    timestamp = round(time.time() * 1000)

                    # Push the data to the new MongoDB database
                    upload_status = mongo_helper.push_dataset(mongo_database, f'{Project_details.problem_statement_name}_{timestamp}', file_path)
                    if download_status != 'Successful' or upload_status != 'Successful':
                        return render(request,'dataProcessing/export-file.html',{"msg":upload_status})

                    # Return the success message to the user
                    message = f'{file_name}_{timestamp} collection created in {mongo_database} database'
                    logging.info(message)
                    return render(request,'dataProcessing/export-file.html',{"msg":message})
    

            # else If source_type==3 then Export to cloud 
            elif source_type=="3":

                # check if selected cloud is AWS
                if fileID == "8":

                    # Getting the input values from the request object
                    region_name = request.POST.get('region_name')
                    aws_access_key_id = request.POST.get('aws_access_key_id')
                    aws_secret_access_key = request.POST.get('aws_secret_access_key')
                    bucket_name = request.POST.get('aws_bucket_name')
                    file_type = request.POST.get('fileTypeAws')

                    # Initializing the AWS S3 helper class
                    aws_s3 = aws_s3_helper(region_name, aws_access_key_id, aws_secret_access_key)

                    # Logging the validation of the user's AWS S3 credentials
                    logging.info("Validating User AWS S3 Credentials")
                    conn_msg = aws_s3.check_connection(bucket_name, 'none')
                    
                    # Checking if the connection to AWS S3 was not successful
                    if conn_msg != 'File does not exist!!':
                        logging.warning(f"AWS S3 Connection Not Successful!! {conn_msg}")
                        # Rendering an error message if the connection was not successful
                        return render(request,'DataFlows/dataProcessing/export-file.html',{"msg":conn_msg})
                    
                    # Logging a successful AWS S3 connection
                    logging.info("AWS S3 Connection Successful!!")
                    
                    # Downloading the collection data from MongoDB
                    download_status, file_path = mongodb.download_collection_data(DATABASE_NAME,Project_details.id, file_type)
                    
                    # Checking if the file could not be downloaded
                    if download_status != "Successful":
                        logging.warning(f"Couldnt Download The File!! {download_status}")
                        # Rendering an error message if the file could not be downloaded
                        render(request,'DataFlows/dataProcessing/export-file.html',{"msg":"OOPS something went wrong!!"})
                    
                    # Creating a timestamp for the uploaded file
                    timestamp = round(time.time() * 1000)
                    
                    # Uploading the file to AWS S3
                    upload_status = aws_s3.push_file_to_s3(bucket_name, file_path,
                                                            f'{Project_details.problem_statement_name}_{timestamp}.{file_type}')
                    
                    # Deleting the temporary file
                    delete_temporary_file([file_path])
                    
                    # Checking if the file could not be uploaded to AWS S3 and render error
                    if upload_status != 'Successful':
                        logging.warning(f"Couldnt Upload The File To s3 Bucket!!{upload_status}")
                        return render(request,'dataProcessing/export-file.html',{"msg":upload_status})
                    
                    # Return the success message to the user
                    message = f"{file_name}_{timestamp}.{file_type} pushed to AWS S3 {bucket_name} bucket"
                    logging.info(message)
                    return render(request,'DataFlows/dataProcessing/export-file.html',{"msg":message})

                # check if selected cloud is GCP
                elif fileID == "9":

                    # Getting the credentials file for the user's GCP account
                    credentials_file = request.FILES['GCP_credentials_file']
                    # Getting the name of the bucket where the data needs to be uploaded
                    bucket_name = request.POST.get('gcp_bucket_name')
                    # Getting the type of file to be uploaded
                    file_type = request.POST.get('fileTypeGcp')

                    # Creating the path for the credentials file
                    credentials_file_path = os.path.join('media/uploads', credentials_file.name)
                    # Handling the uploaded credentials file
                    handle_uploaded_file(credentials_file,credentials_file_path)

                    # Creating a GCP Storage client object
                    gcp = gcp_browser_storage(credentials_file_path)
                    # Logging to check if the connection to GCP Storage is successful
                    logging.info("Validating User GCP Storage Credentials")
                    conn_msg = gcp.check_connection(bucket_name, 'none')
                    # Deleting the temporary credentials file
                    delete_temporary_file([credentials_file_path])
                    # Checking if the connection to the GCP Storage was successful
                    if conn_msg != 'File does not exist!!':
                        # Logging a warning message if the connection was not successful
                        logging.warning(f"GCP Storage Connection Not Successful!! {conn_msg}")
                        # Rendering the error message
                        return render(request,'dataProcessing/export-file.html',{"msg":conn_msg})
                    # Logging a success message if the connection was successful
                    logging.info("GCP Storage Connection Successful!!")

                    # Downloading the data from the database
                    download_status, file_path = mongodb.download_collection_data(DATABASE_NAME,Project_details.id, file_type)
                    # Logging to check if the data was successfully downloaded
                    logging.info("Looking For User File!!")
                    # Checking if the data was successfully downloaded
                    if download_status != "Successful":
                        # Logging an error message if the data was not successfully downloaded
                        logging.info("Couldn't Download The File!!")
                        # Rendering the error message
                        render(request,'dataProcessing/export-file.html',{"msg":"OOPS something went wrong!!"})

                    # Creating a timestamp for the file
                    timestamp = round(time.time() * 1000)
                    # Uploading the file to the specified bucket
                    upload_status = gcp.upload_to_bucket(f'{Project_details.problem_statement_name}_{timestamp}.{file_type}',
                                                        file_path, bucket_name)
                    # Deleting the temporary file
                    delete_temporary_file([file_path])
                    # Checking if the upload was successful
                    if upload_status != 'Successful':
                        # Logging an error message if the upload was not successful
                        logging.info("Couldn't Upload The File To GCP Storage Container!!")
                        # Rendering the error message
                        return render(request,'dataProcessing/export-file.html',{"msg":upload_status})

                    # Creating a success message
                    message = f"{file_name}_{timestamp}.{file_type} pushed to GCP Storage{bucket_name} bucket"
                    logging.info(message)
                    return render(request,'dataProcessing/export-file.html',{"msg":message})

                # check if selected cloud is Azure
                elif fileID == "10":
                       #Getting Azure connection string from the HTML form
                        azure_connection_string = request.POST.get('azure_connection_string')

                        #Getting Azure container name from the HTML form
                        container_name = request.POST.get('container_name')
                        
                        #Getting file type to be uploaded to Azure from the HTML form
                        file_type = request.POST.get('fileTypeAzure')
                        
                        #Creating object of azure_data_helper
                        azure_helper = azure_data_helper(azure_connection_string)
                        #Logging that we are validating the Azure credentials
                        logging.info("Validating User Azure Credentials")
                        
                        #Checking connection with Azure container
                        conn_msg = azure_helper.check_connection(container_name, 'none')
                        #If connection is not established with Azure container
                        if conn_msg != 'File does not exist!!':
                            #Logging the error message
                            logging.warning(f"AzureStorage Connection Not Successful!! {conn_msg}")
                            #Rendering error message on HTML page
                            return render(request,'DataFlows/dataProcessing/export-file.html',{"msg":conn_msg})

                        #Logging that connection to Azure is successful
                        logging.info("AzureStorage Connection Successful!!")
                        #Downloading data from MongoDB collection
                        download_status, file_path = mongodb.download_collection_data(DATABASE_NAME,Project_details.id, file_type)

                        #Logging that we are searching for the user's file
                        logging.info("Looking For User File!!")
                        #If downloading data from MongoDB was not successful
                        if download_status != "Successful":
                            #Logging the error message
                            logging.warning(f"Couldnt Download The File!! {download_status}")
                            #Rendering error message on HTML page
                            render(request,'dataProcessing/export-file.html',{"msg":"OOPS something went wrong!!"})
                        
                        #Generating timestamp
                        timestamp = round(time.time() * 1000)
                        #Uploading file to Azure container
                        upload_status = azure_helper.upload_file(file_path, container_name,
                                                                f'{Project_details.problem_statement_name}_{timestamp}.{file_type}')
                        #Deleting the temporary file
                        delete_temporary_file([file_path])
                        #If uploading file to Azure container was not successful
                        if upload_status != 'Successful':
                            #Logging the error message
                            logging.info(f"Couldnt Upload The File To Azure Container!!{upload_status}")
                            #Rendering error message on HTML page
                            return render(request,'dataProcessing/export-file.html',{"msg":upload_status})
                        
                        #Generating success message to be rendered on HTML page
                        message = f"{Project_details.problem_statement_name}_{timestamp}.{file_type} pushed to Azure {container_name} container"
                        #Rendering success message on HTML page
                        return render('dataProcessing/export-file.html',{"msg":message})

        return render(request,'dataProcessing/export-file.html',{"sources":Source,"msg":"Select Any File Type!!"})

    except Exception as e:
        return render(request,'dataProcessing/export-file.html',{"msg":e.__str__()})


def export_resources(request):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        # Get project details based on the ID read from a text file
        Project_details= upload_Dataset.objects.get(id=int(id_))

        # Create a folder path based on the project's problem statement name
        
        folder_path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name)
        
        # If the folder path doesn't exist, return an error message
        if not os.path.exists(folder_path):
            return render(request,'dataProcessing/export-resources.html',{"status":"error","msg":"No resources found to export"})
        
        # If the request method is POST, retrieve project actions data from the database
        if request.method=="POST":
            folder_path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name)

            # Get project actions data based on the project ID
            all_actions_data = sql_obj.fetch_all(f''' select project_actions.ProjectActionId,project_actions.current_datetime,projectreports.Input,projectreports.ModuleName from projectreports join project_actions on project_actions.Projectid=projectreports.Projectid where project_actions.ProjectId ={int(id_)}
            ''')
            print(all_actions_data)

            # Save project actions data as a CSV file
            if len(all_actions_data) > 0:
                df = pd.DataFrame(np.array(all_actions_data), columns=['ActionId', 'Input', 'Current_date'])
                df.to_csv(os.path.join(folder_path, 'actions.csv'))

            # Zip all files in the folder
            base_path = pathlib.Path(folder_path)
            data = io.BytesIO()
            with zipfile.ZipFile(data, mode='w') as z:
                for f_name in base_path.iterdir():
                    z.write(f_name)
            data.seek(0)

            # Return the zip file as a response with appropriate headers
            response= HttpResponse(data, content_type="application/zip",)
            response["Content-Disposition"]=f"attachment; filename=data.zip"
            return response

        # If the request method is not POST, redirect to the export resources page
        logging.info('Redirect To Export Resources Page')
        return render(request,'dataProcessing/export-resources.html', {'status':"success"})

    # Catch and log any exceptions that occur during the execution of the function
    except Exception as e:
        logging.error(f'Error occured while exporting Resources {e}')
        return render(request,'dataProcessing/export-resources.html',{"msg":e.__str__()})
    

def Custom_script(request):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        proj1 = Project()
        df = proj1.fetch(id=int(id_))    
        if request.method=="POST" and "run-script" in request.POST:
            code = request.POST.get('function_text')
            # Parse the function text into a function object
            
            #Check if the code contains an "import" statement
            if 'import' in code:
                #Display an error message to the user if the code contains an import statement
                messages.error(request,"Import is not allowed")
            #Check if the code contains a double quote
            if '"' in code:
                #Display an error message to the user if the code contains a double quote
                messages.error(request,"Double quote is not allowed")
            # Check if the code input is not None
            if code is not None:
                # Try to execute the code
                try:
                    # Create a dictionary of global parameters to pass to exec()
                    globalsParameter = {'os': None, 'pd': pd, 'np': np}
                    # Create a dictionary of local parameters to pass to exec()
                    localsParameter = {'df': df}
                    # Execute the code with the specified global and local parameters
                    exec(code, globalsParameter, localsParameter)
                    # Write the updated dataframe to the file path
                    messages.success(request,"Custom script successfully run")
                    return render(request,'dataProcessing/custom-script.html',{"updated_data":df.to_html(),'code':code})

                except Exception as e:
                    # render the exception if there was an error in the code execution
                    return render(request,'custom-script.html', {"status":"error","msg":"Code snippets is not valid"})
            else:
                messages.error(request,"Code snippets is not valid")
                
        if request.method=="POST" and 'save-script' in request.POST:
            code = request.POST.get('hidden_input')
            # Parse the function text into a function object
            
            #Check if the code contains an "import" statement
            if 'import' in code:
                #Display an error message to the user if the code contains an import statement
                messages.error(request,"Import is not allowed")
            #Check if the code contains a double quote
            if '"' in code:
                #Display an error message to the user if the code contains a double quote
                messages.error(request,"Double quote is not allowed")
            # Check if the code input is not None
            if code is not None:
                # Try to execute the code
                try:
                    # Create a dictionary of global parameters to pass to exec()
                    globalsParameter = {'os': None, 'pd': pd, 'np': np}
                    # Create a dictionary of local parameters to pass to exec()
                    localsParameter = {'df': df}
                    # Execute the code with the specified global and local parameters
                    exec(code, globalsParameter, localsParameter)
                    # Write the updated dataframe to the file path
                    update_data(df)
                    messages.success(request,"Custom script successfully saved")
                    return render(request,'dataProcessing/custom-script.html')

                except Exception as e:
                    # render the exception if there was an error in the code execution
                    return render(request,'custom-script.html', {"status":"error","msg":"Code snippets is not valid"})
            else:
                messages.error(request,"Code snippets is not valid")
        


        return render(request,'dataProcessing/custom-script.html',{"data":df.to_html()})
    

    except:
        return render(request,'dataProcessing/custom-script.html', {"status":"error","msg":"Code snippets is not valid"})
        

def system_logs(request):
    try:
        lines = []
        path = glob.glob(os.path.join(next(absoluteFilePaths('logs')), '**/*.log'))

        # Sort the list of log files by modification time in descending order (newest first)
        path.sort(key=os.path.getmtime, reverse=True)

        # Get the path of the latest log file (i.e., the first file in the sorted list)
        latest_log_file = path[0]

        with open(latest_log_file, 'r') as file:
            file_lines = file.readlines()
            lines.extend(file_lines)
        
        return render(request,'dataProcessing/systemlogs.html', {"status":"success","logs":lines,"msg":"Success! Showing logs.."})
    
    except Exception as e:
        logging.error(f"{e} In System Logs API")
        return render(request,'dataProcessing/systemlogs.html', {"status":"error","logs":lines,"msg":e.__str__()})


def get_help(request):
    return render(request,'dataProcessing/help.html')
