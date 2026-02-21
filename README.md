## NewsApp - Django News Application

A full-stack Django news platform featuring role-based access control, REST API with JWT authentication.

## About The Project

NewsApp is a full-stack Django web application that serves as a news publishing platform. It allows independent journalists and publishers to submit articles, editors to review and approve content, and readers to subscribe to their favorite journalists and publishers.

### Features 

### User Management
1. Custom user registration with role selection (Reader, Journalist, Editor).
2. JWT token-based authentication for API access.
3. Django Groups for automatic permission assignment.
4. Role-based dashboard showing relevant content per user.

### Publisher Management 
1. **Staff-controlled publisher creation** - Only staff members can create publishers
2. **Join/Leave functionality** - Journalists and editors can join/leave publishers
3. **Publisher browsing** - All users can view publishers and their members
4. **Publisher-article association** - Articles can be linked to publishers
5. **Subscription system** - Readers can subscribe to publishers for notifications


### Reader Features
1. Browse all approved articles and newsletters.
2. Subscribe to publishers and individual journalists.
3. Receive email notifications when subscribed content is published.
4. Access personalized article feed via API

### Journalist Features
1. Create, edit and delete own articles.
2. Create and manage newsletters with curated articles.
3. Submit articles for editorial review.
4. View approval status of submitted articles.

### Editor Features
1. Review pending articles in a dedicated dashboard.
2. Approve or reject article submissions.
3. Edit and delete any article or newsletter.
4. Tabbed interface showing pending vs approved content

## REST API 
1. Full CRUD operations for articles and newsletters.
2. JWT token authentication for all endpoints.
3. Role-based API permissions
4. Subscribed articles endpoint for personalized feeds
5. Browseable API via Django REST Framework

### Technologies Used 
1. Python 3.14.2
2. Django 6.0.2
3. Django REST Framework 3.16.1
4. Djangorestframework-simplejwt 5.5.1
5. pymsql 1.1.2
6. MariaDB
7. Bootstrap 5.3

### Getting Started

### Installation 

### Step1: Navigate to the project directory
```
cd news_application 
```

### Step 2: Create virtual environment 
``` 
python -m venv venv

# Activate on Windows 
venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

### Step 3: Install dependencies
```
pip install -r requirements.txt
```

### Step 4: Create MariaDB database
```
mysql -u root -p
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### Configuration 

### Step 1: Configure database in news_project/settings.py

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'news_db',
        'USER': 'your_mariadb_username',
        'PASSWORD': 'your_mariadb_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### Step 2: Configure email settings 

```
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### Step 3: Configure Twitter/X API

```
TWITTER_BEARER_TOKEN = 'your-twitter-bearer-token'
TWITTER_API_KEY = 'your-api-key'
TWITTER_API_SECRET = 'your-api-secret'
```

### Running The Project 

Navigate to the following directory:

```
cd news_application\news_project
```
## Step 1: Set up user groups and permissions

```
python manage.py setup_groups
```

## Step 2: Apply database migrations 

```
python manage.py makemigrations
python manage.py migrate
```

## Step 3: Create a superuser(optional)

```
python manage.py createsuperuser
```
Enter username, email, and password when prompted.


**Step 4: Register models with Django admin**

Ensure `news_app/admin.py` contains:
```python
from django.contrib import admin
from .models import CustomUser, Article, Newsletter, Publisher

admin.site.register(CustomUser)
admin.site.register(Article)
admin.site.register(Newsletter)
admin.site.register(Publisher)
```

**Step 5: Run the development server**
```bash
python manage.py runserver
```

**Step 6: Visit the application**
```
http://127.0.0.1:8000/
```

# Publisher Management

Publishers are news organizations that journalists can join to publish articles under their name. This section covers the complete publisher management workflow.

### Creating Publishers

**Method 1: Django Admin Panel (Recommended for Initial Setup)**

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to Django admin:
   ```
   http://127.0.0.1:8000/admin/
   ```

3. Login with your superuser credentials

4. Click on **"Publishers"** in the left menu

5. Click **"Add Publisher"** button in the top right

6. Enter publisher details:
   - **Name**: The publisher name (e.g., "BBC News", "CNN", "The Guardian")

7. Click **"Save"**

**Recommended Publishers to Create:**

```
International Publishers:
- BBC News
- CNN
- Reuters
- The Guardian
- Al Jazeera

