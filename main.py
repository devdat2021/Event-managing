import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime
import mysql.connector as sqlc
import smtplib
import pandas as pd


#Database connection 
def db_connection():
    timeout = 10
    try:
        connection = sqlc.connect(
            charset="utf8mb4",
            connection_timeout=timeout,
            database="defaultdb",
            host=st.secrets["mysql"]["host"],
            password=st.secrets["mysql"]["password"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
        )
        return connection
    except sqlc.Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None
#Function to notify/email me
def send_email(subject, body):
    smtp_server = 'smtp.gmail.com'
    port = 465

    sender_email = st.secrets["sender_email"]
    app_password = st.secrets["app_password"]
    receiver_email = sender_email  # sending to yourself

    message = f"Subject: {subject}\n\n{body}"

    with smtplib.SMTP_SSL(smtp_server, port) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message)
#bulk email function
def send_bulk_email(subject, body, email_list):
    smtp_server = 'smtp.gmail.com'
    port = 465
    sender_email = st.secrets["sender_email"]
    app_password = st.secrets["app_password"]

    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, app_password)
            for receiver_email in email_list:
                try:
                    server.sendmail(sender_email, receiver_email, message)
                except Exception as e:
                    print(f"Failed to send to {receiver_email}: {e}")
    except Exception as e:
        st.error(f"Bulk email failed: {e}")


# Function to register a new user
def register():
    st.write("### Register:")
    name = st.text_input("Name")
    usn = st.text_input("USN").upper()
    email = st.text_input("Email", value=usn.lower() + "@nmamit.in", disabled=False)
    st.markdown("⚠️ _Default email ID is `USN@nmamit.in`_")

    password = st.text_input("Password", type="password")
    confirm=st.text_input("Confirm Password", type="password")
    role_claim = st.selectbox("Do you want to apply for a role?", ["None", "Club Leader", "Class CR"])
    consent = st.checkbox("I agree to receive event email updates", value=True)
    if consent:
        consent = 'Y'
    else:
        consent = 'N'


    if st.button("Register"):
        if password==confirm and "NNM" in usn:
            user = {"name": name, "usn": usn, "email": email, "password": password,"consent": consent}
            save_user(user)

            if role_claim != "None":
                subject = f"Role Claim Notification: {role_claim}"
                body = f"""
                New user has claimed a role.

                Name: {name}
                USN: {usn}
                Email: {email}
                Claimed Role: {role_claim}
                """
                send_email(subject, body)
                st.info("Role will be verified soon and changed.")
            st.success("User registered successfully! Please login.")
        else:
            st.error("Please retry with correct details or ensure passwords match.")

# Function to save a new user to the database
def save_user(user):
    timeout = 10
    try:
        connection = db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO users (name, USN, email, password,consent) VALUES (%s, %s, %s, %s,%s)"
        values = (user["name"], user["usn"], user["email"], user["password"],user["consent"])
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
    usn = st.text_input("USN").upper()
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            connection = db_connection()
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM users WHERE USN= %s"
            cursor.execute(query, (usn,))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.user = user  # Store user details in session
                st.rerun()  # Immediately rerun app to refresh UI

            else:
                st.error("Invalid USN or password. Please try again.")

        except sqlc.Error as e:
            st.error(f"Error logging in: {e}")

# Function to fetch events from the database
def fetch_events():
    timeout = 10
    try:
        connection = db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT title, start, end, description, color,USN FROM events")
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
            "color": color,
            "USN": st.session_state.user['USN']  # Add USN of the user
        }
        save_event(event)
        st.success("Event added successfully! Refresh to update calendar.")

# Function to save an event to the database
def save_event(event):
    timeout = 10
    try:
        connection = db_connection()
        cursor = connection.cursor()
        q="SELECT email FROM users where consent='Y';"
        cursor.execute(q)
        emails = cursor.fetchall()

        email_list = [email[0] for email in emails]  # Extract emails from tuples
        query = "INSERT INTO events (title, start, end, description, color, USN) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (event["title"], event["start"], event["end"], event["desc"], event["color"], event["USN"])

        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
        # Notify users via email
        subject = f"New Event: {event['title']}"
        body = f"New Event Created:\n\nTitle: {event['title']}\nStart: {event['start']}\nEnd: {event['end']}\nDescription: {event['desc']}"
        send_bulk_email(subject, body, email_list)
        st.info("Event saved successfully! Notifying users...")

    except sqlc.Error as e:
        st.error(f"Error saving event to MySQL: {e}")
