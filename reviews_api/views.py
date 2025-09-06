from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status, filters, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from django.db import IntegrityError
import re

from .models import User, Movie, Review, Like, Comment, Unlike
from .serializers import (
    UserRegistrationSerializer, UserSerializer,
    MovieSerializer, MovieCreateSerializer,
    ReviewSerializer, ReviewCreateUpdateSerializer,
    CommentSerializer, ChangePasswordSerializer
)
from .services import get_movie_details
from .pagination import StandardResultsSetPagination
from .permissions import IsOwnerOrReadOnly, IsUserOrAdmin


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    API root endpoint providing a discoverable map of all main API routes.
    Links differ based on authentication status (registration vs password change).
    """
    data = {
        'users': reverse('user-list', request=request),
        'movies': reverse('movie-list', request=request),
        'reviews': reverse('review-list', request=request),
    }
    if request.user.is_authenticated:
        data['change-password'] = reverse('change-password', request=request, format=format)
    else:
        data['register'] = reverse('user-register', request=request, format=format)
    return Response(data)


class UserRegistrationView(generics.CreateAPIView):
    """
    Handles user registration:
    - Accepts registration data
    - Creates a new user
    - Generates an authentication token for immediate use
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        headers = self.get_success_headers(serializer.data)
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED, headers=headers)


class UserViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD operations on User model.
    - Custom permission ensures users can only modify their profile unless admin.
    - Supports retrieving current authenticated user details via `current` action.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsUserOrAdmin]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def current(self, request):
        """Retrieve details of the currently authenticated user."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class MovieViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for movies with integration to OMDb API for enrichment.
    Features:
    - Search, filter, and ordering
    - Custom movie creation to fetch details from external API
    - Nested reviews retrieval for a specific movie
    """
    queryset = Movie.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'imdb_id', 'genre', 'director', 'plot']
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """Use a specialized serializer when creating a movie, default otherwise."""
        return MovieCreateSerializer if self.action == 'create' else MovieSerializer

    def _extract_release_year(self, year_str):
        """Safely extract release year from string, handling ranges or invalid data."""
        try:
            return int(year_str)
        except (ValueError, TypeError):
            match = re.search(r'^\d{4}', year_str)
            return int(match.group(0)) if match else None

    def _process_movie_data(self, serializer, movie_data):
        """Populate serializer validated_data with OMDb details and save the movie."""
        if Movie.objects.filter(imdb_id=movie_data.get('imdbID')).exists():
            raise ValidationError(f"Movie already exists with IMDb ID {movie_data.get('imdbID')}.")
        serializer.validated_data.update({
            'imdb_id': movie_data.get('imdbID'),
            'plot': movie_data.get('Plot'),
            'poster': movie_data.get('Poster'),
            'release_year': self._extract_release_year(movie_data.get('Year', '')),
            'genre': movie_data.get('Genre'),
            'director': None if movie_data.get('Director') == 'N/A' else movie_data.get('Director')
        })
        serializer.save()

    def perform_create(self, serializer):
        """Fetch movie data from OMDb API before saving a new movie."""
        movie_data = get_movie_details(serializer.validated_data.get('title'))
        if movie_data and movie_data.get("Response") == "True":
            self._process_movie_data(serializer, movie_data)
        else:
            raise ValidationError({'error': 'Movie not found on OMDB.'})

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Retrieve all reviews associated with this movie."""
        movie = self.get_object()
        serializer = ReviewSerializer(movie.reviews.all(), many=True)
        return Response(serializer.data)


class EmptySerializer(serializers.Serializer):
    """Placeholder serializer for actions that do not require input data."""
    pass


class ReviewViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for reviews.
    Includes custom actions:
    - like / unlike a review
    - add a comment to a review
    Handles permission: only owner or read-only for others.
    """
    queryset = Review.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rating', 'movie__title']
    search_fields = ['movie__title', 'review_text']
    ordering_fields = ['rating', 'review_date']
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """Select the appropriate serializer depending on action type."""
        if self.action in ['create', 'update', 'partial_update']:
            return ReviewCreateUpdateSerializer
        if self.action == 'comment':
            return CommentSerializer
        if self.action in ['like', 'unlike']:
            return EmptySerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """Attach review to the current authenticated user and handle duplicates."""
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({'non_field_errors': ['You have already reviewed this movie.']})

    def _handle_like_unlike(self, review, user, action_type):
        """
        Unified logic to handle liking or unliking a review.
        Returns serialized review data and appropriate HTTP status.
        """
        if action_type == 'like':
            Unlike.objects.filter(user=user, review=review).delete()
            try:
                Like.objects.create(user=user, review=review)
            except IntegrityError:
                return {'status': 'already liked'}, status.HTTP_400_BAD_REQUEST
            message = 'Review liked successfully!'
            status_code = status.HTTP_201_CREATED
        else:
            if not Like.objects.filter(user=user, review=review).exists():
                return {'status': 'cannot unlike an unliked review'}, status.HTTP_400_BAD_REQUEST
            Like.objects.filter(user=user, review=review).delete()
            try:
                Unlike.objects.create(user=user, review=review)
            except IntegrityError:
                return {'status': 'already unliked'}, status.HTTP_400_BAD_REQUEST
            message = 'Review unliked successfully!'
            status_code = status.HTTP_200_OK

        serializer = ReviewSerializer(review, context={'request': self.request})
        return {'message': message, 'review': serializer.data}, status_code

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Like a review, removing any existing unlike."""
        review = self.get_object()
        return Response(*self._handle_like_unlike(review, request.user, 'like'))

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        """Unlike a review only if previously liked."""
        review = self.get_object()
        return Response(*self._handle_like_unlike(review, request.user, 'unlike'))

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def comment(self, request, pk=None):
        """Add a comment to a review."""
        review = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user, review=review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.ModelViewSet):
    """CRUD for comments on reviews with proper ownership permissions."""
    queryset = Comment.objects.all().order_by('created_at')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        """Associate comment with authenticated user and existing review."""
        review_id = self.request.data.get('review')
        if not review_id:
            raise serializers.ValidationError({'review': 'This field is required.'})
        review = get_object_or_404(Review, id=review_id)
        serializer.save(user=self.request.user, review=review)


class ChangePasswordView(generics.UpdateAPIView):
    """
    Allows an authenticated user to change their password.
    Verifies old password before updating.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not user.check_password(serializer.data.get("old_password")):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.data.get("new_password"))
        user.save()
        return Response({
            'status': 'success',
            'code': status.HTTP_200_OK,
            'message': 'Password updated successfully',
            'data': None
        })
