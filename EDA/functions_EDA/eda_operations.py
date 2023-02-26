import pandas as pd
import numpy as np
from logger import logging

pd.set_option('display.width', 1000)
pd.set_option('colheader_justify', 'center')


class EDA:
    data_types = ['bool', "int_", "int8", "int16", "int32", "int64", "uint8", "uint16",
                  "uint32", "uint64", "float_", "float16", "float32", "float64"]
    
    @staticmethod
    def get_data_summary(df):
        """
        
        Method Name: get_data_summary
        Description: This method delivers the data summary of a pandas dataframe.
        
        Args:
            df: dataframe([type]) 
        Output:
            A pandas DataFrame along with 5 point summary.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        dicts_summary= {
        'Column':[],
        'Min':[],
        'Q1':[],
        'Median':[],
        'Q3':[],
        'Max':[],
        'Memory_usage':[],
        'Number_of_Unique_Values':[],
        
        }
        try:
            df_numeric=df.select_dtypes(include=['int','float'])
            for col in df_numeric.columns:
                df_numeric_clean=df[pd.to_numeric(df[col],errors='coerce').notnull()][col]
                
                dicts_summary['Column'].append(col)
                dicts_summary['Min'].append(np.min(df_numeric_clean))
                dicts_summary['Q1'].append(np.percentile(df_numeric_clean, 25))
                dicts_summary['Median'].append(np.median(df_numeric_clean))
                dicts_summary['Q3'].append(np.percentile(df_numeric_clean, 75))
                dicts_summary['Max'].append(np.max(df_numeric_clean))
                dicts_summary['Memory_usage'].append(df_numeric_clean.memory_usage())
                dicts_summary['Number_of_Unique_Values'].append(df_numeric_clean.nunique())
            
            logging.info('Five Point Summary Implemented!')
        except Exception as e:
            logging.error(f"{e} occurred in Five Point Summary!")
        
        return pd.DataFrame(dicts_summary).sort_values(by=['Column'], ascending=True).reset_index(drop=True)
         

    @staticmethod
    def dataType_info(df):
        df1 = pd.DataFrame()
        df1['Column'] = df.dtypes.index.tolist()
        df1['Data_type'] = df.dtypes.values.tolist()
        df1['Nan_value_count'] = df.isna().sum().values.tolist()
        
        return df1

    @staticmethod
    def correlation_report(dataframe, select_method):
        """
        
        Method Name: correlation_report
        Description: This method returns the correlation report of a pandas dataframe.
        
        Args:
            dataframe: dataframe([type])
            select_method: str([type]) 
        Output:
            A pandas DataFrame of correlation report.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            logging.info("Correlation Report Implemented!")
            return dataframe.corr(method=select_method)

        except Exception as e:
            logging.error(f"{e} occurred in Correlation Plot!")

    @staticmethod
    def high_correlation_matrix(df:pd.DataFrame,threshold:float):
        """
        
        Method Name: high_correlation_matrix
        Description: This method returns the higly correlated features in the form of a set.
        
        Args:
            df: dataframe([type])
            threshold: float([type]) 
        Output:
            Returns a set of highly correlated columns
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        corelated_col=set()
        corr_matrix=df.corr()
        for i in range (len(corr_matrix.columns)):
            for j in range (i):
                if abs(corr_matrix.iloc[i,j])>threshold:
                    colname=corr_matrix.columns[i]
                    corelated_col.add(colname)                    
        return corelated_col

    @staticmethod
    def get_no_records(dataframe,count,order_by):
        """
        
        Method Name: get_no_records
        Description: This method returns a dataset with the specified number of rows.
        
        Args:
            dataframe: dataframe([type])
            count: int([type])
            order_by: str([type]) 
        Output:
            Returns a dataframe with set number of records.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            if order_by == 'tail':
                logging.info("Get No of Records by tail Implemented!")
                return dataframe.tail(count)

            elif order_by == 'sample':
                logging.info("Get No of Records by sample Implemented!")
                return dataframe.sample(count)
                
            else:
                logging.info("Get No of Records by head Implemented!")
                return dataframe.head(count)

        except Exception as e:
            logging.error(f"{e} occurred in Get No of Records!")


    @staticmethod
    def find_dtypes(df3):
        try:
            for i in df3.columns:
                yield str(df3[i].dtypes)
            logging.info("Find Dtypes Implemented!")
        except Exception as e:
            logging.error(f"{e} occurred in Find Dtypes!")

    @staticmethod
    def find_median(df3):
        try:
            for i in df3.columns:
                if df3[i].dtypes in EDA.data_types:
                    yield str(round(df3[i].median(), 2))
                else:
                    yield str('-')
            logging.info("Find Median Implemented!")
        except Exception as e:
            logging.error(f"{e} occurred in Find Median!")

    @staticmethod
    def find_mode(df3):
        try:
            for i in df3.columns:
                mode = df3[i].mode()
                yield mode[0] if len(mode) > 0 else '-'
            logging.info("Find Mode Implemented!")
        except Exception as e:
            logging.error(f"{e} occurred in Find Mode!")

    @staticmethod
    def find_mean(df3):
        try:
            for i in df3.columns:
                if df3[i].dtypes in EDA.data_types:
                    yield str(round(df3[i].mean(), 2))
                else:
                    yield str('-')
            logging.info("Find Mean Implemented!")
        except Exception as e:
            logging.error(f"{e} occurred in Find Mean!")

    @staticmethod
    def missing_cells_table(df):
        """
        
        Method Name: missing_cells_table
        Description: This method returns the missing value details in the form of pandas dataframe.
        
        Args:
            df: dataframe([type])
        Output:
            Returns missing value report as a pandas dataframe
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            df = df[[col for col in df.columns if df[col].isnull().any()]]

            if len(df.columns)>0:
                missing_value_df = pd.DataFrame({
                    'Column': df.isnull().sum().index,
                    'Missing values': df.isnull().sum().values,
                    'Missing values (%)': (df.isnull().sum() / df.shape[0]) * 100,
                    'Mean': EDA.find_mean(df),
                    'Median': EDA.find_median(df),
                    'Mode': EDA.find_mode(df),
                    'Datatype': EDA.find_dtypes(df)
                }).sort_values(by='Missing values', ascending=False)
                logging.info("Missing Cells Table Implemented!")
                return missing_value_df.reset_index(drop=True)
            else:
                logging.info("Missing Cells Table is None!")
                return None

        except Exception as e:
            logging.error(f"{e} occurred in Missing Cells Table!")

    @staticmethod
    def outlier_detection_iqr(dataframe, lower_bound=25, upper_bound=75):
        """
        
        Method Name: outlier_detection_iqr
        Description: This method returns an outlier report with the help of Inter Quantile Range(IQR) .
        
        Args:
            dataframe: dataframe([type])
            lower_bound: lower limit of the quantile
            upper_bound: upper limit of the quantile
 
        Output:
            Returns a pandas dataframe containing IQR outlier report
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        outlier_dict = {'Features': [], f'IQR ({lower_bound}-{upper_bound})': [], 'Q3 + 1.5*IQR': [], 'Q1 - 1.5*IQR': [],
                   'Upper outlier count': [],
                   'Lower outlier count': [], 'Total outliers': [], 'Outlier percent': []}
        for column in dataframe.select_dtypes(include=np.number).columns:
            try:
                upper_count = 0
                lower_count = 0
                q1 = np.percentile(dataframe[column].fillna(dataframe[column].mean()), lower_bound)
                q3 = np.percentile(dataframe[column].fillna(dataframe[column].mean()), upper_bound)
                IQR = round(q3 - q1)
                upper_limit = round(q3 + (IQR * 1.5))
                lower_limit = round(q1 - (IQR * 1.5))

                for item in dataframe[column].fillna(dataframe[column].mean()):
                    if item > upper_limit:
                        upper_count += 1
                    elif item < lower_limit:
                        lower_count += 1

                outlier_dict['Features'].append(column)
                outlier_dict[f'IQR ({lower_bound}-{upper_bound})'].append(IQR)
                outlier_dict['Q3 + 1.5*IQR'].append(upper_limit)
                outlier_dict['Q1 - 1.5*IQR'].append(lower_limit)
                outlier_dict['Upper outlier count'].append(upper_count)
                outlier_dict['Lower outlier count'].append(lower_count)
                outlier_dict['Total outliers'].append(upper_count + lower_count)
                outlier_dict['Outlier percent'].append(round((upper_count + lower_count) / len(dataframe[column]) * 100, 2))
            except Exception as e:
                logging.error(f"{e} occurred in Outlier Detection IQR!")
        logging.info("Outlier Detection IQR Implemented!")
        return pd.DataFrame(outlier_dict).sort_values(by=['Total outliers'], ascending=False)

    @staticmethod
    def z_score_outlier_detection(dataframe):
        """
        
        Method Name: z_score_outlier_detection
        Description: This method returns an outlier report with the help of z-Score .
        
        Args:
            dataframe: dataframe([type])
 
        Output:
            Returns a pandas dataframe containing z-score outlier report
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        outlier_dict = {"Features": [], "Mean": [], "Standard deviation": [], 'Upper outlier count': [],
                   'Lower outlier count': [], 'Total outliers': [], 'Outlier percent': []}

        for column in dataframe.select_dtypes(include=np.number).columns:
            try:
                upper_outlier = 0
                lower_outlier = 0
                col_mean = np.mean(dataframe[column])
                col_std = np.std(dataframe[column])

                for item in dataframe[column]:
                    z = (item - col_mean) / col_std
                    if z > 3:
                        upper_outlier += 1
                    elif z < -3:
                        lower_outlier += 1

                outlier_dict["Features"].append(column)
                outlier_dict["Mean"].append(col_mean)
                outlier_dict["Standard deviation"].append(col_std)
                outlier_dict["Upper outlier count"].append(upper_outlier)
                outlier_dict["Lower outlier count"].append(lower_outlier)
                outlier_dict["Total outliers"].append(upper_outlier + lower_outlier)
                outlier_dict["Outlier percent"].append(
                    round((upper_outlier + lower_outlier) / len(dataframe[column]) * 100, 2))

            except Exception as e:
                logging.error(f"{e} occurred in Outlier Detection Zscore!")
        df = pd.DataFrame(outlier_dict).sort_values(by=['Total outliers'], ascending=False).reset_index()
        logging.info("Outlier Detection Zscore Implemented!")
        return df

    @staticmethod
    def outlier_detection(data, kind):
        """
        
        Method Name: outlier_detection
        Description: This method returns an outlier report in a pandas dataframe .
        
        Args:
            dataframe: dataframe([type])
            kind: str([type])
            
        Output:
            Returns a pandas dataframe containing based on selected outlier detection method.
        
        On Failure: Log Exception
        
        Written By: Suhaib
        Version: 1.0
        Revisions: None
        
        """
        try:
            data = pd.Series(data)
            if kind == 'z-score':
                outliers = []
                # threshold = 3
                mean = np.mean(data)
                std = np.std(data)
                data = np.array(data)
                for da in data:
                    val = (da - mean) / std
                    if val > 3:
                        outliers.append(da)
                    elif val < -3:
                        outliers.append(da)
                return outliers
            elif kind == 'iqr':
                outliers = []
                q1, q3 = np.percentile(data, [25, 75])
                iqr = q3 - q1
                data = np.array(data)
                lower_bound_value = q1 - 1.5 * iqr
                upper_bound_value = q3 + 1.5 * iqr

                for da in data:
                    if da < lower_bound_value or da > upper_bound_value:
                        outliers.append(da)

                return outliers
            logging.info("Outlier Detection Implemented!")
        except Exception as e:
            logging.error(f"{e} occurred in Outlier Detection Zscore!")



class StatisticalDataAnalysis:

    def __init__(self, data):
        self.data = data

    def choose_statistical_function(self, function_name, window_size=None):
        if function_name == 'Window':
            return self.window(window_size)
        elif function_name == 'Expanding':
            return self.expanding()
        elif function_name == 'Rolling':
            return self.rolling(window_size)
        elif function_name == 'Percentage change':
            return self.pct_change()
        elif function_name == 'Covariance':
            return self.cov()
        elif function_name == 'Correlation':
            return self.corr()
        elif function_name == 'Ranking':
            return self.rank()
        else:
            logging.error('Function not found.')
            return None

    def window(self, window_size):
        logging.info("Statistical function:Window rolling with mean Implemented!")
        return self.data.rolling(window=window_size)

    def expanding(self):
        logging.info("Statistical function: Expanding Implemented!")
        return self.data.expanding()

    def rolling(self, window_size):
        logging.info("Statistical function:Window rolling with standard deviation Implemented!")
        return self.data.rolling(window=window_size)

    def pct_change(self):
        logging.info("Statistical function:Percentage change Implemented!")
        return self.data.pct_change()

    def cov(self):
        logging.info("Statistical function:Covariance Implemented!")
        return self.data.cov()

    def corr(self):
        logging.info("Statistical function:Correlation Implemented!")
        return self.data.corr()

    def rank(self):
        logging.info("Statistical function:Data Ranking Implemented!")
        return self.data.rank()
