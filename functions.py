from functools import wraps
from flask import redirect, render_template, request, session
from datetime import datetime, timedelta
    

#function to require access routes only when a user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#function to create a connection
def create_connection(person1, person2, room, connection_list, room_list):
    connection = {
    person1: True,
    person2: True,
    "room_name": room
    }
    connection_list.append(connection)
    room_list.append(connection["room_name"])
    