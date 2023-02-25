from django.urls  import path
from .views import *

urlpatterns= [
    path('encoder/',FE_feature_encoding.as_view(),name='encoding'),
    path('imbalanced-data/',FE_handle_imbalanced_data.as_view(),name='imbalanced'),
    path('scaler/',FE_feature_scaling.as_view(),name='scaling'),
]