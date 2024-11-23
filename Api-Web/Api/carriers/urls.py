from django.urls import path
from .views import index, add_user, insert, balance, edit_carrier, update_patent, delete, patents, add_patent, insert_patent, unknown_references, select_owner,add_remmit, select_patent
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [

    path('', index, name="index"),
    path('unknown_references', unknown_references, name="unknown_references"),
    path('select_patent', select_patent, name="select_patent"),
    path('add_remmit', add_remmit, name="add_remmit"),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('select_owner', select_owner, name="select_owner"),
    path('logout/', LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('add_user', add_user, name="add_user"),
    path('add_patent', add_patent, name="add_patent"),
    path('insert', insert, name="insert"),  
    path('insert_patent', insert_patent, name="insert_patent"),
    path('balance', balance, name="balance"),
    path('patents', patents, name="patents"),
    path('edit_carrier', edit_carrier, name="edit_carrier"),
    path('update_patent', update_patent, name="update_patent"),
    path('delete', delete, name="delete"),
]
