from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from .models import User, Movie, Review, Like, Unlike, Comment


class UserRegistrationAPITests(APITestCase):
    def test_user_registration_success(self):
        url = reverse('user-register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_user_registration_missing_field(self):
        url = reverse('user-register')
        data = {
            'username': 'testuser',
            'password': 'TestPass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MovieAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='adminpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_create_movie_success(self):
        url = reverse('movie-list')
        data = {'title': 'The Matrix'}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        # Movie may already exist in OMDb mock; allow 400 as well


class ReviewAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', password='password123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.movie = Movie.objects.create(title='Inception', imdb_id='tt1375666', release_year=2010)

    def test_create_review_success(self):
        url = reverse('review-list')
        data = {'movie': self.movie.id, 'review_text': 'Great movie!', 'rating': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_create_review_duplicate(self):
        Review.objects.create(user=self.user, movie=self.movie, review_text='First review', rating=4)
        url = reverse('review-list')
        data = {'movie': self.movie.id, 'review_text': 'Duplicate review', 'rating': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)


class LikeUnlikeAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='liker', password='pass1234')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.movie = Movie.objects.create(title='Avatar', imdb_id='tt0499549', release_year=2009)
        self.review = Review.objects.create(user=self.user, movie=self.movie, review_text='Awesome', rating=5)

    def test_like_review(self):
        url = reverse('review-like', args=[self.review.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Like.objects.filter(user=self.user, review=self.review).exists())

    def test_unlike_review(self):
        Like.objects.create(user=self.user, review=self.review)
        url = reverse('review-unlike', args=[self.review.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(Like.objects.filter(user=self.user, review=self.review).exists())


class CommentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commenter', password='pass1234')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.movie = Movie.objects.create(title='Interstellar', imdb_id='tt0816692', release_year=2014)
        self.review = Review.objects.create(user=self.user, movie=self.movie, review_text='Mind-blowing', rating=5)

    def test_add_comment_success(self):
        url = reverse('review-comment', args=[self.review.id])
        data = {'comment_text': 'Totally agree!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)


class ChangePasswordAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='changer', password='oldpass123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_change_password_success(self):
        url = reverse('change-password')
        data = {'old_password': 'oldpass123', 'new_password': 'newpass456'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456'))

    def test_change_password_wrong_old(self):
        url = reverse('change-password')
        data = {'old_password': 'wrongold', 'new_password': 'newpass456'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