South African Publishers:
- News24
- Daily Maverick
- Mail & Guardian
- eNCA
- SABC News
- TimesLIVE

Tech/Specialized Publishers:
- TechCrunch
- The Verge
- Wired
```

---

**Method 2: Web Interface (For Staff Users)**

1. Make a user a staff member (via admin panel):
   - Go to http://127.0.0.1:8000/admin/
   - Click on "Users"
   - Select the user
   - Check "Staff status" checkbox
   - Click "Save"

2. Login as the staff user

3. Navigate to:
   ```
   http://127.0.0.1:8000/publishers/
   ```

4. Click **"+ Create Publisher"** button

5. Enter publisher name and submit

---

### Joining Publishers (Journalists & Editors)

**Prerequisites:**
- User must be registered with role 'journalist' or 'editor'
- At least one publisher must exist

**Steps:**

1. Login as a journalist or editor

2. Navigate to:
   ```
   http://127.0.0.1:8000/publishers/
   ```

3. Browse available publishers

4. Click **"Join as Journalist"** or **"Join as Editor"** button

5. Confirm the join action

6. Success! You'll see a badge showing **"Joined as Journalist"** or **"Joined as Editor"**

**What Joining a Publisher Enables:**

For **Journalists**:
- Can select the publisher when creating articles
- Articles published under publisher's name
- Publisher's subscribers receive notifications when article is approved

For **Editors**:
- Can approve articles associated with this publisher
- Can manage publisher's content
- Part of publisher's editorial team

---

### Leaving Publishers

**Steps:**

1. Navigate to:
   ```
   http://127.0.0.1:8000/publishers/
   ```

2. Find the publisher you're currently a member of (shows "Joined" badge)

3. Click **"Leave Publisher"** button

4. Confirm the leave action

5. You're no longer associated with that publisher

**Effects of Leaving:**
- Can no longer publish articles under that publisher
- Existing articles under that publisher remain unchanged
- Can rejoin at any time

---

### Subscribing to Publishers (Readers)

**Prerequisites:**
- User must be registered with role 'reader'
- Publisher must exist

**Steps:**

1. Login as a reader

2. Navigate to:
   ```
   http://127.0.0.1:8000/publishers/
   ```

3. Browse publishers

4. Click **"Subscribe"** button on desired publishers

5. You'll receive email notifications when this publisher's articles are approved

**Managing Subscriptions:**
- Go to http://127.0.0.1:8000/subscriptions/
- View all your subscribed publishers
- Unsubscribe by clicking the button again

---

### API Documentation 

## Authentication 
All API endpoints require JWT authentication 

## Get Token:

```
POST /api/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}

Response:
{
    "access": "eyJ0eXAiOiJKV1...",
    "refresh": "eyJ0eXAiOiJKV1..."
}
```

## Use Token:

```Authorization: Bearer <your_access_token>
```

## Article Endpoints 

GET  ```/api/articles/``` - List all approved articles 
POST  ```/api/articles/``` - Create new article
GET  ```/api/articles/<id>``` - Get single article
PUT  ```/api/articles/<id>/``` - Update article 
DELETE ```/api/articles/<id>/``` - Delete article 
GET  ```/api/articles/subscribed/``` - Get subscribed articles
POST  ```/api/articles/<id>/approve/``` - Approve article

### Newsletter Endpoints 

### GET  ```/api/newsletters/```  - List all newsletters
### POST  ```/api/newsletters/``` - Create newsletter
### GET   ```/api/newsletters/<id>/``` - Get single newsletter
### PUT  ```/api/newsletters/<id>/```  - Update newsletter 
### DELETE  ```/api/newsletters/<id>/```  - Delete newsletter

### Testing 
## Run All Tests

```
python manage.py test news_app
```

