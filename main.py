import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime
import mysql.connector as sqlc


def fetch_events():
    timeout=10
    try:
        connection = sqlc.connect(charset="utf8mb4",
    connection_timeout=timeout,  # Correct parameter name
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
    #time=st.time_input("Time")
    color = st.color_picker("Color", "#ff5722")

    if st.button("Add Event"):
        event = {"title": title, "start": start.isoformat() , "end": end.isoformat(), "desc": desc, "color": color}
        save_event(event)
        st.success("Event added successfully! Refresh to update calendar.")

# Function to save event to Database 
def save_event(event):
    timeout=10
    try:
        connection = sqlc.connect(charset="utf8mb4",
    connection_timeout=timeout,  # Correct parameter name
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

# Initialize session state for event click
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None

name = "Devdat"  # Replace with dynamic input if needed
st.title(f"Hello {name}!")

try:
    events = fetch_events()
    for event in events:
        event["extendedProps"] = {"end": event["end"]}
    
except Exception as e:
    st.error(f"Error fetching events: {e}")
    events = []

# Dropdown for selecting view type
option = st.selectbox("Choose View Type", ["Month View", "Week View", "Day View"])
opts = {"Month View": "dayGridMonth", "Week View": "timeGridWeek", "Day View": "timeGridDay"}

# Calendar options
calendar_options = {
    "initialView": opts.get(option, "dayGridMonth"),
    "editable": False,
    "selectable": True,
    "eventDisplay": "block",
}

# Display the event entry form
enter_event()
# Display the calendar
cal = calendar(events=events, options=calendar_options)
#st.write(cal)
# Handle event clicks
if isinstance(cal, dict) and "callback" in cal:
    if cal["callback"] == "eventClick":
        event_title = cal["eventClick"]["event"]["title"]
        event_start = cal["eventClick"]["event"]["start"]
        event_end = cal["eventClick"]["event"].get("extendedProps", {}).get("end", "No end time available")#cal["eventClick"]["event"].get("end", "No end time available")
        event_description = cal["eventClick"]["event"].get("extendedProps", {}).get("description", "No description available")

        # event_end = cal["eventClick"]["event"].get("end", "No end time")
        # event_description =cal.get("extendedProps", {}).get("description", "No description wtf available") #cal["eventClick"]["event"].get("desc", "No description available") 

        st.session_state.selected_event = {"title": event_title, "start": event_start, "end": event_end, "description": event_description}

#Display event details in an expander
if st.session_state.selected_event:
    with st.expander(f"Event Details: {st.session_state.selected_event['title']}", expanded=True):
        st.write(f"📅 **Start Date:** {st.session_state.selected_event['start']}")
        st.write(f"⏳ **End Date:** {st.session_state.selected_event['end']}")
        st.write(f"📝 **Description:** {st.session_state.selected_event['description']}")
