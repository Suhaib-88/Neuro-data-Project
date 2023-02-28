from django.shortcuts import render,redirect
import pandas as pd
import numpy as np
from django.contrib import messages
# Create your views here.

# from dataProcessing.forms import GetTargetColumn
from dataProcessing.views import Project
from .functions_EDA.eda_operations import EDA, StatisticalDataAnalysis
from src.utils.plotlyFunctions import Plotly_agent
from src.utils.basicFunctions import fetch_num_cat_cols
from src.constants.const import GRAPH_TYPES_LIST, GRAPH_TYPES_LIST_2,SHOWDATA_FUNCTIONS,CORRELATION_METHODS,OUTLIER_DETECT_METHODS,STATISTICAL_FUNCTIONS
from django.shortcuts import render
import numpy as np
from django.views import View
from .models import TaskType, plot_Data
import matplotlib.pyplot as plt
import plotly
import json
import plotly.figure_factory as ff
from src.utils.projectReports import ProjectReports
from data_access.mysql_connect import MySql
from src.utils.basicFunctions import read_configure_file,absoluteFilePaths

from logger import logging
import sys

config_args= read_configure_file("config.yaml")
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)


class EDA_missing(View):
    """
    Class Based View to handle the logic for the Missing values section of Exploratory Data Analysis.
    """
    def get(self,request):
        """
        Handles the GET request to the EDA_missing view.
        
        Retrieves the current project id from the "get_project_id" table, updates the corresponding project in the projects_info 
        table with the ModuleUrl field set to "missing". Then it fetches the project data using the "fetch" method 
        of the Project class. 
        It calculates the missing values table using the "missing_cells_table" method of the EDA 
        class and generates a bar graph of the missing values using the "plot_barplot" method of the Plotly_agent class. 
        
        If the missing values table is not None, the matrix of the data is plotted using the "matrix" method of the msno 
        library, saved as a png file, and moved to the "static/images" folder. The missing values table is converted to 
        HTML using the "to_html" method and inserted into a list. The record of the current step is inserted into the 
        ProjectReports table using the "insert_record_eda" method.
        
        Finally, the view is rendered using the "eda-missing.html" template, passing the missing values table, the bar graph JSON, and the flag indicating if 
        there are missing values or not. 

        If the missing values table is None, a message is passed indicating that the dataset does not contain missing values.
        
        Raises:
            Renders error message: If an exception occurs while executing the logic, the exception message is raised wrapped 
            in the template.
        """
        # retrieve the current project id from the "get_project_id" table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # update the projects_info table with the ModuleUrl field set to "missing"
            query_ = f"UPDATE projects_info set ModuleUrl='missing' where Projectid= {id_}"
            sql_obj.update_records(query_)
            
            # fetch the project data
            proj1=Project()
            df=proj1.fetch(id=id_)
            # calculate the missing values table
            dataframe=EDA.missing_cells_table(df)

            # if dataframe is not empty then perform following functions
            if dataframe is not None:
                # generate a bar graph of the missing values
                bar_graphJSON = Plotly_agent.plot_barplot(dataframe,x='Column', y='Missing values')
                # plot the matrix of the data

                # generate the matrix plot
                missing_df_to_html=[dataframe.to_html(classes='data')]
                # insert the record of the
                
                ProjectReports.insert_record_eda('Redirect To Missing Value')
                return render(request,'EDA/eda-missing.html',{"missing_values":missing_df_to_html, "has_missing":True,"barchart":bar_graphJSON})
            
            # else if dataframe is empty then render message
            else:
                message="This dataset Contains no missing values"
                return render(request,'EDA/eda-missing.html',{"has_missing":False,"msg":message})
        
        except Exception as e:
            logging.error(e)
            return render(request,'EDA/eda-missing.html',{"error":True,"msg":e.__str__()})


