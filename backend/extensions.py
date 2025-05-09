from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_session import Session
import cloudinary
import cloudinary.uploader
import cloudinary.api
from google import genai
import stripe

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
sess = Session()

def init_extensions(app):
    """Initialize all Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Flask-Session
    sess.init_app(app)
    
    # Initialize CORS
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=app.config['CORS_HEADERS'],
         methods=app.config['CORS_METHODS'],
         expose_headers=['Set-Cookie', 'Content-Type', 'Authorization'],
         allow_credentials=True)
    
    # Configure Cloudinary
    try:
        cloud_name = app.config['CLOUDINARY_CLOUD_NAME']
        api_key = app.config['CLOUDINARY_API_KEY'] 
        api_secret = app.config['CLOUDINARY_API_SECRET']
        
        if not cloud_name or not api_key or not api_secret:
            app.logger.warning("Missing Cloudinary credentials - Some file upload features will be limited")
            app.logger.debug(f"Cloudinary config: name={cloud_name}, key={'present' if api_key else 'missing'}, secret={'present' if api_secret else 'missing'}")
        else:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret
            )
            app.logger.info("Cloudinary configured successfully")
    except Exception as e:
        app.logger.error(f"Error configuring Cloudinary: {str(e)}")
    
    # Initialize Gemini
    # We're now initializing the Gemini client directly in ai_utils.py
    if app.config['GOOGLE_API_KEY']:
        print("Google API key found - AI grading will be available")
    else:
        app.logger.warning("GOOGLE_API_KEY not set - AI grading functionality will be limited")
    
    # Initialize Stripe
    stripe.api_key = app.config['STRIPE_SECRET_KEY'] 