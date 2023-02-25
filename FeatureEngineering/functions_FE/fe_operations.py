import pandas as pd
import numpy as np

## for Encoding Categorical Features
from sklearn.preprocessing import OrdinalEncoder,OneHotEncoder


## for Feature Scaling 
from sklearn.preprocessing import RobustScaler, StandardScaler,MinMaxScaler

from dataIngestion.models import upload_Dataset

## for imbalanced data handling
from sklearn.utils import resample
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek
from imblearn.over_sampling import SMOTE
from logger import logging


class FE:

    def encode(df,columns,enc_type,**kwargs):
        """
        
        Method Name: encode
        Description: This method encodes the categortical data into numerical data.
        
        Args:
            df: pandas dataframe([type])
            columns: list([type])
            enc_type:str([type])
            
        Output:
            Returns an encoder object and encoded dataframe.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            if enc_type == 'Label/Ordinal Encoder':
                label = OrdinalEncoder()
                encoded_matrix = label.fit_transform(df[columns])
                logging.info("Label/Ordinal Encoder implemented!")
                label_df=pd.DataFrame(encoded_matrix,columns=columns)
                return label_df, label

                
            elif enc_type == 'Pandas Dummies':
                df_=df.loc[:,columns]
                dummies_df = pd.get_dummies(df_)
                logging.info("Pandas get_dummies implemented!")
                return dummies_df, None
            
            
            elif enc_type == 'One Hot Encoder':
                onehot = OneHotEncoder(handle_unknown='ignore')
                encoded_matrix = onehot.fit_transform(df[columns]).toarray()
                cols_list=[]
                for col in columns:
                    cols_list.extend(df[col].unique().tolist())
                onehot_df=pd.DataFrame(encoded_matrix,columns=cols_list)
                logging.info("Onehotencoder implemented!")
                return onehot_df, onehot
                

        except Exception as e:
            logging.error(f"{e} occurred while Encoding!")

    
    @staticmethod
    def scale(data,cols,scaler_type):
        """
        
        Method Name: scale
        Description: This method standardizes the data into  a fixed range .
        
        Args:
            data: dataframe([type])
            columns: list([type])
            scaler_type: str([type])
            
        Output:
            Returns a scaler object and scaled dataframe .
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:    
            if scaler_type=='Robust Scaler':
                scaler=RobustScaler()
                scaled_data=scaler.fit_transform(data[cols])
                logging.info("Robust Scaler implemented!")



            elif scaler_type=='MinMax Scaler':
                scaler=MinMaxScaler()
                scaled_data=scaler.fit_transform(data[cols])
                logging.info("MinMax Scaler implemented!")
                

            elif scaler_type=='Standard Scaler':
                scaler=StandardScaler()
                scaled_data=scaler.fit_transform(data[cols])
                logging.info("StandardScaler implemented!")

            
            return pd.DataFrame(scaled_data,columns=cols),scaler
        
        except Exception as e:
            logging.error(f"{e} occurred while Feature Scaling!")


    @staticmethod
    def balance_data(df, kind: str, target):
        """
        
        Method Name: balance_data
        Description: This method equalizes the number of inputs for each output classes.
        
        Args:
            dataframe: dataframe([type])
            kind: str([type])
            target: int([type])
            
        Output:
            Returns a pandas dataframe with balanced outputs.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            if len(df[(df[target] == 0)]) >= len(df[(df[target] == 1)]):
                df_majority = df[(df[target] == 0)]
                df_minority = df[(df[target] == 1)]
            else:
                df_majority = df[(df[target] == 1)]
                df_minority = df[(df[target] == 0)]

            logging.info("Found Majority and Minority CLasses")
            if kind == 'US':
                rus = RandomUnderSampler(random_state=42)
                logging.info("UnderSampling Implemented")
                undersample_X, undersample_Y = rus.fit_resample(df.drop(target, axis=1), df[target])
                
                return pd.concat([pd.DataFrame(undersample_X), pd.DataFrame(undersample_Y)], axis=1)
                    
            elif kind=="OS":
                sm = SMOTE(random_state=42)
                oversampled_X, oversampled_Y = sm.fit_resample(df.drop(target, axis=1), df[target])
                logging.info("Smote Implemented")
                
                return pd.concat([pd.DataFrame(oversampled_X), pd.DataFrame(oversampled_Y)], axis=1)
                

            else:
                df_minority_upsampled = resample(df_minority,replace=True,n_samples=len(df_majority),random_state=42)
                logging.info("Resampling Implemented")
                return pd.concat([df_minority_upsampled, df_majority])
            
        except Exception as e:
            logging.error(f"error occured while sampling data at:{e}")
    

    def apply_custom_function(data, function):
        """
        Apply a custom function to a dataset.

        Args:
            data (pandas.DataFrame): The dataset to apply the function to.
            function (function): The custom function to apply to the dataset.

        Returns:
            pandas.DataFrame: The dataset with the function applied.
        """
        return function(data)
