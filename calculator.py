import tkinter as tk
import math

root = tk.Tk()
root.title("Scientific Calculator")
root.geometry("360x450")
root.resizable(False, False)

# ---------------- THEME ----------------
dark = False

def apply_theme():
    bg = "#1e1e1e" if dark else "white"
    fg = "white" if dark else "black"
    btn_bg = "#333333" if dark else "#f0f0f0"

    root.config(bg=bg)
    entry.config(bg=bg, fg=fg, insertbackground=fg)

    for btn in buttons:
        btn.config(bg=btn_bg, fg=fg, activebackground="#555555")

# ---------------- VARIABLES ----------------
expression = ""
input_text = tk.StringVar()

# ---------------- FUNCTIONS ----------------
def press(num):
    global expression
    expression += str(num)
    input_text.set(expression)

def clear():
    global expression
    expression = ""
    input_text.set("")

def equalpress():
    global expression
    try:
        result = str(eval(expression))
        input_text.set(result)
        expression = result
    except:
        input_text.set("Error")
        expression = ""

def toggle_theme():
    global dark
    dark = not dark
    apply_theme()

# Scientific functions
def sin_func():
    global expression
    result = str(math.sin(math.radians(float(expression))))
    input_text.set(result)
    expression = result

def cos_func():
    global expression
    result = str(math.cos(math.radians(float(expression))))
    input_text.set(result)
    expression = result

def tan_func():
    global expression
    result = str(math.tan(math.radians(float(expression))))
    input_text.set(result)
    expression = result

def log_func():
    global expression
    result = str(math.log10(float(expression)))
    input_text.set(result)
    expression = result

def sqrt_func():
    global expression
    result = str(math.sqrt(float(expression)))
    input_text.set(result)
    expression = result

# ---------------- ENTRY ----------------
entry = tk.Entry(
    root,
    textvariable=input_text,
    font=("Arial", 22),
    bd=10,
    relief="ridge",
    justify="right"
)
entry.pack(fill="both", ipadx=10, ipady=20, padx=10, pady=10)

# ---------------- BUTTON FRAME ----------------
frame = tk.Frame(root)
frame.pack()

# ---------------- BUTTONS ----------------
buttons = []

btn_texts = [
    '7','8','9','/',
    '4','5','6','*',
    '1','2','3','-',
    '0','.','=','+'
]

row = 0
col = 0

for text in btn_texts:
    if text == "=":
        btn = tk.Button(frame, text=text, width=8, height=2, command=equalpress)
    else:
        btn = tk.Button(frame, text=text, width=8, height=2,
                        command=lambda t=text: press(t))

    btn.grid(row=row, column=col, padx=3, pady=3)
    buttons.append(btn)

    col += 1
    if col > 3:
        col = 0
        row += 1

# ---------------- SCIENTIFIC BUTTONS ----------------
sc_frame = tk.Frame(root)
sc_frame.pack(pady=10)

tk.Button(sc_frame, text="sin", width=6, command=sin_func).grid(row=0, column=0, padx=2, pady=2)
tk.Button(sc_frame, text="cos", width=6, command=cos_func).grid(row=0, column=1, padx=2, pady=2)
tk.Button(sc_frame, text="tan", width=6, command=tan_func).grid(row=0, column=2, padx=2, pady=2)
tk.Button(sc_frame, text="log", width=6, command=log_func).grid(row=0, column=3, padx=2, pady=2)

tk.Button(sc_frame, text="sqrt", width=6, command=sqrt_func).grid(row=1, column=0, padx=2, pady=2)
tk.Button(sc_frame, text="C", width=6, command=clear).grid(row=1, column=1, padx=2, pady=2)
tk.Button(sc_frame, text="Theme", width=13, command=toggle_theme).grid(row=1, column=2, columnspan=2, padx=2, pady=2)

# ---------------- APPLY THEME ----------------
apply_theme()

# ---------------- RUN ----------------
root.mainloop()