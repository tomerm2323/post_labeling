
import pandas as pd
import tkinter as tk
from tkinter import Entry, Label, Button

# Function to create a labeling form from a CSV file
def create_labeling_form(csv_file):
    data = pd.read_csv(csv_file,encoding='utf8')
    num_entries = len(data)
    curr_row = 0

    def submit_label():
        label = entry.get()
        labels.append(label)

        if len(labels) < num_entries:
            entry.delete(0, tk.END)
            text_label.config(text=data.iloc[len(labels), 0])
        else:
            save_results(labels)
            window.quit()

    def save_results(labels):
        labeled_data = data.copy()
        labeled_data['Label'] = labels

        labeled_data.to_csv("labeled_data.csv", index=False)

    window = tk.Tk()
    window.title("Text Labeling Form - Enter 0 for not pro israel and 1 for pro israel ")

    labels = []
    text_label = Label(window, text=data.iloc[curr_row, 0], wraplength=400, anchor="w", justify="left")
    text_label.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="w")

    label_prompt = Label(window, text=f"Enter hear")
    label_prompt.grid(row=1, column=0)

    entry = Entry(window)
    entry.grid(row=1, column=1)

    submit_button = Button(window, text="Submit", command=submit_label)
    submit_button.grid(row=2, column=0, columnspan=2)
    curr_row += 1
    window.mainloop()
    print(data)

if __name__ == "__main__":
    csv_file = r"C:\Users\Administrator\Desktop\DoccanoExample.csv"  # Replace with your CSV file path
    create_labeling_form(csv_file)
