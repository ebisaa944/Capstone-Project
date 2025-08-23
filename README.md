# Capstone-Project

Movie Review API
This is a Django REST Framework-based API that allows users to create, read, update, and delete movie reviews. It integrates with an external API to fetch movie details and provides features for user authentication, liking reviews, and advanced data filtering.

Features
Authentication: Users can sign up and log in to manage their own reviews.

Movie Management: Movies are automatically created and populated with details from the OMDB API when a review is submitted for a new movie.

Reviews: Authenticated users can create, view, update, and delete their movie reviews.

Engagement: Users can "like" other users' reviews and post comments.

Advanced Filtering: Reviews can be filtered by rating or movie title, searched by title or comment, and ordered by rating or review date.

Scalability: The API uses custom pagination to ensure responses are efficient and not too large.

Security: A custom permission class ensures users can only modify their own reviews.

Technologies Used
Django: The web framework used to build the application.

Django REST Framework (DRF): The toolkit used to create the API.

Django-Filter: Used for advanced filtering capabilities.

Requests: A library for making HTTP requests to external APIs.

Installation
Follow these steps to get a copy of the project up and running on your local machine.

Clone the repository:

git clone https://github.com/ebisaa944/Capstone-Project.git
cd Movie_Review_API

Create and activate a virtual environment:

python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

Install dependencies:
Create a requirements.txt file with the following contents, then install them:

asgiref==3.9.1
certifi==2025.8.3
charset-normalizer==3.4.3
Django==5.2.5
django-filter==25.1
djangorestframework==3.16.1
idna==3.10
requests==2.32.4
sqlparse==0.5.3
tzdata==2025.2
urllib3==2.5.0
```bash
pip install -r requirements.txt

Set up your environment variables:
In movie_review_project/settings.py, ensure your OMDB_API_KEY is set.

Run database migrations:

python manage.py migrate

Create a superuser to access the admin panel:

python manage.py createsuperuser

Run the development server:

python manage.py runserver

The API will be running at http://127.0.0.1:8000/.

API Endpoints
Endpoint

Method

Description

/api/movies/

GET

List all movies.

/api/movies/

POST

Create a new movie entry from an external API.

/api/movies/<id>/reviews/

GET

Get all reviews for a specific movie.

/api/reviews/

GET

List all reviews. Supports filtering, searching, and ordering.

/api/reviews/

POST

Create a new review (requires authentication).

/api/reviews/<id>/

PUT/PATCH/DELETE

Update or delete a specific review.

/api/reviews/<id>/like/

POST

Like a specific review.

/api/users/

GET

List all users.

Author
Ebisa

License
This project is licensed under the MIT License.
