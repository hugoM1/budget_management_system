from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('brand/<int:brand_id>/', views.brand_detail, name='brand_detail'),
] 