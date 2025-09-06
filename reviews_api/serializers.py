from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Movie, Review, Like, Comment, Unlike
import re

User = get_user_model()


# ------------------------------
# User Serializers
# ------------------------------

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering new users.
    Includes:
    - Password validation rules
    - Password confirmation check
    - Unique email enforcement
    """
    password = serializers.CharField(write_only=True, required=True)
    password_confirmation = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirmation")
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value):
        """Ensure the provided email is unique across users."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        """Perform custom password validation."""
        password, password_confirmation = data.get("password"), data.get("password_confirmation")

        if password != password_confirmation:
            raise serializers.ValidationError("Passwords do not match.")

        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")

        if not re.search(r"[a-z]", password):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")

        if sum(1 for c in password if c.isupper()) < 2:
            raise serializers.ValidationError("Password must contain at least two uppercase letters.")

        if not re.search(r"\d", password):
            raise serializers.ValidationError("Password must contain at least one number.")

        if not re.search(r"[!@#$%^&*()\-+?_=,<>/]", password):
            raise serializers.ValidationError("Password must contain at least one special character.")

        return data

    def create(self, validated_data):
        """Create a new user instance with validated data."""
        validated_data.pop("password_confirmation")
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user details.
    - Includes related reviews by primary key reference.
    """
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "reviews"]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing a user's password.
    - Validates old password
    - Ensures new password and confirmation match
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        """Leverage Django's password validators for the new password."""
        validate_password(value)
        return value

    def validate(self, data):
        """Ensure new password matches confirmation."""
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "New passwords must match."})
        return data


# ------------------------------
# Movie Serializers
# ------------------------------

class MovieCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a movie.
    Only requires title; details are populated from external API.
    """
    class Meta:
        model = Movie
        fields = ["title"]


class MovieSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying movie details.
    - Includes related reviews
    - Converts director string into a list of individual names
    """
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    directors = serializers.SerializerMethodField()

    def get_directors(self, obj):
        """Split director string into a list of names."""
        return [d.strip() for d in obj.director.split(",")] if obj.director else []

    class Meta:
        model = Movie
        fields = ["id", "title", "imdb_id", "plot", "poster",
                  "release_year", "genre", "directors", "reviews"]


# ------------------------------
# Review & Comment Serializers
# ------------------------------

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for comments on reviews.
    - Includes nested user information
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "content", "created_at", "user", "review"]


class UnlikeSerializer(serializers.ModelSerializer):
    """
    Serializer for tracking unlikes on reviews.
    - Read-only fields prevent user input modification
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = Unlike
        fields = ["user", "created_at"]
        read_only_fields = ["user", "created_at"]


class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for tracking likes on reviews.
    - Read-only fields prevent user input modification
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ["user", "created_at"]
        read_only_fields = ["user", "created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying reviews.
    - Nested representation of user, movie, and comments
    - Includes likes and unlikes as serialized lists of users
    """
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes = serializers.SerializerMethodField()
    unlikes = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "rating", "review_text", "review_date", "user", "movie", "comments", "likes", "unlikes"]
        read_only_fields = ["review_date", "likes", "unlikes"]

    def get_likes(self, obj):
        """Return users who have liked this review."""
        liked_users = User.objects.filter(likes__review=obj)
        return UserSerializer(liked_users, many=True).data

    def get_unlikes(self, obj):
        """Return users who have unliked this review."""
        unliked_users = User.objects.filter(unlikes__review=obj)
        return UserSerializer(unliked_users, many=True).data


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating or updating a review.
    """
    class Meta:
        model = Review
        fields = ["id", "rating", "review_text", "movie"]
