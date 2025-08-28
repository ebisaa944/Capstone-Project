# reviews_api/serializers.py

from rest_framework import serializers
from .models import User, Movie, Review, Like, Comment

class UserSerializer(serializers.ModelSerializer):
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'reviews']

class MovieSerializer(serializers.ModelSerializer):
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Movie
        fields = ['id', 'title', 'imdb_id', 'plot', 'poster', 'release_year', 'genre', 'director', 'reviews']

class MovieCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['title']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        # The 'text' field from the last attempt was incorrect.
        # You must check your 'reviews_api/models.py' file to find the correct
        # name of the field that stores the comment's content.
        # This code assumes it is called 'content'. Please update if needed.
        fields = ['id', 'content', 'created_at', 'user']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'review_date', 'user', 'movie', 'comments']
        read_only_fields = ['review_date']

class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'movie']

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'
