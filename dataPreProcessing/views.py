from django.shortcuts import render,redirect
import pandas as pd
import os
import numpy as np
from EDA.functions_EDA.eda_operations import EDA
from src.utils.plotlyFunctions import Plotly_agent
from src.utils.basicFunctions import fetch_num_cat_cols,save_project_pca,save_numpy_array,absoluteFilePaths,merge_uploaded_file
from django.contrib import messages


# Create your views here.

from dataProcessing.views import Project
from .functions_DP.preprocessing import Preprocessor 
from django.shortcuts import render,redirect
from src.utils.basicFunctions import update_data,check_file_exists
from src.constants.const import *
from src.utils.projectReports import ProjectReports  
from data_access.mysql_connect import MySql
from src.utils.basicFunctions import read_configure_file
from DF_Components.dataflows_Functions.dataflow_helper import dataSource

#need to check target column after encoding due to multiple columns

config_args= read_configure_file("config.yaml")
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)



class dataCleaning:
    """Class that contains various functions to perform data cleaning operations on the given dataset."""

    def handle_duplicate_data(request):
        """
        This method handles the duplicate data present in a dataframe.
        It first fetches the Projectid from the 'projects_info' table.
        Then it updates the 'ModuleUrl' column to 'duplicates' for the corresponding Projectid.
        Next, it fetches the data of the corresponding Projectid using the 'fetch' method of the Project class.
        Then it removes the duplicate data present in the dataframe and updates the data using the 'update_data' method.
        Finally, it returns the data along with the columns of the dataframe and the number of duplicates.

        Arguments:
        request -- The request object that contains information about the current request.
        
        Returns:
        A render object that displays the data along with the columns of the dataframe and the number of duplicates.
        """
        # Fetch the Projectid from the 'projects_info' table.
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Update the 'ModuleUrl' column to 'duplicates' for the corresponding Projectid.
            query_ = f"UPDATE projects_info set ModuleUrl='duplicates' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Fetch the data of the corresponding Projectid using the 'fetch' method of the Project class.
            proj1 = Project()
            df = proj1.fetch(id=id_)
            duplicate_data = df[df.duplicated()]
            data = duplicate_data.to_html()

            # Insert record into ProjectReports table for Redirect To Handle Duplicate Data.
            ProjectReports.insert_record_dp(id_,'Redirect To Handle Duplicate Data!')

            # Check if the request method is POST.
            if request.method == "POST":
                # drop all duplicates.

                df = df.drop_duplicates(keep='last')

                # Update the data using the 'update_data' method.
                df = update_data(df)
                duplicate_data = df[df.duplicated()]
                data = duplicate_data.to_html()

                # Return the data along with the columns of the dataframe and the number of duplicates.
                return render(request, 'dataPreProcessing/handle_duplicates.html', 
                              {"columns": list(df.columns), "data": data, "duplicate_count": len(duplicate_data),"success":True})

            # Return the data along with the columns of the dataframe and the number of duplicates.            
            return render(request,'dataPreProcessing/handle_duplicates.html', {"columns":list(df.columns), "data":data,"duplicate_count":len(duplicate_data)})

        except Exception as e:
            return render(request,'dataPreProcessing/handle_duplicates.html', {"error":True,"msg":e.__str__()})
            
    def handle_missing_data(request):
        """
        The handle_missing_data function is a view function for the Data Preprocessing module of the project. It takes in a request object as an argument and performs the following operations:

        Fetch the project ID from the get_project_id table and retrieve the corresponding project information from the projects_info table.

        Update the project information with the value 'missings' for the ModuleUrl field.

        Create a Project object and fetch data based on the project ID.

        Call the missing_cells_table method from the EDA class to get the missing values dataframe.

        Drop columns if the missing values are greater than 90%.

        If the request method is POST and the proceedSubmit exists in the POST data, then retrieve the chosen NaN handling method, selected column, unique categories for the selected column, and NaN handling methods based on the data type of the selected column. Render the handle_missing.html template with the necessary data.

        If the request method is POST and the finalSubmit exists in the POST data, then retrieve the chosen NaN handling method and selected column. Apply the selected NaN handling method on the selected column and store the result in the dataframe.

        Call the update_data method to update the data in the dataframe. Add a success message to be displayed on the page and render the handle_missing.html template with the necessary data.

        Returns: A rendered template handle_missing.html with the necessary data.
        """
        try:
            # fetch project ID from the file 'get_project_id' table
            id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

            # update the project info with 'missings' value for ModuleUrl
            query_ = f"UPDATE projects_info set ModuleUrl='missings' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # create a Project object and fetch data based on the project ID
            proj1=Project()
            df=proj1.fetch(id=id_)

            # call the missing_cells_table method from the EDA class to get the missing values dataframe
            DataFrame=EDA.missing_cells_table(df)
            if DataFrame is not None:
                
                # loop through the missing values dataframe to drop columns if the missing values are greater than 90%
                for i in range(len(DataFrame)):
                    if DataFrame['Missing values (%)'][i]>90:
                        df.drop(columns=DataFrame['Column'][i],axis=1,inplace=True)
                    else:
                        continue


                # initialize lists to store the unique categories and nan handling methods
                unique_category = []
                nan_handler_methods = []

                # check if the request method is POST and proceedSubmit exists in the POST data
                if request.method=="POST" and 'proceedSubmit' in request.POST:
                    # retrieve the chosen nan handling method
                    method = request.POST.get('method')
                    # retrieve the selected column from the POST data
                    selected_column = request.POST.get('columns')
                    success = False
                    if len(DataFrame) > 0:
                        # get the unique categories for the selected column
                        unique_category = list(df[df[selected_column].notna()][selected_column].unique())
                        # determine the nan handling methods based on the data type of the selected column
                        if df[selected_column].dtype  == 'object':
                            nan_handler_methods = CATEGORIC_NAN_TYPES
                        else:
                            nan_handler_methods = NUMERIC_NAN_TYPES
                
                    # render the handle_missing.html template with the necessary data
                    return render(request,'dataPreProcessing/handle_missing.html', {"columns":df.columns[df.isna().any()].tolist(),"selected_column":selected_column, "success":success,"unique_category":unique_category,
                    "handler_methods":nan_handler_methods,"has_missing":True})
                
                # check if the request method is POST and finalSubmit exists in the POST data
                if request.method=="POST" and 'finalSubmit' in request.POST:
                    # retrieve the chosen nan handling method
                    method = request.POST.get('method')
                    # retrieve the selected column from the POST data
                    selected_column = request.POST.get('selected_column')
                
                    # apply the selected nan handling method on the selected column and store the result into the dataframe
                    if method == 'Mean':
                        df[selected_column] = Preprocessor.impute_nan_numerical(df, 'Mean', selected_column)
                    elif method == 'Median':
                        df[selected_column] = Preprocessor.impute_nan_numerical(df, 'Median', selected_column)
                    elif method == 'Specific Value':
                        df[selected_column] = Preprocessor.impute_nan_numerical(df, 'Specific Value', selected_column,
                                                                        request.POST.get('arbitrary'))
                    elif method == 'KNNImputer':
                        df[selected_column] = Preprocessor.impute_nan_numerical(df, 'KNNImputer', selected_column)
                    elif method == 'Mode':
                        df[selected_column] = Preprocessor.impute_nan_categorical(df, 'Mode', selected_column,value=None)
                    elif method == 'New Category':
                        df[selected_column] = Preprocessor.impute_nan_categorical(df, 'New Category', selected_column,
                                                                                        request.POST.get('newcategory'))
                    elif method == 'Replace':
                        df[selected_column] = Preprocessor.impute_nan_categorical(df, 'Replace', selected_column,
                                                                                            request.POST.get('selectcategory'))

                    # Call the update_data method to update the data in the dataframe
                    df = update_data(df)
                    success = True
                    columns = list(df.columns)
                    columns.remove(selected_column)

                    # Add a success message to be displayed on the page
                    messages.info(request,"Success! Missing Values Imputed Successfully")
                    # Redirect the user to the missings page
                    return redirect('missings')
            
                missing_df_to_html=[DataFrame.to_html(classes='data')]
                # Convert the dataframe to HTML and store it in a variable for rendering in the template
                return render(request,'dataPreProcessing/handle_missing.html', {"missing_values":missing_df_to_html, "has_missing":True,"columns":df.columns[df.isna().any()].tolist(),"handler_methods":ALL_NAN_TYPES})
                
            else:
                # If the dataframe does not contain any missing values, display a message to the user
                message="This dataset Contains no missing values"
                return render(request,'dataPreProcessing/handle_missing.html',{"has_missing":False,"msg":message})
        
        except Exception as e:
            return render(request,'dataPreProcessing/handle_missing.html', {"error":True,"msg":e.__str__()})


    def delete_columns(request):
        """
        Handles the deletion of columns in the data.
        :param request: The request object
        :return: Renders the 'delete_columns.html' template after deleting data
        """
        try:
            # retrieve the project ID
            id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
   
            # update the ModuleURL to "delete-cols"
            query_ = f"UPDATE projects_info set ModuleUrl='delete-cols' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # fetch the project data
            proj1=Project()
            df=proj1.fetch(id=id_)
            
            # record the status in the ProjectReports table
            ProjectReports.insert_record_dp(id_,'Redirect To Delete Columns!')

            if request.method=="POST":
                # retrieve the selected columns from the POST request data
                columns = request.POST.getlist('columns')
                
                # check if any columns have been selected
                if columns != '':
                    # delete the selected columns
                    df = Preprocessor.delete_cols(df, columns)
                    # update the data in the database
                    df = update_data(df)
                    return render(request,'dataPreProcessing/delete_columns.html', {'columns':list(df.columns),"status" : "success"})        
                
                else:
                    # return the delete column page with the flag "missing_vals_exists" set to False
                    return render(request,'dataPreProcessing/delete_columns.html', {'columns':list(df.columns)})        

            # return the delete column page with the list of columns with missing values
            return render(request,'dataPreProcessing/delete_columns.html', {"columns":list(df.columns)})

        except Exception as e:
            # return the delete column page with an error message
            return render(request,'dataPreProcessing/delete_columns.html', {"error":True,"msg":e.__str__()})

    def handle_inconsistent_data(request):
        """
        Handles the inconsistent values in the specified column of the data.
        :param request: The request object
        :return: Renders the 'handle_inconsistencies.html' template with inconsistencies removed
        """
        try:
            id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

            # fetch the project data
            proj1=Project()
            df=proj1.fetch(id=id_)

            num_cols,cat_cols=fetch_num_cat_cols(df)
            if request.method=="POST" and "check-data" in request.POST:
                selected_column=request.POST.get('column')
                min_value=request.POST.get('minimum_value')
                max_value=request.POST.get('maximum_value')
                message,dataframe=Preprocessor.clean_column(df,selected_column,int(min_value),int(max_value))
                return render(request,'dataPreProcessing/handle_inconsistencies.html', {"columns":num_cols,"data":dataframe.to_html(),"message":message,"select_min":min_value,"select_max":max_value,"select_col":selected_column})

            if request.method=="POST" and "save-data" in request.POST:
                selected_column=request.POST.get('selected-column')
                min_value=request.POST.get('selected-minimum-value')
                max_value=request.POST.get('selected-maximum-value')
                message,dataframe=Preprocessor.clean_column(df,selected_column,int(min_value),int(max_value))
                ProjectReports.insert_record_dp(id_,'Redirect To handle inconsistent data!',selected_column)

                update_data(dataframe)
                return render(request,'dataPreProcessing/handle_inconsistencies.html', {"columns":num_cols,"status":"success"})

            return render(request,'dataPreProcessing/handle_inconsistencies.html', {"columns":num_cols,"data":df.loc[:,num_cols].to_html()})
        
        except Exception as e:
            # return an error message
            return render(request,'dataPreProcessing/handle_inconsistencies.html', {"error":True,"msg":e.__str__()})