class EDA_summary(View):
    def get(self,request):
        """
        This method handles GET request for the EDA summary page. 
        It retrieves the project id from the 'get_project_id' table and updates the module URL in the `projects_info` table. 
        Then, it retrieves the data for the project from the database and performs data summary and data type information operations using the `EDA` class. 
        The resulting data is then passed to the template to display. 
        If an exception is encountered, it renders a `CustomException` with the exception message.

        Returns:
            render: A render object for the EDA summary page with the data summary and data type information.
        """
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
        try:
            # Update the module URL in the `projects_info` table
            query_ = f"UPDATE projects_info set ModuleUrl='summary' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Fetch the data for the project
            proj1 = Project()
            df = proj1.fetch(id=id_)

            # Perform data summary and data type information operations
            dataSummary = EDA.get_data_summary(df)
            dataTypeInfo = EDA.dataType_info(df)

            # Convert the data frames to HTML for display in the template
            summary_to_html = [dataSummary.to_html(classes='data')]
            dtypes_to_html = [dataTypeInfo.to_html(classes='data')]

            # Insert a record for the EDA summary operation
            ProjectReports.insert_record_eda('Redirect To Data Summary')

            # Render the EDA summary page with the data summary and data type information
            return render(request, 'EDA/eda-summary.html', {"table_summary": summary_to_html, "data_types": dtypes_to_html, 'row_count': len(df), 'column_count': len(list(df.columns))})        

        except Exception as e:
            logging.error(e)

            # renders a custom exception with the exception message
            return render(request,'EDA/eda-summary.html',{"error":True,"msg":e.__str__()})



class EDA_showDataset(View):
    """
    Class to handle the display of the dataset on the web page

    """
    def get(self, request):
        """
        Handles the GET request for displaying the dataset
        """
        # Fetch the project id from the 'get_project_id' table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Update the module URL in the database to 'show-dataset'
            query_ = f"UPDATE projects_info set ModuleUrl='show-dataset' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Get the dataframe for the selected project
            proj1 = Project()
            df = proj1.fetch(id=int(id_))
            cols = df.columns

            # Record the redirect to show dataset in the ProjectReports
            ProjectReports.insert_record_eda('Redirect To Show Dataset')

            # Render the EDA/eda-showdata.html template with the length of the dataframe, showOrder and columns as parameters
            return render(request, 'EDA/eda-showdata.html', {"length": len(df), "showOrder": SHOWDATA_FUNCTIONS, "columns": cols})

        except Exception as e:
            logging.error(e)
            # Raise a custom exception if an error occurs
            return render(request,'EDA/eda-showdata.html',{"error":True,"msg":e.__str__()})

    def post(self, request):
        """
        Handles the POST request for displaying the dataset
        """
        # Fetch the project id from the 'get_project_id' table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Get the dataframe for the selected project
            proj1 = Project()
            df = proj1.fetch(id=id_)

            # Get the selected columns, number of rows and the order selected from the form data
            selected_choice = request.POST.getlist('column', '')
            no_of_rows = request.POST.get('range', '')
            order_selected = request.POST.get('order-select', '')

            # Record the show action in the ProjectReports with the number of rows as input
            ProjectReports.insert_record_eda('Show', input=no_of_rows)

            if selected_choice != '':
                # Get the specified number of records from the selected columns in the specified order
                data = EDA.get_no_records(df[selected_choice], count=int(no_of_rows), order_by=order_selected)

                # Convert the data to HTML
                data_to_html = [data.to_html(classes='data')]

                # Render the EDA/eda-showdata.html template with the data, length of the dataframe, showOrder, number of rows and columns as parameters
                return render(request,'EDA/eda-showdata.html',{"data":data_to_html,"length":len(df),"showOrder":SHOWDATA_FUNCTIONS,"number_of_rows":no_of_rows,"columns":df.columns})

        except Exception as e:
            logging.error(e)

            return render(request,'EDA/eda-showdata.html',{"error":True,"msg":e.__str__()})


