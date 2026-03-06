from sqlalchemy import create_engine, text
import streamlit as st

db_url = st.secrets["DATABASE_URL"]
engine = create_engine(db_url, pool_pre_ping=True)

with engine.connect() as conn:
    print(conn.execute(text("select 1")).scalar())