# Define a class named dataIntegration
class dataIntegration:
    """Class that contains various functions to perform data integration operations on the given dataset."""
    
    # Define a function for merging datasets
    def merging_function(request):
        try:
            # If a POST request with 'upload-data' is received, fetch the project data and upload the selected file
            if request.method=="POST" and 'upload-data' in request.POST:            
                id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

                # fetch the project data
                proj1=Project()
                df=proj1.fetch(id=id_)
                file=request.FILES['upload-files']
                merge_uploaded_file(file)
                
                # Check if the uploaded file exists and display it on the UI
                file_name2=sql_obj.fetch_one(f"""SELECT filename FROM file_data WHERE file_number = 3 ORDER BY id DESC LIMIT 1;""")[0]

                get_status,df1= check_file_exists(os.path.join(next(absoluteFilePaths('media')),'dataflow_uploads',file_name2))
                return render(request,'dataPreProcessing/integrate_datasets.html', {'integrate_functions':INTEGRATE_FUNCTIONS,"cols1":list(df.columns),"cols2":list(df1.columns),'is_loaded':get_status,"success":True})        

            # If a POST request with 'get-columns' is received, fetch the project data and perform data integration
            if request.method=="POST" and 'get-columns' in request.POST:
                id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

                proj1=Project()
                df=proj1.fetch(id=id_)
                
                file_name2=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 2 ORDER BY id DESC LIMIT 1;""")[0]

                # Check if the uploaded file exists and get the selected integrate function and columns
                get_status,df1= check_file_exists(os.path.join(next(absoluteFilePaths('media')),'dataflow_uploads',file_name2))
                selected_integrate_function=request.POST.get('select-integrate-function')
                selected_col1=request.POST.get('columns1')
                selected_col2=request.POST.get('columns2')

                # Perform the selected data integration function
                if selected_integrate_function=='merge':
                    data=Preprocessor.integrate_data_function(df,df1,selected_integrate_function,left_on=selected_col1,right_on=selected_col2)

                elif selected_integrate_function=='join':
                    data=Preprocessor.integrate_data_function(df,df1,selected_integrate_function,rsuffix='_')
                
                elif selected_integrate_function=='concat':
                    data=Preprocessor.integrate_data_function(df,df1,selected_integrate_function)

                # Convert the resulting data to HTML format and display it on the UI
                df_to_html=[data.to_html(classes='data')]
                ProjectReports.insert_record_dp(id_,'Perform data integration!',selected_integrate_function)

                # If a POST request with 'get-columns' is received, display the resulting data on the UI
                return render(request,'dataPreProcessing/integrate_datasets.html', {'integrate_functions':INTEGRATE_FUNCTIONS,"data":df_to_html,"success":True,"selected_function":selected_integrate_function,"selected_col_1":selected_col1,"selected_col_1":selected_col2})

            # If a POST request with 'save-data' is received, update the data and display a success message
            if request.method=="POST" and 'save-data' in request.POST:
                id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
                proj1=Project()
                df=proj1.fetch(id=id_)
                
                file_name2=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 2 ORDER BY id DESC LIMIT 1;""")[0]

                # Check if the uploaded file exists and get the selected integrate function and columns
                get_status,df1= check_file_exists(os.path.join(next(absoluteFilePaths('media')),'dataflow_uploads',file_name2))
                selected_integrate_function=request.POST.get('selected-integrate-function')
                selected_col1=request.POST.get('selected-columns1')
                selected_col2=request.POST.get('selected-columns2')

                # Perform the selected data integration function
                if selected_integrate_function=='merge':
                    data=Preprocessor.integrate_data_function(df,df1,selected_integrate_function,left_on=selected_col1,right_on=selected_col2)

                elif selected_integrate_function=='join':
                    data=Preprocessor.integrate_data_function(df,df1,selected_integrate_function,rsuffix='_')
                
                elif selected_integrate_function=='concat':
                    data=Preprocessor.integrate_data_function(df,df1,selected_integrate_function)

                update_data(data)
                return render(request,'dataPreProcessing/integrate_datasets.html', {'integrate_functions':INTEGRATE_FUNCTIONS,"success":True})

            # If no POST request is received, display the UI to select the integration function and columns
            return render(request,'dataPreProcessing/integrate_datasets.html', {'integrate_functions':INTEGRATE_FUNCTIONS})

        except Exception as e:
            # return the integrate_datasets page with an error message
            return render(request,'dataPreProcessing/integrate_datasets.html', {"error":True,"msg":e.__str__()})
    
