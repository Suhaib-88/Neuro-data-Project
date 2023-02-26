from django.urls import path,include
from .views import *


urlpatterns = [
    path('missing/',EDA_missing.as_view(),name='missing'),
    path('show-dataset',EDA_showDataset.as_view(),name='show-dataset'),
    path('data-summary',EDA_summary.as_view(),name='summary'),
    path('correlation-report/correlation-heatmap',EDA_correlation.as_view(),name='corr-heatmap'),
    path('correlation-report/correlated-columns',EDA_higly_correlated.as_view(),name='corr-cols'),
    path('outlier-report/',EDA_outliers.as_view(),name='outlier'),
    path('statistical-report/',EDA_statistical_functions.as_view(),name='statistics'),
    path('plots/',EDA_plots.as_view(),name='plots'),
    path('plot_charts/',plot_helper,name='plotter'),
]