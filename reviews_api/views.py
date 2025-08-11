# reviews_api/views.py

from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from .models import User, Movie, Review, Like
from .serializers import (
    UserSerializer,
    MovieSerializer,
    MovieCreateSerializer,
    ReviewSerializer,
    ReviewCreateUpdateSerializer,
)
from .permissions import IsReviewOwnerOrReadOnly
from .services import get_movie_details
from django.db import IntegrityError

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MovieCreateSerializer
        return MovieSerializer

    def perform_create(self, serializer):
        # Fetch movie details from OMDb API
        movie_data = get_movie_details(serializer.validated_data.get('title'))
        if movie_data and movie_data.get('Response') == 'True':
            serializer.validated_data['imdb_id'] = movie_data.get('imdbID')
            serializer.validated_data['plot'] = movie_data.get('Plot')
            serializer.validated_data['poster'] = movie_data.get('Poster')
            serializer.validated_data['release_year'] = movie_data.get('Year')
            serializer.validated_data['genre'] = movie_data.get('Genre')
            serializer.validated_data['director'] = movie_data.get('Director')
        serializer.save()

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        movie = self.get_object()
        reviews = Review.objects.filter(movie=movie)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    permission_classes = [IsReviewOwnerOrReadOnly]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rating', 'movie__title']
    search_fields = ['movie__title', 'comment']
    ordering_fields = ['rating', 'review_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReviewCreateUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def like(self, request, pk=None):
        review = self.get_object()
        user = request.user
        try:
            Like.objects.create(user=user, review=review)
            return Response({'status': 'liked'}, status=201)
        except IntegrityError:
            return Response({'status': 'already liked'}, status=400)