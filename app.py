from flask import Flask, render_template, request, session, redirect, jsonify, url_for
from flask_session import Session
import requests
import os
import json
from datetime import timedelta
from config import Config, logger
from elasticapm.contrib.flask import ElasticAPM

app = Flask(__name__)

app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': 'FrontEndService_Ilya',
    'SECRET_TOKEN': '',
    'SERVER_URL': '',
    'ENVIRONMENT': 'dev',
    'DEBUG': True,
}

apm = ElasticAPM(app)

# Configure session handling for user state management
app.config["SESSION_PERMANENT"] = Config.SESSION_PERMANENT
app.config["PERMANENT_SESSION_LIFETIME"] = Config.PERMANENT_SESSION_LIFETIME 
app.config["SESSION_TYPE"] = Config.SESSION_TYPE
Session(app)

# Backend service URL from configuration
BACKEND_URL = Config.BACKEND_URL

# Helper function to check if user is authenticated
def require_auth(func):
    def wrapper(*args, **kwargs):
        if not session.get("username"):
            return redirect("/")
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route("/")
def index():
    """Main entry point - shows dashboard for logged-in users, login page otherwise"""
    if not session.get("username"):
        return render_template("index.html")
    return render_template('dashboard.html', username=session.get("username"))

@app.route('/login', methods=['POST'])
def login():
    """Handle user login by forwarding credentials to backend"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    try:
        # Forward login request to backend service
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            # Store user info in session upon successful login
            session['username'] = username
            return redirect("/")
        else:
            message = "Wrong Username or Password"
            return render_template("index.html", error_message=message)
    except requests.RequestException as e:
        logger.error(f"Login request failed: {str(e)}")
        return render_template("index.html", error_message="Service temporarily unavailable")

@app.route('/register')
def register():
    """Show registration page"""
    return render_template('registration.html')

@app.route('/NewUser', methods=['POST'])
def new_user():
    """Handle new user registration"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    try:
        # Forward registration request to backend
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json={
                "username": username,
                "password": password
            }
        )
        
        if response.status_code == 200:
            message = "You have successfully registered. Please sign in."
            return render_template("index.html", positive_message=message)
        else:
            return render_template("registration.html", 
                                 error_message="Registration failed. Please try again.")
    except requests.RequestException as e:
        logger.error(f"Registration request failed: {str(e)}")
        return render_template("registration.html", 
                             error_message="Service temporarily unavailable")
    
    
@app.route("/google-login")
def google_login():
    """
    Instead of initiating the Google login directly, we redirect to the backend's
    Google login endpoint, which will then handle the OAuth process
    """
    return redirect(f"{Config.BACKEND_URL}/google-login")

@app.route("/google-login/callback")
def google_callback():
    """
    This route handles the callback from Google after authentication.
    We receive the authorization code and forward it to our backend.
    """
    try:
        # Forward all query parameters to the backend
        callback_response = requests.get(
            f"{Config.BACKEND_URL}/google-login/callback",
            params=request.args
        )

        if callback_response.ok:
            # If authentication was successful, set up the session
            user_data = callback_response.json()
            session["username"] = user_data.get("email")
            session["full_name"] = user_data.get("name")
            session["profile_picture"] = user_data.get("picture")
            session["is_google_user"] = True
            logger.info(f"Successfully authenticated Google user: {session['username']}")
            return redirect(url_for('index'))
        else:
            logger.error("Backend authentication failed")
            return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error during Google callback: {str(e)}")
        return redirect(url_for('index'))



@app.route('/checkUserAvaliability', methods=['GET'])
def check_user_availability():
    """Check if username is available during registration"""
    username = request.args.get('username')
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/auth/check-username",
            params={"username": username}
        )
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Username check failed: {str(e)}")
        return jsonify({"available": False, "error": "Service unavailable"})

@app.route('/check_domains', methods=['POST'])
@require_auth
def check_domains():
    """Forward domain checking request to backend"""
    try:
        data = request.get_json()
        response = requests.post(
            f"{BACKEND_URL}/api/domains/check",
            json={
                "domains": data.get('domains', []),
                "username": session['username']
            }
        )
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Domain check failed: {str(e)}")
        return jsonify({'message': 'Service temporarily unavailable', 
                       'error': str(e)}), 500

@app.route('/get_domains', methods=['GET'])
@require_auth
def get_domains():
    """Retrieve user's domains from backend"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/domains/list",
            params={"username": session['username']}
        )
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Get domains failed: {str(e)}")
        return jsonify({'message': 'Service temporarily unavailable', 
                       'error': str(e)}), 500

@app.route('/remove_domain', methods=['DELETE'])
@require_auth
def remove_domain():
    """Remove a domain from user's list"""
    try:
        domain = request.args.get('domain')
        response = requests.delete(
            f"{BACKEND_URL}/api/domains/remove",
            params={
                "username": session['username'],
                "domain": domain
            }
        )
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Remove domain failed: {str(e)}")
        return jsonify({'message': 'Service temporarily unavailable', 
                       'error': str(e)}), 500

# Scheduling endpoints
@app.route("/schedule/hourly", methods=["POST"])
@require_auth
def schedule_hourly():
    """Set up hourly domain checking schedule"""
    try:
        data = request.json
        response = requests.post(
            f"{BACKEND_URL}/api/schedule/hourly",
            json={
                "username": session['username'],
                "interval": data.get('interval', 1)
            }
        )
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Hourly schedule setup failed: {str(e)}")
        return jsonify({'message': 'Service temporarily unavailable', 
                       'error': str(e)}), 500

@app.route("/schedule/daily", methods=["POST"])
@require_auth
def schedule_daily():
    """Set up daily domain checking schedule"""
    try:
        data = request.json
        response = requests.post(
            f"{BACKEND_URL}/api/schedule/daily",
            json={
                "username": session['username'],
                "time": data.get('time', '00:00')
            }
        )
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Daily schedule setup failed: {str(e)}")
        return jsonify({'message': 'Service temporarily unavailable', 
                       'error': str(e)}), 500

@app.route("/schedule/stop", methods=["POST"])
@require_auth
def stop_schedule():
    """Stop all scheduled tasks for current user"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/schedule/stop",
            json={"username": session['username']}
        )
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Schedule stop failed: {str(e)}")
        return jsonify({'message': 'Service temporarily unavailable', 
                       'error': str(e)}), 500

@app.route("/schedule/status", methods=["GET"])
@require_auth
def schedule_status():
    """Get status of scheduled tasks for current user"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/schedule/status",
            params={"username": session['username']}
        )
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Schedule status check failed: {str(e)}")
        return jsonify({'message': 'Service temporarily unavailable', 
                       'error': str(e)}), 500

@app.route("/logout")
def logout():
    """Clear user session and redirect to login page"""
    username = session.get('username')
    if username:
        logger.info(f"User logged out: {username}")
    session.clear()
    return redirect("/")

# Static file routes
@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return app.send_static_file('favicon.ico')

@app.route('/<filename>')
def static_files(filename):
    """Serve static files"""
    return app.send_static_file(filename)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Log application startup
    logger.info(f"Starting frontend service on {Config.FLASK_HOST}:{Config.FLASK_PORT}")
    
    app.run(
        debug=Config.FLASK_DEBUG,
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT
    )