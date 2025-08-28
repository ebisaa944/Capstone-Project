# In reviews_api/views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.reverse import reverse
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db import IntegrityError
import re # This import was missing and is now added.

from .models import User, Movie, Review, Like, Comment
from .serializers import (
    UserSerializer,
    MovieSerializer,
    MovieCreateSerializer,
    ReviewSerializer,
    ReviewCreateUpdateSerializer,
    LikeSerializer,
    CommentSerializer,
)
from .permissions import IsReviewOwnerOrReadOnly # Assuming this permission is defined in a separate file
from .services import get_movie_details


# Custom permission to allow only the owner to edit or delete their own objects.
# This is a more general-purpose version than the one in your code.
class IsOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a 'user' attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request.
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user

# The root of the Movie Review API, providing a list of available endpoints.
@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'movies': reverse('movie-list', request=request, format=format),
        'reviews': reverse('review-list', request=request, format=format),
        'comments': reverse('comment-list', request=request, format=format),
    })


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class MovieViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows movies to be viewed or created.
    """
    queryset = Movie.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'imdb_id', 'genre', 'director', 'plot']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MovieCreateSerializer
        return MovieSerializer

    def perform_create(self, serializer):
        # Fetch movie details from OMDb API
        movie_data = get_movie_details(serializer.validated_data.get('title'))
        
        # Check if the movie was found
        if movie_data and movie_data.get('Response') == 'True':
            imdb_id = movie_data.get('imdbID')
            
            # Check if the movie already exists in the database
            try:
                # If it exists, we raise a ValidationError to prevent a duplicate entry.
                existing_movie = Movie.objects.get(imdb_id=imdb_id)
                raise ValidationError(f"Movie '{existing_movie.title}' already exists with IMDb ID {imdb_id}.")
            except Movie.DoesNotExist:
                # If the movie does not exist, we proceed to create it.
                
                # Update the serializer's validated data with fetched details
                serializer.validated_data['imdb_id'] = imdb_id
                serializer.validated_data['plot'] = movie_data.get('Plot')
                serializer.validated_data['poster'] = movie_data.get('Poster')
                
                # Handle the year field which can sometimes be a range.
                year_str = movie_data.get('Year', '')
                try:
                    serializer.validated_data['release_year'] = int(year_str)
                except (ValueError, TypeError):
                    match = re.search(r'^\d{4}', year_str)
                    serializer.validated_data['release_year'] = int(match.group(0)) if match else None

                serializer.validated_data['genre'] = movie_data.get('Genre')
                serializer.validated_data['director'] = movie_data.get('Director')
                
                # Save the movie with the validated and enriched data.
                serializer.save()
        else:
            raise ValidationError({'error': 'Movie not found on OMDB.'})

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        movie = self.get_object()
        reviews = Review.objects.filter(movie=movie)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reviews to be viewed, created, updated, or deleted.
    """
    queryset = Review.objects.all()
    # Using the custom permission class to check for ownership.
    permission_classes = [IsOwnerOrReadOnly]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rating', 'movie__title']
    search_fields = ['movie__title', 'comment']
    ordering_fields = ['rating', 'review_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReviewCreateUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        # Automatically associate the review with the current authenticated user.
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        # Ensure the user is the owner before updating the review.
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to edit this review.")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Ensure the user is the owner before deleting the review.
        if instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to delete this review.")
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        review = self.get_object()
        user = request.user
        try:
            Like.objects.create(user=user, review=review)
            return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'status': 'already liked'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        review = self.get_object()
        user = request.user
        try:
            like = Like.objects.get(user=user, review=review)
            like.delete()
            return Response({'status': 'unliked'}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response({'status': 'not liked'}, status=status.HTTP_400_BAD_REQUEST)

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments on reviews to be viewed, created, updated, or deleted.
    """
    # Order comments by creation date to show them chronologically.
    queryset = Comment.objects.all().order_by('created_at')
    serializer_class = CommentSerializer
    # Using the IsOwnerOrReadOnly to ensure only the owner can edit/delete.
    permission_classes = [IsOwnerOrReadOnly]
    
    def perform_create(self, serializer):
        # Automatically associate the comment with the current authenticated user.
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Ensure the user is the owner before updating the comment.
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to edit this comment.")
        serializer.save()

    def perform_destroy(self, instance):
        # Ensure the user is the owner before deleting the comment.
        if instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to delete this comment.")
        instance.delete()
