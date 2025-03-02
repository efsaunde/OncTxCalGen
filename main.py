import streamlit as st
import pandas as pd
from datetime import timedelta, datetime
from streamlit_calendar import calendar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
st.markdown("## Oncology Treatment Calendar Generator")
st.markdown("""
**Disclaimer:** This tool is for informational purposes only and is not a substitute for professional medical judgment. Healthcare professionals are responsible for verifying all outputs and ensuring appropriate care.
""")
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

    # Filter protocols by Subtype
    subtypes = sorted({p.subtype for p in filtered_protocols if p.subtype})
    subtypes.insert(0, "All")
    selected_subtype = st.selectbox("Select Subtype", subtypes)

    if selected_subtype != "All":
        filtered_protocols = [p for p in filtered_protocols if p.subtype == selected_subtype]

    # Clinical Protocol selection with a placeholder.
    protocol_names = sorted({p.name for p in filtered_protocols})
    protocol_options = ["Select Clinical Protocol…"] + protocol_names
    selected_protocol_name = st.selectbox("Select Clinical Protocol", protocol_options)

    # Only proceed if a valid protocol is selected.
    if selected_protocol_name != "Select Clinical Protocol…":
        # Narrow down to the variants of the selected protocol.
        protocol_variants = [p for p in filtered_protocols if p.name == selected_protocol_name]
        if protocol_variants:
            # Choose available versions for this protocol, defaulting to the highest.
            versions = sorted({p.version for p in protocol_variants if p.version},
                              key=lambda v: float(v) if v.replace(".", "", 1).isdigit() else v,
                              reverse=True)
            selected_version = st.selectbox("Select Protocol Version", versions)
            # Choose the protocol record with the selected version.
            selected_protocol = next((p for p in protocol_variants if p.version == selected_version), None)

            if selected_protocol:
                # Phase selection.
                phase_names = [phase.phase_name for phase in selected_protocol.phases]
                if not phase_names:
                    st.warning("No phases available for the selected protocol.")
                else:
                    selected_phase_name = st.selectbox("Select Phase", phase_names)
                    selected_phase = next((phase for phase in selected_protocol.phases
                                           if phase.phase_name == selected_phase_name), None)

                    # Treatment and start date selection.
                    start_date = st.date_input("Day 1", value=datetime.today())

                    # Combine treatments from all cycles within the selected phase.
                    treatments = []
                    if selected_phase:
                        for cycle in selected_phase.cycles:
                            treatments.extend(cycle.treatments)

                    if treatments:
                        schedule_df = generate_schedule_df(treatments, start_date)
                        # Display protocol details.
                        protocol_text = "\n".join(
                            [f"{treatment.medication}: Days {treatment.days} | Dose: {treatment.dose}"
                             for treatment in treatments]
                        )
                        st.text_area("Clinical Protocol", protocol_text, height=300)

                        if not schedule_df.empty:
                            events = [
                                {
                                    "title": row["Treatment"],
                                    "start": row["Date"].strftime("%Y-%m-%dT%H:%M:%S"),
                                    "end": (row["Date"] + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                                    "description": row["Dosage"],
                                    "allDay": True
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
                    else:
                        st.info("No treatments found for the selected phase.")
        else:
            st.error("No variants found for the selected protocol.")
st.markdown("""
*Reference: Data and protocol information provided by Systemic Anti-Cancer Therapy Regimen Library from NZ Formulary (https://srl.org.nz/regimens/).*
""")
