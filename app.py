
import os
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from requests_oauthlib import OAuth2Session
import requests
from dotenv import load_dotenv

load_dotenv()
# Allow http redirect URIs during local development
os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI')
API_BASE_URL = 'https://discord.com/api'
OAUTH2_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'
SCOPE = ['identify', 'guilds', 'applications.commands']
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=DISCORD_CLIENT_ID,
        token=token,
        state=state,
        scope=scope or SCOPE,
        redirect_uri=DISCORD_REDIRECT_URI
    )


def get_bot_guild_ids():
    """Return a set of guild IDs the bot is a member of."""
    if not DISCORD_BOT_TOKEN:
        return set()
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
    try:
        resp = requests.get(API_BASE_URL + "/users/@me/guilds", headers=headers)
        if resp.status_code == 200:
            return {g["id"] for g in resp.json()}
    except Exception as e:
        print("failed to fetch bot guilds", e)
    return set()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/commands')
def commands():
    return render_template('commands.html')

@app.route('/dashboard')
def dashboard():
    if 'discord_token' not in session:
        return redirect(url_for('login'))
    user = session.get('user')
    guilds = session.get('guilds', [])
    return render_template('dashboard.html', user=user, guilds=guilds, DISCORD_CLIENT_ID=DISCORD_CLIENT_ID)

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
        user_data = user.json()
        user_guilds = guilds.json()

        bot_guild_ids = get_bot_guild_ids()
        if bot_guild_ids:
            user_guilds = [g for g in user_guilds if g['id'] in bot_guild_ids]

        session['user'] = user_data
        session['guilds'] = user_guilds
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
        updated = {
            'leveling': 'leveling' in request.form,
            'prefix': request.form.get('prefix', '!'),
            'welcome_message': request.form.get('welcome_message', ''),
            'welcome_channel': request.form.get('welcome_channel', ''),
            'log_channel': request.form.get('log_channel', ''),
            'autoroles': request.form.get('autoroles', '').split(',') if request.form.get('autoroles') else [],
            'moderation': {
                'ban': 'ban' in request.form,
                'kick': 'kick' in request.form
            },
            'commands': {

 
main
                'general': 'general_cmds' in request.form,
                'utility': 'utility_cmds' in request.form,
                'moderation': 'moderation_cmds' in request.form,
                'security': 'security_cmds' in request.form,
                'fun': 'fun_cmds' in request.form,
                'music': 'music_cmds' in request.form,
                'text': 'text_cmds' in request.form,
                'image': 'image_cmds' in request.form,
                'ascii': 'ascii_cmds' in request.form,
                'games': 'games_cmds' in request.form,
                'ai': 'ai_cmds' in request.form
            }
        }
        print('updated settings for', guild_id, updated)
        return redirect(url_for('dashboard'))
    # Example settings
    settings = {
        'leveling': True,
        'prefix': '!',
        'welcome_message': 'welcome to the server!',
        'welcome_channel': '',
        'log_channel': '',
        'autoroles': ['member'],
        'moderation': {'ban': True, 'kick': True},

 

        'commands': {
            'general': True,
            'utility': True,
            'moderation': True,
            'security': True,
            'fun': True,
            'music': True,
            'text': True,
            'image': True,
            'ascii': True,
            'games': True,
            'ai': True
        }
 

    }
    return render_template('guild_dashboard.html', guild_id=guild_id, settings=settings)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
