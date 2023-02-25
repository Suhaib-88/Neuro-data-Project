from django.urls import path
from .views import *
urlpatterns = [
    path('Component/',ComponentsList.as_view(),name='component-list'),
    ]

htmx_urlpatterns = [
    path('addComponent/',add_component,name='add-component'),
    path('searchComponent',search_component,name='search-component'),
    path('delete-film/<int:pk>/', delete_component, name='delete-component'),
    path('clear/', clear_component, name='clear'),
    path('sort/', sort_component, name='sort'),

    ]

urlpatterns += htmx_urlpatterns


