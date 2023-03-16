# Imports
import os
import slack_sdk
import pyperclip
import sys
import re
import tkinter
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageTk


# Variables
client = WebClient(token="xoxb-627196878261-4876665458785-PMMJ8GvCuKhIORq2swxwxkuo")

# Fetch the user list only once and cache it for future use
cached_users = None

def get_users():
    global cached_users
    if cached_users is None:
        try:
            response = client.users_list()
            cached_users = response["members"]
        except SlackApiError as e:
            print(f"Error: {e}")
            cached_users = []
    return cached_users

exclude_real_names = set()
exclude_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exclude_real_names.txt")

if os.path.exists(exclude_file):
    with open(exclude_file) as f:
        for line in f:
            exclude_real_names.add(line.strip())

filtered_users = [user for user in get_users() if not user["is_bot"] and not user["deleted"] and user["real_name"] not in exclude_real_names]

# Sort users by real name
filtered_users = sorted(filtered_users, key=lambda user: user["real_name"])

# Function to send the message to the selected user
def send_message(user_name):
    for user in filtered_users:
        if user["real_name"] == user_name:
            user_id = user["id"]
            clipboard_content = pyperclip.paste()
            # Extract the name attribute from the XML
            name_match = re.search(r"name='([\w\s]+)'(?=\sposition=)", clipboard_content)
            if name_match:
                # add to name the text that is inside ActiveUser.txt
                active_user_file = os.path.join(os.path.expanduser("~"), "Documents", "SlackSenderVariables", "ActiveUser.txt")
                with open(active_user_file, "r") as f:
                    active_user = f.read()
                    filename = active_user + name_match.group(1).strip() + ".txt"
            else:
                filename = "UNKONWN TEXT.txt"
            # Save the temporary file on the desktop
            desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            filename_fullpath = os.path.join(desktop_path, filename)
            with open(filename_fullpath, "w") as f:
                f.write(clipboard_content)
            try:
                response = client.files_upload(
                    channels=user_id,
                    file=filename_fullpath
                )
                os.remove(filename_fullpath)
                button.config(text="Uploaded!", bg="green")
                window.after(1000, reset_button)
            except SlackApiError as e:
                print(f"Error: {e}")
                button.config(text="Fail", bg="red")
                window.after(1000, reset_button)
            break

# Function to reset button text and color
def reset_button():
    button.config(text="Send", bg="white")

# Function to close the tkinter window
def quit_window(icon, item):
   icon.stop()
   window.destroy()

# Define a function to show the window again
def show_window(icon, item):
   icon.stop()
   window.after(0,window.deiconify())


# Set the icon path to the file in the same directory as the script
icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')


# Create a GUI window that displays the filtered user names, and a button that sends the message to the selected user. 
window = tkinter.Tk()
window.title("Slack Sender")
window.geometry("200x400")
window.configure(background="white")


# Set the icon for the window and taskbar
window.iconbitmap(icon_path)
window.call('wm', 'iconphoto', window._w, tkinter.PhotoImage(file=icon_path))

#Make the window stay on top
window.wm_attributes("-topmost", 1)

# Bind the Escape and Alt+F4 keys to the close_window function
window.bind("<Escape>", quit_window)
window.bind("<Alt-F4>", quit_window)

# Bind the window close event to the close_window function
window.protocol("WM_DELETE_WINDOW", quit_window)

#Bind the Enter key and Spacebar to the send_message function
window.bind("<Return>", lambda event: send_message(listbox.get(listbox.curselection())))
window.bind("<space>", lambda event: send_message(listbox.get(listbox.curselection())))

# Create a listbox to display the user names
listbox = tkinter.Listbox(window, font=("Arial", 13))
for user in filtered_users:
    listbox.insert(tkinter.END, user["real_name"])
listbox.pack(fill=tkinter.BOTH, expand=1)

# Create last_selection.txt if it doesn't exist
last_selection_file = os.path.join(os.path.expanduser("~"), "Documents", "SlackSenderVariables", "last_selection.txt")
if not os.path.exists(last_selection_file):
    os.makedirs(os.path.dirname(last_selection_file), exist_ok=True)
    with open(last_selection_file, "w") as f:
        f.write("0")

# Highlight the last selected item
with open(last_selection_file, "r") as f:
    last_selection = int(f.read())
listbox.selection_set(last_selection)

# Give focus to the listbox so that arrow key navigation works without clicking on it first
listbox.focus_set()

# Bind the listbox selection event to save the last selected item
def save_last_selection(event):
    with open(last_selection_file, "w") as f:
        f.write(str(listbox.curselection()[0]))
listbox.bind("<<ListboxSelect>>", save_last_selection)

# Create a button to send the message
button = tkinter.Button(window, text="Send", command=lambda: send_message(listbox.get(listbox.curselection())), width=20, height=2, bg="white", fg="black")
button.pack(pady=10)

# Hide the window and show on the system taskbar
def hide_window():
   window.withdraw()
   #open image on D:\\_OPERATIVO_research\\1825_Raul\\Github\\00_Playground\\image.ico
   image=Image.open("D:\\_OPERATIVO_research\\1825_Raul\\Github\\00_Playground\\image.ico")
   menu=(item('Quit', quit_window), item('Show', show_window))
   icon=pystray.Icon("name", image, "My System Tray Icon", menu)
   icon.run()

window.protocol('WM_DELETE_WINDOW', hide_window)

# Start the tkinter event loop
window.mainloop()