class EDA_correlation(View):
    """
    This class is a view for correlation analysis of the data in a project. It is responsible for handling both the GET and POST requests and rendering the result.
    """
    def get(self,request):
        """
        This method handles the GET request. It retrieves the project ID, updates the Module URL in the database, and fetches the data for the project.
        It then gets the numerical and categorical columns in the data, and renders the EDA-correlation template.

        :param request: GET request
        :return: rendered EDA-correlation template with the list of numerical columns
        """
        # fetching the project id from a table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # updating the module URL in the database
            query_ = f"UPDATE projects_info set ModuleUrl='corr-heatmap' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # fetching the project data
            proj1=Project()
            df=proj1.fetch(id=id_)

            # insert record for redirecting to correlation
            ProjectReports.insert_record_eda('Redirect To Correlation')
            
            # fetching numerical and categorical columns
            num_cols,cat_cols= fetch_num_cat_cols(df)
            # render the HTML template with numerical columns and correlation methods
            return render(request,'EDA/eda-correlation.html',{"columns":num_cols,"corr_methods":CORRELATION_METHODS})

        except Exception as e:
            # logging the error
            logging.error(e)
            # raising a custom exception
            return render(request,'EDA/eda-correlation.html',{"error":True,"msg":e.__str__()})

    def post(self,request):
        """
        This method handles the POST request. It retrieves the project ID, fetches the data for the project, gets the numerical and categorical columns in the data,
        retrieves the selected columns and correlation method from the request, and generates a correlation heatmap using Plotly.

        :param request: POST request
        :return: rendered EDA-correlation template with the correlation heatmap plot
        """

        # fetching the project id from a table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # fetching the project data
            proj1=Project()
            df=proj1.fetch(id=id_)
            # fetching numerical and categorical columns
            num_cols,cat_cols= fetch_num_cat_cols(df)

            # getting the selected columns from the form
            col_selected=request.POST.getlist('column','')
            # getting the selected correlation method from the form
            method_selected=request.POST.get('method','')

            # insert record for redirecting to correlation with the selected method
            ProjectReports.insert_record_eda('Redirect To Correlation', input=method_selected)

            if method_selected is not None :
                # generate the correlation matrix
                correlation_matrix=EDA.correlation_report(df,method_selected)
                if len(col_selected) == 0:
                    col_selected = correlation_matrix.columns

                # selecting the specified columns in the correlation matrix
                _corr = correlation_matrix.loc[:, col_selected]
                # converting the correlation matrix to a 2-dimensional list
                _data = list(np.around(np.array(_corr.values), 2))
                # creating an annotated heatmap from the data
                fig = ff.create_annotated_heatmap(_data, x=list(_corr.columns),
                                                            y=list(_corr.index), colorscale='Viridis')
                # converting the figure to a JSON object
                graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

                # render the HTML template with heatmap graph,numerical columns and correlation methods
                return render(request,'EDA/eda-correlation.html',{"data":graphJSON, "columns":num_cols,"method":method_selected,"corr_methods":CORRELATION_METHODS})
            else:
                # render the HTML template with message
                return render(request,'EDA/eda-correlation.html',{"msg":"Selected Method is invalid"})
        
        except Exception as e:
            logging.error(e)
            return render(request,'EDA/eda-correlation.html',{"error":True,"msg":e.__str__()})


class EDA_higly_correlated(View):
    """
    Class to implement the view for the highly correlated features in the EDA module

    This class implements the get and post methods to display the high correlation matrix based on the threshold selected by the user.

    """

    def get(self,request):    
        """
        Returns the template for the high correlation feature view

        Parameters
        ----------
        request : HttpRequest
            The incoming request object

        Returns
        -------
        HttpResponse
            The rendered template for the high correlation feature view
        """
        return render(request,'EDA/eda-high-corr.html')

    def post(self,request):
        """
        Updates the ModuleUrl in the projects_info table for the project, calls the fetch method from Project class to retrieve the project data, calls the high_correlation_matrix method from EDA class to retrieve the highly correlated columns based on the threshold, inserts the record of the redirect to the highly correlated feature view, and returns the template with the highly correlated columns and threshold

        Parameters
        ----------
        request : HttpRequest
            The incoming request object

        Returns
        -------
        HttpResponse
            The rendered template with the highly correlated columns and threshold

        Raises
        ------
        CustomException
            If an error occurs, the exception is logged and raised to display the error message.
        """
        # Fetch the project ID
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Update the ModuleUrl in the projects_info table
            query_ = f"UPDATE projects_info set ModuleUrl='corr-cols' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Call the fetch method from Project class
            proj1=Project()
            df=proj1.fetch(id=id_)

            # Get the threshold from the request
            threshold= request.POST.get('select-thresh','')

            # Call the high_correlation_matrix method from EDA class
            highly_correlated_cols=EDA.high_correlation_matrix(df,float(threshold))

            # Insert the record of the redirect to the highly correlated feature view
            ProjectReports.insert_record_eda('Redirect To highly correlated features', input=threshold)

            if highly_correlated_cols != set():
                # Return the template with the highly correlated columns and threshold
                return render(request,'EDA/eda-high-corr.html',{ "thresh":threshold,"Exists":True,"output_corr":highly_correlated_cols})
                
            # Return the template with the no correlated columns found
            return render(request,'EDA/eda-high-corr.html',{"thresh":threshold,"Exists":False,"msg":"No correlated column matches this threshold"})

        except Exception as e:
            logging.error(e)
            return render(request,'EDA/eda-high-corr.html',{"error":True,"msg":e.__str__()})



