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
    ChangePasswordView,
)

# Initialize DRF router and register viewsets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"movies", MovieViewSet, basename="movie")
router.register(r"reviews", ReviewViewSet, basename="review")
router.register(r"comments", CommentViewSet, basename="comment")

urlpatterns = [
    # Root endpoint
    path("", api_root, name="api-root"),

    # Authentication and user management
    path("api-token-auth/", auth_views.obtain_auth_token, name="api-token-auth"),
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),

    # ViewSets from the router
    path("", include(router.urls)),
]
