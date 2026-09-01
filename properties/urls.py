from django.urls import path

from .views import (
    FilterOptionsView,
    LocationListView,
    PropertyDetailView,
    PropertyImageUploadView,
    PropertyListCreateView,
    PropertyManageDetailView,
    PropertyManageListCreateView,
)

urlpatterns = [
    path("properties/", PropertyListCreateView.as_view(), name="property-list"),
    path(
        "properties/upload-images/",
        PropertyImageUploadView.as_view(),
        name="property-upload-images",
    ),
    path("properties/manage/", PropertyManageListCreateView.as_view(), name="property-manage-list"),
    path(
        "properties/manage/<int:pk>/",
        PropertyManageDetailView.as_view(),
        name="property-manage-detail",
    ),
    path("properties/<int:pk>/", PropertyDetailView.as_view(), name="property-detail"),
    path("locations/", LocationListView.as_view(), name="location-list"),
    path("filter-options/", FilterOptionsView.as_view(), name="filter-options"),
]
