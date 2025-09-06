from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Movie, Review, Like, Comment
import re

User = get_user_model()


# ------------------------------
# User Serializers
# ------------------------------

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for registering new users with password validation.
    """
    password = serializers.CharField(write_only=True, required=True)
    password_confirmation = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirmation")
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
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
        validated_data.pop("password_confirmation")
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user details with related reviews.
    """
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "reviews"]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for handling user password change requests.
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "New passwords must match."})
        return data


# ------------------------------
# Movie Serializers
# ------------------------------

class MovieCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new movie (fetching from an external API).
    Only requires the title.
    """
    class Meta:
        model = Movie
        fields = ["title"]


class MovieSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying movie details with related reviews.
    Converts 'director' string into a list of names.
    """
    reviews = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    directors = serializers.SerializerMethodField()

    def get_directors(self, obj):
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
    Serializer for comments with nested user details.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "content", "created_at", "user", "review"]


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviews with nested user, movie, and comments.
    """
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ["id", "rating", "review_text", "review_date", "user", "movie", "comments"]
        read_only_fields = ["review_date"]


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating or updating reviews.
    """
    class Meta:
        model = Review
        fields = ["id", "rating", "review_text", "movie"]


# ------------------------------
# Like Serializer
# ------------------------------

class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for likes.
    """
    class Meta:
        model = Like
        fields = "__all__"
