from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from .models import Movie, Review, Like, Comment
import re

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user registration.
    """
    password = serializers.CharField(write_only=True, required=True)
    password_confirmation = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirmation')
        extra_kwargs = {
            'email': {'required': True},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("Passwords do not match.")

        password = data.get('password')
        
        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")

        if not re.search(r'[a-z]', password):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        uppercase_count = sum(1 for c in password if c.isupper())
        if uppercase_count < 2:
            raise serializers.ValidationError("Password must contain at least two uppercase letters.")

        if not re.search(r'\d', password):
            raise serializers.ValidationError("Password must contain at least one number.")

        special_characters = r'[!@#$%^&*()-+?_=,<>/]'
        if not re.search(special_characters, password):
            raise serializers.ValidationError("Password must contain at least one special character.")

        return data

    def create(self, validated_data):
        # We pop the password_confirmation field before creating the user
        validated_data.pop('password_confirmation')
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


# ---
# New Password Change Serializer
# ---

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change requests.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords must match."})
        return data


# ---
# Movie, Review, and Comment Serializers
# ---

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
        # The field name for the comment's text is 'content'.
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
        # 'review_text' is now used to match the updated Review model.
        fields = ['id', 'rating', 'review_text', 'review_date', 'user', 'movie', 'comments']
        read_only_fields = ['review_date']

class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """
    A separate serializer for creating and updating reviews,
    only requiring the movie, rating, and comment fields.
    """
    class Meta:
        model = Review
        # 'review_text' is now used to match the updated Review model.
        fields = ['id', 'rating', 'review_text', 'movie']

class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Like model.
    """
    class Meta:
        model = Like
        fields = '__all__'
