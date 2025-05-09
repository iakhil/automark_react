from flask import session
from models import User
from extensions import db
import uuid

class AuthService:
    """Service for handling authentication-related operations"""
    
    @staticmethod
    def login(username, password):
        """
        Authenticate a user and create a session
        
        Args:
            username (str): User's username
            password (str): User's password
            
        Returns:
            tuple: (success, user, session_id)
        """
        print(f"Login attempt for user: {username}")
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            
            # Store user information in session
            session.clear()  # Clear any existing session data first
            session['user_id'] = user.id
            session['role'] = user.role
            session['_permanent'] = True  # Make the session permanent
            
            # Force the session to be saved
            session.modified = True
            
            print(f"Login successful for user {username} (ID: {user.id}) with role {user.role}")
            print(f"Session after login: {session}")
            print(f"Session data: {dict(session)}")
            
            return True, user, session_id
        
        print(f"Login failed for user {username}")
        return False, None, None
    
    @staticmethod
    def register(username, password, role='student'):
        """
        Register a new user
        
        Args:
            username (str): User's username
            password (str): User's password
            role (str): User's role (default: 'student')
            
        Returns:
            tuple: (success, user or error_message)
        """
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return False, "Username already exists"
        
        # Create new user
        user = User(username=username, role=role)
        user.set_password(password)
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        return True, user
    
    @staticmethod
    def logout():
        """
        Log out a user by clearing their session
        
        Returns:
            bool: True if successful
        """
        session.clear()
        return True 