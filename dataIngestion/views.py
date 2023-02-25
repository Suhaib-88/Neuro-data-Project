from django.shortcuts import render,redirect,HttpResponseRedirect
from .forms import *
from django.contrib import messages
from .models import upload_Dataset,importSources,import_Data
from django.views import View
from django.utils.translation import gettext_lazy as _
# Create your views here.
from src.utils.basicFunctions import delete_temporary_file
from src.utils.basicFunctions import handle_uploaded_file
from src.utils.cloudFunctions import aws_s3_helper,azure_data_helper,gcp_browser_storage
from src.utils.databaseFunctions import mongo_data_helper,mysql_data_helper,cassandra_connector
from data_access.mysql_connect import MySql
import os
from src.utils.basicFunctions import read_configure_file
from logger import logging

config_args = read_configure_file("./config.yaml")

# initializing MySql object
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)




class Import_Helper(View):
    def get(self,request):    
        source_=request.GET.get('import-data-source')

        source_type=import_Data.objects.filter(import_sources=source_)
        return render(request,'partials/import-choices.html',{"choices":source_type})



class Adding_Module(View):
    """
    Adding_Module is a class-based view that handles the process of uploading a new dataset into the project.
    It has two methods: `get` and `post`.
    """
    def __init__(self):
        super().__init__()

    context={}
    form =DatasetDetails()

    def get(self,request):
        """
        Handles the GET request for the add_module page.
        
        :param request: The request sent by the user.
        :return: A rendered template with the form to add a new dataset and a list of all the data sources.
        """
        try:
            form=DatasetDetails()
            Source= importSources.objects.all()
            context={'form':form,"sources":Source}
            return render(request,'dataIngestion/add_module.html',context)
        except Exception as e:
            logging.error(e)

    def post(self,request):
        """
        Handles the POST request for the add_module page.
        
        :param request: The request sent by the user.
        :return: A redirect to the home page on successful addition of the dataset, or a re-rendering of the form on failure.
        """
        try:
            # Status for the file download
            download_status = None
            # Path to the file uploaded
            file_path = None

            # Check if the user wants to upload a file
            uploadFile = request.POST.get('uploadFile')
            # Check if the user wants to use a data resource
            uploadResource = request.POST.get('uploadResource')

            # If the user selects upload a file
            if uploadFile == 'on':
                form = DatasetDetails(request.POST, request.FILES)

                # If the form is valid
                if form.is_valid():
                    # Get the user details
                    user = self.request.user
                    # Get the problem type from the form
                    problem_type = form.cleaned_data['problem_statement_type']
                    # Get the problem name from the form
                    problem_name = form.cleaned_data['problem_statement_name']
                    # Get the problem description from the form
                    problem_description = form.cleaned_data['problem_statement_description']
                    # Get the file uploaded by the user
                    file = form.cleaned_data.get('file_upload')

                    # Create an instance of the upload_Dataset model
                    data = upload_Dataset(user=user, problem_statement_type=problem_type, problem_statement_name=problem_name,
                                        problem_statement_description=problem_description, file_upload=file)
                    # Save the instance to the database
                    data.save()

                    # Add a success message for the user
                    messages.success(request, 'Sucessfully uploaded file')
                    # Log the successful addition of the project
                    logging.info(f'added project sucessfully with {problem_name}')

                    # Redirect the user to the home page
                    return redirect('home')
                else:
                    # If the form is not valid, re-render the form
                    form = DatasetDetails()
                    return render(request,'dataIngestion/add_module.html',{"form":form})
            
            # Checking if the user selected to upload a resource
            elif uploadResource=='on':

                # Allowed file extensions for resource
                ALLOWED_EXTENSIONS= ['csv', 'tsv', 'json', 'xlsx']
                # Getting the selected resource type
                resource_type=request.POST.get('get-source')
                
                # If the selected resource type is mysql
                if resource_type == "10":
                    # Getting the mysql host, port, username, password, and database details
                    host = request.POST['host']
                    port = request.POST['port']
                    username = request.POST['user']
                    password = request.POST['password']
                    database = request.POST['database']
                    table_name = request.POST['tablename']
                    # Setting the file path for the retrieved mysql table
                    file_path = os.path.join('media/uploads', (table_name + ".csv"))
                    
                    # Validating the form data
                    form = DatasetDetails(request.POST,request.FILES)
                    if form.is_valid():
                        # Getting the user, problem type, name, and description
                        user=self.request.user
                        problem_type=form.cleaned_data['problem_statement_type']
                        problem_name=form.cleaned_data['problem_statement_name']
                        problem_description=form.cleaned_data['problem_statement_description']
                        # Setting the file path for the retrieved mysql table
                        File=file_path  
                        # Creating an instance of upload_Dataset and saving it to the database
                        data=upload_Dataset(user=user,problem_statement_type=problem_type,problem_statement_name=problem_name,problem_statement_description=problem_description,file_upload=None,file_from_resources=File)
                        data.save()
                        # Showing success message to the user
                        messages.success(request,'Sucessfully uploaded file')

                    # Creating an instance of mysql_data_helper
                    mysql_data = mysql_data_helper(host, port, username, password, database)
                    logging.info("Validating User's Mysql Credentials!!")
                    # Checking the mysql connection
                    conn_msg = mysql_data.check_connection(table_name)
                    
                    # If the connection is not successful
                    if conn_msg != 'Successful':
                        logging.info("User's Msql Connection Not Successful")
                        # Returning an error message to the user
                        return render(request,'dataIngestion/add_module.html', {"msg":conn_msg})
                    logging.info("User's Msql Connection Successful")
                    # Retrieving the dataset from the mysql table
                    download_status = mysql_data.retrive_dataset_from_table(table_name, file_path)
                    # Redirecting the user to the home page
                    return redirect('home')

                # Check if the selected resource type is Cassandra               
                if resource_type == "11":
                    # Retrieve the uploaded secure connect bundle file from the form
                    secure_connect_bundle = request.FILES['secure_connect_bundle']
                    
                    # Retrieve the client id and secret from the form
                    client_id = request.POST['client_id']
                    client_secret = request.POST['client_secret']
                    
                    # Retrieve the keyspace and table name from the form
                    keyspace = request.POST['keyspace']
                    table_name = request.POST['tablename']
                    
                    # Retrieve the data in tabular format from the form
                    data_in_tabular = request.POST['data_in_tabular']
                    
                    # Define the file path for the uploaded secure connect bundle
                    secure_connect_bundle_file_path = os.path.join('media/uploads',secure_connect_bundle.name)
                    
                    # Call the function to handle the uploaded secure connect bundle file
                    handle_uploaded_file(secure_connect_bundle,secure_connect_bundle_file_path)
                    
                    # Define the file path for the retrieved data from Cassandra
                    file_path = os.path.join('media/uploads', (table_name + ".csv"))
                    
                    # Validate the data entered in the form
                    form = DatasetDetails(request.POST,request.FILES)
                    if form.is_valid():
                        # Retrieve the user who uploaded the data
                        user=self.request.user
                        
                        # Retrieve the problem type, name, and description from the form
                        problem_type=form.cleaned_data['problem_statement_type']
                        problem_name=form.cleaned_data['problem_statement_name']
                        problem_description=form.cleaned_data['problem_statement_description']
                        
                        # Set the file path to be saved in the database
                        File=file_path  
                        
                        # Create an instance of the "upload_Dataset" model and save it to the database
                        data=upload_Dataset(user=user,problem_statement_type=problem_type,problem_statement_name=problem_name,problem_statement_description=problem_description,file_upload=None,file_from_resources=File)
                        data.save()
                        
                        # Show a success message
                        messages.success(request,'Sucessfully uploaded file')

                    # Connect to Cassandra using the provided credentials
                    cassandra_db = cassandra_connector(secure_connect_bundle_file_path, client_id, client_secret, keyspace)
                    logging.info("Validating User's Cassandra Credentials!!")
                    conn_msg = cassandra_db.check_connection(table_name)
                    
                    # Delete the temporary secure connect bundle file
                    delete_temporary_file([secure_connect_bundle_file_path])
                    
                    # Check if the connection was successful
                    if conn_msg != 'Successful':
                        logging.info("User's Cassandra Connection Not Successful")
                        return render(request,'dataIngestion/add_module.html', {"msg":conn_msg})

                    # if the connection was successful then download the data into local system
                    logging.info("Users Cassandra Connection Successful")
                    if data_in_tabular == None:
                        # Retrieving the dataset from cassandra if it is not in tabular format
                        download_status = cassandra_db.retrive_table(table_name, file_path)
                        logging.info(download_status)
                    elif data_in_tabular == "on":
                        # Retrieving the dataset from cassandra if it is in tabular format
                        download_status = cassandra_db.retrive_uploded_dataset(table_name, file_path)
                        logging.info(download_status)

                    # Redirecting the user to the home page
                    return redirect('home')


                # Check if the selected resource type is MongoDB               
                if resource_type == "12":
                    # Get the MongoDB URL from the request
                    mongo_db_url = request.POST['mongo_db_url']
                    
                    # Get the MongoDB database name from the request
                    mongo_database = request.POST['mongo_database']
                    
                    # Get the collection name from the request
                    collection = request.POST['collection']
                    
                    # Create the file path for the dataset
                    file_path = os.path.join('media/uploads', (collection + ".csv"))
                    
                    # Create a form instance with the request data
                    form = DatasetDetails(request.POST,request.FILES)
                    # If the form is valid
                    if form.is_valid():
                        # Get the user from the request
                        user=self.request.user
                        # Get the problem type from the form data
                        problem_type=form.cleaned_data['problem_statement_type']
                        # Get the problem name from the form data
                        problem_name=form.cleaned_data['problem_statement_name']
                        # Get the problem description from the form data
                        problem_description=form.cleaned_data['problem_statement_description']
                        # Get the file path
                        File=file_path
                        # Create an instance of the upload_Dataset class
                        data=upload_Dataset(user=user,problem_statement_type=problem_type,problem_statement_name=problem_name,problem_statement_description=problem_description,file_upload=None,file_from_resources=File)
                        # Save the instance to the database
                        data.save()
                        # Show a success message
                        messages.success(request,'Sucessfully uploaded file')

                    # Create an instance of the mongo_data_helper class
                    mongo_helper = mongo_data_helper(mongo_db_url)
                    # Log that we are validating the user's MongoDB credentials
                    logging.info("Validating User's MongoDB Credentials!!")
                    # Check the connection to the MongoDB database
                    conn_msg = mongo_helper.check_connection(mongo_database, collection)
                    # If the connection is not successful
                    if conn_msg != 'Successful':
                        # Log a warning message
                        logging.warning(f"User's MongoDB Connection Not Successful {conn_msg}")
                        # Return the error message to the template
                        return render(request,'dataIngestion/add_module.html', {"msg":conn_msg})
                    # Log that the user's MongoDB connection is successful
                    logging.info("User's MongoDB Connection Successful")
                    # Retrieve the dataset from MongoDB
                    download_status = mongo_helper.retrive_dataset(mongo_database, collection, file_path)
                    # Log the download status
                    logging.info(download_status)

                    # Redirect to the home page
                    return redirect('home')


                # Check if the selected resource type is AWS cloud               
                if resource_type == "13":

                    # Get the region name from the form data
                    region_name = request.POST['region_name']
                    # Get the AWS access key ID from the form data
                    aws_access_key_id = request.POST['aws_access_key_id']
                    # Get the AWS secret access key from the form data
                    aws_secret_access_key = request.POST['aws_secret_access_key']
                    # Get the bucket name from the form data
                    bucket_name = request.POST['bucket_name']
                    # Get the file name from the form data
                    file_name = request.POST['file_name']
                    
                    # Check if the file format is allowed
                    if file_name.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                        # Log a message if the file format is not allowed
                        message = 'This file format is not allowed, please select mentioned one'
                        logging.info(message)
                        # Render an error message to the user
                        return render(request,'dataIngestion/add_module.html',{"msg":message})
                    
                    # Create the file path
                    file_path = os.path.join('media/uploads', file_name)
                    # Initialize the AWS S3 helper
                    aws_s3 = aws_s3_helper(region_name, aws_access_key_id, aws_secret_access_key)
                    # Log a message that the user's AWS credentials are being validated
                    logging.info("Validating User's AWS Credentials!!")
                    # Check the connection to the AWS S3 bucket
                    conn_msg = aws_s3.check_connection(bucket_name, file_name)
                    # If the connection is not successful, log a warning and render an error message to the user
                    if conn_msg != 'Successful':
                        logging.warning(f"AWS Connection Not Successful {conn_msg}")
                        return render(request,'dataIngestion/add_module.html', {"msg":conn_msg})
                    # If the connection is successful, log a message
                    logging.info("AWS Connection Successful!!")
                    # Download the file from the AWS S3 bucket
                    download_status = aws_s3.download_file_from_s3(bucket_name, file_name, file_path)
                    # Log the download status
                    logging.info(download_status)

                    # Redirect to the home page
                    return redirect('home')



                # Check if the selected resource type is GCP cloud               
                if resource_type == "14":
                    # Get the credentials file from the request
                    credentials_file = request.FILES['GCP_credentials_file']
                    # Get the bucket name from the request
                    bucket_name = request.POST['bucket_name']
                    # Get the file name from the request
                    file_name = request.POST['file_name']
                    
                    # Check if the file extension is allowed
                    if file_name.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                        # If the extension is not allowed, set the message to indicate that
                        message = 'This file format is not allowed, please select mentioned one'
                        # Render the add_module.html template with the error message
                        return render(request,'dataIngestion/add_module.html', {"msg":message})
                    
                    # Set the path to save the credentials file
                    credentials_file_path = os.path.join('media/uploads',credentials_file.name)
                    # Save the credentials file
                    handle_uploaded_file(credentials_file,credentials_file_path)
                    # Set the path to save the file from the GCP bucket
                    file_path = os.path.join('media/uploads', file_name)
                    # Create a gcp_browser_storage object with the credentials file
                    gcp = gcp_browser_storage(credentials_file_path)
                    # Log that we are validating the user's GCP credentials
                    logging.info("Validating User's GCP Credentials!!")
                    # Check the connection to the GCP bucket
                    conn_msg = gcp.check_connection(bucket_name, file_name)
                    # Delete the temporary credentials file
                    delete_temporary_file([credentials_file_path])
                    # Check if the connection was not successful
                    if conn_msg != 'Successful':
                        # Log the unsuccessful connection and set an error message
                        logging.warning("GCP Connection Not Successful {conn_msg}")
                        return render(request,'dataIngestion/add_module.html', {"msg":conn_msg})
                    # Log that the connection was successful
                    logging.info("GCP Connection Successful")
                    # Download the file from the GCP bucket
                    download_status = gcp.download_file_from_bucket(file_name, file_path, bucket_name)
                    # Log the status of the file download
                    logging.info(download_status)
                    
                    # Redirect to the home page
                    return redirect('home')



                # Check if the selected resource type is Azure cloud               
                if resource_type == "15":
                    # Get the Azure connection string from the request
                    azure_connection_string = request.POST['azure_connection_string']
                    # Get the container name from the request
                    container_name = request.POST['container_name']
                    # Get the file name from the request
                    file_name = request.POST['file_name']

                    # Check if the file extension is in the list of allowed extensions
                    if file_name.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                        message = 'This file format is not allowed, please select mentioned one'
                        # Return a message if the file extension is not allowed
                        return render(request,'dataIngestion/add_module.html', {"msg":message})

                    # Set the file path
                    file_path = os.path.join('media/uploads', file_name)
                    # Create an instance of the azure_data_helper class
                    azure_helper = azure_data_helper(azure_connection_string)

                    # Validate the user's Azure credentials
                    logging.info("Validating User's Azure Credentials!!")
                    conn_msg = azure_helper.check_connection(container_name, file_name)
                    # Check if the connection was successful
                    if conn_msg != 'Successful':
                        # Log a warning if the connection was not successful
                        logging.info(f"User's Azure Connection Not Successful :{conn_msg}")
                        # Return a message if the connection was not successful
                        return render(request,'dataIngestion/add_module.html', {"msg":conn_msg})
                    # Log a message if the connection was successful
                    logging.info("User's Azure Connection Successful")

                    # Download the file
                    download_status = azure_helper.download_file(container_name, file_name, file_path)
                    # Log the status of the file download
                    logging.info(download_status)
                    
                    # Redirect to the home page
                    return redirect('home')


            form=DatasetDetails()
            return render(request,'dataIngestion/add_module.html',{"form":form,"msg":"Upload field left empty: Please upload a file from local or from resources"})
        except Exception as e:
            logging.error(f"error occured while importing data from resources:{e}")
            return render(request,'dataIngestion/add_module.html', {"msg":e.__str__()})


