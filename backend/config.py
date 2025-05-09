import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///ai_grader.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    
    # Session cookie settings
    SESSION_COOKIE_SECURE = True  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'  # None allows cross-domain cookies
    SESSION_COOKIE_DOMAIN = None  # Allow browser to set automatically
    SESSION_COOKIE_PATH = '/'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File upload configuration
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # CORS settings
    CORS_ORIGINS = [
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'https://automark-react.onrender.com'
    ]
    CORS_HEADERS = ['Content-Type', 'Authorization', 'Cookie']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    # Cloudinary settings
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
    
    # AI services
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    
    # Stripe
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow non-HTTPS in development
    SESSION_COOKIE_SAMESITE = 'Lax'  # Less strict SameSite policy for development
    SESSION_COOKIE_DOMAIN = None  # Auto-determine domain
    SESSION_COOKIE_PATH = "/"    # Cookie available for all paths
    CORS_ORIGINS = [
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'http://localhost:3000',
        'http://127.0.0.1:3000'
    ]

class ProductionConfig(Config):
    DEBUG = False
    # Production-specific settings

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 