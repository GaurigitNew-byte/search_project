from django.urls import path
from .views import SearchViewPage,DownloadCSVView
urlpatterns = [
    path('', SearchViewPage.as_view(), name='search_home'),
    path('download_csv/', DownloadCSVView.as_view(), name='download_csv'),
]