class dataReduction:
    """Class that contains various functions to perform data reduction operations on the given dataset."""
    def dimensionality_reduction(request):
        """
        The function performs dimensionality reduction on the selected data. It first checks if the feature scaling has already been performed, if not it returns an error message.
        If the feature scaling has been performed, it then checks if the dimensionality reduction has already been performed, if it has then it returns an error message.
        If both feature scaling and dimensionality reduction haven't been performed, it then performs the dimensionality reduction based on the method selected and the number of components selected.

        Parameters:
        request (HttpRequest object): The request object that is used to handle the request made by the user.

        Returns:
        HttpResponse object: Returns a response with a status of success or error and other information needed to be displayed to the user.
        """

        # Get the ID of the current project
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        # Try to execute the following code block
        try:
            # Update the URL of the current project
            query_ = f"UPDATE projects_info set ModuleUrl='reducing' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Create a new Project object
            proj1=Project()
            # Fetch the data for the current project
            df=proj1.fetch(id=id_)
            # Get the target column of the current project
            target_=sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={id_}""")[0]

            # Check if the dimensionality reduction has already been performed
            query_ = f"Select * from Project_Actions  where ProjectId={id_} AND ProjectActionId=4"
            rows = sql_obj.fetch_all(query_)
            # If the dimensionality reduction has already been performed, return an error message
            if len(rows) > 0:
                return render(request,'dataPreProcessing/dimensionality.html',{"columns":[], "status":"error","not_allowed":True,"msg":"You Already Performed Dimensionalty Reduction. Don't do this again"})

            # Check if the feature scaling has been performed
            query_ = f"Select * from Project_Actions  where ProjectId={id_} AND ProjectActionId=3"
            rows = sql_obj.fetch_all(query_)
            # If the feature scaling has not been performed, return an error message
            if len(rows)==0:
                return render(request,'dataPreProcessing/dimensionality.html',{"columns":[], "status":"error","not_allowed":True,"msg":"Please Perform Feature Scaling First"})

            # If a target column has been set, create a new DataFrame with all columns except the target column
            if target_ !="None":
                columns = [col for col in df.columns if col != target_]
            df_ = df.loc[:, columns]
            # Store the first 5 rows of the DataFrame as an HTML table
            data = df.head(5).to_html()
            
            if request.method=="POST":
                # Get the number of PCA components to use
                no_pca_selected = request.POST.get('range')
                # Get the selected dimensionality reduction method
                method= request.POST.get('method')
                
                
                # If the method selected is TSNE or PCA, to perform dimensionality reduction
                df_,model=Preprocessor.dimension_reduction(df_, method,int(no_pca_selected))

                # Save the model
                save_project_pca(model)
                # Truncate the data frame to only include the selected number of PCA components
                df_ = df_[:, :int(no_pca_selected)]
                # Convert the reduced data to a pandas DataFrame
                data = pd.DataFrame(df_, columns=[f"Col_{col + 1}" for col in np.arange(0, df_.shape[1])])
                # If a target column was specified, add it back to the reduced data
                if target_ !="None":
                    data[target_] = df.loc[:, target_]
                # Update the data frame with the reduced data
                df = update_data(data)

                # Log the PCA action in the project reports
                ProjectReports.insert_project_action_report(id_,PROJECT_ACTIONS.get("PCA"),no_pca_selected)

                # Convert the data to HTML for display
                data = df.head(5).to_html()
                # Render the dimensionality reduction template with success status, HTML data, line plot, and dimensionality reduction methods
                return render(request,'dataPreProcessing/dimensionality.html', {"status":"success","data":data,"dimensionality_methods":DIMENSIONALITY_REDUCTION_TYPES })

            # Render the dimensionality reduction template with data, number of columns, and dimensionality reduction methods
            return render(request,'dataPreProcessing/dimensionality.html', {"data":data,"length":len(df_.columns),"dimensionality_methods":DIMENSIONALITY_REDUCTION_TYPES})
    
        except Exception as e:        
            return render(request,'dataPreProcessing/dimensionality.html', {"status":"error","msg":e.__str__()})


class dataTransformation:
    """Class that contains various functions to perform data transformation operations on the given dataset."""

    def rename_columns(request):
        """
        This function handles the POST request made by the user to rename the columns of a given dataframe.
        :param request: The POST request made by the user containing the selected column and the new column name.
        :return: A template with either a success message or an error message, and the updated list of columns in the dataframe.
        """
        try:
            # Fetch the project id from the get_project_id table
            id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

            # Update the ModuleUrl to "rename" in the projects_info table
            query_ = f"UPDATE projects_info set ModuleUrl='rename' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Create an instance of the Project class
            proj1=Project()
            # Fetch the dataframe for the given project id
            df=proj1.fetch(id=id_)

            if request.method=="POST":
                # Get the selected column and the new column name from the POST request
                selected_column = request.POST.get('selected_column')
                column_name = request.POST.get('column_name','')
                # Use the rename_columns method from the Preprocessor class to rename the selected column
                df = Preprocessor.rename_columns(df, selected_column, column_name.strip())
                # Update the data in the dataframe
                df = update_data(df)
                # Return a template with a success message and the updated list of columns
                return render(request,'dataPreProcessing/rename-cols.html',{"status":"success", "columns":list(df.columns)})
                    
            ProjectReports.insert_record_dp(id_,'Redirect To Change Column Name')
            return render(request,'dataPreProcessing/rename-cols.html',{"columns":list(df.columns)})
        except Exception as e:
             # Return a template with an error message and the list of columns in the dataframe
            return render(request,'dataPreProcessing/rename-cols.html',{"status":"error", "columns":list(df.columns),"msg":e.__str__()})

    def change_dtype(request):
        """
        The function is responsible for converting the data type of a selected column in the DataFrame.

        Arguments:
            request: HTTP request object, which contains the information about the request being made.

        Returns:
            render: A render function that returns the HTML template 'dataPreProcessing/change-dtypes.html' along with the status of the operation, the columns data types, the supported data types, the selected column name, and the changed data type.
        """
        # Fetch the project ID from the file 'get_project_id' table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Update the 'ModuleUrl' in the 'projects_info' table for the given project ID
            query_ = f"UPDATE projects_info set ModuleUrl='change-dtype' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Fetch the DataFrame for the given project ID
            proj1=Project()
            df=proj1.fetch(id=id_)
            
            # If there are missing values in the DataFrame, display a warning message and redirect to the missing values module
            if df.isnull().any().any()==True:
                messages.warning(request,"Please impute missing values first")
                return redirect('missings')
            
            # Get the numeric and categorical columns from the DataFrame
            num_cols,cat_cols=fetch_num_cat_cols(df)
            column_lists=list(df.columns)
            target_=sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={id_}""")[0]

            # If a target column is set, remove it from the list of columns to be displayed
            if target_ !="None":
                column_lists = [col for col in df.columns if col != target_]
            if request.method=="POST":
                try:
                    # Get the selected column and the new data type from the POST request
                    selected_column = request.POST.get('column','')
                    datatype = request.POST.get('datatype','')
                    ProjectReports.insert_record_dp(id_,'Change dtypes!',datatype)
                    
                    # If the selected column is a categorical column, clean the data and convert it to the specified data type
                    if selected_column in cat_cols:
                        df= Preprocessor.clean_data(df,selected_column)
                        data = Preprocessor.convert_dtype(df, selected_column, datatype)
                    
                    # Convert the selected column to the specified data type
                    data = Preprocessor.convert_dtype(df, selected_column, datatype)
                    df = update_data(data)
                    
                    # Return the HTML template with the status of the operation, the columns data types, the supported data types, the selected column name, and the changed data type
                    return render(request,'dataPreProcessing/change-dtypes.html',{"status":"success","columns":df.dtypes.apply(lambda x: x.name).to_dict().items(),"supported_dtypes":ALLOWED_DTYPES,"col_name":selected_column,"changed_dtype":datatype})
                
                except Exception as e:
                    return render(request,'dataPreProcessing/change-dtypes.html', {"supported_dtypes": ALLOWED_DTYPES,
                                                            "allowed_operation":"not",
                                                            "columns":df.loc[:, column_lists].dtypes.apply(lambda x: x.name).to_dict().items(),
                                                            "status":"error",
                                                            "msg":f'{e}'})
        

            ProjectReports.insert_record_dp(id_,'Redirect To Handle DataType')
            return render(request,'dataPreProcessing/change-dtypes.html',{"columns":df.loc[:, column_lists].dtypes.apply(lambda x: x.name).to_dict().items(),"supported_dtypes":ALLOWED_DTYPES})
            
        except Exception as e:
            return render(request,'dataPreProcessing/change-dtypes.html', {"supported_dtypes": ALLOWED_DTYPES,
                                                        "allowed_operation":"not",
                                                        "columns" :df.loc[:, column_lists].dtypes.apply(lambda x: x.name).to_dict(),
                                                        "status":"error",
                                                        "msg":f'{e}'})

    def handle_outliers(request):
        """
        This function is used to handle outliers in a given dataframe. 
        The function performs the following operations:
            1. Fetches the project id from the projects_info table using a SQL query.
            2. Updates the ModuleUrl in the projects_info table with "outliers".
            3. If there are missing values in the dataframe, displays a warning message.
            4. If the request method is POST and checkOutliers is in the request, it performs outlier detection using the selected method (either IQR or Z-Score).
            The function then creates a boxplot or distplot based on the selected method and creates a pie chart to show the count of unique outlier values.
            It also returns the unique outlier values and the count of outliers in the dataframe.
            5. If the request method is POST and removeOutliers is in the request, it removes the selected outlier values from the dataframe and updates the data.
            The function displays a success message after removing the outliers.
        """
        try:
             # fetch project id from database using sql query
            id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

            # update the project module URL in database
            query_ = f"UPDATE projects_info set ModuleUrl='outliers' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # create Project object and fetch the project data based on the id
            proj1 = Project()
            df = proj1.fetch(id=id_)

            # check if the data frame contains any missing values
            if df.isnull().any().any() == True:
                # display warning message if missing values are present
                messages.warning(request, "Please impute missing values first")
                # redirect to missing values handling page
                return redirect('missings')

            # insert a record in the ProjectReports table
            ProjectReports.insert_record_dp(id_,'Redirect To Handler Outlier!')
            # fetch the numerical and categorical columns from the data frame
            num_cols, cat_cols = fetch_num_cat_cols(df)

            # check if the request method is POST and the checkOutliers button is clicked
            if request.method == "POST" and "checkOutliers" in request.POST:
                # fetch the selected method and column from the POST request
                method = request.POST.get('method')
                column = request.POST.get('columns')

                # initialize the outliers list, graphJSON, and pie_graphJSON variables
                outliers_list = []
                graphJSON = ''
                pie_graphJSON = ''

                # check if the selected method is IQR
                if method == "iqr":
                    # detect outliers using the IQR method
                    result = EDA.outlier_detection_iqr(df.loc[:, [column]])
                    # check if any outliers are detected
                    if len(result) > 0:
                        # create boxplot for the selected column
                        graphJSON = Plotly_agent.boxplot_single(df, column)

                    # convert the result data frame to HTML
                    data = result.to_html()
                    # detect outliers using the list method
                    outliers_list = EDA.outlier_detection(list(df.loc[:, column]), 'iqr')

                # check if the selected method is Z-score
                elif method == "z-score":
                    # detect outliers using the Z-score method
                    result = EDA.z_score_outlier_detection(df.loc[:, [column]])
                    # convert the result data frame to HTML
                    data = result.to_html()
                    # detect outliers using the list method
                    outliers_list = EDA.outlier_detection(list(df.loc[:, column]), 'z-score')
                    # create a distribution plot for the selected column
                    graphJSON = Plotly_agent.create_distplot([outliers_list], [column])

                # create a data frame containing the outliers value counts
                df_outliers = pd.DataFrame(pd.Series(outliers_list).value_counts(), columns=['value']).reset_index(
                                    level=0)

                # if the length of dataframe is greater than 0 then plot a pieplot
                if len(df_outliers) > 0:
                    pie_graphJSON = Plotly_agent.plot_pieplot(df_outliers, names='index', values='value',
                                                                        title='Outlier Value Count')

                return render(request,'dataPreProcessing/handle_outliers.html', {'columns':num_cols, "method":method,"methods":OUTLIER_DETECT_METHODS, "selected_column":column,
                                                    "outliers_list":outliers_list, "unique_outliers":np.unique(outliers_list),
                                                    "pie_graphJSON":pie_graphJSON, "data":data,
                                                    "outliercount":result['Total outliers'][0] if len(
                                                        result['Total outliers']) > 0 else 0,
                                                    "graphJSON":graphJSON})        


            # Check if the request method is POST and "removeOutliers" is present in the POST data
            if request.method == "POST" and "removeOutliers" in request.POST:
                
                
                # Get the selected column from the POST data
                column = request.POST.get('selected_column')

                # Get the outlier values from the POST data as a list
                outlier_lists = request.POST.getlist('outlier-values','')
                
                # Convert the outlier values to either int or float based on whether they contain a decimal point or not
                outlier_vals = [ float(item) if "." in item else int(item) for item in outlier_lists ]
                
                # Call the remove_outliers method from Preprocessor and get the index of the outlier rows
                index_ = Preprocessor.remove_outliers(df, column, outlier_vals)
                
                # Drop the rows with outliers from the dataframe and reset the index
                updated_data = df.drop(index_, axis=0).reset_index(drop=True)
                
                # Update the data
                update_data(updated_data)

                # Add a success message to be displayed on the page
                messages.success(request,f'Congrats outliers removed from: {column}!')
                
                # Redirect the user to the 'outliers' page
                return redirect('outliers')
                        
            # Render the 'handle_outliers.html' template with the list of columns and the list of outlier detection methods
            return render(request,'dataPreProcessing/handle_outliers.html', {'columns':num_cols,"methods":OUTLIER_DETECT_METHODS})

        except Exception as e:
            return render(request,'dataPreProcessing/handle_outliers.html', {"error":True,"msg":e.__str__()})


    def data_splitter(request):
        """
        This function performs dataset spitting based on user set test size.
        It saves the splitted data as a numpy array in the artifacts for this project.

        Parameters:
        request (HttpRequest object): The HttpRequest object from Django

        Returns:
        HttpResponse object: The HttpResponse object with either return a success or an error message.

        """
        try:
             # fetch project id from database using sql query
            id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

            # update the ModuleUrl to 'split-data' in database
            query_ = f"UPDATE projects_info set ModuleUrl='split-data' where Projectid= {id_}"
            sql_obj.update_records(query_)
            
            if request.method=="POST": 
                proj1=Project()
                df=proj1.fetch(id=id_)
                target_col=sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={id_}""")[0]

                test_size=request.POST.get("select-thresh")
                X_train, X_test, y_train, y_test=Preprocessor.train_test_splitter(df.drop(columns=target_col).values,df[target_col].values,test_size=float(test_size),random_state=42)
                save_numpy_array(X_train, X_test, y_train, y_test)
    
                ProjectReports.insert_record_dp(id_,'Perform dataset splitting into train and test sets!',test_size)
                return render(request,'dataPreProcessing/train-test-splitter.html',{"success":True})
            return render(request,'dataPreProcessing/train-test-splitter.html')

        except Exception as e:
            return render(request,'dataPreProcessing/train-test-splitter.html', {"msg":e.__str__(),"error":True})
    
    def string_operations(request):
        """
        This function performs string operations on the selected columns in the dataframe.
        It updates the dataframe in the database and redirects to the page to show the updated dataframe.

        Parameters:
        request (HttpRequest object): The HttpRequest object from Django

        Returns:
        HttpResponse object: The HttpResponse object with either the updated dataframe or an error message.

        """
        try:
            # fetch project id from database using sql query
            id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
            # update the ModuleUrl to 'str-operation' in database
            query_ = f"UPDATE projects_info set ModuleUrl='str-operation' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # fetch data for the project
            proj1=Project()
            df=proj1.fetch(id=id_)
            
            # check for missing values
            if df.isnull().any().any()==True:
                messages.warning(request,"Please impute missing values first")
                return redirect('missings')

            # fetch numerical and categorical columns
            num_columns,cat_columns=fetch_num_cat_cols(df)
            eligible_cols=[]
            
            # find the eligible columns for string operations
            for i in df[cat_columns]:
                if len(df.loc[0,i].split())>2:
                    eligible_cols.append(i)

            if request.method=="POST":
                # perform string operation on selected column
                column_name=request.POST.get('columns')
                cleaned_dataframe=Preprocessor.perform_string_operations_(df,column_name)
                data=pd.concat([df,cleaned_dataframe],axis=1)
                final_df=update_data(data)
                # return the updated data frame
                return render(request,'dataPreProcessing/string_operator.html',{"data":final_df.sample(10).to_html()})

            if len(eligible_cols)>0:
                return render(request,'dataPreProcessing/string_operator.html',{"columns":eligible_cols,"isSuccess":True,"msg":"Success! updated dataframe successfully"})
                
            # if there are no eligible columns for string operations
            return render(request,'dataPreProcessing/string_operator.html',{"columns":eligible_cols,"allowed_operation":"not","msg":"This operation is not allowed for the components","isSuccess":False})

        except Exception as e:
            return render(request,'dataPreProcessing/string_operator.html', {"msg":e.__str__(),"isSuccess":False})


