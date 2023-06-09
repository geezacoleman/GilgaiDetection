import os
import cv2
import csv
import numpy as np

from gilgai_detection import load_slider_values

def process_directory(image_directory, json_file_path="parameters.json", output_csv_path="output.csv"):
    # Load the slider values from the JSON file
    parameters = load_slider_values(json_file_path)
    if parameters is None:
        print("Error: No JSON file found.")
        return

    green_lower = np.array([parameters[f"Green {color} lower"] for color in ["H", "S", "V"]])
    green_upper = np.array([parameters[f"Green {color} upper"] for color in ["H", "S", "V"]])
    gilgai_lower = np.array([parameters[f"Gilgai {color} lower"] for color in ["H", "S", "V"]])
    gilgai_upper = np.array([parameters[f"Gilgai {color} upper"] for color in ["H", "S", "V"]])

    # Initialize the results list
    results = []

    # Iterate through all images in the directory
    for file_name in os.listdir(image_directory):
        # Check if the file is an image
        if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(image_directory, file_name)

            # Load and process the image
            img = cv2.imread(img_path)
            img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            green_mask = cv2.inRange(img_hsv, green_lower, green_upper)
            gilgai_mask = cv2.inRange(img_hsv, gilgai_lower, gilgai_upper)

            # Calculate percentages
            total_pixels = img.shape[0] * img.shape[1]
            green_percentage = (np.sum(green_mask > 0) / total_pixels) * 100
            gilgai_percentage = (np.sum(gilgai_mask > 0) / total_pixels) * 100

            # Create green and red colored masks
            green_colored_mask = cv2.cvtColor(green_mask, cv2.COLOR_GRAY2BGR)
            red_colored_mask = cv2.cvtColor(gilgai_mask, cv2.COLOR_GRAY2BGR)
            green_colored_mask[:, :, 0] = 0
            green_colored_mask[:, :, 2] = 0
            red_colored_mask[:, :, 0] = 0
            red_colored_mask[:, :, 1] = 0

            # Overlay masks with 50% transparency
            green_overlay = cv2.bitwise_and(img, img, mask=green_mask)
            gilgai_overlay = cv2.bitwise_and(img, img, mask=gilgai_mask)
            alpha = 0.5
            img_with_green = cv2.addWeighted(green_colored_mask, alpha, img, 1 - alpha, 0)
            img_with_gilgai = cv2.addWeighted(red_colored_mask, alpha, img_with_green, 1, 0)

            # Convert to RGB for Tkinter
            img_with_gilgai_rgb = cv2.cvtColor(img_with_gilgai, cv2.COLOR_BGR2RGB)

            # Add the result to the results list
            results.append(
                {"file_name": file_name, "green_percentage": green_percentage, "gilgai_percentage": gilgai_percentage,
                 "image": img_with_gilgai_rgb})

    # Save the results to a CSV file
    with open(output_csv_path, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Image Name", "Wheat (%)", "Gilgai (%)"])

        for result in results:
            csv_writer.writerow(result)

    return results

if __name__ == "__main__":
    process_directory(image_directory="images")