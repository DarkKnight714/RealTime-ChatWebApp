CC project: Real-time chat app

Overview
It is a real-time chat web application with the following functionality:

1. Google OAuth Login:
   - Users can log in to the application using their Google account.
   - If it's the user's first time logging in, they are prompted to choose a unique username.

2. User Profile:
   - After logging in, users can view their profile details.
   - The user's profile includes information like email and username.

3. Room Management:
   - Users can navigate to a home page where they have the option to either join an existing chat room by entering a room code or create a new chat room.
   - Room creation generates a unique room code.
   - The application uses WebSocket technology (via Flask-SocketIO) to enable real-time messaging and interaction within chat rooms.

4. Chat Room:
   - Each chat room maintains a list of members and messages.
   - Messages are displayed in real-time, and users can send messages directly within the web interface.
   - The chat room page (`room.html`) handles message display and interaction via JavaScript and SocketIO.

5. Additional Features:
   - The application utilizes Flask for its backend framework, SQLAlchemy for database management (SQLite in this case), and SocketIO for real-time communication.
   - Styling and dynamic content rendering are achieved using Jinja2 templates with HTML and CSS.

Description of the Flow:

1. Login with Google:
   - Users access the application and are prompted to log in using their Google account.
   - Upon successful login, users are redirected to either their profile page (if previously registered) or a username selection page (for new users).



2. Choose Username (if new user):
   - New users are required to choose a unique username.
   - The chosen username is stored in the database.


3. Home Page:
   - The home page presents options to join an existing chat room by entering a room code or creating a new chat room.


4. Chat Room Interaction:
   - Users interact with chat rooms in real-time, sending and receiving messages.
   - WebSocket technology ensures instant message delivery and updates.


5. Profile Page:
   - Users can view their profile information, including email and chosen username.


6. Logout:
   - Users can log out of the application, ending their session.

Technologies Used:
- Backend: Flask (Python web framework), SQLAlchemy (ORM for database management)
- Frontend: HTML, CSS, JavaScript (with Jinja2 templating for dynamic content)
- Authentication: Google OAuth for user login
- Real-Time Communication: Flask-SocketIO for WebSocket support
- Database: SQLite (for local development/testing, can be replaced with other databases for production)

This web application allows users to engage in real-time chat room interactions, leveraging Google authentication for user management and Flask-SocketIO for WebSocket-based communication. The front-end components are integrated with the backend using Flask's routing mechanisms and SocketIO event handling.


Requirements
Python 3.8
Wheel 
Flask 
Flask-socketio
Flask-Sqlalchemy
Requests
Gunicorn
Eventlet
Nginx


Google OAuth2 setup:
- Navigate on Google Console to “API’s & Services” > “Credentials” > “Create> “OAuth client ID” with application type as “web application”
- Set test user emails & redirect and authorization URL 
- Acquire CLIENT_ID and CLIENT_SECRET


Installation:
1. Create a virtual environment and activate it
python3 -m venv myprojectvenv
source venv/bin/activate 
2. Install all the requirements 

Configuration
Environment Variables:
- SECRET_KEY: Secret key for Flask session management.
- DATABASE_URI: URI for the SQLite database.
- CLIENT_ID: Google OAuth client ID.
- CLIENT_SECRET: Google OAuth client secret.
- REDIRECT_URI: Redirect URI for Google OAuth.
- AUTHORIZATION_BASE_URL: Google OAuth authorization URL.
- TOKEN_URL: Google OAuth token URL.
- SCOPE: Google OAuth scope for accessing user information.
```
Flask App Folder
    ├── app.py
    ├── templates/  
        ├── login.html    
        ├── choose_username.html 
        ├── base.html
        ├── home.html
        ├── profile.html
        ├── room.html
    ├── static/  
        ├── profilestyle.css    
        ├── style.css 
        ├── styles.css
        ├── username.css
        ├── log.jpg
        ├── login.jpg
        ├── prof.jpg
```
Deployment with Gunicorn and NGINX

1. Create a Gunicorn configuration file (`gunicorn_config.py`) with the following content:
   ```python
   bind = '0.0.0.0:5000'
   accesslog = '/path/to/access.log'
   errorlog = '/path/to/error.log'
   loglevel = 'info'
   worker_class = 'eventlet'
   ```


2. Automating start of Gunicorn with the Flask app:

- sudo systemctl start myproject
- sudo systemctl enable myproject
3. Creating an NGINX configuration file (e.g., `/etc/nginx/sites-available/myproject`) with the following content:

```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;

           # WebSocket proxying
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

```bash
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled
sudo nginx -t 
sudo systemctl restart nginx
```




Troubleshooting
- Check Gunicorn logs (`/path/to/error.log`) for server errors.
- Review NGINX logs (`/var/log/nginx/error.log`) for proxy-related issues.


Understanding Flask Application (‘app.py’)

1. **Database Model (`User`)**:
   - Defines a `User` model with attributes `id`, `email`, and `username` using SQLAlchemy.

2. **Configuration and Initialization**:
   - Configures a Flask application (`app`) with SQLAlchemy for database management.
   - Sets up Google OAuth2 configuration parameters (`CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`, `AUTHORIZATION_BASE_URL`, `TOKEN_URL`, `SCOPE`).

3. **Routes**:
   - **`/(index)`**:
     - Displays a login page (`login.html`), redirecting to the profile page (`profile.html`) if the user is authenticated.
   - **`/profile`**:
     - Shows user profile information after successful authentication.
   - **`/login`**:
     - Redirects users to Google's OAuth2 login page for authentication.
   - **`/logout`**:
     - Logs out the user by removing the `google_token` from the session.
   - **`/login/authorized`**:
     - Handles the callback after Google authentication, exchanging the authorization code for an access token and fetching user details.
   - **`/choose_username`**:
     - Allows users to choose a unique username after initial authentication.

4. **Helper Functions**:
   - **`exchange_code_for_token(code)`**:
     - Exchanges the authorization code received from Google for an access token.
   - **`get_user_email(access_token)`**:
     - Retrieves the user's email using the access token.
   - **`get_or_create_user(email)`**:
     - Fetches an existing user or creates a new user based on the email address.

5. **WebSocket and Chat Logic**:
   - **`/home`**:
     - Manages the home page, allowing users to create or join chat rooms.
   - **`/room`**:
     - Manages the chat room, displaying messages and handling message sending via WebSocket.
   - **SocketIO Event Handlers** (`message`, `connect`, `disconnect`):
     - Handle WebSocket events for sending and receiving chat messages and managing room participants.

6. **SocketIO Initialization**:
   - Initializes Flask-SocketIO (`socketio`) with the Flask app (`app`) and sets the async mode to `'eventlet'`.



Github link
https://github.com/DarkKnight714/RealTime-ChatWebApp

