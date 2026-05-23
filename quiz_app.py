# ===============================
# QUIZ APPLICATION WITH GUI
# ===============================

import tkinter as tk
from tkinter import messagebox

# -------------------------------
# Questions Data
# -------------------------------
questions = [
    {
        "question": "What is the capital of India?",
        "options": ["Mumbai", "Delhi", "Pune", "Chennai"],
        "answer": "Delhi"
    },
    {
        "question": "Which language is used for Python programming?",
        "options": ["Java", "C++", "Python", "HTML"],
        "answer": "Python"
    },
    {
        "question": "Which planet is called Red Planet?",
        "options": ["Earth", "Mars", "Venus", "Jupiter"],
        "answer": "Mars"
    },
    {
        "question": "What is 10 + 5 ?",
        "options": ["12", "15", "18", "20"],
        "answer": "15"
    },
    {
        "question": "Who developed Python?",
        "options": [
            "Dennis Ritchie",
            "Guido van Rossum",
            "James Gosling",
            "Elon Musk"
        ],
        "answer": "Guido van Rossum"
    }
]

# -------------------------------
# Main Window
# -------------------------------
root = tk.Tk()
root.title("Quiz Application")
root.geometry("700x500")
root.config(bg="#f0f8ff")

# -------------------------------
# Variables
# -------------------------------
username = tk.StringVar()
current_question = 0
score = 0
selected_option = tk.StringVar()

# -------------------------------
# Sign In Page
# -------------------------------
login_frame = tk.Frame(root, bg="#f0f8ff")

title = tk.Label(
    login_frame,
    text="Welcome to Quiz App",
    font=("Arial", 24, "bold"),
    bg="#f0f8ff",
    fg="darkblue"
)
title.pack(pady=30)

name_label = tk.Label(
    login_frame,
    text="Enter Your Name",
    font=("Arial", 14),
    bg="#f0f8ff"
)
name_label.pack()

name_entry = tk.Entry(
    login_frame,
    textvariable=username,
    font=("Arial", 14),
    width=30
)
name_entry.pack(pady=10)


# -------------------------------
# Quiz Frame
# -------------------------------
quiz_frame = tk.Frame(root, bg="#ffffff")

question_label = tk.Label(
    quiz_frame,
    text="",
    font=("Arial", 18, "bold"),
    wraplength=500,
    bg="#ffffff"
)
question_label.pack(pady=20)

radio_buttons = []

for i in range(4):
    rb = tk.Radiobutton(
        quiz_frame,
        text="",
        variable=selected_option,
        value="",
        font=("Arial", 14),
        bg="#ffffff",
        anchor="w"
    )
    rb.pack(fill="x", padx=100, pady=5)
    radio_buttons.append(rb)

score_label = tk.Label(
    quiz_frame,
    text="Score: 0",
    font=("Arial", 12, "bold"),
    bg="#ffffff",
    fg="green"
)
score_label.pack(pady=10)


# -------------------------------
# Functions
# -------------------------------
def load_question():
    global current_question

    if current_question < len(questions):

        q = questions[current_question]

        question_label.config(
            text=f"Q{current_question + 1}. {q['question']}"
        )

        selected_option.set(None)

        for i in range(4):
            radio_buttons[i].config(
                text=q["options"][i],
                value=q["options"][i]
            )

    else:
        show_result()


def next_question():
    global current_question, score

    selected = selected_option.get()

    if selected == "":
        messagebox.showwarning(
            "Warning",
            "Please select an option!"
        )
        return

    correct_answer = questions[current_question]["answer"]

    if selected == correct_answer:
        score += 1

    score_label.config(text=f"Score: {score}")

    current_question += 1
    load_question()


def show_result():
    percentage = (score / len(questions)) * 100

    if percentage >= 80:
        performance = "Excellent"
    elif percentage >= 50:
        performance = "Good Job"
    else:
        performance = "Keep Practicing"

    messagebox.showinfo(
        "Quiz Result",
        f"Name: {username.get()}\n\n"
        f"Final Score: {score}/{len(questions)}\n"
        f"Percentage: {percentage}%\n"
        f"Performance: {performance}"
    )

    root.destroy()


def start_quiz():
    if username.get() == "":
        messagebox.showerror(
            "Error",
            "Please enter your name!"
        )
        return

    login_frame.pack_forget()
    quiz_frame.pack(fill="both", expand=True)

    load_question()


# -------------------------------
# Buttons
# -------------------------------
start_button = tk.Button(
    login_frame,
    text="Start Quiz",
    font=("Arial", 14, "bold"),
    bg="darkblue",
    fg="white",
    padx=20,
    pady=10,
    command=start_quiz
)
start_button.pack(pady=20)

next_button = tk.Button(
    quiz_frame,
    text="Next",
    font=("Arial", 14, "bold"),
    bg="green",
    fg="white",
    padx=20,
    pady=10,
    command=next_question
)
next_button.pack(pady=20)

# -------------------------------
# Show Login Page
# -------------------------------
login_frame.pack(fill="both", expand=True)

# -------------------------------
# Run Application
# -------------------------------
root.mainloop()