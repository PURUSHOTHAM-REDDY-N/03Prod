# Timetable 1.0 - A-Level Revision Platform

A web-based timetable application designed to help students manage their A-Level revision efficiently. The system uses a confidence-based algorithm to prioritize topics and subtopics that need more attention.

## Features

- **Confidence-Based Task Generation**: Tasks are generated based on confidence levels to focus on weaker areas
- **Subtopic Prioritization**: Mark specific subtopics as priorities to ensure they appear more frequently
- **Curriculum Browser**: View and manage your curriculum structure with confidence tracking
- **Progress Tracking**: Monitor your study progress over time
- **Calendar View**: Visualize your study schedule and completed tasks
- **Dark Mode Support**: Choose between light and dark themes
- **Dual Database Support**: Local database for development and Railway database for production
- **Exam Date Integration**: Add and track upcoming exam dates for better preparation
- **Mobile-Responsive Design**: Access your timetable on any device

## Project Structure

```
timetable/
├── app/                    # Main application package
│   ├── models/            # Database models
│   ├── routes/            # Route definitions
│   ├── static/            # Static files (CSS, JS)
│   ├── templates/         # HTML templates
│   ├── utils/             # Utility functions
│   └── __init__.py        # App initialization
├── config/                # Configuration files
├── data/                  # Data files (curriculum.jsonc)
├── migrations/            # Database migrations
├── tests/                 # Test files
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── run.py                 # Application entry point
```

## Technologies Used

- **Backend**: Python with Flask
- **Database**: PostgreSQL
- **Frontend**: HTML, JavaScript, CSS
- **CSS Framework**: Custom CSS with glassmorphism design
- **Charts**: Chart.js for visualizations
- **Icons**: Font Awesome
- **Deployment**: Railway

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/timetable.git
   cd timetable
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env` file:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your_secret_key
   
   # Local Database
   LOCAL_DATABASE_URI=postgresql://user:password@localhost:5432/timetable
   
   # Railway Database
   DATABASE_URL=postgresql://postgres:password@postgres.railway.internal:5432/railway
   ```

4. Initialize the database:
   ```
   flask init-db
   ```

5. Import curriculum data:
   ```
   flask import-data
   ```

6. Run the application:
   ```
   flask run
   ```

## Database Configuration

The application is configured to support two database connections:

1. **Local Database**: Used for development and testing
2. **Railway Database**: Used for production deployment

The database connection is determined by the `FLASK_ENV` environment variable. The application uses the local database in development mode and the Railway database in production mode.

## Confidence System

The confidence system is based on a 1-5 scale:

- **1**: Not confident at all
- **2**: Slightly confident
- **3**: Moderately confident
- **4**: Confident
- **5**: Very confident

The weighting system gives higher priority to topics with lower confidence levels using the formula: (7 - confidence_level)²

## Task Generation

Tasks are generated based on:

1. The user's study hours per day
2. A balanced distribution across subjects
3. Confidence levels for topics and subtopics
4. Prioritized subtopics
5. Task types enabled by the user
6. Upcoming exam dates

## Development

To run the application in development mode:

```
export FLASK_ENV=development
flask run
```

For database migrations:

```
flask db migrate -m "Migration message"
flask db upgrade
```

## Recent Updates

- Added exam date tracking and integration with task generation
- Improved mobile responsiveness
- Enhanced user interface for better usability
- Optimized database queries for better performance
- Added comprehensive test suite

## License

This project is licensed under the MIT License - see the LICENSE file for details.