class EDA_outliers(View):
    """
    The EDA_outliers class is a View that displays the outlier detection page and processes the user's input to detect outliers in the dataset.

    It contains two methods: `get` and `post`. 
    """
    def get(self,request):
        """
        This method is called when an HTTP GET request is made to the EDA/eda-outlier.html page.

        Returns:
            A render of the EDA/eda-outlier.html page with the list of outlier detection methods.
        """
        context={"methods":OUTLIER_DETECT_METHODS}
        return render(request,'EDA/eda-outlier.html',context)

    def post(self,request):
        """
        This method is called when an HTTP POST request is made to the EDA/eda-outlier.html page.

        It processes the user's input to detect outliers in the dataset using either the Z-score method or the Interquartile Range (IQR) method. The method then updates the module URL in the projects_info table and logs the user's input in the project reports table. Finally, it returns the EDA/eda-outlier.html page with the outlier detection results plotted in a bar chart and pie chart.

        Returns:
            A render of the EDA/eda-outlier.html page with the outlier detection results plotted in a bar chart and pie chart.

        Raises:
            CustomException: An error message is raised if there is an error during the outlier detection process.
        """
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Update the module URL in the projects_info table
            query_ = f"UPDATE projects_info set ModuleUrl='outlier' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Fetch the data for the selected project
            proj1 = Project()
            df = proj1.fetch(id=id_)

            # Get the selected outlier detection method from the user's input
            selected_outlier_method = request.POST.get('outlier-method', '')

            # Log the user's input in the project reports table
            ProjectReports.insert_record_eda('Redirect To Outlier', input=selected_outlier_method)

            # Detect outliers using the Z-score method or the Interquartile Range (IQR) method
            if selected_outlier_method == 'z-score':
                # creating outlier report for z-score
                df = EDA.z_score_outlier_detection(df)

                # creating an barplot from the data
                graphJSON = Plotly_agent.plot_barplot(df,x='Features', y='Total outliers')
                # creating an pieplot from the data
                pie_graphJSON = Plotly_agent.plot_pieplot(df.sort_values(by='Total outliers', ascending=False).loc[: 10 if len(df) > 10 else len(df)-1, :],names='Features', values='Total outliers', title='Top 10 Outliers')
                
                # Convert the outlier data to HTML
                outlier_to_html=[df.to_html(classes='data')]
                context={"method":selected_outlier_method,"methods":OUTLIER_DETECT_METHODS,"barplot":graphJSON, "pieplot":pie_graphJSON,"outliers":outlier_to_html}
                return render(request,'EDA/eda-outlier.html',context)
            
            else:
                # creating outlier report for iqr
                df= EDA.outlier_detection_iqr(df)

                # creating an barplot from the data
                graphJSON = Plotly_agent.plot_barplot(df,x='Features', y='Total outliers')
                # creating an pieplot from the data
                pie_graphJSON = Plotly_agent.plot_pieplot(df.sort_values(by='Total outliers', ascending=False).loc[:10 if len(df) > 10 else len(df)-1, :],names='Features', values='Total outliers', title='Top 10 Outliers')
                

                # Convert the outlier data to HTML
                outlier_to_html=[df.to_html(classes='data')]
                context={"method":selected_outlier_method,"methods":OUTLIER_DETECT_METHODS,"barplot":graphJSON, "pieplot":pie_graphJSON,"outliers":outlier_to_html}
                return render(request,'EDA/eda-outlier.html',context)
        
        except Exception as e:
            logging.error(e)
            return render(request,'EDA/eda-outlier.html',{"error":True,"msg":e.__str__()})


