from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


# ------------------------------
# User Model
# ------------------------------

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Designed for flexibility to allow future custom fields or behaviors.
    """
    pass


# ------------------------------
# Movie Model
# ------------------------------

class Movie(models.Model):
    """
    Stores information about movies.
    
    Fields may be automatically populated from an external API (e.g., OMDB).
    """
    title = models.CharField(max_length=255)
    release_year = models.PositiveIntegerField(null=True, blank=True)
    imdb_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    plot = models.TextField(null=True, blank=True)
    poster = models.URLField(null=True, blank=True)
    genre = models.CharField(max_length=255, null=True, blank=True)
    director = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title


# ------------------------------
# Review Model
# ------------------------------

class Review(models.Model):
    """
    Represents a user's review of a movie.
    
    - Each review is associated with one user and one movie.
    - Users can review each movie only once.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Rating must be between 0.0 and 5.0",
    )
    review_text = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "movie")  # ensures a user can only review a movie once
        ordering = ["-review_date"]  # newest reviews appear first

    def __str__(self):
        return f"{self.user.username} → {self.movie.title}"


# ------------------------------
# Like Model
# ------------------------------

class Like(models.Model):
    """
    Represents a user's like on a review.
    
    - One like per user per review.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "review")

    def __str__(self):
        return f"{self.user.username} liked review {self.review.id}"


# ------------------------------
# Unlike Model
# ------------------------------

class Unlike(models.Model):
    """
    Represents a user's unlike on a review.
    
    - One unlike per user per review.
    - Useful for tracking removal of a previous like.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="unlikes")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="unlikes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "review")

    def __str__(self):
        return f"{self.user.username} unliked review {self.review.id}"


# ------------------------------
# Comment Model
# ------------------------------

class Comment(models.Model):
    """
    Represents a comment made by a user on a review.
    
    - Linked to both a user and a review.
    - Ordered by creation date, newest first.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} on review {self.review.id}"
