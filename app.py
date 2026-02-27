import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
import matplotlib.pyplot as plt

from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

st.set_page_config(layout="wide")
st.title("🏫 Smart Vocabulary Test ERP")

DATA_FILE = "results.csv"

# ===============================
# Smart Sentence Generator
# ===============================

def generate_sentences(word):

    word = word.lower()

    correct_templates = [
        f"I learned the meaning of {word} today.",
        f"The teacher explained the word {word} clearly.",
        f"She used the word {word} in a sentence.",
        f"Understanding {word} helps improve vocabulary."
    ]

    wrong_templates = [
        f"{word} are running fast.",
        f"He eat {word} yesterday.",
        f"{word} jumping over sky.",
        f"They was {word} happily."
    ]

    correct_sentence = random.choice(correct_templates)
    options = [correct_sentence] + random.sample(wrong_templates, 3)
    random.shuffle(options)

    return options, correct_sentence


# ===============================
# Keep Only 6 Columns
# ===============================

def filter_dataframe(df):

    required_columns = [
        "Student Name",
        "Vocabulary Word",
        "Selected Answer",
        "Correct Answer",
        "Result",
        "Date Time"
    ]

    df = df.loc[:, ~df.columns.duplicated()]
    df = df[[col for col in required_columns if col in df.columns]]

    return df


# ===============================
# Save Result
# ===============================

def save_result(student, word, selected, correct):

    result_text = "Right" if selected == correct else "Wrong"

    new_data = pd.DataFrame([{
        "Student Name": student,
        "Vocabulary Word": word,
        "Selected Answer": selected,
        "Correct Answer": correct,
        "Result": result_text,
        "Date Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data

    df.to_csv(DATA_FILE, index=False)


# ===============================
# FIXED PDF Generator (No Overlap)
# ===============================

def generate_pdf(df, student_name):

    pdf_file = "student_report.pdf"
    doc = SimpleDocTemplate(pdf_file)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>Student Report: {student_name}</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    df = filter_dataframe(df)

    if len(df) > 0:

        wrapped_data = []
        header = df.columns.tolist()
        wrapped_data.append(header)

        for row in df.values.tolist():
            wrapped_row = []
            for cell in row:
                wrapped_row.append(Paragraph(str(cell), styles["Normal"]))
            wrapped_data.append(wrapped_row)

        table = Table(wrapped_data, repeatRows=1)

        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))

        elements.append(table)

    else:
        elements.append(Paragraph("No Data Found", styles["Normal"]))

    doc.build(elements)
    return pdf_file


# ===============================
# UI SECTION
# ===============================

col1, col2 = st.columns(2)

student_name = col1.text_input("Enter Student Name")
word_input = col2.text_input("Vocabulary Word")

if st.button("Generate Question"):

    if student_name and word_input:

        options, correct_sentence = generate_sentences(word_input)

        st.session_state.options = options
        st.session_state.correct_sentence = correct_sentence

        st.success("Question Generated")

if "options" in st.session_state:

    selected = st.radio("Select Correct Sentence", st.session_state.options)

    if st.button("Check Answer"):

        if selected == st.session_state.correct_sentence:
            st.success("✅ Correct Answer")
        else:
            st.error("❌ Wrong Answer")

        save_result(
            student_name,
            word_input,
            selected,
            st.session_state.correct_sentence
        )


# ===============================
# DASHBOARD
# ===============================

st.subheader("📊 Student Dashboard")

if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE)
    df = filter_dataframe(df)

    search = st.text_input("Search Student")

    if search:
        df = df[df["Student Name"].str.contains(search, case=False)]

    st.dataframe(df, use_container_width=True)

    # ===============================
    # VERY SMALL GRAPHS
    # ===============================

    if len(df) > 0:

        st.subheader("📈 Performance Graphs")

        fig1, ax1 = plt.subplots()
        fig1.set_size_inches(2, 1)

        df["Result"].value_counts().plot(kind="bar", ax=ax1)
        ax1.set_title("Result", fontsize=6)
        ax1.tick_params(labelsize=5)

        st.pyplot(fig1, use_container_width=False)

        fig2, ax2 = plt.subplots()
        fig2.set_size_inches(2, 1)

        df["Vocabulary Word"].value_counts().head(5).plot(kind="bar", ax=ax2)
        ax2.set_title("Words", fontsize=6)
        ax2.tick_params(labelsize=5)

        st.pyplot(fig2, use_container_width=False)

    # ===============================
    # REPORT + WHATSAPP SHARE
    # ===============================

    st.subheader("📄 Report & WhatsApp Share")

    student_share = st.text_input("Enter Student Name for Share")

    if student_share:

        filtered_df = df[df["Student Name"].str.contains(student_share, case=False)]

        if st.button("Generate Student PDF"):

            pdf_path = generate_pdf(filtered_df, student_share)

            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download Student PDF",
                    data=f,
                    file_name="student_report.pdf",
                    mime="application/pdf"
                )

        whatsapp_message = f"Student {student_share} report is ready."
        whatsapp_url = f"https://wa.me/?text={whatsapp_message}"

        st.markdown(f"[Share via WhatsApp]({whatsapp_url})")