class EDA_statistical_functions(View):
    """
    Class view for performing statistical analysis on a dataset as part of exploratory data analysis (EDA).
        get(self, request):
        Renders the EDA statistical analysis page and checks if the dataset contains categorical or missing data.

    post(self, request):
        Updates the ModuleUrl in the projects_info table to 'statistics' for the current project.
        Performs the selected statistical analysis method on the dataset and returns the resulting dataset.
        Renders selected method for customized info
    """
    def get(self,request):
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
        # Call the fetch method from Project class
        proj1=Project()
        df=proj1.fetch(id=id_)

        if len(df.columns[df.dtypes == 'float']) < 0 or len(df.columns[df.dtypes == 'int']) < 0:    
            return render(request,'EDA/eda-statistical.html',{"allowed_operation":"not", "status":"error","msg":"Statistical Operations can't be performed at this point, data does not contain any numerical data!"})

        context={"methods":STATISTICAL_FUNCTIONS}
        return render(request,'EDA/eda-statistical.html',context)


    def post(self,request):
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Update the ModuleUrl in the projects_info table
            query_ = f"UPDATE projects_info set ModuleUrl='statistics' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Call the fetch method from Project class
            proj1=Project()
            df=proj1.fetch(id=id_)
            num_cols,cat_cols=fetch_num_cat_cols(df)
            df=df.loc[:,num_cols]
            
            select_method=request.POST.get('select-stats-method')
            applied_dataframe = StatisticalDataAnalysis(df)
            if select_method=="Window":
                window_size=request.POST.get('windowsize-norm')
                # Choose a function to perform and provide any necessary arguments
                dataframe=applied_dataframe.choose_statistical_function(select_method, window_size=int(window_size)).mean()

            elif select_method=="Expanding":
                # Choose a function to perform and provide any necessary arguments
                dataframe=applied_dataframe.choose_statistical_function(select_method).sum()
            
            elif select_method=="Rolling":
                window_size=request.POST.get('windowsize-roll')
                # Choose a function to perform and provide any necessary arguments
                dataframe=applied_dataframe.choose_statistical_function(select_method, window_size=int(window_size)).std()

            elif select_method=="Percentage change":
                # Choose a function to perform and provide any necessary arguments
                dataframe=applied_dataframe.choose_statistical_function(select_method)


            elif select_method=="Covariance":
                # Choose a function to perform and provide any necessary arguments
                dataframe=applied_dataframe.choose_statistical_function(select_method)

            elif select_method=="Covariance":
                # Choose a function to perform and provide any necessary arguments
                dataframe=applied_dataframe.choose_statistical_function(select_method)

            elif select_method=="Ranking":
                # Choose a function to perform and provide any necessary arguments
                dataframe=applied_dataframe.choose_statistical_function(select_method)

            context={"selected_method":select_method,"data":dataframe.to_html(),"methods":STATISTICAL_FUNCTIONS}
            return render(request,'EDA/eda-statistical.html',context)

        except Exception as e:
            logging.error(e)


def plot_helper(request):    
    task_type_=request.GET.get('tasker')

    type_chart=plot_Data.objects.filter(task_type=task_type_)
    return render(request,'partials/charttype.html',{"charts":type_chart})

