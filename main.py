import streamlit as st
import pandas as pd
from datetime import timedelta, datetime
from streamlit_calendar import calendar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import your ORM models – adjust the import if your models are in a separate module
from models import Protocol  # Protocol, Phase, Cycle, Treatment

st.set_page_config(layout="wide")

# -------------------------------
# 1. Setup SQLAlchemy Database
# -------------------------------
engine = create_engine("sqlite:///protocols.db")
Session = sessionmaker(bind=engine)
session = Session()

# -------------------------------
# 2. Helper Functions
# -------------------------------


def parse_days(days_str):
    """Convert a CSV string with ranges (e.g., '2 to 5, 9 to 12') into a list of integers."""
    days = []
    segments = days_str.split(',')
    for segment in segments:
        segment = segment.strip()
        if 'to' in segment:
            start_str, end_str = segment.split('to')
            try:
                start = int(start_str.strip())
                end = int(end_str.strip())
                days.extend(range(start, end + 1))
            except ValueError:
                continue  # skip if conversion fails
        else:
            try:
                days.append(int(segment))
            except ValueError:
                continue
    return days


def generate_schedule_df(treatments, start_date):
    """Generate a schedule DataFrame from a list of treatment records."""
    schedule_data = {'Date': [], 'Treatment': [], 'Dosage': []}
    for treatment in treatments:
        days = parse_days(treatment.days)
        for day in days:
            schedule_data['Date'].append(start_date + timedelta(days=day - 1))
            schedule_data['Treatment'].append(treatment.medication)
            schedule_data['Dosage'].append(treatment.dose)
    df = pd.DataFrame(schedule_data)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

# -------------------------------
# 3. Streamlit UI and Database Query
# -------------------------------


with st.container():
    st.markdown("## Oncology Treatment Calendar Generator")

    with st.expander("Protocol Details and Inputs"):
        # Retrieve all protocols from the database
        all_protocols = session.query(Protocol).all()
        if not all_protocols:
            st.error("No protocols found in the database.")
        else:
            # Filter protocols by Cancer Type
            cancer_types = sorted({p.cancer_type for p in all_protocols if p.cancer_type})
            cancer_types.insert(0, "All")
            selected_cancer_type = st.selectbox("Select Cancer Type", cancer_types)

            if selected_cancer_type != "All":
                filtered_protocols = [p for p in all_protocols if p.cancer_type == selected_cancer_type]
            else:
                filtered_protocols = all_protocols

            # Filter protocols by Subtype from the remaining protocols
            subtypes = sorted({p.subtype for p in filtered_protocols if p.subtype})
            subtypes.insert(0, "All")
            selected_subtype = st.selectbox("Select Subtype", subtypes)

            if selected_subtype != "All":
                filtered_protocols = [p for p in filtered_protocols if p.subtype == selected_subtype]

            # Now list available protocol names
            protocol_names = [p.name for p in filtered_protocols]
            if not protocol_names:
                st.error("No protocols match the selected filters.")
            else:
                selected_protocol_name = st.selectbox('Clinical Protocol', protocol_names)
                selected_protocol = next((p for p in filtered_protocols if p.name == selected_protocol_name), None)

                if selected_protocol:
                    # List available phases for the selected protocol
                    phase_names = [phase.phase_name for phase in selected_protocol.phases]
                    if not phase_names:
                        st.warning("No phases available for the selected protocol.")
                    else:
                        selected_phase_name = st.selectbox('Select Phase', phase_names)
                        selected_phase = next((phase for phase in selected_protocol.phases
                                               if phase.phase_name == selected_phase_name), None)

                        # Combine treatments from all cycles within the selected phase
                        treatments = []
                        if selected_phase:
                            for cycle in selected_phase.cycles:
                                treatments.extend(cycle.treatments)

                        start_date = st.date_input('Day 1', value=datetime.today())
                        if treatments:
                            schedule_df = generate_schedule_df(treatments, start_date)
                            # Display protocol details in text_area
                            protocol_text = '\n'.join(
                                [f"{treatment.medication}: Days {treatment.days} | Dose: {treatment.dose}"
                                 for treatment in treatments]
                            )
                            st.text_area('Clinical Protocol', protocol_text, height=300)
                        else:
                            st.info("No treatments found for the selected phase.")

    # -------------------------------
    # 4. Calendar Rendering
    # -------------------------------
    if 'schedule_df' in locals() and not schedule_df.empty:
        events = [
            {
                'title': row['Treatment'],
                'start': row['Date'].strftime('%Y-%m-%dT%H:%M:%S'),
                'end': (row['Date'] + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
                'description': row['Dosage'],
                'allDay': True
            }
            for _, row in schedule_df.iterrows()
        ]

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

        calendar(events=events, options=calendar_options, custom_css=None)
