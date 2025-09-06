from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, BasePermission
from rest_framework.reverse import reverse
from rest_framework.exceptions import PermissionDenied, ValidationError
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
)
from .services import get_movie_details


# Custom permission to allow users to view their own profile or if they are an admin.
class IsUserOrAdmin(BasePermission):
    """
    Object-level permission to allow a user to view/edit their own profile
    or if the user is a superuser.
    """
    def has_object_permission(self, request, view, obj):
        # A superuser can access any object.
        if request.user.is_superuser:
            return True
        
        # All other users can only access their own profile.
        return obj == request.user


# Custom permission to allow only the owner to edit or delete their own objects.
class IsOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a 'user' attribute that links it to the User model.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request.
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions (POST, PUT, DELETE) are only allowed to the owner of the object.
        return obj.user == request.user


# The root of the Movie Review API, providing a list of available endpoints.
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    This is the API root, providing a discoverable list of all main API endpoints.
    It also serves as a registration endpoint for new users.
    """
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    response_data = {
        'users': reverse('user-list', request=request),
        'movies': reverse('movie-list', request=request),
        'reviews': reverse('review-list', request=request),
        'comments': reverse('comment-list', request=request),
        'register': reverse('user-register', request=request, format=format)
    }
    return Response(response_data)


# New view for user registration.
class UserRegistrationView(generics.CreateAPIView):
    """
    A view for handling user registration. This endpoint allows a new user to be created.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    It customizes the standard ModelViewSet to enforce that users can only interact with their own profile.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsUserOrAdmin]


class MovieViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows movies to be viewed or created.
    This viewset includes search, filtering, and custom creation logic that pulls from an external API.
    """
    queryset = Movie.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'imdb_id', 'genre', 'director', 'plot']
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        """
        Dynamically returns a different serializer based on the action.
        """
        if self.action == 'create':
            return MovieCreateSerializer
        return MovieSerializer

    def _process_movie_data(self, serializer, movie_data):
        """
        Helper method to process and validate movie data from the OMDB API.
        """
        imdb_id = movie_data.get('imdbID')
        
        # Check if the movie already exists in the database by its unique IMDb ID.
        if Movie.objects.filter(imdb_id=imdb_id).exists():
            raise ValidationError(f"Movie already exists with IMDb ID {imdb_id}.")
        
        # Update the serializer's validated data with fetched details.
        serializer.validated_data['imdb_id'] = imdb_id
        serializer.validated_data['plot'] = movie_data.get('Plot')
        serializer.validated_data['poster'] = movie_data.get('Poster')
        
        # Handle the year field which can sometimes be a range (e.g., "2001-2003").
        year_str = movie_data.get('Year', '')
        try:
            serializer.validated_data['release_year'] = int(year_str)
        except (ValueError, TypeError):
            # If the year is not a simple integer, use a regex to extract the first four digits.
            match = re.search(r'^\d{4}', year_str)
            serializer.validated_data['release_year'] = int(match.group(0)) if match else None

        serializer.validated_data['genre'] = movie_data.get('Genre')
        
        # Check for "N/A" from the API and set the director to None if found.
        director_data = movie_data.get('Director')
        serializer.validated_data['director'] = None if director_data == 'N/A' else director_data
        
        serializer.save()

    def perform_create(self, serializer):
        """
        Overridden method to handle the creation of a new movie.
        Before saving, it fetches additional movie details from the OMDb API.
        """
        movie_data = get_movie_details(serializer.validated_data.get('title'))
        
        if movie_data and movie_data.get("Response") == "True":
            self._process_movie_data(serializer, movie_data)
        else:
            raise ValidationError({'error': 'Movie not found on OMDB.'})

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        A custom action to retrieve all reviews for a specific movie.
        """
        movie = self.get_object()
        reviews = Review.objects.filter(movie=movie)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reviews to be viewed, created, updated, or deleted.
    """
    queryset = Review.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rating', 'movie__title']
    search_fields = ['movie__title', 'comment']
    ordering_fields = ['rating', 'review_date']

    def get_serializer_class(self):
        """
        Dynamically returns the correct serializer based on the action.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return ReviewCreateUpdateSerializer
        if self.action == 'comment':
            return CommentSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        """
        This method is called when a new review is created.
        It automatically associates the review with the current authenticated user.
        """
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            return Response({'non_field_errors': ['You have already reviewed this movie.']}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        A custom action to add a like to a review.
        """
        review = self.get_object()
        user = request.user
        try:
            Like.objects.create(user=user, review=review)
            return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'status': 'already liked'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """
        A custom action to remove a like from a review.
        """
        review = self.get_object()
        user = request.user
        try:
            like = Like.objects.get(user=user, review=review)
            like.delete()
        except Like.DoesNotExist:
            return Response({'status': 'not liked'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'unliked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def comment(self, request, pk=None):
        """
        A custom action to add a comment to a review.
        """
        review = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=self.request.user, review=review)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments on reviews to be viewed, created, updated, or deleted.
    """
    queryset = Comment.objects.all().order_by('created_at')
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        """
        This method is called when a new comment is created.
        """
        serializer.save(user=self.request.user)
