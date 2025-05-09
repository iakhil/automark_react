import os
from flask import Flask, send_from_directory, session, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from extensions import db, init_extensions
from config import config
from models import User
from api import auth_bp, exam_bp, submission_bp
from datetime import timedelta

def create_app(config_name='default'):
    """Application factory function"""
    # Load environment variables
    load_dotenv()
    
    # Initialize the Flask application
    app = Flask(__name__, static_folder='static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure secret key is set
    if not app.config['SECRET_KEY']:
        app.config['SECRET_KEY'] = 'dev-key-for-testing-only'
        print("WARNING: Using development SECRET_KEY. This should be properly set in production.")
    
    # Configure session settings
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None' 
    app.config['SESSION_COOKIE_SECURE'] = True      # Require HTTPS
    app.config['SESSION_COOKIE_DOMAIN'] = None  
    app.config['SESSION_FILE_THRESHOLD'] = 100  # Number of sessions stored in memory before writing to disk
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session expiry time
    
    # Fix for proxies
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(submission_bp)
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize the database
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Create a test user only if it doesn't exist
        if not User.query.filter_by(username='test').first():
            test_user = User(username='test', role='teacher')
            test_user.set_password('test')
            db.session.add(test_user)
            db.session.commit()
            print("Created test user: username='test', password='test', role='teacher'")
    
    # Route to serve files from the upload folder
    @app.route('/uploads/<path:filename>')
    def serve_file(filename):
        """Serve uploaded files"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Debug route for session testing
    @app.route('/api/debug/session')
    def debug_session():
        """Debug endpoint to check session data"""
        return jsonify({
            'session_data': dict(session),
            'cookies': {key: request.cookies.get(key) for key in request.cookies},
            'session_cookie_name': app.config.get('SESSION_COOKIE_NAME', 'session'),
            'session_cookie_present': app.config.get('SESSION_COOKIE_NAME', 'session') in request.cookies,
            'session_config': {
                key: app.config[key] for key in app.config if key.startswith('SESSION_')
            }
        })
    
    # After request handler to debug session headers
    @app.after_request
    def after_request_func(response):
        print(f"Response cookies: {response.headers.get('Set-Cookie', 'None')}")
        return response
    
    return app

app = create_app(os.getenv('FLASK_CONFIG', 'development'))
# Run the app when this script is executed directly
if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG', 'development'))
    app.run(debug=(os.getenv('FLASK_ENV', 'development') == 'development')) 