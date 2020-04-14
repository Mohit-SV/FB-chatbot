from django.conf.urls import url
from .views import Talk_Back_View
urlpatterns = [
                url(r'^webhook/?$', Talk_Back_View.as_view())                 
               ]
               