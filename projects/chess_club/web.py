import streamlit as st

st.header("Welcome to --- Festival scheduling system")

if 'total' not in st.session_state:
    st.session_state.total=0
# st.session_state['total']=0 # synonymous with the line above
if st.button('+'):
    st.session_state.total+=1
        st.write(st.session_state.total)