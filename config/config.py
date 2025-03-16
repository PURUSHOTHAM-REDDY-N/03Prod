import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Default to SQLite database for development simplicity
    SQLALCHEMY_DATABASE_URI = os.environ.get('LOCAL_DATABASE_URI', 'sqlite:///app.db')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration using Railway database."""
    DEBUG = False
    TESTING = False
    
    # Database configuration with fallback
    database_url = os.environ.get('DATABASE_URL')
    
    # Log the available environment variables for debugging
    print(f"Environment variables: {list(os.environ.keys())}")
    print(f"DATABASE_URL: {database_url}")
    
    # Check if we're on Railway by looking for specific environment variables
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_SERVICE_ID'):
        # Use Railway's PostgreSQL environment variables directly
        pg_user = os.environ.get('PGUSER', 'postgres')
        pg_password = os.environ.get('PGPASSWORD', '')
        pg_host = os.environ.get('PGHOST', 'localhost')
        pg_port = os.environ.get('PGPORT', '5432')
        pg_database = os.environ.get('PGDATABASE', 'railway')
        
        # Construct the SQLAlchemy URI using environment variables
        SQLALCHEMY_DATABASE_URI = f"postgresql+pg8000://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
        print(f"Using constructed database URL from Railway environment variables: {SQLALCHEMY_DATABASE_URI}")
    elif database_url:
        # Format the URL for pg8000 driver for non-Railway deployments
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+pg8000://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
        print(f"Using database URL: {database_url}")
    else:
        # Fallback to SQLite if no DATABASE_URL is provided
        print("No DATABASE_URL found, falling back to SQLite")
        SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'

# Configuration dictionary to easily access different configs
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_database_uri(environment='default'):
    """Helper function to get the correct database URI based on environment."""
    return config[environment].SQLALCHEMY_DATABASE_URI

def configure_app(app, environment='default'):
    """Configure the Flask application with the specified environment."""
    app.config.from_object(config[environment])
    app.config['ENVIRONMENT'] = environment
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
