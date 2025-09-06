from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'movies', views.MovieViewSet, basename='movie')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'comments', views.CommentViewSet, basename='comment')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    # The browsable API is now the default view for the root URL
    path('', include(router.urls)),
    # Add a separate URL for user registration.
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
]
