from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as auth_views
from .views import (
    UserViewSet,
    MovieViewSet,
    ReviewViewSet,
    CommentViewSet,
    api_root,
    UserRegistrationView,
    ChangePasswordView
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'movies', MovieViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'comments', CommentViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    # The main API root and user registration endpoint.
    path('', api_root, name='api-root'),
    
    # URL to obtain an authentication token.
    path('api-token-auth/', auth_views.obtain_auth_token),

    # New URL for changing a password
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Include the router's URLs for the viewsets.
    path('', include(router.urls)),

    # This is an older URL for user registration. It's kept for reference.
    path('register/', UserRegistrationView.as_view(), name='user-register'),
]
