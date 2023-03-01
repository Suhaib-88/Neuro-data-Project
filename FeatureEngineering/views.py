from django.shortcuts import render,redirect
import pandas as pd
import numpy as np

from django.contrib import messages
from src.utils.plotlyFunctions import Plotly_agent
from src.utils.basicFunctions import update_data,save_project_encoding,save_project_scaler,fetch_num_cat_cols
from src.utils.projectReports import ProjectReports
# Create your views here.
from src.constants.const import *
from dataProcessing.views import Project
from .functions_FE.fe_operations import FE
from django.shortcuts import render
from dataIngestion.models import upload_Dataset
from django.views import View
from data_access.mysql_connect import MySql
from src.utils.basicFunctions import read_configure_file


config_args= read_configure_file("config.yaml")
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)


class FE_feature_encoding(View):
    '''
    This class implements the feature encoding view for the feature engineering module.
  
    '''
    def get(self,request):
        """
        This method is used to display the feature encoding page. It performs the following tasks:

        1. Fetch the project ID from the 'get_project_id' table
        2. Update the Module URL in the projects_info table to 'encoding'
        3. Create an object of the Project class and fetch the project data with the given ID
        4. Get the project details from the upload_Dataset table
        5. Fetch the target column from the projects_info table
        6. Insert a record in the ProjectReports table with 'Redirect To Encoding' as the message
        7. If the problem statement type is not "Clustering" and the target column is not set, render the target_col.html template
        8. If the encoding action has already been performed, render the feat-encoding.html template with an error message
        9. If no errors are encountered, render the feat-encoding.html template with the encoding types

        Parameters:
            request : HttpRequest
                The request object passed from the view

        Returns:
            HttpResponse
                A HttpResponse object containing the rendered template.
        """
        # Fetching project id from the 'get_project_id' table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Updating the Module URL in the projects_info table to 'encoding'
            query_ = f"UPDATE projects_info set ModuleUrl='encoding' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Creating an object of the Project class
            proj1 = Project()
            # Fetching project data with the given id
            df = proj1.fetch(id=id_)
            # Getting the project details from the upload_Dataset table
            Project_details = upload_Dataset.objects.get(id=id_)

            # Fetching the target column from the projects_info table
            target_ = sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={Project_details.id}""")[0]

            # Inserting a record in the ProjectReports table
            ProjectReports.insert_record_fe(id_,'Redirect To Encoding')        

            # If the problem statement type is not "Clustering" and the target column is not set
            if Project_details.problem_statement_type != "Clustering" and target_ == 'None':
                # Render the target_col.html template
                return render(request,'dataProcessing/target_col.html',{"Projects":Project_details,"cols":list(df.columns),"isSetTarget":False,"msg":"Please select a target column first"})

            # Checking if the encoding action has already been performed
            query_ = f"Select * from Project_Actions  where ProjectId={Project_details.id} and ProjectActionId=2"
            rows = sql_obj.fetch_all(query_)

            # if rows are not none and greater than 0 that means encoding has been already performed, render message
            if rows is not None:
                if len(rows) > 0:
                    return render(request,'FeatureEngineering/feat-encoding.html',{ "encoding_types":GET_ENCODING_TYPES,"allowed_operation":"not","columns":[], "status":"error","msg":"You Already Performed Encoding Don't do this again"})

            return render(request,'FeatureEngineering/feat-encoding.html',{"encoding_types":GET_ENCODING_TYPES, "status":"success"})

        except Exception as e:
            return render(request,'FeatureEngineering/feat-encoding.html',{"status":"error", "encoding_types":GET_ENCODING_TYPES,'msg':e.__str__()})
    
    def post(self,request):
        """
        This function is used to perform encoding and save the encoding result.
        
        When the user submits the encoding form, the `post` request is triggered and it performs the following actions:
        - Fetch the project ID from a sql table named `get_project_id`.
        - Get the data for the project.
        - Split the data into numerical columns and categorical columns.
        - Remove the categorical columns with more than 5 unique values.
        - If the user has clicked on the "Check Result" button, perform encoding on the remaining categorical columns and display a sample of the encoded data to the user.
        - If the user has clicked on the "Save Result" button, perform encoding on the remaining categorical columns, save the encoding result, update the data in the database, and redirect the user to the scaling page.
        """
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            proj1=Project()
            data=proj1.fetch(id=id_)

            num_column,cat_column=fetch_num_cat_cols(data)
            df=data[data.notnull().all(axis=1)].reset_index(drop=True)
            encoding_cols=list()
            
            for i in cat_column:
                if df[i].nunique()>5:
                    df.drop(columns=i,inplace=True)
                else:
                    encoding_cols.append(i)

            if request.method=='POST' and 'checkResult' in request.POST:
                encoding_type=request.POST.get('encoding_type')

                ProjectReports.insert_record_fe(id_,'Perform Encoding', encoding_type)
                
                non_encoded_columns=[col for col in df.columns if col not in encoding_cols]            
                
                encoded_df,encoder=FE.encode(df,encoding_cols,encoding_type)
                
                rem_data=df.loc[:,non_encoded_columns]
                df = pd.concat([encoded_df, rem_data], axis=1)
                df_to_html=[df.sample(10).to_html(classes='data')]
                return render(request,'FeatureEngineering/feat-encoding.html',{"encoding_types":GET_ENCODING_TYPES,'data':df_to_html})

            if request.method=='POST' and 'saveResult' in request.POST:
                encoding_type=request.POST.get('encoding_type')
                non_encoded_columns=[col for col in df.columns if col not in encoding_cols]            
                encoded_df,encoder=FE.encode(df,encoding_cols,encoding_type)
                rem_data=df.loc[:,non_encoded_columns]
                df = pd.concat([encoded_df, rem_data], axis=1)
                save_project_encoding(encoder)
                update_data(df)
            
        
                ProjectReports.insert_project_action_report(id_,PROJECT_ACTIONS.get("ENCODING"),input_=",".join(encoding_cols))
                messages.success(request,'Successfully performed encoding')
                return redirect('scaling')
                            
        except Exception as e:
            return render(request,'FeatureEngineering/feat-encoding.html',{"status":"error", "encoding_types":GET_ENCODING_TYPES,
                                                'msg':e.__str__(),})
                

class FE_feature_scaling(View):
    """
    The Class-based View is used to perform feature scaling on the given dataset.
    This class handles the feature scaling of data by taking the scaling method selected by the user.
    The data is then scaled using the selected method and the result is displayed on the HTML template.

    """

    def get(self,request):
        '''
        Purpose: This function is used to handle the GET request for feature scaling.
        It performs several checks to validate the request and returns an error message if the request is invalid.
        If the request is valid, it fetches the dataset and returns the columns that can be used for scaling.

        '''
        
        # Fetch the project id from the table 'get_project_id'
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Update the project status to 'scaling'
            query_ = f"UPDATE projects_info set ModuleUrl='scaling' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Fetch the project object
            proj1=Project()
            df=proj1.fetch(id=id_)
            
            # Check if the dataset contains categorical or object data.
            # If it does, return an error message indicating that encoding must be performed first.
            if len(df.columns[df.dtypes == 'category']) > 0 or len(df.columns[df.dtypes == 'object']) > 0:    
                return render(request,'FeatureEngineering/feat-scaling.html',{"scaler_types":ALLOWED_SCALE_TYPES,"allowed_operation":"not","columns":[], "status":"error","msg":"Scaling can't be performed at this point, data contain categorical data. Please perform encoding first"})

            # Fetch the project details
            Project_details= upload_Dataset.objects.get(id=id_)
            
            # Fetch the target column
            target_=sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={Project_details.id}""")[0]
            
            # Insert a record for redirecting to scaling
            ProjectReports.insert_record_fe(id_,'Redirect To Scaling')

            # If the problem statement type is not clustering and the target column is not set, return an error message
            # indicating that the target column must be set first.
            if Project_details.problem_statement_type != "Clustering" and target_ == 'None':
                return render(request,'dataProcessing/target_col.html',{"Projects":Project_details,"cols":list(df.columns),"isSetTarget":False,"msg":"Please select a target column first"})


            # Check if scaling has already been performed for this project
            query_ = f"Select * from Project_Actions  where ProjectId={Project_details.id} and ProjectActionId=3"            
            rows = sql_obj.fetch_all(query_)
            
            # if rows are not none and greater than 0 that means scaling has been already performed, render message
            if rows is not None:        
                if len(rows) > 0:
                    return render(request,'FeatureEngineering/feat-scaling.html',{ "scaler_types":ALLOWED_SCALE_TYPES,"allowed_operation":"not","columns":[], "status":"error","msg":"You Already Performed Scaling. Don't do this again"})

            return render(request,'FeatureEngineering/feat-scaling.html', {"scaler_types":ALLOWED_SCALE_TYPES,"columns":list(df.columns)})
        
        except Exception as e:
            raise Exception(e)
                        
    def post(self,request):
        """
        POST method for handling feature scaling of data

        This method retrieves the project id, fetches the project data, gets the project details,
        target column and scaling method selected by the user. The data is then scaled using the selected method,
        and the result is rendered on the HTML template.
        
        Args:
        request: The request made by the user

        Returns:
        A rendered HTML template with the scaling types and scaled data.
        """
        # fetching project id from the 'get_project_id' table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:    
            # creating an object of the Project class
            proj1 = Project()
            # fetching project data with the given id
            df = proj1.fetch(id=id_)
            # getting the project details from the database
            Project_details = upload_Dataset.objects.get(id=id_)
            
            # fetching the target column from the database
            target_ = sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={Project_details.id}""")[0]
            
            # getting the selected scaling method from the form
            scaling_method = request.POST['scaling_method']
            
            # inserting the scaling method used into the ProjectReports
            ProjectReports.insert_record_fe(id_,"Perform Scaling",scaling_method)

            
            if target_:
                columns = [col for col in df.columns if col != target_]
            
            # scaling the data using the selected method
            df[columns], scaler = FE.scale(df[columns], scaling_method)
            # converting the scaled data into HTML format
            df_to_html = [df.sample(10).to_html(classes='data')]
            
            # saving the scaler used for scaling
            save_project_scaler(scaler)
            # updating the dataframe
            update_data(df)
            
            # inserting an action report into the ProjectReports
            ProjectReports.insert_project_action_report(id_,PROJECT_ACTIONS.get("SCALING"),input_=scaling_method)
            
            # rendering the HTML template with the scaling types and scaled data
            return render(request,'FeatureEngineering/feat-scaling.html',{"scaler_types":ALLOWED_SCALE_TYPES,'data':df_to_html})

        except Exception as e:
            return render(request,'FeatureEngineering/feat-scaling.html', {"status":"error", "scaler_types":ALLOWED_SCALE_TYPES,"columns":list(df.columns[df.dtypes != 'object'])})



class FE_handle_imbalanced_data(View):
    """
    Class based view to handle imbalanced data in a dataset. 
    """
    def get(self,request):
        """
        Handles the GET request for imbalanced data handling.
        
        Args:
            request: a request object

        Returns:
            A HTML render for imbalanced data handling page if data is a classification problem and contains only numerical independent features.
            A HTML render for target column selection page if the target column is not selected.
            A HTML render for error page if the data is not a classification problem or contains categorical independent features.
        """
        # fetch the project id from a sql table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # update the module URL in the database
            query_ = f"UPDATE projects_info set ModuleUrl='imbalanced' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # fetch the project data using the id
            proj1=Project()
            df=proj1.fetch(id=id_)
            Project_details= upload_Dataset.objects.get(id=id_)
            
            # fetch the target column from the database
            target_=sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={Project_details.id}""")[0]

            # check if the target column is set for the project
            if Project_details.problem_statement_type != "Clustering" and target_ == 'None':
                # return an error message if the target column is not set
                return render(request,'dataProcessing/target_col.html',{"Projects":Project_details,"cols":list(df.columns),"isSetTarget":False,"msg":"Please select a target column first"})

            # check if the problem statement type is classification
            if  Project_details.problem_statement_type != "Classification":
                # return an error message if the problem statement type is not classification
                return render(request,'FeatureEngineering/handle_imbalanced.html', {"error":"This section only for classification"})

            target_column = target_
            num_cols,cat_cols=fetch_num_cat_cols(df)

            # check if the categorical columns contain the target column
            cols_ = [col for col in cat_cols if col != target_column]
            Categorical_columns = df.loc[:, cols_]
            if len(Categorical_columns.columns) > 0:
                # return an error message if the categorical columns contain the target column
                return render(request,'FeatureEngineering/handle_imbalanced.html', {"columns":list(df.columns),"error":"Data contain some categorical indepedent features, please perform encoding first"})

            # render the handle imbalanced data page with the target column
            return render(request,'FeatureEngineering/handle_imbalanced.html',{
                                                    "target_column":target_column,"imbalance_methods":SAMPLING_METHODS})        
        except Exception as e:
            return render(request,'FeatureEngineering/feat-scaling.html', {"status":"error","msg":e.__str__()})

    

    def post(self,request):
        """
        Handle the post request for handling imbalanced data

        The post request is used to balance the data and show the results on the UI. It performs the following steps:
            - Fetch the project id from the 'get_project_id' table
            - Fetch the project details using the project id
            - Fetch the target column of the project
            - Balance the data using the selected method (OS, US, or RandomOverSampler)
            - Update the data in the database
            - Create a bar graph and pie chart to show the count of different target categories
            - Return the results to the UI

        Returns:
            A rendered HTML page 'FeatureEngineering/handle_imbalanced.html' with the balanced data, graphs, and results.
        """
        try:
            id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

            # Fetch the project details
            proj1 = Project()
            df = proj1.fetch(id=id_)

            Project_details = upload_Dataset.objects.get(id=id_)
            target_column = sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={Project_details.id}""")[0]

            # Get the selected method for handling imbalanced data
            method = request.POST.get('method')

            # Balance the data using the selected method
            if method == 'OS':
                new_df = FE.balance_data(df, method, target_column)
            elif method == 'US':
                new_df = FE.balance_data(df, method, target_column)
            else:
                new_df = FE.balance_data(df, method, target_column)
            
            # Update the balanced data in the dataframe
            df = update_data(new_df)
            
            # Create a bar graph and pie chart to show the count of different target categories
            df_counts = pd.DataFrame(df.groupby(target_column).count()).reset_index(level=0)
            y = list(pd.DataFrame(df.groupby(target_column).count()).reset_index(level=0).columns)[-1]
            df_counts['Count'] = df_counts[y]
            graphJSON = Plotly_agent.plot_barplot(df_counts,x=target_column, y='Count')
            pie_graphJSON = Plotly_agent.plot_pieplot(df_counts, names=target_column, values=y, title='')
            data = {}

            # Create a dictionary to store the count of different target categories
            for (key, val) in zip(df_counts[target_column], df_counts['Count']):
                data[str(key)] = val
            
            # Return the results to the 'FeatureEngineering/handle_imbalanced.html'
            return render(request,'FeatureEngineering/handle_imbalanced.html',{"target_column":target_column,"pie_graphJSON":pie_graphJSON, "graphJSON":graphJSON,"data":data.items(), "success":True,"imbalance_methods":SAMPLING_METHODS})

        except Exception as e:
            return render(request,'FeatureEngineering/handle_imbalanced.html',{"status":"error","msg":e.__str__()})
            
