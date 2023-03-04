from django.shortcuts import render,redirect
from django.views.generic.list import ListView
from django.views import View
from.models import DataFlowComponent,UserComponents
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,HttpResponseRedirect
from django.contrib import messages
from logger import logging
from .dataflows_Functions.dataflow_helper import dataSource
from .dataflows_Functions.dataflow_helper import commonTasks,otherTransformations
import pandas as pd
import os,zipfile,pathlib,io,csv
import numpy as np
from src.constants.const import *
from src.utils.basicFunctions import fetch_num_cat_cols,get_latest_file,check_file_exists,absoluteFilePaths
from from_root import from_root

from src.utils.basicFunctions import read_configure_file
from data_access.mysql_connect import MySql


config_args= read_configure_file("config.yaml")
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)



# Create your views here.
class ComponentsList(LoginRequiredMixin,ListView):
    template_name='DF_Components/components.html'
    model=DataFlowComponent
    context_object_name="components"

    def get_queryset(self):
        """
        Returns a queryset of all User Components associated with the current user.
        """
        return UserComponents.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        """
        Adds additional context data to be passed to the template.
        """
        file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
        file_name2=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 2 ORDER BY id DESC LIMIT 1;""")[0]

        # Get the path of the uploaded file
        path=os.path.join(next(absoluteFilePaths('media')),'dataflow_uploads',file_name)
        path2=os.path.join(next(absoluteFilePaths('media')),'dataflow_uploads',file_name2)
        
        context = super().get_context_data(*args, **kwargs)

        # Read the uploaded file as a Pandas DataFrame
        status,df=check_file_exists(path)
        status,df2=check_file_exists(path2)

        context['columns'] = list(df.columns)
        context['columns2']= list(df2.columns)

        # Get the numerical and categorical columns in the DataFrame
        num_cols,cat_cols=fetch_num_cat_cols(df)
        context['num_columns'] = list(num_cols)
        context['cat_columns'] = list(cat_cols)

        # Add the various options for components, operations, etc. to the context
        context['aggregate_functions']=AGG_FUNCTIONS
        context['operations'] = OPERATIONS
        context['dtypes'] = DTYPES
        context['conditions'] = CONDITIONS
        context['methods'] = FILE_METHODS
        context['join_methods'] = MODES
        context['casing_methods']=CASING
        context['operation_functions']=OPERATIONS_PIVOT
        return context

    def post(self,request):
        """
        Handles a POST request and saves the selected components.
        The code checks which component id is present in the list `component_ids`.
        Depending on the component id, different functions are being called from `otherTransformations` and `commonTasks` modules.
        The result of these functions is stored in the `status` variable.
        If the status is "success", a success message is displayed using the `messages.success` method.
        # The modified dataframe is then saved to the path specified.
        """
        if request.method == "POST" and "save-all" in request.POST:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            component_ids=request.POST.getlist('component_ids')
            path=os.path.join(next(absoluteFilePaths('media')),'dataflow_uploads',file_name)

            # Check if "35" exists in the list of selected component ids
            if "35" in component_ids:
                # Get the database uri from the request POST data
                db_engine_url=request.POST.get("db-uri")
                
                # Get the table name from the request POST data
                table_name=request.POST.get("table-name1")
                # If the import is successful
                status=dataSource.import_database(db_engine_url,table_name)
                if status=='success':
                    # Add a success message to the request object
                    messages.success(request,"Successfully Imported data via Database")
            

            # Check if "36" exists in the list of selected component ids
            if "36" in component_ids:
                # Get the file from the request POST data
                file=request.FILES.get('upload-file')
                status=dataSource.handle_uploaded_file(file)
                # If the import is successful
                if status=='success':
                    # Add a success message to the request object
                    messages.success(request,"Successfully Imported data via file upload")


            # Check if "37" exists in the list of selected component ids
            if "37" in component_ids:
                # Get the URL of the uploaded cloud file from the request POST data
                s3endpoint_url = request.POST.get("upload-cloud")
                # Get the table name from the request POST data
                table_name = request.POST.get("table-name2") 
                # Call the import_cloud function with the given s3endpoint_url and table_name
                status = dataSource.import_cloud(s3endpoint_url, table_name)
                # If the import is successful
                if status == 'success':
                    # Add a success message to the request object
                    messages.success(request, "Successfully Imported data via cloud")

            # Check if "38" exists in the list of selected component ids
            if "38" in component_ids:
                # Get the selected column name from the request POST data
                selected_column = request.POST.get("columns-1")
                # Get the new name for the aggregated column from the request POST data
                column_new_name = request.POST.get("aggregator-name")
                # Get the aggregating function from the request POST data
                agg_function = request.POST.get("agg-function")
                # Call the aggregate_component function from commonTasks with the given path, selected_column, column_new_name, and agg_function
                status = commonTasks.aggregate_component(path, selected_column, column_new_name, agg_function)
                # If the aggregation is successful
                if status == 'success':
                    # Add a success message to the request object
                    messages.success(request, "Aggregate component successfully added")

            # Check if "39" exists in the list of selected component ids
            if "39" in component_ids:
                # Call the balanced_data_distributor function from commonTasks with the given path
                status,res1,res2 = commonTasks.balanced_data_distributor(path)

                full_path=f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/balanced_data_distributor'''
                if not os.path.isdir(full_path):
                    os.makedirs(full_path)

                # If the balanced data distributor component is added successfully
                with open(os.path.join(full_path,'data1.csv'), 'w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=res1[0].keys())
                    writer.writeheader()
                    writer.writerows(res1)

                with open(os.path.join(full_path,'data2.csv'), 'w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=res2[0].keys())
                    writer.writeheader()
                    writer.writerows(res2)

                if status == 'success':
                    # Add a success message to the request object
                    messages.success(request, "Balanced data distributor component successfully added")

            # Check if "40" exists in the list of selected component ids
            if "40" in component_ids:
                # Get the selected condition type from the request POST data
                select_condition = request.POST.get("select-condition")
                # Get the user defined condition from the request POST data
                user_condition = request.POST.get('enter-condition')
                # Get the selected column for conditional splitting from the request POST data
                selected_column = request.POST.get('columns-2')
                # Call the conditional_split_component function from commonTasks with the given path, select_condition, selected_column, and user_condition
                status = commonTasks.conditional_split_component(path, select_condition, selected_column, user_condition)
                # If the conditional split component is added successfully
                if status == 'success':
                    # Add a success message to the request object
                    messages.success(request, "Conditional splitter component successfully added")


            # Check if component with ID 41 is selected
            if "41" in component_ids: 
                # Get the selected column and new data type from the request
                selected_column = request.POST.get('columns-3')
                new_dtype = request.POST.get('data-type-1')
                # Call the data_conversion_component function from commonTasks
                status = commonTasks.data_conversion_component(path, selected_column, new_dtype)
                # If the function returns "success", display a success message
                if status == 'success':
                    messages.success(request, "Data conversion component successfully added")

            # Check if component with ID 42 is selected
            if "42" in component_ids: 
                # Get the selected method from the request
                selected_method = request.POST.get('select-method-1')

                # Call the data_stream_destination function from commonTasks
                full_path=f"""{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/data_stream_destination"""
                if not os.path.isdir(full_path):
                    os.makedirs(full_path)
                latest=get_latest_file(next(absoluteFilePaths('output_dataflows')))[0]
                status = commonTasks.data_stream_destination(selected_method,latest, os.path.join(full_path,'data.csv'))
                # If the function returns "success", display a success message
                if status == 'success':
                    messages.success(request, "Data streaming destination successfully added")

            # Check if component with ID 44 is selected
            if "44" in component_ids: 
                # Get the selected export columns from the request
                selected_columns = request.POST.getlist("export-columns",'')
                # Call the export_column_component function from commonTasks
                status = commonTasks.export_column_component(path, selected_columns)
                # If the function returns "success", display a success message
                if status == "success":
                    messages.success(request, "Export column component successfully added")

            # Check if component with ID 45 is selected
            if "45" in component_ids: 
                file_name2=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 2 ORDER BY id DESC LIMIT 1;""")[0]

                # Get the selected columns and method from the request
                column_1 = request.POST.get('columns-4')
                column_2 = request.POST.get('columns-5')
                select_method = request.POST.get('select-method-2')
                # Call the merge_join_component function from commonTasks
                status = commonTasks.merge_join_component(path, os.path.join(next(absoluteFilePaths('media')),'dataflow_uploads',file_name2), column_1, column_2, select_method)
                # If the function returns "success", display a success message
                if status == 'success':
                    messages.success(request, "Merge-join component successfully added")

            # Check if component with ID 46 is selected
            if "46" in component_ids: 
                # Call the multicast_component function from commonTasks
                status = commonTasks.multicast_component(path,"SQLite_Python.db")
                # If the function returns "success", display a success message
                if status == 'success':
                    messages.success(request, "Multicast component successfully added")

            # Check if component with ID 47 is selected
            if "47" in component_ids: 
                # Call the rowcount_component function from commonTasks
                status = commonTasks.rowcount_component(path)
                # If the function returns "success",display a success message

                if status=='success':
                    messages.success(request,"Row count component successfully added")

            # Check if component 48 is in the list of selected component ids
            if "48" in component_ids: 
                # Get the selected column for sort rows component
                selected_column = request.POST.get('columns-6')
                # Call the sortRows_component function from the commonTasks module
                status = commonTasks.sortRows_component(path, selected_column)
                # Check if the component was added successfully
                if status == 'success':
                    # Show a success message
                    messages.success(request, "Sort rows component successfully added")

            # Check if component 49 is in the list of selected component ids
            if "49" in component_ids: 
                file_name2=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 2 ORDER BY id DESC LIMIT 1;""")[0]

                file=request.FILES.get('add-new-file')
                status=dataSource.handle_uploaded_file_2(file)

                # Call the unionAll_component function from the commonTasks module
                status = commonTasks.unionAll_component(path, os.path.join(next(absoluteFilePaths('media')),'dataflow_uploads',file_name2))
                # Check if the component was added successfully
                if status == 'success':
                    # Show a success message
                    messages.success(request, "Union all component successfully added")

            # Check if component 50 is in the list of selected component ids
            if "50" in component_ids: 
                # Get the selected column for duplicate resolver component
                selected_column = request.POST.getlist('columns-7')
                # Call the duplicateResolver_component function from the commonTasks module
                status = commonTasks.duplicateResolver_component(path, selected_column)
                # Check if the component was added successfully
                if status == 'success':
                    # Show a success message
                    messages.success(request, "Duplicate resolver component successfully added")

            # Check if component 51 is in the list of selected component ids
            if "51" in component_ids: 
                # Call the audit_datapack function from the otherTransformations module
                status, package_descriptor = otherTransformations.audit_datapack(path)
                full_path=f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/audit_component'''
                if not os.path.isdir(full_path):
                    os.makedirs(full_path)

                # Writing audit data pack description to a csv file 
                with open(os.path.join(full_path,'data.csv'), mode='w', newline='') as file:
                    writer = csv.writer(file)
                    for resource in package_descriptor['resources']:
                        writer.writerow(['Path', 'Profile', 'Name', 'Format'])
                        writer.writerow([resource['path'], resource['profile'], resource['name'], resource['format']])
                        writer.writerow([])
                        writer.writerow(['Field Name', 'Field Type', 'Field Format'])
                        for field in resource['schema']['fields']:
                            writer.writerow([field['name'], field['type'], field['format']])

                # Check if the component was added successfully
                if status == 'success':
                    # Show a success message
                    messages.success(request, "Audit component successfully added")

            # Check if component 52 is in the list of selected component ids
            if "52" in component_ids: 
                # Call the cdc_splitter function from the otherTransformations module
                status = otherTransformations.cdc_splitter()
                # Check if the component was added successfully
                if status == 'success':
                    # Show a success message
                    messages.success(request, "CDC splitter component successfully added")

            # Check if component 53 is in the list of selected component ids
            if "53" in component_ids: 
                # Get the selected column and casing kind for character map transform component
                selected_column = request.POST.get('columns-8')
                casing_kind = request.POST.get("select-method-3")
                # Call the character_map_transform function from the otherTransformations module
                status = otherTransformations.character_map_transform(path, selected_column, casing_kind)
                # Check if the component was added successfully
                if status == 'success':
                    # Show a success message
                    messages.success(request, "Character map transform component successfully added")

            
            # Check if component id "54" is in the list of component ids
            if "54" in component_ids: 
                # Get the selected column name from the POST request
                selected_column=request.POST.get('columns-9')
                # Get the new name for the selected column from the POST request
                col_new_name=request.POST.get("new-col-name")
                # Get the data type for the new column from the POST request
                dtype=request.POST.get('select-dtype')

                # Call the copy_column_transfomer function from the otherTransformations module
                # to perform the copy column operation
                status=otherTransformations.copy_column_transfomer(path,select_condition,col_new_name,dtype)
                # If the copy column operation was successful, show a success message
                if status=='success':
                    messages.success(request,"Copy column component successfully added")

            # Check if component id "55" is in the list of component ids
            if "55" in component_ids: 
                # Get the selected column name from the POST request
                selected_column=request.POST.get('columns-10')
                # Get the data type for the new column from the POST request
                dtype=request.POST.get('select-dtype2')
                # Get the find string from the POST request
                finder=request.POST.get('find-string')
                # Get the replace string from the POST request
                replacer=request.POST.get('replace-string')
                # Get the casing method from the POST request
                casing_method=request.POST.get('select-method-4')

                # Call the dqs_cleansing function from the otherTransformations module
                # to perform the DQS cleansing operation
                status=otherTransformations.dqs_cleansing(path,selected_column,dtype,finder,replacer,casing_method)
                # If the DQS cleansing operation was successful, show a success message
                if status=='success':
                    messages.success(request,"DQS cleansing component successfully added")

            # Check if component id "56" is in the list of component ids
            if "56" in component_ids: 
                # Get the selected percentage range from the POST request
                selected_range=request.POST.get('percent-range')

                # Call the row_percentage_sampling function from the otherTransformations module
                # to perform the row percentage sampling operation
                status=otherTransformations.row_percentage_sampling(path,float(selected_range))
                # If the row percentage sampling operation was successful, show a success message
                if status=='success':
                    messages.success(request,"Row Percentage sampling component successfully added")

            # Check if component id "57" is in the list of component ids
            if "57" in component_ids: 
                # Get the selected header column from the POST request
                selected_header_col=request.POST.get('columns-11')
                # Get the selected value column from the POST request
                selected_value_col=request.POST.get('columns-12')
                # Get the selected index column from the POST request
                selected_index_col=request.POST.get('columns-13')
                # Get the selected operation from the POST request
                selected_operation=request.POST.get('select-operation1')

                status=otherTransformations.pivot_component(path,selected_value_col,selected_index_col,selected_header_col,selected_operation)
                # If the pivot operation was successful, show a success message
                if status=='success':
                    messages.success(request,"Pivot component successfully added")

            
            #Check if component with ID 58 is selected
            if "58" in component_ids:
                #Retrieve the new column name from the user input
                new_col_name=request.POST.get('new-col-name2')
                #Retrieve the data type selected by the user
                dtype=request.POST.get('select-dtype3')
                #Retrieve the user input for the unpivot component
                user_input=request.POST.get('user-input1')

                #Perform the unpivot transformation
                status=otherTransformations.unpivot_component(path,new_col_name,dtype,user_input)
                #Check if the transformation was successful
                if status=='success':
                    #Display a success message to the user
                    messages.success(request,"Unpivot component successfully added")

            #Check if component with ID 59 is selected
            if "59" in component_ids:
                #Retrieve the number of records to sample from the user input
                no_of_reccords=request.POST.get("select-records")
                #Perform the row count sampling transformation
                if no_of_reccords !='':
                    status=otherTransformations.row_count_sampling(path,int(no_of_reccords))
                    #Check if the transformation was successful
                    if status=='success':
                        #Display a success message to the user
                        messages.success(request,"Row count sampling component successfully added")

            #Check if component with ID 60 is selected
            if "60" in component_ids:
                #Retrieve the operation selected by the user
                perform_operation=request.POST.get('select-operation-2')
                #Retrieve the column selected by the user
                selected_column=request.POST.get('column-14')
                #Retrieve the user input for the derived column component
                user_input=request.POST.get('user-input2')

                #Perform the derived column transformation
                status=commonTasks.derived_column_component(path,perform_operation,selected_column,user_input)                
                #Check if the transformation was successful
                if status=='success':
                    #Display a success message to the user
                    messages.success(request,"Derived column component successfully added")

            #Check if component with ID 61 is selected
            if "61" in component_ids:
                file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

                #Retrieve the path to the file to be transformed
                path=os.path.join(path,file_name)
                #Read the data into a pandas dataframe
                status,df=check_file_exists(path)

                #Retrieve the code provided by the user for the custom script component
                code=request.POST.get('code')
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
                        df.to_csv(path,index=False,mode='w')
                        # Show a success message if the code was executed successfully
                        messages.success(request,"Custom script component successfully added")
                    except Exception as e:
                        # render the exception if there was an error in the code execution
                        return render(request,'custom-script.html', {"status":"error","msg":"Code snippets is not valid"})
                else:
                    messages.error(request,"Code snippets is not valid")
            
            return HttpResponseRedirect(self.request.META.get('HTTP_REFERER')) 
        
        
        if request.method == "POST" and "submit-all" in request.POST:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            folder_path = os.path.join(next(absoluteFilePaths('output_dataflows')), file_name.split('.')[0])
            # Zip all files in the folder
            data = io.BytesIO()
            with zipfile.ZipFile(data, mode='w') as z:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.endswith('.csv'):
                            file_path = os.path.join(root, file)
                            z.write(file_path, os.path.relpath(file_path, folder_path))

            data.seek(0)

            # Return the zip file as a response with appropriate headers
            response= HttpResponse(data, content_type="application/zip",)
            response["Content-Disposition"]=f"attachment; filename=data.zip"
            messages.success(request,"Downloading data...")
            return response



@login_required
def add_component(request):
    """
    This view allows a user to add a new component to their list of components.
    """
    try:
        # Get the name of the component from the request
        name = request.POST.get('componentname')
        # Get or create the DataFlowComponent object with the specified name
        component_obj = DataFlowComponent.objects.get_or_create(name=name)[0]
        # Add the component to the user's list of components
        request.user.components.add(component_obj)
        # Create a UserComponents object that links the user and the component
        if not UserComponents.objects.filter(components=component_obj, user=request.user).exists():
            UserComponents.objects.create(
                components=component_obj, 
                user=request.user, 
            )

        # Get all of the user's components
        components = UserComponents.objects.filter(user=request.user)
        logging.info(f"Successfully added components :{component_obj}")
        # Send a success message to the user
        messages.success(request, f"Added {name} to list of components")
        # Return a template fragment with the list of the user's components
        return render(request, 'partials/components-list.html', {'components': components})

    except Exception as e:
        # Log the error message if there was a problem adding the component
        logging.error(f"Error while adding components :{e}")

@login_required
def delete_component(request, pk):
    try:
        """
        This view allows a user to delete a component from their list of components.
        """
        ...
        # Remove the specified component from the user's list of components
        UserComponents.objects.get(pk=pk).delete()

        # Return a template fragment with the updated list of the user's components
        components = UserComponents.objects.filter(user=request.user)
        return render(request, 'partials/components-list.html',{"components":components})
    except Exception as e:
        # log the error message if an error occurs while deleting the components
        logging.error(f'Error while deleting components: {e}')


@login_required
def search_component(request):
    """
    This view allows a user to search for components.
    """
    try:
        # Get the search text from the request
        search_text = request.POST.get('search')

        # Look up all components that contain the search text, excluding the user's components
        userComponents = UserComponents.objects.filter(user=request.user)
        results = DataFlowComponent.objects.filter(name__icontains=search_text).exclude(name__in=userComponents.values_list('components__name',flat=True))
        logging.info(f"Searching components :{results}")
        
        # Return a template fragment with the search results
        context = {"results": results}
        return render(request, 'partials/search-results.html', context)
    
    except Exception as e:
        # Log the error message if there was a problem searching for components
        logging.error(f'Error while searching components: {e}')


def clear_component(request):
    return HttpResponse("")


def sort_component(request):
    """
    This function sorts the components by their order as specified by the user.
    This function takes the list of components' primary keys in the order that the user wants them to be sorted, updates their order in the database, and then renders a template with all of the user's components in the specified order.
    Args:
        request: an instance of the `django.http.request.HttpRequest` class.
    Returns:
        A render object that displays the `components-list.html` template with all of the user's components in the specified order.
    Raises:
        Exception: If an error occurs while sorting the components, a log message is written to the log with the error message.
    """
    try:
        # get the order of the components from the request
        component_pks_order = request.POST.getlist('component_order')

        # initialize an empty list to hold all the components
        components_all = []

        # loop over each primary key in the specified order
        for idx, film_pk in enumerate(component_pks_order, start=1):
            # get the user component with the specified primary key
            usercomponent = UserComponents.objects.get(pk=film_pk)

            # save the updated order of the component
            usercomponent.save()

            # add the component to the list of all components
            components_all.append(usercomponent)

        # log the sort order of the components
        logging.info(f"Sort order of components :{component_pks_order}")

        # return the template with the sorted components
        return render(request, 'partials/components-list.html', {'components': components_all})

    except Exception as e:
        # log the error message if an error occurs while sorting the components
        logging.error(f'Error while sorting components: {e}')