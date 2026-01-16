from django.urls import path
from .import views
from sales.views import listorders,listcustomers,deepseek_stream_view

urlpatterns = [
    path('deepseek/',views.deepseek_stream_view),

    path('orders/', listorders),
    path('customers/', listcustomers),
]