from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class User(AbstractUser):
    # Django's AbstractUser provides username, email, password, etc.
    # You can add custom fields here if needed.
    pass

class Movie(models.Model):
    title = models.CharField(max_length=100)
    imdb_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    plot = models.TextField(null=True, blank=True)
    poster = models.URLField(max_length=200, null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    genre = models.CharField(max_length=128, null=True, blank=True)
    director = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    review_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} review for {self.movie.title}'

# Add to reviews_api/models.py
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')
# reviews_api/models.py
# Add this model
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.review.id}'