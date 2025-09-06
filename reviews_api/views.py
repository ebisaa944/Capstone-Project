from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters, generics, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db import IntegrityError
import re

from .models import User, Movie, Review, Like, Comment
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    MovieSerializer,
    MovieCreateSerializer,
    ReviewSerializer,
    ReviewCreateUpdateSerializer,
    LikeSerializer,
    CommentSerializer,
    ChangePasswordSerializer,
)
from .services import get_movie_details
from .pagination import StandardResultsSetPagination
from .permissions import IsOwnerOrReadOnly, IsUserOrAdmin


# ------------------------------
# API Root
# ------------------------------

@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    Root API endpoint listing available routes.
    """
    return Response({
        "users": reverse("user-list", request=request, format=format),
        "movies": reverse("movie-list", request=request, format=format),
        "reviews": reverse("review-list", request=request, format=format),
        "comments": reverse("comment-list", request=request, format=format),
        "register": reverse("user-register", request=request, format=format),
        "change-password": reverse("change-password", request=request, format=format),
    })


# ------------------------------
# User Views
# ------------------------------

class UserRegistrationView(generics.CreateAPIView):
    """
    Endpoint for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """
    Endpoint for viewing and editing users.
    Only allows superusers or the user themselves.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsUserOrAdmin]
    pagination_class = StandardResultsSetPagination


# ------------------------------
# Movie Views
# ------------------------------

class MovieViewSet(viewsets.ModelViewSet):
    """
    Endpoint for viewing and creating movies.
    Supports search, filtering, and external API integration.
    """
    queryset = Movie.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "imdb_id", "genre", "director", "plot"]
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        return MovieCreateSerializer if self.action == "create" else MovieSerializer

    def _process_movie_data(self, serializer, movie_data):
        imdb_id = movie_data.get("imdbID")

        if Movie.objects.filter(imdb_id=imdb_id).exists():
            raise ValidationError({"imdb_id": f"Movie already exists with IMDb ID {imdb_id}."})

        year_str = movie_data.get("Year", "")
        try:
            release_year = int(year_str)
        except (ValueError, TypeError):
            match = re.search(r"^\d{4}", year_str)
            release_year = int(match.group(0)) if match else None

        serializer.save(
            imdb_id=imdb_id,
            plot=movie_data.get("Plot", ""),
            poster=movie_data.get("Poster", ""),
            release_year=release_year,
            genre=movie_data.get("Genre", ""),
            director=None if movie_data.get("Director") == "N/A" else movie_data.get("Director"),
        )

    def perform_create(self, serializer):
        movie_data = get_movie_details(serializer.validated_data.get("title"))
        if movie_data and movie_data.get("Response") == "True":
            self._process_movie_data(serializer, movie_data)
        else:
            raise ValidationError({"error": "Movie not found on OMDB."})

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        """
        Retrieve reviews for a given movie.
        """
        movie = self.get_object()
        reviews = Review.objects.filter(movie=movie)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


# ------------------------------
# Review Views
# ------------------------------

class ReviewViewSet(viewsets.ModelViewSet):
    """
    Endpoint for viewing, creating, updating, and deleting reviews.
    """
    queryset = Review.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["rating", "movie__title"]
    search_fields = ["movie__title", "review_text"]
    ordering_fields = ["rating", "review_date"]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ReviewCreateUpdateSerializer
        if self.action == "comment":
            return CommentSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({"non_field_errors": ["You have already reviewed this movie."]})

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        """
        Like a review.
        """
        review = self.get_object()
        try:
            Like.objects.create(user=request.user, review=review)
        except IntegrityError:
            return Response({"status": "already_liked"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": "liked"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def unlike(self, request, pk=None):
        """
        Remove like from a review.
        """
        review = self.get_object()
        like = Like.objects.filter(user=request.user, review=review).first()
        if not like:
            return Response({"status": "not_liked"}, status=status.HTTP_400_BAD_REQUEST)
        like.delete()
        return Response({"status": "unliked"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def comment(self, request, pk=None):
        """
        Add a comment to a review.
        """
        review = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, review=review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ------------------------------
# Comment Views
# ------------------------------

class CommentViewSet(viewsets.ModelViewSet):
    """
    Endpoint for viewing and managing comments on reviews.
    """
    queryset = Comment.objects.all().order_by("created_at")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        review_id = self.request.data.get("review")
        if not review_id:
            raise serializers.ValidationError({"review": "This field is required."})

        review = get_object_or_404(Review, id=review_id)
        serializer.save(user=self.request.user, review=review)


# ------------------------------
# Password Change
# ------------------------------

class ChangePasswordView(generics.UpdateAPIView):
    """
    Endpoint for changing the authenticated user's password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        if not user.check_password(serializer.validated_data.get("old_password")):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data.get("new_password"))
        user.save()

        return Response({
            "status": "success",
            "code": status.HTTP_200_OK,
            "message": "Password updated successfully"
        })
