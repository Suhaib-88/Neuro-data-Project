import pandas as pd
import numpy as np
import nltk
import re
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

from logger import logging

## for Imputing
from sklearn.impute import KNNImputer

## for PCA
from sklearn.decomposition import PCA

## for TSNE
from sklearn.manifold import TSNE
from sklearn.model_selection import train_test_split
# nltk.download('stopwords')


class Preprocessor:
    
    @staticmethod
    def delete_cols(df,column_names):
        """
        
        Method Name: delete_cols
        Description: This method deletes columns that contain Nan values.
        
        Args:
            df: dataframe([type])
            column_names: list([type])
            
        Output:
            Returns a pandas dataframe after dropping columns.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            list_cols=[i for i in column_names if i in df.columns] 
            
            df.drop(columns=list_cols,inplace=True)
            logging.info(f"Dropped columns: {list_cols}")

            return df
        except Exception as e:
            logging.error(f"Error while deleting columns occured at: {e}")

    @staticmethod
    def impute_nan_numerical(df, impute_type, columns, value=None):
        """
        
        Method Name: impute_nan_numerical
        Description: This method imputes numerical Nan values.
        
        Args:
            df: dataframe([type])
            columns: list([type])
            impute_type: str([type])
            
        Output:
            Returns a pandas dataframe after imputing numerical missing values.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        temp_list=list()
        temp_list.append(columns)
        for i in temp_list:
            if i in df.columns:
                continue
            else:
                logging.warning("Column not found")
                return 'Column Not Found'
        
        if impute_type == 'Mean':
            try:
                logging.info("Missing Values Imputed with Mean")
                return df[columns].fillna(np.mean(df[columns]))
            except Exception as e:
                logging.info(f"Error while imputing nan values with mean occured at :{e}")
        elif impute_type == 'Median':
            try:
                logging.info("Missing Values Imputed by Median")
                return df[columns].replace(np.nan,df[columns].median())

            except Exception as e:
                logging.info(f"Error while imputing nan values with median occured at :{e}")

        elif impute_type == 'Specific Value':
            try:
                logging.info("Missing Values imputed with Specific Value")
                return df[columns].fillna(value)
            except Exception as e:
                logging.info(f"Error while imputing nan values with specific value occured at :{e}")

        elif impute_type == 'KNNImputer':
            try:
                imputer = KNNImputer(n_neighbors=3)
                
                logging.info("Missing Values filled with neighbouring values using KNNImputer")
                return  pd.DataFrame(np.round(imputer.fit_transform(df[columns].values.reshape(-1,1))),columns=df[[columns]].columns)

            except Exception as e:
                logging.info(f"Error while imputing nan values with KNNImputer occured at :{e}")
        
        else:
            logging.warning("Invalid Input")
            return 'Type Not present'


    @staticmethod
    def impute_nan_categorical(df, impute_type, column, value):
        """
        
        Method Name: impute_nan_categorical
        Description: This method imputes categorical Nan values.
        
        Args:
            df: dataframe([type])
            impute_type: str([type])
            column:str([type])
            value:int([type])
            
        Output:
            Returns a pandas dataframe after imputing categorical missing values.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            temp_list=list()
            temp_list.append(column)
            for i in temp_list:
                if i in df.columns:
                    continue
                else:
                    return 'Column Not Found'
                    
            if impute_type == 'Replace':
                if column and value is not None:
                    logging.info("Categorical Values Filled with Replace")
                    return df[column].replace(np.nan,value)
                else:
                    return 'Provide valid column and value'

            elif impute_type == 'Mode':
                if column is not None:
                    logging.info("Categorical Values Filled with Mode")
                    return df[column].fillna(df.mode()[column][0])
                else:
                    return 'Provide valid column'

            elif impute_type == 'New Category':
                if column is not None:
                    logging.info("Categorical Values Filled with New Category")
                    return df[column].fillna(value)
                else:
                    return 'Provide valid column'
            else:
                logging.warning("Invalid Input")
                return 'Type not found'
        except Exception as e:
            logging.error(f"Error while imputing numerical nan values occured at :{e}")

    
    @staticmethod
    def remove_outliers(df,column,outlier_vals):
        """
        
        Method Name: remove_outliers
        Description: This method appends outlier values into a list in order to remove them.
        
        Args:
            df: dataframe([type])
            column: str([type])
            outlier_vals:list([type])
            
        Output:
            Returns a list of indexes for those columns that contain outlier values.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            idx=df[df[column].isin(outlier_vals)].index.tolist()
            return idx
        except Exception as e:
            logging.error("Error while removing outliers occured at: {e}")


    @staticmethod
    def clean_column(df, col_name, min_value, max_value):
        """
        Removes rows with inconsistent values in the specified column of a Pandas DataFrame.

        Args:
        - df: Pandas DataFrame
        - col_name: str, name of the column to clean
        - min_value: int or float, minimum valid value for the column
        - max_value: int or float, maximum valid value for the column

        Returns:
        - df: cleaned Pandas DataFrame
        """
        # Check for inconsistent values in the specified column
        invalid_data = df.loc[(df[col_name] < min_value) | (df[col_name] > max_value)]

        # Remove rows with inconsistent values
        df = df.query(f'{col_name} >= {min_value} and {col_name} <= {max_value}')

        # Print the number of removed rows, if any
        num_removed = len(invalid_data)
        if num_removed > 0:
            message=f"Removed {num_removed} rows with inconsistent {col_name} values"
        else:
            message=f"No rows with {col_name} values to remove"
        return message,df

    @staticmethod
    def integrate_data_function(df,df1,kind,**kwargs):
        """
        
        Method Name: integrate_data_function
        Description: This method integrates data from various sources into single dataframe.
        
        Args:
            df: dataframe([type])
            df1: dataframe([type])
            kind: str([type])
            
        Output:
            Returns data after performing integration function.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            if kind=="merge":
                data= pd.merge(df,df1,**kwargs)
            
            elif kind=="join":
                data=df.join(df1,**kwargs)

            elif kind=="concat":
                data= pd.concat([df,df1])

            return data
        except Exception as e:
            logging.error("Error while integrating data occured at: {e}")


    @staticmethod
    def dimension_reduction(data,kind ,number_of_components):
        """
        
        Method Name: dimension_reduction
        Description: This method reduces number of features/dimensions in the dataset.
        
        Args:
            data: dataframe([type])
            kind: str([type])
            number_of_components:int([type])
            
        Output:
            Returns a pandas dataframe after performing dimensionality reduction.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        
        try:
            if kind == "PCA":
                model = PCA(n_components=number_of_components)
                pca = model.fit_transform(data)
                logging.info("PCA implemented !")
                return pca, model
            
            if kind == "TSNE":
                model = TSNE(n_components = number_of_components)
                tsne = model.fit_transform(data)
                logging.info("TSNE implemented !")
                return tsne, model
        except Exception as e:
            logging.error(f"error while dimensionality reduction occured at:{e}") 


    def get_dtype(df, column_name):
        return df[column_name].dtypes

    def clean_data(df,column):
        try:
            df[column] = df[column].str.replace(r"[^0-9a-zA-Z\d\_]+", " ").str.strip()
            return df
        except Exception as e:
            logging.error(f"Error while cleaning data occured at: {e}")

    @staticmethod
    def convert_dtype(df, column_name,datatype):
        """
        
        Method Name: convert_dtype
        Description: This method converts datatype of a column in the dataset.
        
        Args:
            df: dataframe([type])
            column_name: str([type])
            datatype:str,int,bool,datetime([type])
            
        Output:
            Returns a pandas dataframe after converting data types.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            df[column_name]=df[column_name].astype(datatype)
            return df
        
        except Exception as e:
            logging.error(f"Error while converting datatypes occured at: {e}")


    @staticmethod
    def rename_columns(df,col_name,changed_col_name):
        """
        
        Method Name: rename_columns
        Description: This method renames a column by taking user input in the dataset.
        
        Args:
            df: dataframe([type])
            col_name: str([type])
            changed_col_name:str([type])
            
        Output:
            Returns a pandas dataframe after renaming the column.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            df.rename(columns={col_name:changed_col_name},inplace=True)
            return df
        except Exception as e:
            logging.error(f"Error while renaming columns occured at: {e}")

    
    @staticmethod
    def perform_string_operations_(df,column):
        """
        
        Method Name: perform_string_operations_
        Description: This method performs various string operations on the dataset.
        
        Args:
            df: dataframe([type])
            column: str([type])
            
        Output:
            Returns a pandas dataframe after performing various string operations.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            ps=PorterStemmer()
            corpus=[]
            corpus_len=[]
            for i in range(0,len(df)):
                content=re.sub('[^a-zA-Z]',' ',df[column][i])
                content=content.lower()
                content=content.split()
                
                content =[ps.stem(word) for word in content if not word in stopwords.words('english')]
                content = ' '.join(content)
                corpus.append(content)
                
                content_length=len(content.split())
                corpus_len.append(content_length)

            cleaned_df=pd.DataFrame({"Clean_data":corpus,"Clean_data_len":corpus_len})
            logging.info("Successfully performed string operations")
            return cleaned_df
        
        except Exception as e:    
            logging.error(f"Error while performing string operation occured at: {e}")
        
    @staticmethod
    def train_test_splitter(DataFrame, label,**kwargs):
        """
        
        Method Name: train_test_splitter
        Description: This method splits the dataset into train and test sets.
        
        Args:
            DataFrame: dataframe([type])
            label: str([type])
            
        Output:
            Returns training and test set of the data.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            X_train, X_test, y_train, y_test = train_test_split(DataFrame, label, **kwargs)
            logging.info("Train Test Split implemented!")
            return X_train, X_test, y_train, y_test
        except Exception as e:
            logging.error(f"{e} occurred in Train Test Split!")


    @staticmethod
    def handleDatetime(frame, cols):
        try:
            year = pd.DataFrame()
            day = pd.DataFrame()
            month = pd.DataFrame()
            count = 0
            for col in cols:
                frame[col] = pd.to_datetime(frame[col])

                year[f'{col}_{count}'] = pd.to_datetime(frame[col]).dt.year
                count += 1
                day[f'{col}_{count}'] = pd.to_datetime(frame[col]).dt.day
                count += 1
                month[f'{col}_{count}'] = pd.to_datetime(frame[col]).dt.month
                count += 1

            frame = pd.concat([frame, year, day, month], axis=1)
            logging.info("Handle Date-Time implemented!")
            return frame
        except Exception as e:
            logging.error(f"{e} occurred in Handle Date-Time Encoder!")
