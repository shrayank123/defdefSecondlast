
import customtkinter as ctk
from PIL import Image
import cv2
from customtkinter import CTkImage
from pyzbar.pyzbar import decode
import json
from datetime import datetime
import os

cap = cv2.VideoCapture(0)

# Paths for JSON records
sis_path = 'records/sis_smg.json'
Jc1_path = 'records/jc1.json'
Jc2_path = 'records/jc2.json'


# Ensure JSON file is cleared on program start
def clear_json(path):
    with open(path, 'w') as f:
        json.dump({}, f)

# Clear JSON attendance record on start
clear_json(sis_path)

# Initialize `customtkinter` settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Time limit for attendance
eight_am = datetime.strptime("08:00 AM", "%I:%M %p")

# Ensure JSON files exist
def ensure_json_exists(path):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump({}, f)

# Load JSON data
def load_json(path):
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# Save JSON data
def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)



# Main `customtkinter` GUI setup
root = ctk.CTk()
root.title("Webcam Attendance System")
root.geometry("1000x600")  # Increase window size to allow more space for webcam feed

# Frame for webcam feed (increase width and height)
webcam_frame = ctk.CTkFrame(root)
webcam_frame.place(relwidth=0.75, relheight=0.9, relx=0.02, rely=0.05)  # Adjusted size for larger view
webcam_label = ctk.CTkLabel(webcam_frame, text="")
webcam_label.pack(fill="both", expand=True)  # Make label fill frame completely

# Frame for time display (move to a smaller space on the right)
time_frame = ctk.CTkFrame(root)
time_frame.place(relx=0.78, rely=0.05, relwidth=0.2, relheight=0.15)  # Adjust position and size
time_label = ctk.CTkLabel(time_frame, text="Time", font=("Helvetica", 16))
time_label.pack()

# Frame for list of earliest attendees
list_frame = ctk.CTkFrame(root)
list_frame.place(relx=0.78, rely=0.25, relwidth=0.2, relheight=0.7)  # Adjust position and size
list_label = ctk.CTkLabel(list_frame, text="Top 10 Earliest People", font=("Helvetica", 12))
list_label.pack()
people_listbox = ctk.CTkTextbox(list_frame, font=("Helvetica", 10), width=100, height=300)
people_listbox.pack(fill=ctk.BOTH, expand=True)

# Function to display webcam feed and handle QR scanning
def show_webcam():
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        qr_info = decode(frame)

        if qr_info:
            qr = qr_info[0]
            data = qr.data.decode()
            rect = qr.rect
            cv2.putText(frame, data, (rect.left, rect.top), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

            # Extract grade and name from QR code data
            student_name = data[4:]  # assuming last part is student name
            student_grade = data[:3]  # assuming first part is grade

            # Print to debug values
            print("Scanned Grade:", student_grade)  # Check what grade is being read
            print("Scanned Name:", student_name)

            # Time check
            now = datetime.now()
            formatted_time = now.strftime("%I:%M %p")
            formatted_date = now.strftime("%Y-%m-%d")
            parsed_time = datetime.strptime(formatted_time, "%I:%M %p")
            state = 'absent' if parsed_time.time() > eight_am.time() else 'present'

            # Update attendance data
            # Update attendance data
            student_data = load_json(sis_path)

            # Create a unique key for each student based on their grade and name
            entry_key = f"{student_grade}_{student_name}"

            student_data[entry_key] = {
                'name': student_name,
                'grade': student_grade,
                "time": formatted_time,
                'date': formatted_date,
                'state': state
            }

            # Save to the main attendance file
            save_json(sis_path, student_data)

            # Save to the specific grade path
            if student_grade == 'Jc2':
                grade_data = load_json(Jc2_path)
                grade_data[entry_key] = student_data[entry_key]
                save_json(Jc2_path, grade_data)
            elif student_grade == 'Jc1':
                grade_data = load_json(Jc1_path)
                grade_data[entry_key] = student_data[entry_key]
                save_json(Jc1_path, grade_data)

            # Update displayed list with new entry if needed
            people_listbox.delete("1.0", ctk.END)
            for key, value in student_data.items():
                people_listbox.insert(ctk.END, f"{value['name']} ({value.get('grade', 'N/A')}) -- {value['time']}\n")

        # Convert frame to RGB for Tkinter
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = CTkImage(light_image=img, dark_image=img, size=(webcam_label.winfo_width(), webcam_label.winfo_height()))
        webcam_label.imgtk = imgtk
        webcam_label.configure(image=imgtk)

    webcam_label.after(10, show_webcam)

show_webcam()

# Function to update the time label
def update_time():
    current_time = datetime.now().strftime('%H:%M:%S')
    time_label.configure(text=current_time)
    root.after(1000, update_time)

update_time()

# Properly release the camera on exit
def on_closing():
    cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter main loop
root.mainloop()