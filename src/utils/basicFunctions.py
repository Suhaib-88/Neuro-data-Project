import os
import yaml
import pandas as pd
import numpy as np
import glob
import shutil
from dataIngestion.models import upload_Dataset
import pickle
from logger import logging
from data_access.mysql_connect import MySql 

def read_configure_file(config_file):
    try:
        with open(config_file) as File:
            load_content = yaml.safe_load(File)
        
        logging.info("Reading contents of configure file!")
        return load_content

    except Exception as e:
        logging.error(f"Error occurred while loading configure file: {e}!")

def absoluteFilePaths(directory):
    for dirpath,_,filenames in os.walk(directory):
        yield os.path.abspath(dirpath)

config_args= read_configure_file("config.yaml")
sql_obj= MySql(
    host = config_args['confidential_info']['host'],
    port = config_args['confidential_info']['port'],
    user = config_args['confidential_info']['user'],
    password = config_args['confidential_info']['password'],
    database = config_args['confidential_info']['database'],)



def move_file(src_dir,dst_dir,file_extension):
    for file in glob.iglob(os.path.join(src_dir, file_extension)):
        shutil.copy(file, dst_dir)


def get_latest_file(directory:str)->list:
    csv_files=[]
    latest_dir=max(glob.glob(os.path.join(directory,'*')),key=os.path.getctime)
    for subdir,dirs,files in os.walk(latest_dir):
        for file in files:
            if file.endswith(".csv") and "checkpoint" not in file:
                csv_files.append(os.path.join(subdir,file))
    return csv_files


def handle_uploaded_file(f,file_path):
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def check_file_exists(file_path):
    try:
        if file_path.endswith('csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('tsv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('json'):
            df = pd.read_json(file_path)
        elif file_path.endswith('xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('xml'):
            df = pd.read_xml(file_path)
        else:
            df = False, None
        logging.info("Reading data from various file formats!")
        return True, df
    except Exception as e:
        logging.error(f"Cant read files due to: {e}!")
        return False,None



def fetch_num_cat_cols(df):
    try:
        num_cols = df.select_dtypes(include=['int','float']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object','bool']).columns.tolist()
        logging.info("Fetching categorical and numerical columns!")
        return num_cols, cat_cols

    except Exception as e:
        logging.error(f" Cant fetch columns due to: {e}!")



def delete_temporary_file(list_of_path):
    """
    remove_temp_files
    removes temp files from the specified paths
    params : list of paths
    """
    try:
        for path in list_of_path:
            os.remove(path)
            print('removed', path)
        logging.info("removed temp files successfully!")
        
    except Exception as e:
        logging.error(f"{e} occurred in deleting temp files!")



def update_data(df):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        Project_details= upload_Dataset.objects.get(id=int(id_))
        if Project_details.file_from_resources is not None:
            file_path=Project_details.file_from_resources    

        elif Project_details.file_from_resources is None:
            file_path=Project_details.file_upload.url


        full_path=os.path.join(next(absoluteFilePaths('media')),'uploads',os.path.basename(file_path))
        delete_temporary_file([full_path])
        df.to_csv(full_path, index=False)
        
        logging.info(f"DataFrame updated successfully!")
        return df
    except Exception as e:
        logging.error(f"{e} occurred in Updating Data!")

        

def save_project_encoding(encoder):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
        Project_details= upload_Dataset.objects.get(id=int(id_))
        Project_details.problem_statement_name= "_".join(Project_details.problem_statement_name.split())
        path = os.path.join(next(absoluteFilePaths('artifacts')),Project_details.problem_statement_name)
        if not os.path.isdir(path):
            os.makedirs(path)

        file_name = os.path.join(path, 'encoder.pkl')
        pickle.dump(encoder, open(file_name, 'wb'))

    except Exception as e:
        logging.error(f"Error occurred While saving project encoding: {e}!")


def load_project_encoding():
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        Project_details= upload_Dataset.objects.get(id=int(id_))
        Project_details.problem_statement_name= "_".join(Project_details.problem_statement_name.split())
        
        path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name, 'encoder.pkl')
        if os.path.exists(path):
            with open(path, 'rb') as pickle_file:
                model = pickle.load(pickle_file)
            return model
        else:
            return None
            
    except Exception as e:
        logging.error(f"Error occurred While loading project encoding: {e}!")


def save_project_scaler(scaler):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
        Project_details= upload_Dataset.objects.get(id=int(id_))
        Project_details.problem_statement_name= "_".join(Project_details.problem_statement_name.split())
        
        path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name)
        if not os.path.isdir(path):
            os.makedirs(path)

        file_name = os.path.join(path, 'scaler.pkl')
        pickle.dump(scaler, open(file_name, 'wb'))

    except Exception as e:
        logging.error(f"Error occurred While saving project scaler: {e}!")


def load_project_scaler():
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
        Project_details= upload_Dataset.objects.get(id=int(id_))
        Project_details.problem_statement_name= "_".join(Project_details.problem_statement_name.split())
        

        path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name, 'scaler.pkl')
        if os.path.exists(path):
            with open(path, 'rb') as pickle_file:
                model = pickle.load(pickle_file)
            return model
        else:
            return None

    except Exception as e:
        logging.error(f"Error occurred While loading project scaler: {e}!")



