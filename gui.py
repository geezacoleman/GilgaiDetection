import os
import csv
from tkinter import Tk, Button, Label, Entry, Text, filedialog, messagebox, Scrollbar, Canvas, Frame, font
from process_directory import process_directory

from PIL import Image, ImageTk

def browse_directory(entry):
    directory = filedialog.askdirectory()
    entry.delete(0, "end")
    entry.insert(0, directory)

def process_directory_gui(image_directory, json_file_path, output_widget):
    global images
    if not os.path.exists(image_directory):
        messagebox.showerror("Error", "Please select a valid image directory.")
        return

    results = process_directory(image_directory, json_file_path)
    if not results:
        messagebox.showerror("Error", "No JSON file found.")
        return

    images = results

    if images:
        # Display the first image
        show_image_on_canvas(image_canvas, 0)
    else:
        messagebox.showerror("Error", "No images found in the selected directory.")

    # Display the first image
    show_image_on_canvas(image_canvas, 0)
    update_image_navigation_buttons()

    output_widget.delete(1.0, "end")
    output_widget.insert("end", "Image Name\tGreen Wheat (%)\tGilgai (%)\n")
    output_widget.insert("end", "-" * 80 + "\n")

    for result in results:
        output_widget.insert("end", f"{result['file_name']}\t{result['green_percentage']:.2f}\t{result['gilgai_percentage']:.2f}\n")


def set_threshold_values():
    messagebox.showinfo("Set Threshold Values", "To set the threshold values, please run the script separately.")


def show_image_on_canvas(canvas, image_index):
    global images, current_image_index
    current_image_index = image_index
    img = images[image_index]["image"]

    # Update the tkinter window size based on the image size
    root.geometry()

    canvas.config(width=img.shape[1], height=img.shape[0])
    canvas.image = ImageTk.PhotoImage(image=Image.fromarray(img))
    canvas.create_image(0, 0, anchor="nw", image=canvas.image)
    update_image_navigation_buttons()

    # Update gilgai and Wheat percentages labels
    gilgai_percentage = images[image_index]["gilgai_percentage"]
    wheat_percentage = images[image_index]["green_percentage"]
    gilgai_percentage_label.config(text=f"Gilgai: {gilgai_percentage:.2f}%")
    wheat_percentage_label.config(text=f"Wheat: {wheat_percentage:.2f}%")


def show_next_image(canvas):
    global current_image_index
    if current_image_index < len(images) - 1:
        show_image_on_canvas(canvas, current_image_index + 1)

def show_previous_image(canvas):
    global current_image_index
    if current_image_index > 0:
        show_image_on_canvas(canvas, current_image_index - 1)


def update_image_navigation_buttons():
    global current_image_index, images
    back_button["state"] = "normal" if current_image_index > 0 else "disabled"
    forward_button["state"] = "normal" if current_image_index < len(images) - 1 else "disabled"


# Initialize the main window
root = Tk()
root.title("Wheat-Gilgai Analysis")
root.geometry()

# Define the font style
custom_font = font.nametofont("TkDefaultFont")
custom_font.config(size=14, weight="bold")

current_image_index = 0
images = []

# Define the widgets and layout
directory_label = Label(root, text="Image Directory:")
directory_label.grid(row=0, column=0, padx=10, pady=10)

directory_entry = Entry(root, width=60)
directory_entry.grid(row=0, column=1, padx=10, pady=10)

browse_button = Button(root, text="Browse", command=lambda: browse_directory(directory_entry))
browse_button.grid(row=0, column=2, padx=10, pady=10)

process_button = Button(root, text="Process Images", command=lambda: process_directory_gui(directory_entry.get(), json_file_path, output_text))
process_button.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

set_threshold_button = Button(root, text="Set Threshold Values", command=lambda: set_threshold_values(json_file_path))
set_threshold_button.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

image_canvas = Canvas(root, bg="white", width=300, height=300)
image_canvas.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

# Create a frame for buttons and labels
button_frame = Frame(root)
button_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

# Add back and forward buttons
back_button = Button(button_frame, text="Back", state="disabled", width=12, command=lambda: show_previous_image(image_canvas))
back_button.grid(row=0, column=0, padx=(10, 0), pady=10)

forward_button = Button(button_frame, text="Forward", state="disabled", width=12, command=lambda: show_next_image(image_canvas))
forward_button.grid(row=0, column=1, padx=(0, 10), pady=10)

# Add gilgai and Wheat percentages labels
gilgai_percentage_label = Label(button_frame, text="Gilgai: -", anchor="w")
gilgai_percentage_label.grid(row=1, column=0, padx=(10, 0), pady=(0, 10))

wheat_percentage_label = Label(button_frame, text="Wheat: -", anchor="w")
wheat_percentage_label.grid(row=1, column=1, padx=(0, 10), pady=(0, 10))

output_text_label = Label(root, text="CSV Output", anchor="w")
output_text_label.grid(row=6, column=0, padx=(0, 10), pady=(0, 10))
output_text = Text(root, wrap="none", width=80, height=15)
output_text.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

scrollb_x = Scrollbar(root, orient="horizontal", command=output_text.xview)
scrollb_x.grid(row=8, column=0, columnspan=3, padx=10, sticky="ew")

scrollb_y = Scrollbar(root, orient="vertical", command=output_text.yview)
scrollb_y.grid(row=7, column=3, pady=10, sticky="ns")

output_text.configure(xscrollcommand=scrollb_x.set, yscrollcommand=scrollb_y.set)

if __name__ == "__main__":
    json_file_path = "parameters.json"
    root.mainloop()