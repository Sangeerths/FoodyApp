from django.urls import path
from . import views  

urlpatterns = [
    path('', views.home, name='home'),
    # add more paths here
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
]
