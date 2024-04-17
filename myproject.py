from flask import Flask, redirect, url_for, session, request, render_template
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
import os
import requests
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Initialize the database
db.init_app(app)

with app.app_context():
    db.create_all()

# Google OAuth configuration
CLIENT_ID = '****'
CLIENT_SECRET = '****'
REDIRECT_URI = '****'
AUTHORIZATION_BASE_URL = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
SCOPE = 'https://www.googleapis.com/auth/userinfo.email'

@app.route('/')
def index():
    if 'google_token' in session:
        email = get_user_email(session['google_token'][0])
        username = get_or_create_user(email)
        return render_template('login.html', username=username)
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'google_token' in session:
        email = get_user_email(session['google_token'][0])
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('profile.html', user=user)
    return redirect(url_for('index'))

@app.route('/login')
def login():
    google_auth_url = f"{AUTHORIZATION_BASE_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}&response_type=code"
    return redirect(google_auth_url)

@app.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('index'))

@app.route('/login/authorized')
def authorized():
    code = request.args.get('code')
    token_data = exchange_code_for_token(code)
    if token_data:
        session['google_token'] = (token_data['access_token'], '')
        email = get_user_email(token_data['access_token'])
        # Check if the user exists
        user = User.query.filter_by(email=email).first()
        if user:
            if user.username:
                return redirect(url_for('home'))
            else:
                return redirect(url_for('choose_username'))
        else:
            return redirect(url_for('choose_username'))
    return 'Failed to login'

@app.route('/choose_username', methods=['GET', 'POST'])
def choose_username():
    if request.method == 'POST':
        email = get_user_email(session['google_token'][0])
        username = request.form['username']
        if not User.query.filter_by(username=username).first():
            user = User(email=email, username=username)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('home'))
        else:
            return render_template('choose_username.html', message='Username already exists, please choose a different one.')
    return render_template('choose_username.html', message=None)

def exchange_code_for_token(code):
    token_request_data = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    response = requests.post(TOKEN_URL, data=token_request_data)
    if response.status_code == 200:
        return response.json()
    return None

def get_user_email(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
    if response.status_code == 200:
        return response.json().get('email')
    return None

def get_or_create_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        return user.username
    else:
        username = choose_username()
        new_user = User(email=email, username=username)
        db.session.add(new_user)
        db.session.commit()
        return username


socketio = SocketIO(app, async_mode='eventlet', manage_session=False)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code



@app.route("/home", methods=["GET", "POST"])
def home():
    email = get_user_email(session['google_token'][0])
    user = User.query.filter_by(email=email).first()
    name = user.username

    if request.method == "POST":
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(5)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html", name=name)


@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")


if __name__ == '__main__':
    app.run(debug=True)
