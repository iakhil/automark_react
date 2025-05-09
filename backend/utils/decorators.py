from functools import wraps
from flask import request, session, jsonify, redirect, url_for, flash

def login_required(role=None):
    """
    Decorator to check if user is authenticated and optionally has a specific role
    
    Args:
        role (str, optional): Required role (e.g., 'teacher', 'student')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(f"Checking authentication for {request.path}. User ID in session: {session.get('user_id')}")
            print(f"Session type: {type(session)}")
            print(f"Session contents: {dict(session)}")
            print(f"Request cookies: {request.cookies}")
            print(f"Session cookie present: {'session' in request.cookies}")
            
            if 'user_id' not in session:
                # Check if request path starts with /api
                if request.path.startswith('/api'):
                    print(f"Authentication failed for {request.path}")
                    return jsonify({'success': False, 'message': 'Authentication required'}), 401
                return redirect(url_for('index'))
                
            if role and session.get('role') != role:
                if request.path.startswith('/api'):
                    print(f"Authorization failed for {request.path}. User role: {session.get('role')}, required role: {role}")
                    return jsonify({'success': False, 'message': 'Unauthorized access'}), 403
                flash('Unauthorized access')
                return redirect(url_for('index'))
                
            print(f"Authentication successful for user {session.get('user_id')} with role {session.get('role')}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator 