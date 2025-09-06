# reviews_api/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


# We extend the AbstractUser model to potentially add custom fields in the future.
class User(AbstractUser):
    """Custom user model."""
    pass


class Movie(models.Model):
    """
    Model for storing movie details.
    The data for these fields will be auto-populated from the OMDB API.
    """
    title = models.CharField(max_length=255)
    release_year = models.IntegerField(null=True, blank=True)
    imdb_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    plot = models.TextField(null=True, blank=True)
    poster = models.URLField(null=True, blank=True)
    genre = models.CharField(max_length=255, null=True, blank=True)
    director = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title


class Review(models.Model):
    """
    Model for user reviews of a movie.
    Each review is linked to a user and a movie.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    # Renamed this field to 'review_text' to avoid confusion with the 'Comment' model.
    review_text = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures a user can only review a specific movie once.
        unique_together = ('user', 'movie')
        ordering = ['-review_date']

    def __str__(self):
        return f"{self.user.username}'s review of {self.movie.title}"


class Like(models.Model):
    """
    Model to track which users have liked which reviews.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents a user from liking the same review more than once.
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user.username} likes {self.review.id}"


class Comment(models.Model):
    """
    Model for comments on reviews.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on review {self.review.id}"