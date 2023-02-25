from django.urls import path
from .views import *

urlpatterns = [

    path('delete-columns/',dataCleaning.delete_columns,name='delete-cols'),
    path('handle-duplicate/',dataCleaning.handle_duplicate_data,name='duplicates'),
    path('handle-missing/',dataCleaning.handle_missing_data,name='missings'),
    path('handle-inconsistent-data/',dataCleaning.handle_inconsistent_data,name='consistency'),

    path('merging/',dataIntegration.merging_function,name='merging'),
    
    path('dimension-reducer/',dataReduction.dimensionality_reduction,name='reducing'),

    path('handle-outliers/',dataTransformation.handle_outliers,name='outliers'),
    path('change-dtypes/',dataTransformation.change_dtype,name='change-dtype'),
    path('rename-column/',dataTransformation.rename_columns,name='rename'),
    path('data-splitter/',dataTransformation.data_splitter,name='split-data'),
    path('string-operations/',dataTransformation.string_operations,name='str-operation'),
]