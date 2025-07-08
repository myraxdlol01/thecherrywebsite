import os
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI')
API_BASE_URL = 'https://discord.com/api'
OAUTH2_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'
SCOPE = ['identify', 'guilds']

@app.route('/static-test')
def static_test():
    return render_template('static_test.html')


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=DISCORD_CLIENT_ID,
        token=token,
        state=state,
        scope=scope or SCOPE,
        redirect_uri=DISCORD_REDIRECT_URI
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/commands')
def commands():
    # Placeholder: Replace with dynamic command loading
    commands = [
        {'name': 'ping', 'desc': 'checks bot latency'},
        {'name': 'ban', 'desc': 'bans a user'},
        {'name': 'kick', 'desc': 'kicks a user'}
    ]
    return render_template('commands.html', commands=commands)

@app.route('/dashboard')
def dashboard():
    if 'discord_token' not in session:
        return redirect(url_for('login'))
    user = session.get('user')
    guilds = session.get('guilds', [])
    return render_template('dashboard.html', user=user, guilds=guilds)

@app.route('/login')
def login():
    discord = make_session(scope=SCOPE)
    auth_url, state = discord.authorization_url(OAUTH2_URL)
    session['oauth2_state'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if request.values.get('error'):
        return redirect(url_for('index'))
    discord = make_session(state=session.get('oauth2_state'))
    try:
        token = discord.fetch_token(
            TOKEN_URL,
            client_secret=DISCORD_CLIENT_SECRET,
            authorization_response=request.url
        )
        session['discord_token'] = token
        # Fetch user info
        discord = make_session(token=token)
        user = discord.get(API_BASE_URL + '/users/@me')
        guilds = discord.get(API_BASE_URL + '/users/@me/guilds')
        if user.status_code != 200 or guilds.status_code != 200:
            return render_template('callback.html', error='failed to fetch user or guilds')
        session['user'] = user.json()
        session['guilds'] = guilds.json()
        return redirect(url_for('dashboard'))
    except Exception as e:
        return render_template('callback.html', error=str(e))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/guild/<guild_id>', methods=['GET', 'POST'])
def guild_dashboard(guild_id):
    if 'discord_token' not in session:
        return redirect(url_for('login'))
    # Placeholder: Load and save settings here
    if request.method == 'POST':
        # Save settings logic
        return redirect(url_for('dashboard'))
    # Example settings
    settings = {
        'leveling': True,
        'welcome_message': 'welcome to the server!',
        'autoroles': ['member'],
        'moderation': {'ban': True, 'kick': True}
    }
    return render_template('guild_dashboard.html', guild_id=guild_id, settings=settings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
