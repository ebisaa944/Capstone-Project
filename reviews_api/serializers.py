# reviews_api/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Movie, Review, Like, Comment

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user registration.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {
            'email': {'required': True},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Includes a read-only field to show related reviews.
    """
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'reviews']

class MovieCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new Movie.
    Only requires the title to fetch data from an external API.
    """
    class Meta:
        model = Movie
        fields = ['title']

class MovieSerializer(serializers.ModelSerializer):
    """
    Serializer for the Movie model.
    Includes a read-only field to show related reviews.
    """
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    # Use a SerializerMethodField to convert the director string to a list of names.
    directors = serializers.SerializerMethodField()

    def get_directors(self, obj):
        # Splits the director string by commas and strips whitespace.
        # This will return a list of director names.
        if obj.director:
            return [d.strip() for d in obj.director.split(',')]
        return []
    
    class Meta:
        model = Movie
        # Now we use 'directors' instead of 'director' in the fields.
        fields = ['id', 'title', 'imdb_id', 'plot', 'poster', 'release_year', 'genre', 'directors', 'reviews']

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model.
    Uses a nested UserSerializer to display details of the comment's author.
    """
    # The 'user' field is a nested serializer that displays the user's details.
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        # The field name for the comment's text is 'content', not 'comment'.
        # We also add the 'review' field to show which review the comment belongs to.
        fields = ['id', 'content', 'created_at', 'user', 'review']

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for the Review model.
    Includes nested serializers for the user, movie, and related comments.
    """
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'review_date', 'user', 'movie', 'comments']
        read_only_fields = ['review_date']

class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """
    A separate serializer for creating and updating reviews,
    only requiring the movie, rating, and comment fields.
    """
    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'movie']

class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Like model.
    """
    class Meta:
        model = Like
        fields = '__all__'
