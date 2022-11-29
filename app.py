from flask import Flask, flash, redirect, render_template, request, session, get_flashed_messages
from flask_session import Session
from flask_socketio import SocketIO, send, join_room, emit
from werkzeug.security import check_password_hash, generate_password_hash
from functions import login_required, create_connection

from datetime import datetime

#Library for getting my current timezone
from pytz import timezone

#Importing all my tables from my database in base.py
from base import db_session, Users, Contacts

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "config later"

socketio = SocketIO(app)

Session(app)

#database session
db = db_session()

#List of dictionaries for rooms of two people
#1 dictionary equates to 1 distinct connection of 2 people
#1 dictionary has 3 key-value pair:first person, second person, and room/connection name
CONNECTIONS = []

#A list of connection names between user to upload into front end
ROOMS = []

@app.after_request
def after_request(response):

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

#login route
@app.route("/login", methods = ["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        #Does not accept blank values
        if not username or not password:

            flash("Username and Password field is required", "error")
            return redirect("/login")

        else:
            
            #Checks if username and password exists in database or not
            user = db.query(Users).filter_by(username = username).scalar()
            if not user or not check_password_hash(user.hash, password):

                flash("Username/Password does not exist", "error")
                return redirect("/login")

            else:
                #Logs in the user and saves his id in session
                session["user_id"] = user.id
                flash("Successful Log-in", "success")
                return redirect("/")

    return render_template("login.html")

#register route
@app.route("/register", methods = ["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        
        #Does not accept blank values
        if not username or not password:
            flash("Username and/or Password Required!", "error")
            return redirect("/register")
        
        #Checks if the username already exists in the database
        user_check = db.query(Users).filter_by(username = username).scalar()
        if user_check:
            flash("Username already exists! ", "error")
            return redirect("/register")
            
        #Adds the new user to the database
        user = Users(
            username = username,
            hash = generate_password_hash(password)
        )
        db.add(user)
        db.commit()
        flash("Registered Successfuly!", "success")
        return redirect("/login")

    return render_template("register.html")

@app.route("/", methods = ["GET", "POST"])
@login_required
def index():
        if request.method == "POST":
            username = request.form.get("username")
            #Blank field not accepted
            if not username:
                flash("Field cannot be empty!", "error")
                return redirect("/")
            
            #Checks if the username trying to be added by the user exists in the database
            contact_user = db.query(Users).filter_by(username = username).scalar()
            if not contact_user:
                flash("User does not exist", "error")
                return redirect("/")
            #Adds the contact to the user's contact list
            new_contact = Contacts(
                user_id = session["user_id"],
                contact_name = username,
            )
            db.add(new_contact)
            db.commit()
            flash("User added!", "success")
            return redirect("/")

        
        #renders index page
        user = db.query(Users).filter_by(id = session["user_id"]).scalar()
        contacts = db.query(Contacts).filter_by(user_id = session["user_id"]).join(Users).all()
        return render_template("index.html", user = user, contacts = contacts)

@app.route("/chat", methods = ["GET", "POST"])
@login_required
def chat():
    
    if request.method == "POST":
        #To remove contact from contact list
        db.query(Contacts).filter_by(contactlist_id = request.form.get("id")).delete()
        db.commit()
        flash("Removed Success", "success")
        return redirect("/")
    #Initialize the room
    room = None
    
    #Username of the person the user is trying to chat
    contact = request.args.get("name")
    
    #Current user
    user = db.query(Users).filter_by(id = session["user_id"]).scalar()
    
    #Check if already added in contacts
    connected = db.query(Contacts).filter_by(user_id = session["user_id"], contact_name = contact).scalar()
    
    if connected:
        #If there are no current connections/rooms, create one for the current connection
        if not CONNECTIONS:
            room_name = "chat" + str(len(ROOMS))
            create_connection(user.username, contact, room_name, CONNECTIONS, ROOMS)
            return render_template("chat.html", username = user.username, contact=contact, room = room_name)
        else:
            #If there are already existing connections, check if current user has already a chat..
            #..connection with the another person. If yes, connect to that connection...
            #.. If not create a new one and append another..
            #..connection/room to the list.
            for connection in CONNECTIONS:
                #check if the current user and contact already have a room
                if user.username in connection and contact in connection:
                    room = connection["room_name"]
                    return render_template("chat.html", username = user.username, contact=contact, room = room)
                continue
            room_name = "chat" + str(len(ROOMS))
            create_connection(user.username, contact, room_name, CONNECTIONS, ROOMS)
            return render_template("chat.html", username = user.username, contact=contact, room = room_name)
    
    #done
    #Just a failsafe
    flash("Not Connected", "error")
    return redirect("/chat")

#Logout route
@app.route("/logout") 
@login_required
def logout():
    #Clears the session and logs the user out
    session.clear()
    flash("Logged Out!", "success")
    return redirect("/login")

#Route for messages to be displayed in the frontend side
@socketio.on("message")
def message(data):
    #"Data" is the data passed from the frontend side
    msg = data["msg"]
    username = data["username"]
    room = data["room"]
    date = datetime.now(timezone("Asia/Singapore"))
    current_time = date.strftime("%H:%M")
    #Send this dictionary to the frontend side
    send({"msg" : data["msg"], "username": data["username"], "timestamp": current_time}, room=room)

#Route for when a user joins a connection/room
@socketio.on("join")
def join(data):
    username = data["username"]
    room = data["room"]
    join_room(room)

    # Broadcast that the another user has joined
    send({"msg": username + " has joined the chat."}, room=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)