class EDA_plots(View):
    """
    The EDA_plots class is a view that generates and displays various EDA plots for a project.

    Methods:
    `get` and `post`
    """
    def get(self,request):
        '''
        This method is called when a GET request is made to the view.
        
        -It fetches the current project ID and updates the project's module URL to 'plots'. 
       
        -It then retrieves the project's data and the different tasks available,
        and calls the fetch_num_cat_cols function to get the numerical and categorical columns in the data.
        
        -It then inserts a record of the EDA plot in the ProjectReports table 
        and finally returns a rendered HTML template with the columns and numerical columns in the data as context. 
        
        -If an error occurs, it logs the error and raises a CustomException.
        '''
        # Retrieve the project ID from the 'get_project_id' table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
        try:
            # Update the module URL in the projects_info table to 'plots'
            query_ = f"UPDATE projects_info set ModuleUrl='plots' where Projectid= {id_}"
            sql_obj.update_records(query_)

            # Create an instance of the Project class
            proj1 = Project()
            # Fetch the data for the project with the specified ID
            df = proj1.fetch(id=id_)

            # Get all the task types from the TaskType model
            tasks = TaskType.objects.all()
            # Get the numerical and categorical columns from the dataframe
            num_cols, cat_cols = fetch_num_cat_cols(df)
            
            # Insert a record in the ProjectReports table for the 'Plots' page
            ProjectReports.insert_record_eda('Plots')

            # Render the EDA/eda-plots.html template and pass the data to the template
            return render(request,'EDA/eda-plots.html',{ "columns":list(df.columns), "x_list":list(df.columns),"y_list":num_cols,'tasks':tasks})
        
        except Exception as e:
            # log error
            logging.error(e)

            return render(request,'EDA/eda-plots.html',{"error":True,"msg":e.__str__()})

    def post(self,request):
        '''
         This method is called when a POST request is made to the view. 
         It fetches the current project ID and retrieves the project's data,
          and the numerical and categorical columns in the data. 
        It then retrieves the selected graph type from the POST request and sets the selected graph type as a string.
        For example:If the selected graph type is 'scatterplot', it retrieves the x-column and y-column from the POST request.
        '''
        # Retrieve the project ID from the 'get_project_id' table
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        try:
            # Create an instance of the Project class
            proj1 = Project()
            # Fetch the data for the project with the specified ID
            df = proj1.fetch(id=id_)

            # Get the numerical and categorical columns from the dataframe
            num_cols, cat_cols = fetch_num_cat_cols(df)
            # Get all the task types from the TaskType model
            tasks = TaskType.objects.all()
            
            # Get the target column from the projects_info table
            target_ = sql_obj.fetch_one(f"""SELECT SetTarget FROM projects_info WHERE Projectid={id_}""")[0]
    
            # Get the selected graph method from the POST request data
            get_by_id = request.POST.get('graph-method','')
            # Get the plot data object with the specified ID
            plot_data_object = plot_Data.objects.get(pk=get_by_id) 
    
            # Get the string representation of the selected graph method
            selected_graph_type=plot_data_object.__str__()

            # Check which type of graph was selected
            if selected_graph_type == "scatterplot":
                # Get the x and y columns for the scatter plot from the POST request data
                x_column = request.POST.get('scatter-xcolumn','')
                y_column = request.POST.get('scatter-ycolumn','')
                # Check if there is a target column specified
                if target_ !="None":
                    # Create a scatter plot with the target column for coloring
                    graphJSON = Plotly_agent.plot_scatterplot(df, x=x_column, y=y_column, title='Scatter Plot with target',color=target_)
                    # Render the EDA/eda-plots.html template with the scatter plot and other information
                    return render(request,'EDA/eda-plots.html', {'tasks':tasks,"selected_graph_type":selected_graph_type,"columns":list(df.columns),"x_list":list(df.columns),"y_list":num_cols,"graphJSON":graphJSON})
                # Create a scatter plot without a target column
                graphJSON = Plotly_agent.plot_scatterplot(df, x=x_column, y=y_column, title='Scatter Plot')
            
            elif selected_graph_type == "pieplot":
                # Get the x column for the pie plot from the POST request data
                x_column = request.POST.get('pieplot-xcolumn')
                # Group the data by the x column
                new_df = df.groupby(x_column).count()
                # Create a temporary DataFrame to store the values for the pie plot
                temp_df = pd.DataFrame()
                temp_df[x_column] = list(new_df.index)
                temp_df['Count'] = list(new_df.iloc[:, 0])
                # Create the pie plot
                graphJSON = Plotly_agent.plot_pieplot(temp_df, names=x_column, values='Count', title='Pie Chart')
            
            elif selected_graph_type == "barplot":
                # Get the x column for the bar plot from the POST request data
                x_column = request.POST.get('barplot-xcolumn')
                # Group the data by the x column
                new_df = df.groupby(x_column).count()
                # Create a temporary DataFrame to store the values for the bar plot
                temp_df = pd.DataFrame()
                temp_df[x_column] = list(new_df.index)
                temp_df['Count'] = list(new_df.iloc[:, 0])
                # Call the function to create the bar plot with the x and y values
                graphJSON = Plotly_agent.plot_barplot(temp_df,x=x_column, y='Count')

            elif selected_graph_type == "distplot":
                # Get the x and y columns for the distplot from the POST request data
                x_column = request.POST.get('distplot-xcolumn')
                y_column = request.POST.get('distplot-ycolumn')
                # Check if there is a target column specified
                if target_ !="None":
                    # Create a distplot with the target column for coloring
                    graphJSON = Plotly_agent.plot_distplot(df, x=x_column, y=y_column,color=target_,nbins=30, histnorm='density', barmode='overlay')
                    # Render the EDA/eda-plots.html template with the scatter plot and other information
                    return render(request,'EDA/eda-plots.html', {'tasks':tasks,"selected_graph_type":selected_graph_type,"columns":list(df.columns),"x_list":list(df.columns),"y_list":num_cols,"graphJSON":graphJSON})
                
                
                # Call the function to create the distplot with the data and categories
                graphJSON = Plotly_agent.plot_distplot(df,x=x_column,y=y_column,nbins=30, histnorm='density', barmode='overlay')

            elif selected_graph_type == "histogram":
                # Get the x column for the histogram from the POST request data
                x_column = request.POST.get('histo-xcolumn')
                # Call the function to create the histogram with the x values
                graphJSON = Plotly_agent.plot_histogram(df, x=x_column)

            elif selected_graph_type == "lineplot":
                # Get the x and y columns for the line plot from the POST request data
                x_column = request.POST.get('line-xcolumn')
                y_column = request.POST.get('line-xcolumn')
                # Call the function to create the line plot with the x and y values
                graphJSON = Plotly_agent.plot_lineplot(df, x=x_column, y=y_column)

            elif selected_graph_type == "violinplot":
                # Get the y column for the violin plot from the POST request data
                y_column = request.POST.get('violinplot-ycolumn')
                # Call the function to create the violin plot with the y values
                graphJSON = Plotly_agent.plot_violinplot(df, y=y_column)

            elif selected_graph_type == "boxplot":
                # Get the x and y columns for the box plot from the POST request data
                x_column = request.POST.get('boxplot-xcolumn')
                y_column = request.POST.get('boxplot-ycolumn')
                # Call the function to create the box plot with the x and y values
                graphJSON = Plotly_agent.plot_boxplot(df, x=x_column, y=y_column)

            elif selected_graph_type == "heatmap":
                # Call the function to create a heatmap
                graphJSON = Plotly_agent.show_heatmap(df)
                
                
            elif selected_graph_type == "pairplot":
                # Call the function to create a pairplot
                if target_ !="None":
                    graphJSON = Plotly_agent.plot_pairplot(df,dimensions=list(df.drop(target_,axis=1).columns),color=target_)
                    return render(request,'EDA/eda-plots.html', {'tasks':tasks,"selected_graph_type":selected_graph_type,"columns":list(df.columns),"x_list":list(df.columns),"y_list":num_cols,"graphJSON":graphJSON})
                graphJSON = Plotly_agent.plot_pairplot(df)
            
            else:
                # If the selected graph type is not found, return an error message
                error_message = "The selected graph type is not supported."
                return render(request,'EDA/eda-plots.html', {'tasks':tasks,"error_message":error_message})
            

            ProjectReports.insert_record_eda('Redirect to Plot', input=selected_graph_type)
                        
            return render(request,'EDA/eda-plots.html', {'tasks':tasks,"selected_graph_type":selected_graph_type,"columns":list(df.columns),"x_list":list(df.columns),"y_list":num_cols,"graphJSON":graphJSON})

        
        except plot_Data.DoesNotExist:
            # If the specified plot data object does not exist, return an error message
            error_message = "The specified plot data object does not exist."
            return render(request,'EDA/eda-plots.html', {'tasks':tasks,"error":error_message})
        
        except Exception as e:
            #log error 
            logging.error(e)            
            return render(request,'EDA/eda-plots.html',{"error":True,"msg":e.__str__()})
