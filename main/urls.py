from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('',home,name = 'home'),
    path('create_cv/', create_cv, name='create_cv'),
    path('resume_preview/<str:resume_id>/', resume_preview, name='resume_preview'),
    path('payment_success/<str:resume_id>/', payment_success, name='payment_success'),
    path('payment_process/', payment_process, name='payment_process'),
    path('payment_failed/', payment_failed, name='payment_failed'),
    path('enhance/', enhance_text, name='enhance_text'),
    path('submit_feedback/', submitFeedback, name='submit_feedback'),
]