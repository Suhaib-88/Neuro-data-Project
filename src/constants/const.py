GRAPH_TYPES_LIST = ["Selet Any", "Bar Graph", "Histogram", "Scatter Plot", "Pie Chart", "Line Chart", "Box Plot",
                     "Dist Plot", "Heat Map"]
                     
GRAPH_TYPES_LIST_2 = ["Selet Any", "Scatter Plot", "Line Chart", "Heat Map"]

ALLOWED_DTYPES = ['object', 'int64', 'float64', 'bool', 'datetime64', 'category', 'timedelta']

ALLOWED_SCALE_TYPES=['MinMax Scaler', 'Standard Scaler', 'Robust Scaler']

GET_ENCODING_TYPES=['Pandas Dummies', 'Label/Ordinal Encoder', 'One Hot Encoder']

NUMERIC_NAN_TYPES = ['Mean', 'Median', 'Specific Value', 'KNNImputer']
CATEGORIC_NAN_TYPES = ['Mode', 'New Category', 'Replace']
ALL_NAN_TYPES = ['Mean', 'Median', 'Specific Value', 'KNNImputer','Mode', 'New Category', 'Replace']


SHOWDATA_FUNCTIONS=["head","sample","tail"]

CORRELATION_METHODS=['pearson','spearman','kendall']

OUTLIER_DETECT_METHODS=['z-score','iqr']

STATISTICAL_FUNCTIONS=['Window','Expanding','Rolling','Percentage change','Covariance','Correlation','Ranking']

SAMPLING_METHODS=['UnderSampling','Resample','SMOTE']

AGGREGATE_FUNCTIONS=['count','nunique','sum','min','mean','max']

SORT_METHODS=["Ascending","Descending"]

DIMENSIONALITY_REDUCTION_TYPES=["PCA","TSNE"]

PROJECT_ACTIONS=    {
    "INITIALIZATION":1,
    "ENCODING" : 2,
    "SCALING" : 3,
    "PCA" : 4,
    }

AGG_FUNCTIONS=['sum','min','avg','max','first','last','count']
CONDITIONS=['greater than equals','lesser than equals','equals','not equals']
DTYPES=['string','number','integer']
OPERATIONS=['add','subtract','divide','multiply']
MODES=['full-outer','half-outer','inner']
CASING=['upper','lower']
FILE_METHODS=['csv','json']
OPERATIONS_PIVOT=['Sum','Mean','Standard Deviation']

INTEGRATE_FUNCTIONS=['merge','join','concat']