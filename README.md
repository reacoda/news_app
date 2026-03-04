# News App

A Django-based news application with role-based access control for 
Readers, Journalists, and Editors. Features article management, 
newsletters, subscriptions, and a REST API with JWT authentication.

---

## Running with Virtual Environment

### Prerequisites
- Python 3.12+
- MySQL or MariaDB installed and running

### Steps

1. Clone the repository:
```bash
   git clone https://github.com/reacoda/news_app.git
   cd news_app/news_project
```

2. Create and activate a virtual environment:
```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac/Linux
   python -m venv venv
   source venv/bin/activate
```

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

4. Set up your environment variables:
   - Create a `.env` file in the project root
   - Use `.env.example` as a template:
```bash
   cp .env.example .env
```
   - Fill in your own values in `.env`

5. Set up the database:
   - Create a MySQL database called `news_db`
   - Make sure your `.env` has the correct DB credentials

6. Run migrations:
```bash
   python manage.py migrate
```

7. Create user groups and permissions:
```bash
   python manage.py setup_groups
```

8. Start the development server:
```bash
   python manage.py runserver
```

9. Visit: `http://localhost:8000` 

---

## Running with Docker

### Prerequisites
- Docker Desktop installed and running

### Steps

1. Clone the repository:
```bash
   git clone https://github.com/reacoda/news_app.git
   cd news_app/news_project
```

2. Build and start all containers:
```bash
   docker-compose up --build
```

3. Visit: `http://localhost:8000` 

4. To stop the containers:
```bash
   docker-compose down
```

---

## Environment Variables

Never commit your `.env` file! Use `.env.example` as a guide.
Create your own `.env` file with these variables:

| Variable | Description | Example |
|---|---|---|
| `DB_NAME` | Database name | `news_db` |
| `DB_USER` | Database username | `root` |
| `DB_PASSWORD` | Database password | `yourpassword` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |

---

## Documentation

Full Sphinx documentation is available in the `docs/` folder.

To view it, open `docs/_build/html/index.html` in your browser.

---

## Docker Hub

The Docker image is publicly available at:
```
docker pull tiisetsomphuthi/news-app:latest
```

---

## Project Structure
```
news_project/
├── news_app/           # Main Django application
│   ├── models.py       # Database models
│   ├── views.py        # Web views
│   ├── api_views.py    # REST API views
│   ├── serializers.py  # DRF serializers
│   ├── forms.py        # Django forms
│   ├── utils.py        # Helper functions
│   └── tests.py        # Automated tests
├── docs/               # Sphinx documentation
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Multi-container setup
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variable template
```

---

## User Roles

| Role | Permissions |
|---|---|
| **Reader** | Browse articles, subscribe to publishers/journalists |
| **Journalist** | Create and manage articles and newsletters |
| **Editor** | Approve, edit, and delete all content |
```

---
