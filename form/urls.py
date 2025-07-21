from django.urls import path
from .views import *
from . import views
urlpatterns = [
    path('', views.form_builder_view, name='form-builder'),

    path('submit-contact/', views.submit_contact_form, name='submit_contact'),

]