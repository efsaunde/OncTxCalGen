import os
import streamlit as st
import pandas as pd
import json
from datetime import timedelta
from streamlit_calendar import calendar

st.set_page_config(layout="wide")

# Function to generate the schedule DataFrame
def generate_schedule_df(protocol_details, start_date):
    schedule_data = {'Date': [], 'Treatment': [], 'Dosage': []}
    for treatment in protocol_details:
        for day in treatment['days']:
            schedule_data['Date'].append(start_date + timedelta(days=day - 1))
            schedule_data['Treatment'].append(treatment['name'])
            schedule_data['Dosage'].append(treatment['dosage'])
    df = pd.DataFrame(schedule_data)
    df['Date'] = pd.to_datetime(df['Date'])  # Ensure 'Date' column is datetime
    return df


# Protocol files
protocol_files = {
    "PERSEUS": "PERSEUS.json",
    "CALGB 10403": "CALGB_10403.json"
}

# Main section for displaying the calendar
with st.container():
    st.markdown("## Oncology Treatment Calendar Generator")

    # Expander for protocol details and inputs
    with st.expander("Protocol Details and Inputs"):
        selected_protocol = st.selectbox('Clinical protocol', list(protocol_files.keys()))

        with open(protocol_files[selected_protocol], 'r') as f:
            protocol_details = json.load(f)

        phase_names = [phase["phase"] for phase in protocol_details]
        selected_phase = st.selectbox('Select Phase', phase_names)
        protocol_details = next(phase for phase in protocol_details if phase["phase"] == selected_phase)["treatments"]

        start_date = st.date_input('Day 1')
        schedule_df = generate_schedule_df(protocol_details, start_date)

        protocol_text = '\n'.join(
            [f"{treatment['name']}: Days {', '.join(map(str, treatment['days']))} {treatment['dosage']}" for treatment
             in protocol_details])
        st.text_area('Clinical Protocol', protocol_text, height=300)

    # Generate events for the calendar
    events = [
        {
            'title': row['Treatment'],
            'start': row['Date'].strftime('%Y-%m-%dT%H:%M:%S'),
            'end': (row['Date'] + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
            'description': row['Dosage']
        }
        for _, row in schedule_df.iterrows()
    ]

    # Calendar options with larger size
    calendar_options = {
        "editable": True,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        },
        "initialView": "dayGridMonth",
        "height": "1024px",
        "contentHeight": "auto",
        "aspectRatio": 2
    }

    # Display the calendar
    calendar(events=events, options=calendar_options, custom_css=None)
