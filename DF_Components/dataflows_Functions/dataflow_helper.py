from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from dataflows import Flow,load,join_with_self,filter_rows,set_type, \
add_computed_field,join,dump_to_path,dump_to_sql,sources,set_primary_key,deduplicate,sort_rows, add_field,unpivot,find_replace 
from sqlalchemy import create_engine
from dataflows.base.schema_validator import ignore
import collections
from collections import abc
collections.MutableMapping = abc.MutableMapping
# import hdfs3
from datetime import datetime
import os
import pandas as pd
import numpy as np
from logger import logging
from tabulator import Stream,Writer
import csv
import json
import re
import sqlite3
from src.utils.basicFunctions import read_configure_file,absoluteFilePaths
from data_access.mysql_connect import MySql


config_args= read_configure_file("config.yaml")
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)

class dataSource:
    def handle_uploaded_file(file):
        """
        Handle the uploaded file from the user. 
        Parameters:
            file (file object): The uploaded file
        Returns:
            status (str): The status of the file handling process (success/failure)
        """

        if file is not None:
            # Save the uploaded file to the specified path
            path = default_storage.save('dataflow_uploads/' + file.name, ContentFile(file.read()))
            
            sql_obj.insert_records(f'''INSERT INTO file_data_info (filename, file_number)
            VALUES ('{file.name}','1');
            ''')

            sql_obj.insert_records(f'''INSERT INTO file_change_capture (filename)
            VALUES ('{file.name}');
            ''')            
            

            # Return success status
            status="success"
            return status

    def handle_uploaded_file_2(file2):
        """
        Handle the uploaded file from the user. 
        Parameters:
            file (file object): The uploaded file
        Returns:
            status (str): The status of the file handling process (success/failure)
        """

        if file2 is not None:
            # Save the uploaded file to the specified path
            path = default_storage.save('dataflow_uploads/' + file2.name, ContentFile(file2.read()))
            
            
            sql_obj.insert_records(f'''INSERT INTO file_data_info (filename, file_number)
            VALUES ('{file2.name}','2');
            ''')

            sql_obj.insert_records(f'''INSERT INTO file_change_capture (filename)
            VALUES ('{file2.name}');
            ''')            

            # Return success status
            status="success"
            return status

    def import_database(sql_uri=None,table_name=None):
        """
        Import a database using SQL URI and table name.
        Parameters:
            sql_uri (str): The SQL URI of the database (e.g. 'sqlite:///SQLite_Python.db')
            table_name (str): The name of the table to be imported
        Returns:
            status (str): The status of the import process (success/failure)
        """

        file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
        if sql_uri != '':
            # Import the database using the given SQL URI and table name
            Flow(
                Stream(sql_uri,table=table_name,headers=1).open(),
                dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/sql_''')
            ).process()

            # Return success status
            status="success"
            return status

    def import_cloud(s3_endpoint_url,table_name):
        """
        Import a cloud database using S3 endpoint URL and table name.
        Parameters:
            s3_endpoint_url (str): The S3 endpoint URL of the database
            table_name (str): The name of the table to be imported
        Returns:
            status (str): The status of the import process (success/failure)
        """

        if s3_endpoint_url != '':
            # Import the cloud database using the given S3 endpoint URL and table name
            Flow(
                Stream(s3_endpoint_url,table=table_name).open(),
                dump_to_path('media/output/')
            ).process()

            # Return success status
            status="success"
            return status


class commonTasks:
    """
    Class that performs various data manipulation tasks, including aggregation, data distribution, etc.
    """

    def aggregate_component(filename:str,column,column_new_name,agg_func):
        """
        Aggregate a specific column of a dataframe
        Args:
        filename (str): name of the file to be processed.
        column (str): name of the column to be aggregated.
        column_new_name (str): new name for the aggregated column.
        agg_func (str): aggregation function to be applied.
        Returns:
        str: 'success' if the function runs successfully.
        Raises:
        Logs Exception
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            if column != '':

                # Load the dataframe and set the column data type to number
                Flow(
                    load(filename, name='dataframe'),
                    set_type(column, type='number'), 
                    
                    # Join the dataframe with itself and perform the aggregation
                    join_with_self(
                        'dataframe',
                        column,
                        {
                            column_new_name:{
                                "name": column,
                                'aggregate': agg_func
                            },
                        }
                    ),
                    
                    # Dump the results to a specific path
                    dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/aggregate''')
                ).process()

                status="success"
                return status
        except Exception as e:
            logging.error(f"Error while aggregating components: {e}")

    def balanced_data_distributor(filename:str):
        """
        Distributes the data in a dataframe into two equal parts
        Args:
        filename (str): name of the file to be processed.
        Returns:
        str: 'success' if the function runs successfully.
        res1 (pandas.DataFrame): First part of the split data.
        res2 (pandas.DataFrame): Second part of the split data.
        Raises:
        Exception: if any error occurs while processing the data.
        """
        try:
            # Load the dataframe
            df = pd.read_csv(filename)
            mid = len(df)//2

            # Split the dataframe into two parts and store the results in two separate dataframes
            res1 = Flow(
                load(filename),
            ).results()[0][0][:mid]
            
            res2 = Flow(
                load(filename),
            ).results()[0][0][mid:]
            
            status = "success"
            return status, res1, res2
        
        except Exception as e:
            logging.error(f"{e}")



    def conditional_split_component(filename,condition,column_name,user_input):
        """
        This function filters the rows in the file based on the given condition and column.
        Parameters:
            file_name (str): The file name to be processed
            condition (str): The condition to be applied to the data. Can be "greater than equals", "lesser than equals", "equals", or "not equals".
            column_name (str): The name of the column to be processed.
            user_input (str): The value to be used as a filter based on the condition.
        Returns:
            status (str): The processing status. "success" if the processing is successful, otherwise an error message is returned.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

            if condition=="greater than equals":
                Flow(load(f'{filename}'), 
                        filter_rows(condition=lambda row: row[f"{column_name}"]>=f'{user_input}'),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/conditional_splitter''')
                    ).process()
            elif condition=="lesser than equals":
                Flow(load(f'{filename}'), 
                        filter_rows(condition=lambda row: row[f"{column_name}"]<=f'{user_input}'),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/conditional_splitter''')
                    ).process()
            
            elif condition=="equals":
                Flow(load(f'{filename}'), 
                        filter_rows(condition=lambda row: row[f"{column_name}"]==f'{user_input}'),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/conditional_splitter''')
                        
                    ).process()
            
            elif condition=="not equals":
                Flow(load(f'{filename}'), 
                        filter_rows(condition=lambda row: row[f"{column_name}"]!=f'{user_input}'),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/conditional_splitter''')
                    ).process()
    
            status="success"
            return status

        except Exception as e:
            logging.error(f"{e}")


    def data_conversion_component(filename:str,column_name,new_dtype):
        """
        This function converts the data type of a specified column in the file.
        Parameters:
            filename (str): The file name to be processed.
            column_name (str): The name of the column to be processed.
            new_dtype (str): The new data type to be set for the specified column.
        Returns:
            status (str): The processing status. "success" if the processing is successful, otherwise an error message is returned.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

            if column_name != '--None--':
                Flow(load(filename),
                        set_type(column_name, type=new_dtype, on_error=ignore),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/datatype_conversion''')
                    ).process()

                status="success"
                return status

        except Exception as e:
            logging.error(f"{e}")

    def data_stream_destination(method,source,target):
        """
        This function writes the data from a source stream to a target file in either CSV or JSON format.
        
        Args:
            method (str): The method to use to write the data. Either 'csv' or 'json'.
            source (str): The source stream.
            target (str): The target file.
        
        Returns:
            str: The status of the operation. Either 'success' or an error message.
        """
        try:
            if method != '--None--':
                
                class CustomWriter(Writer):
                    options = []

                    def __init__(self, **options):
                        pass
                    
                    if method=='csv':

                        def write(self, source, target, headers=None, encoding=None):
                            with open(target, 'w', newline='', encoding=encoding) as f:
                                writer = csv.writer(f)
                                if headers:
                                    writer.writerow(headers)
                                for row in source:
                                    writer.writerow(row)
                        
                    elif method=='json':
                    
                        def write(self, source, target, headers=None, encoding=None):
                            with open(target, 'w', encoding=encoding) as f:
                                data = []
                                if headers:
                                    data.append(dict(zip(headers, row)))
                                for row in source:
                                    data.append(dict(zip(headers, row)))
                                json.dump(data, f, ensure_ascii=False)
                        
                with Stream(source, custom_writers={'custom': CustomWriter}) as stream:
                    stream.save(target)

                status="success"
                return status

        except Exception as e:
            logging.error(f"{e}")    
    

    def derived_column_component(filename:str,operation,column_name,number):
        """
        This function performs mathematical operations on a specified column in a data file.
        Args:
            filename (str): The data file.
            operation (str): The operation to perform on the specified column. Can be either 'multiply', 'divide', 'subtract', or 'add'.
            column_name (str): The name of the column to perform the operation on.
            number (float): The number to use in the operation.
        Returns:
            str: The status of the operation. Either 'success' or an error message.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            if column_name != '--None--':
    
                if operation=='multiply':
                    Flow(load(f'{filename}'),
                        add_computed_field([
                            dict(target=dict(name='new_column', type='number'),
                                operation=lambda row: float(row[f'{column_name}']) * float(number)),
                            dict(target=dict(name='created', type='date'), operation='constant', with_=datetime.today()),
                        ]),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/derived_column''')

                        ).process()

                elif operation=='divide':
                    Flow(load(f'{filename}'),
                        add_computed_field([
                            dict(target=dict(name='new_column', type='number'),
                                operation=lambda row: float(row[f'{column_name}']) / float(number)),
                            dict(target=dict(name='created', type='date'), operation='constant', with_=datetime.today()),
                        ]),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/derived_column''')

                        ).process()
                    
                elif operation=='subtract':
                    Flow(load(f'{filename}'),
                        add_computed_field([
                            dict(target=dict(name='new_column', type='number'),
                                operation=lambda row: float(row[f'{column_name}']) - float(number)),
                            dict(target=dict(name='created', type='date'), operation='constant', with_=datetime.today()),
                        ]),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/derived_column''')

                        ).process()
                
                elif operation=='add':
                    Flow(load(f'{filename}'),
                        add_computed_field([
                            dict(target=dict(name='new_column', type='number'),
                                operation=lambda row: float(row[f'{column_name}']) + float(number)),
                            dict(target=dict(name='created', type='date'), operation='constant', with_=datetime.today()),
                        ]),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/derived_column''')

                        ).process()

                status="success"
                return status

        except Exception as e:
            logging.error(f"{e}")

    def export_column_component(path,selected_cols):
        """
        This function reads a csv file from the given path, selects the columns specified in `selected_cols` 
        and exports the selected columns into a csv file at the specified output path.
        Parameters:
        path (str): Path to the input csv file.
        selected_cols (str): Comma separated string of columns to be selected. If "--None--" is passed, all columns will be exported.
        Returns:
        status:(str)
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            if selected_cols !="--None--":
                df=pd.read_csv(path,usecols=selected_cols)

                path=f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/export_column'''
                if not os.path.isdir(path):
                    os.makedirs(path)
                df.to_csv(os.path.join(path,'export.csv'))
                status="success"
                return status

        except Exception as e:
            logging.error(f"{e}")


    def merge_join_component(filename1:str,filename2:str,col1,col2,mode_of_join):
        """
        This function performs a merge join on two csv files specified by `filename1` and `filename2` on the columns `col1` and `col2` respectively.
        The type of join is specified by `mode_of_join` and the output is saved to a specified path.
        Parameters:
        filename1 (str): Path to the first csv file.
        filename2 (str): Path to the second csv file.
        col1 (str): Column in `filename1` to join on.
        col2 (str): Column in `filename2` to join on.
        mode_of_join (str): Type of join to be performed.
        Returns:
        status (str): Returns "success" if the operation is successful, otherwise an error message is logged.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            if col1 != '--None--':
             
                Flow(load(f'{filename1}'),
                    load(f'{filename2}'),
                    join(f'{filename1.split(".")[0]}',[f'{col1}'],f'{filename2.split(".")[0]}',[f'{col2}'],mode=f'{mode_of_join}'),
                    dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/merge_join''')
                    ).process()

                status="success"
                return status

        except Exception as e:
            logging.error(f"{e}")



    def multicast_component(filename:str,database):
        """
        This function reads a csv file from the specified path and outputs the data to two locations:
        a csv file and a SQLite database table.
        Parameters:
        filename (str): Path to the input csv file.
        Returns:
        status (str): Returns "success" if the operation is successful, otherwise an error message is logged.
        """
        try:    
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            sqlite3.connect(database)
            enginer = create_engine(f'sqlite:///{database}')
            Flow(
                load(filename,name='dataframe'),
                dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/multicast'''),
                dump_to_sql(dict(
                            output_table={
                                'resource-name': 'dataframe'
                            }
                        ),engine=enginer)
            ).process()

            status="success"
            return status
        
        except Exception as e:
            logging.error(f"{e}")


    def rowcount_component(filename:str):
        """
        This function is used to count the number of rows in a given csv file.
        Parameters:
        filename (str): The name of the input csv file.
        Returns:
        status (str): Returns "success" if the operation is successful.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

            f=Flow(
                    # Same one as above
                    load(f'{filename}'),
                    dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/row_count''')

                ).process()[1]
            data= pd.DataFrame({"Count_of_records":f})

            path=f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/row_count'''
            if not os.path.isdir(path):
                os.makedirs(path)
            
            data.to_csv(os.path.join(path,'rowcounter.csv'))
            status="success"

            return status

        except Exception as e:
            logging.error(f"{e}")

    def sortRows_component(filename,col_name1):
        """
        This function is used to sort the rows in a given csv file based on a specified column.
        Parameters:
        filename (str): The name of the input csv file.
        col_name1 (str): The name of the column on which the rows will be sorted.
        Returns:
        status (str): Returns "success" if the operation is successful.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            if col_name1 != '--None--':

                Flow(load(filename),
                    sort_rows(key='{0}'.format(col_name1),reverse=False),
                    dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/sort_rows''')

                    ).process()

                status="success"
                return status
        except Exception as e:
            logging.error(f"{e}")


    def unionAll_component(filename1:str,filename2:str):
        """
        This function is used to perform a union all operation on two csv files.
        Parameters:
        filename1 (str): The name of the first input csv file.
        filename2 (str): The name of the second input csv file.
        Returns:
        status (str): Returns "success" if the operation is successful.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            Flow(
                sources(
                    load(filename1),
                    load(filename2),
                ),
            dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/union_All''')

            ).process()
            status="success"
            return status

        except Exception as e:
            logging.error(f"{e}")


    def duplicateResolver_component(filename,columns):
        """
        This function resolves duplicate records in the given file based on the specified columns.
        Parameters:
        filename (str): The name of the file to resolve duplicates in.
        columns (list): The columns to use as the primary key for deduplication.
        Returns:
        str: "success" if the function completes successfully, otherwise it logs the error message.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            if columns != '--None--':
                
                Flow(load(filename),
                    set_primary_key(columns),
                    deduplicate(),
                    dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/duplicate_resolver''')
                    ).process()
        
                status="success"
                return status

        except Exception as e:
            logging.error(f"{e}")


class otherTransformations:
    def audit_datapack(filename):
        """
        This function audits the data in the specified file and returns its descriptor.
        Parameters:
        filename (str): The name of the file to audit.
        Returns:
        tuple: A tuple containing the status ("success" if the function completes successfully, otherwise it logs the error message) and the data descriptor of the file.
        """
        try:
            f = Flow(
                load(filename),
                )
            results, dp, stats = f.results()
            status="success"

            return status,dp.descriptor
        
        except Exception as e:
            logging.error(f"{e}")

    def cdc_splitter():
        """
        This function splits the change data capture information from the SQL Server into a CSV file.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

            rows=sql_obj.fetch_all('''SELECT * FROM file_data_changes''')
            df = pd.DataFrame.from_records(rows, columns=['change_id','change_type','file_id','change_date'])
            path=f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/cdc_splitter'''
            if not os.path.isdir(path):
                os.makedirs(path)
            df.to_csv(os.path.join(path,'cdc.csv'))

            status="success"
            return status

        except Exception as e:
            logging.error(f"{e}")
    
    
    def character_map_transform(filename,col_name,kind):
        """
        Transform a column in a file to either upper or lower case.
        Args:
        filename (str): Name of the file to be transformed
        col_name (str): Name of the column to be transformed
        kind (str): The desired case to be transformed to ("upper" or "lower")
        Returns:
        status (str): The status of the transformation, either "success" or an error message.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

            if col_name != '--None--':
                def lowerData(row):
                    row[col_name] = row[col_name].lower()

                def upperData(row):
                    row[col_name] = row[col_name].upper()

                if kind == "upper":
                    Flow(
                            load(filename),
                            upperData,
                            dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/char_map_transform''')

                        ).process()

                elif kind == "lower":
                    Flow(
                            load(filename),
                            lowerData,
                            dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/char_map_transform''')

                        ).process()
            
                status="success"
                return status

        except Exception as e:
            logging.error(f"{e}")

    def copy_column_transfomer(filename,col_name,col_new_name,dtype):
        """
        Copy a column in a file and create a new column with a different name and data type.
        Args:
        filename (str): Name of the file to be transformed
        col_name (str): Name of the column to be copied
        col_new_name (str): The new name of the copied column
        dtype (str): The data type of the new copied column
        Returns:
        status (str): The status of the transformation, either "success" or an error message.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

            if col_new_name != '':
                def copyData(row):
                    row[col_new_name] = row[col_name]

                Flow(
                    load(filename),
                    add_field(col_new_name, type=dtype),
                    copyData,
                    dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/copy_column''')

                        ).process()

                status="success"
                return status
    
        except Exception as e:
            logging.error(f"{e}")

    def dqs_cleansing(filename,column_name,new_dtype,find_item,replace_item,casing_kind):
        """
        This function performs data quality checks and cleansing operations on a specific column of a given file.
        
        Args:
        filename (str): name of the file, which should be read and processed
        column_name (str): name of the column, on which data quality checks and cleansing operations should be performed. If "--None--", then no operations will be performed.
        new_dtype (str): desired data type for the column.
        find_item (str): item to be found in the column.
        replace_item (str): item to replace the found item with.
        casing_kind (str): 'upper' for converting the values of the column to uppercase, and 'lower' for converting the values to lowercase.
        
        Returns:
        status (str): the string 'success' if the function runs successfully, otherwise an error message will be logged.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

            if column_name != '--None--':

                def upperData(row):
                    """
                    Converts values in the column to uppercase
                    """
                    row[column_name] = row[column_name].upper()

                def lowerData(row):
                    """
                    Converts values in the column to lowercase
                    """
                    row[column_name] = row[column_name].lower()

                def remove_numerics(row):
                    """
                    Removes numeric values from the column
                    """
                    row[column_name] = re.sub(r'\d+','',row[column_name])

                def remove_punct(row): 
                    """
                    Removes punctuation values from the column
                    """
                    row[column_name]=re.sub(r'[^\w\s]','', row[column_name])

                def remove_whitespaces(row): 
                    """
                    Removes white spaces from the column
                    """
                    row[column_name]=row[column_name].strip()

                if casing_kind=='upper':
                    Flow(load(filename,extract_missing_values=True),
                            set_type(f'{column_name}', type=f'{new_dtype}', on_error=ignore),
                            upperData,
                            remove_numerics,
                            remove_punct,
                            remove_whitespaces,
                        

                        find_replace([dict(
                            name=f'{column_name}',
                            patterns=[
                                dict(find=find_item, replace=replace_item),
                            ]
                        )]),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/dqs_cleansing''')

                        ).process()
            
                elif casing_kind=='lower':
                    Flow(load(filename,extract_missing_values=True),
                            set_type(f'{column_name}', type=f'{new_dtype}', on_error=ignore),
                            lowerData,
                            remove_numerics,
                            remove_punct,
                            remove_whitespaces,
                        

                        find_replace([dict(
                            name=f'{column_name}',
                            patterns=[
                                dict(find=find_item, replace=replace_item),
                            ]
                        )]),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/dqs_cleansing''')

                        ).process()

            
                status="success"
                return status

        except Exception as e:
            logging.error(f"{e}")


    def row_percentage_sampling(filename:str,percentage_of_records:float):
        """
        This function performs row percentage sampling on the input csv file.
        Parameters:
        filename (str): The input csv file name.
        percentage_of_records (float): The fraction of the input records to be sampled.
        Returns:
        status (str): A string indicating the status of the function execution. Returns "success" if the function executed successfully, otherwise logs the error.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            df=pd.read_csv(filename)
            sampled_df=df.sample(frac=percentage_of_records)

            path=f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/row_percent_sampler'''
            if not os.path.isdir(path):
                os.makedirs(path)
            sampled_df.to_csv(os.path.join(path,'row_percent.csv'))

            status="success"
            return status
        except Exception as e:
            logging.error(f"{e}")



    def pivot_component(filename:str,value_col,index_cols,header_cols,selected_operation):
        """
        This function performs pivot operation on the input csv file.
        Parameters:
        filename (str): The input csv file name.
        value_col (str): The column to be used as values in the pivot table.
        index_cols (list): The columns to be used as index in the pivot table.
        header_cols (list): The columns to be used as header in the pivot table.
        selected_operation (str): The aggregate operation to be performed on the values in the pivot table. 
        The supported operations are "Sum", "Mean", and "Standard Deviation".
        Returns:
        status (str): A string indicating the status of the function execution. Returns "success" if the function executed successfully, otherwise logs the error.
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
            
            if selected_operation=='Sum':
                table = pd.pivot_table(pd.read_csv(filename), values =value_col, index =index_cols,
                                    columns =header_cols, aggfunc = np.sum)

            elif selected_operation=='Mean':
                table = pd.pivot_table(pd.read_csv(filename), values =value_col, index =index_cols,
                                    columns =header_cols, aggfunc = np.mean)
            elif selected_operation=='Standard Deviation':
                table = pd.pivot_table(pd.read_csv(filename), values =value_col, index =index_cols,
                                    columns =header_cols, aggfunc = np.std)

            path=f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/Pivot_component'''
            if not os.path.isdir(path):
                os.makedirs(path)
            table.to_csv(os.path.join(path,"pivot.csv"))
            
            status="success"
            return status
        
        except Exception as e:
            logging.error(f"{e}")


    def unpivot_component(filename:str,new_field_name,new_field_type,input_column):
        """
        This function takes in a filename and performs unpivot on the data present in the file. 
        The new field name and type are provided as arguments to the function.
        The input column is used to identify which column to unpivot in the data.
        Parameters:
        filename (str): name of the file to be unpivoted
        new_field_name (str): name of the newly created field after unpivot operation
        new_field_type (str): type of the newly created field
        input_column (str): column to be unpivoted
        Returns:
        str: Returns "success" if the operation was successful, otherwise returns None
        """ 
        try:
            if input_column != '--None--':

                file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]
                unpivoting_fields = [
                { 'name': r'([a-zA-Z]+)', 'keys': {f'{input_column}': r'\1'} }
                ]

                # A newly created column header would be 'year' with type 'year':
                extra_keys = [ {'name': f'{input_column}', 'type': 'any'} ]
                # And values will be placed in the 'value' column with type 'string':
                extra_value = {'name': f'{new_field_name}', 'type': f'{new_field_type}'}
                Flow( load(filename),
                        unpivot(unpivoting_fields, extra_keys, extra_value),
                        dump_to_path(f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/unpivot''')
                        ).process()

                status="success"
                return status
        except Exception as e:
            logging.error(f"{e}")
    
    
    def row_count_sampling(filename:str,num_of_records:int):
        """
        This function takes in a filename and a number of records as input and performs random sampling on the data present in the file. 
        The number of records to be sampled is provided as an argument to the function.
        Parameters:
        filename (str): name of the file to be sampled
        num_of_records (int): number of records to be sampled from the data
        Returns:
        str: Returns "success" if the operation was successful, otherwise returns None
        """
        try:
            file_name=sql_obj.fetch_one(f"""SELECT filename FROM file_data_info WHERE file_number = 1 ORDER BY id DESC LIMIT 1;""")[0]

            df=pd.read_csv(filename)
            sampled_df=df.sample(n=num_of_records)
            
            path=f'''{next(absoluteFilePaths('output_dataflows'))}/{file_name.split('.')[0]}/row_sampler'''
            if not os.path.isdir(path):
                os.makedirs(path)
            sampled_df.to_csv(os.path.join(path,"row_sample.csv"))

            status="success"
            return status
        except Exception as e:
            logging.error(f"{e}")
