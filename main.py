import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime
import mysql.connector as sqlc

# Function to register a new user
def register():
    st.write("### Register:")
    name = st.text_input("Name")
    usn = st.text_input("USN")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        user = {"name": name, "usn": usn, "email": email, "password": password}
        save_user(user)
        st.success("User registered successfully! Please login.")

# Function to save a new user to the database
def save_user(user):
    timeout = 10
    try:
        connection = sqlc.connect(
            charset="utf8mb4",
            connection_timeout=timeout,
            database="defaultdb",
            host="mysqldb-nmam-events.h.aivencloud.com",
            password="AVNS_YgAtatHm_yR2IzgTItR",
            port=25203,
            user="avnadmin",
        )
        cursor = connection.cursor()
        query = "INSERT INTO users (name, USN, email, password) VALUES (%s, %s, %s, %s)"
        values = (user["name"], user["usn"], user["email"], user["password"])
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
    except sqlc.Error as e:
        st.error(f"Error saving user to MySQL: {e}")

# Function to display the login page
def login_page():
    st.title("Welcome to the ScheduleSync event management app!")

    # Choose between login and registration
    option = st.radio("Select an option:", ["Login", "Register"])
    if option == "Register":
        register()
    elif option == "Login":
        login()

# Function to handle user login
def login():
    st.write("### Login:")
    usn = st.text_input("USN")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            connection = sqlc.connect(
                charset="utf8mb4",
                database="defaultdb",
                host="mysqldb-nmam-events.h.aivencloud.com",
                password="AVNS_YgAtatHm_yR2IzgTItR",
                port=25203,
                user="avnadmin",
            )
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM users WHERE USN= %s"
            cursor.execute(query, (usn,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user = user  # Store user details in session
                st.success(f"*Press login again*  \nWelcome back, {user['name']}!")
            else:
                st.error("Invalid USN or password. Please try again.")

        except sqlc.Error as e:
            st.error(f"Error logging in: {e}")

# Function to fetch events from the database
@st.cache_data
def fetch_events():
    timeout = 10
    try:
        connection = sqlc.connect(
            charset="utf8mb4",
            connection_timeout=timeout,
            database="defaultdb",
            host="mysqldb-nmam-events.h.aivencloud.com",
            password="AVNS_YgAtatHm_yR2IzgTItR",
            port=25203,
            user="avnadmin",
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT title, start, end, description, color FROM events")
        events = cursor.fetchall()
        cursor.close()
        connection.close()

        # Convert date/datetime fields to string format
        for event in events:
            event["start"] = event["start"].isoformat() if isinstance(event["start"], (datetime,)) else str(event["start"])
            event["end"] = event["end"].isoformat() if isinstance(event["end"], (datetime,)) else str(event["end"])

            # Ensure extendedProps contains "end" for eventClick
            event["extendedProps"] = {
                "end": event["end"],
                "description": event.get("description", "No description available")
            }

        return events

    except sqlc.Error as e:
        st.error(f"Error fetching events from MySQL: {e}")
        return []

# Function to enter event details
def enter_event():
    st.write("### Enter Event Details:")
    title = st.text_input("Title")
    start = st.date_input("Start Date")
    end = st.date_input("End Date")
    desc = st.text_input("Description")
    color = st.color_picker("Color", "#ff5722")

    if st.button("Add Event"):
        event = {
            "title": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "desc": desc,
            "color": color
        }
        save_event(event)
        st.success("Event added successfully! Refresh to update calendar.")

# Function to save an event to the database
def save_event(event):
    timeout = 10
    try:
        connection = sqlc.connect(
            charset="utf8mb4",
            connection_timeout=timeout,
            database="defaultdb",
            host="mysqldb-nmam-events.h.aivencloud.com",
            password="AVNS_YgAtatHm_yR2IzgTItR",
            port=25203,
            user="avnadmin",
        )
        cursor = connection.cursor()
        query = "INSERT INTO events (title, start, end, description, color) VALUES (%s, %s, %s, %s, %s)"
        values = (event["title"], event["start"], event["end"], event["desc"], event["color"])
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
    except sqlc.Error as e:
        st.error(f"Error saving event to MySQL: {e}")

# Ensure login state exists
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if not st.session_state.logged_in:
    login_page()
    st.stop()

# Ensure event selection state exists
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None

st.title(f"Hello {st.session_state.user['name']}!")  # Fix user name display

try:
    events = fetch_events()
except Exception as e:
    st.error(f"Error fetching events: {e}")
    events = []

option = st.selectbox("Choose View Type", ["Month View", "Week View", "Day View", "Events View"])
opts = {"Month View": "dayGridMonth", "Week View": "timeGridWeek", "Day View": "timeGridDay", "Events View": "listWeek"}

calendar_options = {
    "initialView": opts.get(option, "dayGridMonth"),
    "editable": False,
    "selectable": True,
    "eventDisplay": "block",
}

enter_event()

# Sidebar logout button
with st.sidebar:
    st.write("## Profile")
    img_url = f"https://university-student-photos.s3.ap-south-1.amazonaws.com/049/student_photos%2F{st.session_state.user['USN']}.JPG"
    st.image(img_url, width=150, caption=st.session_state.user['name'])
    st.write(f"**USN:** {st.session_state.user['USN']}")
    st.write(f"**Name:** {st.session_state.user['name']}")
    st.write(f"**Email:** {st.session_state.user['email']}")

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None  # Clear user data
        st.rerun()  # Refresh the app to show login page

# Render the calendar
cal = calendar(events=events, options=calendar_options)

# Handle event clicks
if isinstance(cal, dict) and "callback" in cal:
    if cal["callback"] == "eventClick":
        event_data = cal["eventClick"]["event"]
        event_title = event_data["title"]
        event_start = event_data["start"]
        event_end = event_data.get("extendedProps", {}).get("end", "No end time available")
        event_description = event_data.get("extendedProps", {}).get("description", "No description available")

        st.session_state.selected_event = {
            "title": event_title, "start": event_start, "end": event_end, "description": event_description
        }

# Display event details
if st.session_state.selected_event:
    with st.expander(f"Event Details: {st.session_state.selected_event['title']}", expanded=True):
        st.write(f"📅 **Start Date:** {st.session_state.selected_event['start']}")
        st.write(f"⏳ **End Date:** {st.session_state.selected_event['end']}")
        st.write(f"📝 **Description:** {st.session_state.selected_event['description']}")
