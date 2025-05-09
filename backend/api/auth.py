from flask import Blueprint, request, jsonify, session, current_app
from services import AuthService

# Create a blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    print(f"LOGIN REQUEST: username={username}")
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Missing username or password'}), 400
    
    success, user, session_id = AuthService.login(username, password)
    
    if success:
        # Debug information
        print(f"Login SUCCESS: User ID {user.id} added to session")
        print(f"Current session: {dict(session)}")
        
        # Create the response
        response = jsonify({
            'success': True, 
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            },
            'debug_info': {
                'session_id': str(session.sid) if hasattr(session, 'sid') else None,
                'cookie_settings': {
                    'secure': current_app.config.get('SESSION_COOKIE_SECURE'),
                    'samesite': current_app.config.get('SESSION_COOKIE_SAMESITE'),
                    'domain': current_app.config.get('SESSION_COOKIE_DOMAIN'),
                }
            }
        })
        
        return response
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """Handle user registration"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student')  # Default to student if not specified
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    success, result = AuthService.register(username, password, role)
    
    if success:
        return jsonify({'success': True, 'user': result.to_dict()})
    else:
        return jsonify({'success': False, 'message': result}), 400

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    AuthService.logout()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@auth_bp.route('/api/check-session', methods=['GET'])
def check_session():
    """Check if the user has a valid session"""
    print(f"Checking session: {dict(session)}")
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'authenticated': True,
            'user_id': session['user_id'],
            'role': session['role'],
            'session_data': dict(session)
        })
    else:
        return jsonify({
            'success': True,
            'authenticated': False,
            'session_data': dict(session)
        }), 401 