# Feedback function 
def feedback():
    st.write("### Feedback / Report an Error")

    # Get user info from session_state or fallback to empty strings
    name = st.session_state.user['name']
    email = st.session_state.user['email']

    # Show auto-filled but disabled inputs
    st.text_input("Your Name", value=name, disabled=True)
    st.text_input("Your Email", value=email, disabled=True)

    message = st.text_area("Describe your feedback or the problem")

    if st.button("Send Feedback"):
        if message.strip() != "":
            subject = "New Feedback / Error Report"
            body = f"""
            Feedback from: {name}
            Email: {email}

            Message:
            {message}
            """

            send_email(subject, body)
            st.success("Thanks for your feedback! We will look into it soon.")
        else:
            st.error("Please enter your feedback or problem description.")

# Fetch users 
def fetch_users():
    timeout = 10
    try:
        connection = db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        connection.close()
        return users
    except sqlc.Error as e:
        st.error(f"Error fetching users from MySQL: {e}")
        return []


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

user_list=fetch_users()


# Sidebar logout button
with st.sidebar:
    st.write("## Profile")
    img_url = f"https://university-student-photos.s3.ap-south-1.amazonaws.com/049/student_photos%2F{st.session_state.user['USN']}.JPG"
    st.image(img_url, width=150, caption=st.session_state.user['name'])
    st.write(f"**USN:** {st.session_state.user['USN']}")
    st.write(f"**Name:** {st.session_state.user['name']}")
    st.write(f"**Email:** {st.session_state.user['email']}")
    st.write(f"**Designation:** {st.session_state.user['desig']}")

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None  # Clear user data
        st.rerun()  # Refresh the app to show login page


if st.session_state.user['desig'] == "Admin":
    st.write("#### Users List")
    df= pd.DataFrame(user_list)
    st.dataframe(df, use_container_width=True)
    
if st.session_state.user['desig'] != "Student":
    enter_event()

option = st.selectbox("Choose View Type", ["Month View","Events View","Week View", "Day View"])
opts = {"Events View": "listMonth","Month View": "dayGridMonth", "Week View": "timeGridWeek", "Day View": "timeGridDay"}
calendar_options = {
    "initialView": opts.get(option, "DayGridMonth"),
    "editable": False,
    "selectable": True,
    "eventDisplay": "block",
}
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
        event_usn= event_data.get("extendedProps", {}).get("USN", None) #st.session_state.user['USN'] event_data.get("extendedProps", {}).get("USN", None)
        
        users_dict = {user["USN"]: user["name"] for user in user_list}  # users_list = list of users
        event_creator_name = users_dict.get(event_usn, "Unknown")
        st.session_state.selected_event = {
            "title": event_title, "start": event_start, "end": event_end, "description": event_description, "USN": event_usn, "creator": event_creator_name
        }

# Display event details
if st.session_state.selected_event:
    selected_usn= st.session_state.selected_event['USN']
    with st.expander(f"Event Details: {st.session_state.selected_event['title']}", expanded=True):
        st.write(f"📅 **Start Date:** {st.session_state.selected_event['start']}")
        st.write(f"⏳ **End Date:** {st.session_state.selected_event['end']}")
        st.write(f"📝 **Description:** {st.session_state.selected_event['description']}")
        #with st.popover(st.write(f"👤 **Created By:** {st.session_state.selected_event['creator']}")):
        with st.popover(f"👤 Created By: {st.session_state.selected_event['creator']}"):

            if st.session_state.selected_event['creator'] !="Unknown":
                for user in user_list:
                    if user['USN']== selected_usn:
                        selected_desig = user['desig']
                        selected_email = user['email']
                img_url = f"https://university-student-photos.s3.ap-south-1.amazonaws.com/049/student_photos%2F{st.session_state.selected_event['USN']}.JPG"
                st.image(img_url, width=150, caption=st.session_state.user['name'])
                st.write(f"**USN:** {st.session_state.selected_event['USN']}")
                st.write(f"**Name:** {st.session_state.selected_event['creator']}")
                st.write(f"**Email:** {selected_email}")
                st.write(f"**Designation:** {selected_desig}")


# Feedback section
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False

if st.button("Feedback / Report an Error"):
    st.session_state.show_feedback = True

if st.session_state.show_feedback:
    feedback()

