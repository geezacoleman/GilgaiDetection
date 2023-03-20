import cv2
import json
import numpy as np


def save_slider_values(slider_values, file_path):
    with open(file_path, "w") as json_file:
        json.dump(slider_values, json_file)

def load_slider_values(file_path):
    try:
        with open(file_path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return None

def on_trackbar(*args):
    pass

def gilgai_detection(image_path):
    # Load the image
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Create windows
    cv2.namedWindow("Output")

    param_img = np.zeros((1, 500, 3), np.uint8)
    cv2.namedWindow("Parameters", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Parameters", 500, 400)

    # Create trackbars for green wheat
    for i, color in enumerate(["H", "S", "V"]):
        cv2.createTrackbar(f"Green {color} lower", "Parameters", 0, 255, on_trackbar)
        cv2.createTrackbar(f"Green {color} upper", "Parameters", 255, 255, on_trackbar)

    # Create trackbars for scolds
    for i, color in enumerate(["H", "S", "V"]):
        cv2.createTrackbar(f"Gilgai {color} lower", "Parameters", 0, 255, on_trackbar)
        cv2.createTrackbar(f"Gilgai {color} upper", "Parameters", 255, 255, on_trackbar)

    json_file_path = "parameters.json"
    saved_values = load_slider_values(json_file_path)
    if saved_values is not None:
        for key, value in saved_values.items():
            cv2.setTrackbarPos(key, "Parameters", value)

    while True:
        # Get trackbar values for green wheat
        green_lower = np.array([cv2.getTrackbarPos(f"Green {color} lower", "Parameters") for color in ["H", "S", "V"]])
        green_upper = np.array([cv2.getTrackbarPos(f"Green {color} upper", "Parameters") for color in ["H", "S", "V"]])

        # Get trackbar values for scolds
        gilgai_lower = np.array([cv2.getTrackbarPos(f"Gilgai {color} lower", "Parameters") for color in ["H", "S", "V"]])
        gilgai_upper = np.array([cv2.getTrackbarPos(f"Gilgai {color} upper", "Parameters") for color in ["H", "S", "V"]])

        # Create masks for green wheat and white/red-brown scolds
        green_mask = cv2.inRange(img, green_lower, green_upper)
        gilgai_mask = cv2.inRange(img, gilgai_lower, gilgai_upper)

        masked_green = cv2.bitwise_and(img, img, mask=green_mask)
        masked_green = cv2.cvtColor(masked_green, cv2.COLOR_HSV2BGR)

        masked_gilgai = cv2.bitwise_and(img, img, mask=gilgai_mask)
        masked_gilgai = cv2.cvtColor(masked_gilgai, cv2.COLOR_HSV2BGR)

        # Calculate percentages
        total_pixels = img.shape[0] * img.shape[1]
        green_percentage = (np.sum(green_mask > 0) / total_pixels) * 100
        gilgai_percentage = (np.sum(gilgai_mask > 0) / total_pixels) * 100

        # Overlay percentage text on images
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        font_color = (255, 255, 255)
        font_thickness = 2

        green_text = f"Wheat: {green_percentage:.2f}%"
        scold_text = f"Gilgai: {gilgai_percentage:.2f}%"

        cv2.putText(masked_green, green_text, (10, 30), font, font_scale, font_color, font_thickness)
        cv2.putText(masked_gilgai, scold_text, (10, 30), font, font_scale, font_color, font_thickness)

        resized_img = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2))
        resized_img = cv2.cvtColor(resized_img, cv2.COLOR_HSV2BGR)
        cv2.putText(resized_img, "Original", (10, 30), font, font_scale, font_color, font_thickness)

        stack = np.hstack((masked_green, masked_gilgai))
        stack = np.vstack((resized_img, stack))

        # Show masked images
        cv2.imshow("Output", stack)
        cv2.imshow("Parameters", param_img)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    slider_values = {}
    for color in ["H", "S", "V"]:
        slider_values[f"Green {color} lower"] = cv2.getTrackbarPos(f"Green {color} lower", "Parameters")
        slider_values[f"Green {color} upper"] = cv2.getTrackbarPos(f"Green {color} upper", "Parameters")
        slider_values[f"Gilgai {color} lower"] = cv2.getTrackbarPos(f"Gilgai {color} lower", "Parameters")
        slider_values[f"Gilgai {color} upper"] = cv2.getTrackbarPos(f"Gilgai {color} upper", "Parameters")

    save_slider_values(slider_values, json_file_path)

    # Close all windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    image_path = "images/twitter_test.png"
    gilgai_detection(image_path)
