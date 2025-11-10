# app.py
import streamlit as st
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

st.title("📨 Ma Newsletter quotidienne")

subject = st.text_input("Sujet de la newsletter")
body = st.text_area("Contenu de la newsletter")

if st.button("Envoyer maintenant"):
    sender = "ton.email@gmail.com"
    password = st.secrets["EMAIL_PASSWORD"]  # stocke ton mot de passe dans Streamlit Secrets
    recipients = ["destinataire1@gmail.com", "destinataire2@gmail.com"]

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

    st.success("✅ Newsletter envoyée avec succès !")
