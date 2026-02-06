import streamlit as st
from datetime import datetime, timedelta
from main import ChessClub, read_json, write_json

st.set_page_config(page_title="Critical Mass Chess Club", layout="wide", page_icon="♟️")

#initialize
if 'club' not in st.session_state:
    club = ChessClub()
    club.load_initial_data()
    club.load_file()
    st.session_state.club = club
    # snapshot original resources.json for restore-to-defaults
    import copy
    st.session_state.defaults = copy.deepcopy(read_json("resources.json") or {})
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
page = st.selectbox("Menu", ["Events", "Add Event", "Find Slot", "Resources", "Save/Load", "Settings"])

#events
if page == "Events":
    st.header("Events")
    if not club.events:
        st.write("No events")
    else:
        filter_date = st.date_input("Filter by date", value=None)
        events = club.events if not filter_date else [e for e in club.events if e.start.date() == filter_date]

        # show spare pieces availability for the selected date
        if filter_date:
            existing_events_same_date = [e for e in club.events if e.start.date() == filter_date]
            total_needed = len(existing_events_same_date) * club.spare_per_event
            remaining = club.spare_per_day - total_needed
            st.info(f"Spare pieces available on {filter_date}: {max(0, remaining)} (policy: {club.spare_per_event} per event, {club.spare_per_day} per day)")
        
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
    # show current spare pieces policy
    st.subheader("Spare Pieces Policy")
    st.write(f"{club.spare_per_event} per event, {club.spare_per_day} per day")
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
    
    spare_pieces_for_event = st.number_input("Spare pieces for this event (0 = use default)", min_value=0, value=0, step=1)
    
    st.write("Resources:")
    cols = st.columns(3)
    selected = []
    for i, r in enumerate(club.resources):
        with cols[i % 3]:
            if st.checkbox(r.name, key=f"res_{r.id}"):
                selected.append(r.id)
    
    #check for busy coaches and show recommendations
    busy_coaches = []
    for coach_id in ["fm", "im", "gm"]:
        if coach_id in selected:
            workload = club.get_coach_workload(coach_id)
            if workload > 48:
                coach_name = next((r.name for r in club.resources if r.id == coach_id), coach_id)
                busy_coaches.append((coach_id, coach_name, workload))
    
    if busy_coaches:
        st.warning("**Busy Coach Alert**")
        for coach_id, coach_name, workload in busy_coaches:
            st.write(f"**{coach_name}** has {workload:.1f}h of events this week (>48h threshold)")
            alt_coach = club.suggest_alternative_coach(coach_id)
            if alt_coach:
                st.info(f"Consider **{alt_coach.name}** instead ({club.get_coach_workload(alt_coach.id):.1f}h this week)")
    
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
            spare_for_sched = spare_pieces_for_event if spare_pieces_for_event > 0 else None
            ok, msg = club.schedule_event(name, event_type, start, end, selected, spare_pieces=spare_for_sched)
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

