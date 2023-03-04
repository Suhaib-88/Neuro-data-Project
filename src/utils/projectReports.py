from data_access.mysql_connect import MySql
import pandas as pd
from src.utils.basicFunctions import read_configure_file
from logger import logging

config_args= read_configure_file("config.yaml")
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)


class ProjectReports:
    id = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

    @staticmethod
    def insert_project_info(project_id,project_type,project_name,init_status):
        try:
            query = f"""INSERT INTO projects_info (Projectid, ModuleId, ProjectType, ProjectName, SetTarget, ModuleUrl, IsInitialized)
                        VALUES ("{project_id}", '1', "{project_type}", "{project_name}", "None", "None", {init_status});
                    """

            logging.info(f"{ProjectReports.id} : Sucessfully entered Project Details!")
            rowcount = sql_obj.insert_records(query)
            return rowcount    
        
        except Exception as e:
            logging.error(f"{ProjectReports.id} Project Details failed to insert")
        

    @staticmethod
    def insert_record_eda(project_id,actionName, input=''):
        try:
            query = f"""INSERT INTO 
            ProjectReports(`Projectid`, `ModuleId`,`ModuleName`, `ActionName`, `Input`)
             VALUES ('{project_id}',2,'EDA','{actionName}','{input}')"""
            logging.info(f"{project_id} details uploaded successfully for EDA!")
            rowcount = sql_obj.insert_records(query)
        except Exception as e:
            logging.error(f"{project_id} details upload failed for EDA!")

    @staticmethod
    def insert_record_dp(project_id,actionName, input=''):
        try:
            query = f"""INSERT INTO 
            ProjectReports(`Projectid`, `ModuleId`,`ModuleName`, `ActionName`, `Input`)
            VALUES ('{project_id}',3,'DP','{actionName}','{input}')"""
            logging.info(f"{project_id} details uploaded successfully for Data Preprocessing!")
            rowcount = sql_obj.insert_records(query)
        except Exception as e:
            logging.error(f"{project_id} details upload failed for Data Preprocessing!")

    @staticmethod
    def insert_record_fe(project_id,actionName, input=''):
        try:
            query = f"""INSERT INTO 
            ProjectReports(`ProjectId`, `ModuleId`,`ModuleName` ,`ActionName`, `Input`)
            VALUES ('{project_id}',4,'FE','{actionName}','{input}')"""

            logging.info(f"{project_id} details uploaded successfully for Feature Engineering!")
            sql_obj.insert_records(query)
        except Exception as e:
            logging.error(f"{project_id} details upload failed for Feature Engineering!")
    
    @staticmethod
    def insert_project_action_report(project_id,projectActionId,input_=''):
        try:
            query = f"""INSERT INTO 
            Project_Actions(ProjectId, ProjectActionId,Input)
            VALUES ("{project_id}",{projectActionId},'{input_}')"""
            
            logging.info(f"Project actions performed for: {ProjectReports.id}!")
            rowcount = sql_obj.insert_records(query)
            return rowcount
        except Exception as e:
            logging.error(f"Unable to insert actions performed for: {ProjectReports.id}!")
            

    @staticmethod
    def retrive_project_reports(project_id):
        try:
            query_=f"""
            select projectreports.ModuleId, projectreports.ModuleName, projectreports.ActionName, project_actions.ProjectActionId, projectreports.current_datetime from projectreports inner join project_actions on (project_actions.Projectid=projectreports.ProjectId) where projectreports.Projectid={project_id};
            """

            rows_data = sql_obj.fetch_all(query_)

            records = pd.DataFrame(rows_data, columns=['ModuleId','ModuleName','Actions Performed','ActionId','Timings'])
            return records

        except Exception as e:
            logging.error(f"Unable to retrive project reports for: {ProjectReports.id}!")
            