class projects_view(View):
    def get(self,request,userID):
        context = {}
        lists_of_headers=["Project Name",'Problem Type','File Name:','Last Modified:',"Actions"]
        try:
            context = {}
            lists_of_headers=["Project Name",'Problem Type','File Name:','Last Modified:',"Actions"]
            try:
                problem_details= upload_Dataset.objects.filter(user_id=userID).values()
            except upload_Dataset.DoesNotExist:
                problem_details=None

            context['PROJECTS']= problem_details
            context['userID']=userID
            context['LISTS']=lists_of_headers
            return render(request,'dataIngestion/projects.html',context)
        except Exception as e:
            logging.error(e)
            return render(request,'dataIngestion/projects.html',{"error":True,'msg':e.__str__()})


def update_data(request,id):
    """
    This function updates a dataset based on the id in the database

    Args:
    request : The request object that contains the information of the user request
    id : The id of the dataset that needs to be updated in the database

    Returns:
    render : A render object that redirects to the update form of the dataset

    """
    if request.method=="POST":
        # Get the instance of the dataset that needs to be updated
        instance=upload_Dataset.objects.get(pk=id)
        # Create a form instance with the data from the request object
        form = DatasetDetails(request.POST,request.FILES,instance=instance)
        # Check if the form is valid
        if form.is_valid():
            problem_type=form.cleaned_data['problem_statement_type']
            problem_name=form.cleaned_data['problem_statement_name']

            sql_obj.update_records(f''' UPDATE projects_info SET ProblemType="{problem_type}", ProblemName="{problem_name}"''')
            # Save the form data
            form.save()
            # Show a success message to the user
            messages.info(request,'Updated sucessfully')

    # Get the instance of the dataset that needs to be updated
    instance_=upload_Dataset.objects.get(pk=id)
    # Create a form instance with the data from the instance object
    form = DatasetDetails(instance=instance_)
    # Create a context dictionary with the form instance
    context= {"form":form}
    # Render the update form with the context dictionary
    return render(request,'dataIngestion/updateform.html' ,context)



def delete_data(request,id):
    """
    This function deletes a dataset based on the id in the database

    Args:
    request : The request object that contains the information of the user request
    id : The id of the dataset that needs to be deleted from the database

    Returns:
    HttpResponseRedirect : A HttpResponseRedirect object that redirects to the homepage

    """
    if request.method=="POST":
        # Try to get the dataset based on the id
        try:
            problem_details= upload_Dataset.objects.get(pk=id)
        except upload_Dataset.DoesNotExist:
            # If the dataset doesn't exist, set it to None
            problem_details=None
        # Delete the dataset from the database
        problem_details.delete()
        sql_obj.delete_records(f"""delete from projects_info where Projectid={id} """)
        # Show a success message to the user
        messages.info(request,'Project sucessfully deleted ')

        # Redirect to the homepage
        return HttpResponseRedirect('/')



