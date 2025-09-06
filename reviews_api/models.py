# reviews_api/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Custom user model with flexibility for future extensions."""
    pass


class Movie(models.Model):
    """
    Stores movie details.
    Data for these fields may be auto-populated from the OMDB API.
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


class Review(models.Model):
    """
    User reviews of movies.
    Each review is linked to one user and one movie.
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
        unique_together = ("user", "movie")  # user can only review a movie once
        ordering = ["-review_date"]

    def __str__(self):
        return f"{self.user.username} → {self.movie.title}"


class Like(models.Model):
    """
    Tracks which users have liked which reviews.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "review")  # one like per user per review

    def __str__(self):
        return f"{self.user.username} liked review {self.review.id}"


class Comment(models.Model):
    """
    Comments made by users on reviews.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} on review {self.review.id}"
