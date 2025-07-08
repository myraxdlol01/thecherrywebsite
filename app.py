from flask import Flask, request, redirect, jsonify, session
from requests_oauthlib import OAuth2Session
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Discord OAuth2 credentials
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI')
DISCORD_API_BASE_URL = 'https://discord.com/api'

# OAuth2 configuration
DISCORD_OAUTH2_URL = f'{DISCORD_API_BASE_URL}/oauth2/authorize'
DISCORD_TOKEN_URL = f'{DISCORD_API_BASE_URL}/oauth2/token'

def token_updater(token):
    session['oauth2_token'] = token

def make_session(token=None, state=None):
    return OAuth2Session(
        client_id=DISCORD_CLIENT_ID,
        token=token,
        state=state,
        redirect_uri=DISCORD_REDIRECT_URI,
        scope=['identify', 'guilds'],
        token_updater=token_updater
    )

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/auth/login')
def login():
    discord = make_session()
    authorization_url, state = discord.authorization_url(DISCORD_OAUTH2_URL)
    session['oauth2_state'] = state
    return jsonify({'url': authorization_url})

@app.route('/api/auth/callback')
def callback():
    if request.values.get('error'):
        return redirect('/login?error=access_denied')
    
    discord = make_session(state=session.get('oauth2_state'))
    try:
        token = discord.fetch_token(
            DISCORD_TOKEN_URL,
            client_secret=DISCORD_CLIENT_SECRET,
            authorization_response=request.url
        )
        session['oauth2_token'] = token
        return redirect('/dashboard')
    except Exception as e:
        print(f"Error during token exchange: {e}")
        return redirect('/login?error=token_exchange')

@app.route('/api/auth/user')
def get_user():
    token = session.get('oauth2_token')
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401
    
    discord = make_session(token=token)
    try:
        user = discord.get(f'{DISCORD_API_BASE_URL}/users/@me').json()
        return jsonify(user)
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return jsonify({'error': 'Failed to fetch user data'}), 500

@app.route('/api/auth/guilds')
def get_guilds():
    token = session.get('oauth2_token')
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401
    
    discord = make_session(token=token)
    try:
        guilds = discord.get(f'{DISCORD_API_BASE_URL}/users/@me/guilds').json()
        return jsonify(guilds)
    except Exception as e:
        print(f"Error fetching guilds: {e}")
        return jsonify({'error': 'Failed to fetch guilds'}), 500

@app.route('/api/auth/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # For development only
    app.run(debug=True) 