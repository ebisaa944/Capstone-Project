# Capstone-Project

# 🎬 Movie Review API  
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)  
![Django](https://img.shields.io/badge/Django-5.2-green.svg)  
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A Django REST Framework-based API that allows users to **create, read, update, and delete movie reviews**.  
It integrates with the OMDB API to fetch movie details and includes **authentication, liking, comments, and advanced filtering** features.  

---

## 🚀 Features

- **Authentication:** Users can sign up and log in to manage their own reviews.  
- **Movie Management:** Movies are auto-created with details fetched from the OMDB API.  
- **Reviews:** Authenticated users can create, view, update, and delete their reviews.  
- **Engagement:** Users can like reviews and post comments.  
- **Advanced Filtering:** Search and filter reviews by title, comment, rating, or review date.  
- **Scalability:** Custom pagination ensures lightweight API responses.  
- **Security:** Custom permissions ensure users can only modify their own reviews.  

---

## 🛠️ Technologies Used

- **Django** – Web framework  
- **Django REST Framework (DRF)** – API toolkit  
- **Django-Filter** – Advanced filtering support  
- **Requests** – HTTP client for external API calls  

---

## ⚙️ Installation

Follow these steps to set up the project locally:  

1. Clone the repository
```bash
git clone https://github.com/ebisaa944/Capstone-Project.git
cd Movie_Review_API

2. Create and activate a virtual environment
python -m venv venv

On Windows:
.\venv\Scripts\activate

On macOS/Linux:
source venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Set up environment variables
In movie_review_project/settings.py, configure your OMDB_API_KEY.

5. Apply migrations
python manage.py migrate

6. Create a superuser
python manage.py createsuperuser

7. Run the development server
python manage.py runserver
Your API will be live at:
👉 http://127.0.0.1:8000/

📡 API Endpoints
Endpoint	Method	Description
/api/movies/	GET	List all movies
/api/movies/	POST	Create a new movie from OMDB API
/api/movies/<id>/reviews/	GET	Get all reviews for a specific movie
/api/reviews/	GET	List all reviews (with filtering & search)
/api/reviews/	POST	Create a new review (requires authentication)
/api/reviews/<id>/	PUT/PATCH/DELETE	Update or delete a review
/api/reviews/<id>/like/	POST	Like a review
/api/users/	GET	List all users

👨‍💻 Author
Ebisa Achame Mihirate