#settings
elif page == "Settings":
    st.header("Settings")
    data = read_json("resources.json") or {}

    #add event type
    with st.expander("Add Event Type"):
        et_id = st.text_input("ID (e.g. lightning)", key="et_id")
        et_name = st.text_input("Display name", key="et_name")
        et_min = st.number_input("Min duration (h)", 0.1, 8.0, 0.5, step=0.1, key="et_min")
        if st.button("Add Event Type"):
            if et_id and et_name:
                data.setdefault("event_types", []).append({"id": et_id, "name": et_name, "min_duration": et_min})
                write_json(data, "resources.json")
                club.event_types[et_id] = {"id": et_id, "name": et_name, "min_duration": et_min}
                st.success(f"Event type '{et_name}' added")
                st.rerun()
            else:
                st.error("ID and name are required")

    #add resource
    with st.expander("Add Resource"):
        res_cat = st.selectbox("Category", ["equipment", "rooms", "staff"], key="res_cat")
        res_id = st.text_input("ID (e.g. board_5)", key="res_id")
        res_name = st.text_input("Display name", key="res_name")
        res_type = st.text_input("Type (e.g. board, clock, coach)", key="res_type")
        if st.button("Add Resource"):
            if res_id and res_name:
                entry = {"id": res_id, "name": res_name}
                if res_cat != "rooms":
                    entry["type"] = res_type
                data.setdefault(res_cat, []).append(entry)
                write_json(data, "resources.json")
                from main import Resource
                r_type = res_cat.rstrip("s") if res_cat == "rooms" else (res_type or res_cat)
                club.resources.append(Resource(res_id, res_name, r_type))
                st.success(f"Resource '{res_name}' added to {res_cat}")
                st.rerun()
            else:
                st.error("ID and name are required")

    #add restriction
    with st.expander("Add Restriction"):
        r_type = st.selectbox("Type", ["co_requirement", "exclusion"], key="r_type")
        r_name = st.text_input("Name / description", key="r_name")
        if r_type == "co_requirement":
            r_case = st.selectbox("Applies to event type", list(club.event_types.keys()), key="r_case")
            r_requires = st.multiselect("Required resources", [r.id for r in club.resources], key="r_requires")
            r_min = st.number_input("Minimum required", 1, len(club.resources), 1, key="r_min")
            if st.button("Add Co-requirement"):
                if r_name and r_requires:
                    restriction = {"type": "co_requirement", "name": r_name, "case": r_case, "requires": r_requires, "min_amount": r_min}
                    data.setdefault("restrictions", []).append(restriction)
                    write_json(data, "resources.json")
                    club.restrictions.append(restriction)
                    st.success(f"Co-requirement '{r_name}' added")
                    st.rerun()
                else:
                    st.error("Name and resources are required")
        else:
            r_resources = st.multiselect("Affected resources", [r.id for r in club.resources], key="r_resources")
            r_allowed = st.multiselect("Allowed event types", list(club.event_types.keys()), key="r_allowed")
            if st.button("Add Exclusion"):
                if r_name and r_resources:
                    restriction = {"type": "exclusion", "name": r_name, "resources": r_resources, "allowed_events": r_allowed}
                    data.setdefault("restrictions", []).append(restriction)
                    write_json(data, "resources.json")
                    club.restrictions.append(restriction)
                    st.success(f"Exclusion '{r_name}' added")
                    st.rerun()
                else:
                    st.error("Name and resources are required")

    #current items
    st.subheader("Current Event Types")
    for i, et in enumerate(data.get("event_types", [])):
        col1, col2 = st.columns([3, 1])
        col1.write(f"{et['name']} - {et['id']}, min {et.get('min_duration', '?')}h")
        if col2.button("Remove", key=f"rm_et_{i}"):
            data["event_types"].pop(i)
            write_json(data, "resources.json")
            club.event_types.pop(et["id"], None)
            st.rerun()

    st.subheader("Current Restrictions")
    for i, r in enumerate(data.get("restrictions", [])):
        col1, col2 = st.columns([3, 1])
        col1.write(f"{r.get('name', 'Unnamed')} ({r['type']})")
        if col2.button("Remove", key=f"rm_r_{i}"):
            data["restrictions"].pop(i)
            write_json(data, "resources.json")
            club.restrictions = data["restrictions"]
            st.rerun()

    st.subheader("Current Resources")
    for cat in ["rooms", "equipment", "staff"]:
        for i, item in enumerate(data.get(cat, [])):
            col1, col2 = st.columns([3, 1])
            col1.write(f"{item['name']} - {item['id']} - {cat}")
            if col2.button("Remove", key=f"rm_{cat}_{i}"):
                data[cat].pop(i)
                write_json(data, "resources.json")
                club.resources = [r for r in club.resources if r.id != item["id"]]
                st.rerun()

    #spare pieces policy
    with st.expander("Spare Pieces Policy"):
        col1, col2 = st.columns(2)
        spare_day = col1.number_input("Spare per day", min_value=0, value=int(club.spare_per_day), step=1, key="spare_day")
        spare_event = col2.number_input("Spare per event", min_value=0, value=int(club.spare_per_event), step=1, key="spare_event")
        if st.button("Update Spare Policy"):
            club.spare_per_day = int(spare_day)
            club.spare_per_event = int(spare_event)
            data = read_json("resources.json") or {}
            cfg = data.get("config", {})
            cfg["spare_per_day"] = int(spare_day)
            cfg["spare_per_event"] = int(spare_event)
            data["config"] = cfg
            write_json(data, "resources.json")
            st.success("Spare policy updated")

    #restore defaults
    if st.button("Restore Defaults"):
        defaults = st.session_state.get("defaults", {})
        if defaults:
            write_json(defaults, "resources.json")
            #reload club
            new_club = ChessClub()
            new_club.load_initial_data()
            new_club.load_file()
            st.session_state.club = new_club
            st.success("Restored to defaults")
            st.rerun()
        else:
            st.error("No defaults available")