def save_project_pca(pca):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
        Project_details= upload_Dataset.objects.get(id=int(id_))
        Project_details.problem_statement_name= "_".join(Project_details.problem_statement_name.split())
        

        path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name)
        if not os.path.isdir(path):
            os.makedirs(path)

        file_name = os.path.join(path, 'pca.pkl')
        pickle.dump(pca, open(file_name, 'wb'))

    except Exception as e:
        logging.error(f"Error occurred While saving PCA: {e}!")

def load_project_pca():
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        Project_details= upload_Dataset.objects.get(id=int(id_))
        Project_details.problem_statement_name= "_".join(Project_details.problem_statement_name.split())
        

        path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name, 'pca.pkl')
        if os.path.exists(path):
            with open(path, 'rb') as pickle_file:
                model = pickle.load(pickle_file)
            return model
        else:
            return None
        
    except Exception as e:
        logging.error(f"Error occurred While loading PCA: {e}!")


def save_project_model(model, name='model_temp.pkl'):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]
        Project_details= upload_Dataset.objects.get(id=int(id_))
        Project_details.problem_statement_name= "_".join(Project_details.problem_statement_name.split())
        

        path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name)
        if not os.path.isdir(path):
            os.makedirs(path)

        file_name = os.path.join(path, name)
        pickle.dump(model, open(file_name, 'wb'))

    except Exception as e:
        logging.error(f"Error occurred While saving project model: {e}!")

def load_project_model():
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        Project_details= upload_Dataset.objects.get(id=int(id_))
        Project_details.problem_statement_name= "_".join(Project_details.problem_statement_name.split())
        
        
        path = os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name, 'model_temp.pkl')
        if os.path.exists(path):
            with open(path, 'rb') as pickle_file:
                model = pickle.load(pickle_file)
            return model
        else:
            return None

    except Exception as e:
        logging.error(f"Error occurred While loading project model: {e}!")


def save_numpy_array(X_train,X_test,y_train,y_test):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        Project_details= upload_Dataset.objects.get(id=int(id_))
        path=os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name,'dataset_splitter.npy')
        if os.path.isdir(path):
            os.makedirs(path)

        with open (path,'wb') as f:
            np.save(f,X_train)
            np.save(f,X_test)
            np.save(f,y_train)
            np.save(f,y_test)

    except Exception as e:
        logging.error(f"Error occurred While saving numpy array: {e}!")
    
def load_numpy_array(X_train,X_test,y_train,y_test):
    try:
        id_ = sql_obj.fetch_one(f"""SELECT project_id FROM get_project_id ORDER BY id DESC LIMIT 1;""")[0]

        Project_details= upload_Dataset.objects.get(id=int(id_))
        
        path=os.path.join(next(absoluteFilePaths('artifacts')), Project_details.problem_statement_name,'dataset_splitter.npy')
        if os.path.exists(path):
            with open (path,'rb') as f:
                X_train=np.load(f,allow_pickle=True)
                X_test=np.load(f,allow_pickle=True)
                y_train=np.load(f,allow_pickle=True)
                y_test=np.load(f,allow_pickle=True)
            return X_train,X_test,y_train,y_test
    except Exception as e:
        logging.error(f"Error occurred While loading numpy array: {e}!")
