import streamlit as st
from datetime import datetime, timedelta
from main import ChessClub, read_json

st.set_page_config(page_title="Critical Mass Chess Club", layout="wide", page_icon="♟️")

#initialize
if 'club' not in st.session_state:
    club = ChessClub()
    club.load_initial_data()
    club.load_file()
    st.session_state.club = club
else:
    club = st.session_state.club

#gui
st.markdown("""
<style>
    h1 {
        color: #2c3e50;
    }
    h2, h3 {
        color: #34495e;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border: none;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

st.title("♟️ Critical Mass Chess Club")

#stats
col1, col2 = st.columns(2)
col1.write(f"Events: {len(club.events)}")
col2.write(f"Resources: {len(club.resources)}")

#navigation
page = st.selectbox("Menu", ["Events", "Add Event", "Find Slot", "Resources", "Save/Load"])

#events
if page == "Events":
    st.header("Events")
    if not club.events:
        st.write("No events")
    else:
        filter_date = st.date_input("Filter by date", value=None)
        events = club.events if not filter_date else [e for e in club.events if e.start.date() == filter_date]
        
        for event in sorted(events, key=lambda e: e.start):
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"{event.name} ({event.type})")
            col2.write(f"{event.start.strftime('%m-%d %H:%M')}")
            col3.write(f"{len(event.resources)} res")
            if st.button("Delete", key=f"del_{event.id}"):
                club.delete_event(event.id)
                club.save_file()
                st.rerun()

#add event
elif page == "Add Event":
    st.header("Schedule Event")
    # Show scheduling message if present
    if "schedule_msg" in st.session_state:
        msg, msg_type = st.session_state.pop("schedule_msg")
        if msg_type == "success":
            st.success(msg)
        else:
            st.error(msg)
    name = st.text_input("Name")
    event_type = st.selectbox("Type", list(club.event_types.keys()) if club.event_types else [])
    tomorrow = datetime.now().date() + timedelta(days=1)
    date = st.date_input("Date", value=tomorrow)
    hour = st.number_input("Hour", 9, 20, 14)
    duration = st.number_input("Duration (h)", 0.5, 8.0, 2.0, step=0.5)
    
    st.write("Resources:")
    cols = st.columns(3)
    selected = []
    for i, r in enumerate(club.resources):
        with cols[i % 3]:
            if st.checkbox(r.name, key=f"res_{r.id}"):
                selected.append(r.id)
    
    if st.button("Schedule"):
        today = datetime.now().date()
        if not name or not event_type or not selected:
            st.session_state["schedule_msg"] = ("Fill missing fields", "error")
            st.rerun()
        elif date <= today:
            st.session_state["schedule_msg"] = ("events can only be scheduled from tomorrow", "error")
            st.rerun()
        else:
            start = datetime.combine(date, datetime.min.time().replace(hour=int(hour)))
            end = start + timedelta(hours=duration)
            ok, msg = club.schedule_event(name, event_type, start, end, selected)
            if ok:
                club.save_file()
                st.session_state["schedule_msg"] = (msg, "success")
                st.rerun()
            else:
                st.session_state["schedule_msg"] = (msg, "error")
                st.rerun()

#find slot
elif page == "Find Slot":
    st.header("Find Slot")
    duration = st.number_input("Duration (h)", 0.5, 8.0, 2.0, step=0.5)
    
    st.write("Resources:")
    cols = st.columns(3)
    selected = []
    for i, r in enumerate(club.resources):
        with cols[i % 3]:
            if st.checkbox(r.name, key=f"find_{r.id}"):
                selected.append(r.id)
    
    if st.button("Search"):
        if not selected:
            st.error("Select resources")
        else:
            slot = club.find_next_slot(duration, selected)
            if slot:
                end = slot + timedelta(hours=duration)
                st.success(f"{slot.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%H:%M')}")
            else:
                st.warning("No slot in next 7 days")

#resources
elif page == "Resources":
    st.header("Resources")
    for type_name in set([r.type for r in club.resources]):
        st.subheader(type_name)
        cols = st.columns(3)
        for i, r in enumerate([x for x in club.resources if x.type == type_name]):
            with cols[i % 3]:
                count = len([e for e in club.events if r in e.resources])
                st.write(f"{r.name}")
                st.caption(f"{count} events")

#save and load
elif page == "Save/Load":
    st.header("Save/Load")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save"):
            club.save_file()
            st.success("Saved")
    with col2:
        if st.button("Reload"):
            club.load_file()
            st.success("Reloaded")
