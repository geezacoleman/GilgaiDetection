from datetime import datetime
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image

import streamlit as st
import pandas as pd
import numpy as np
import imutils
import cv2

@st.cache_data
def thresholding(image, original_image, lower, upper, colour=None):
    mask = cv2.inRange(image, lower, upper)
    coloured_mask = np.zeros_like(image)
    coloured_mask[mask > 0] = colour

    coverage = np.count_nonzero(mask) / (mask.shape[0] * mask.shape[1]) * 100

    inverse_mask = cv2.bitwise_not(mask)

    masked_image = cv2.bitwise_and(original_image, original_image, mask=inverse_mask)
    output = cv2.add(masked_image, coloured_mask)

    return output, coverage

@st.cache_data
def convert_colour_space(image, colour_space):
    if colour_space == "HSV":
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2HSV)
    elif colour_space == "LAB":
        return cv2.cvtColor(image.copy(), cv2.COLOR_BGR2Lab)
    else:
        return image.copy()

def deconvert_colour_space(image, colour_space):
    if colour_space == "HSV":
        return cv2.cvtColor(image.copy(), cv2.COLOR_HSV2RGB)
    elif colour_space == "LAB":
        return cv2.cvtColor(image.copy(), cv2.COLOR_Lab2RGB)
    else:
        return image.copy()


def calculate_mean_min_max(pixel_values):
    if len(pixel_values) <= 1:
        mean_min = np.mean(pixel_values, axis=0) - 20
        mean_max = np.mean(pixel_values, axis=0) + 20

    else:
        min_values = np.min(pixel_values, axis=0)
        max_values = np.max(pixel_values, axis=0)
        mean_range = max_values - min_values
        mean_min = np.mean(pixel_values, axis=0) - (1 * mean_range / 1.5)
        mean_max = np.mean(pixel_values, axis=0) + (1 * mean_range / 1.5)

    if len(pixel_values) > 20:
        pixel_values.pop(0)

    mean_min = np.clip(mean_min, 0, 255)
    mean_max = np.clip(mean_max, 0, 255)

    return mean_min, mean_max


def on_slider_change():
    st.session_state.manual_slider_update = True
    # st.session_state["sliders"][f"class_{i + 1}"][j] = selected_range


@st.cache_data
def fetch_image(uploaded_file, height=None):
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)
    if height:
        image = imutils.resize(image.copy(), height=height)

    return image


@st.cache_data
def cached_pil_image(image):
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def setup_page():
    st.title("Coverage Mapping")
    st.write("Find out the coverage of two separate classes in your photos using colour-based thresholding. Select from"
             "RGB (red, green, blue), HSV (hue, saturation, value) or L*a*b to segment each image.")
    st.write("Once you are happy "
             "with the results, click Save Results and Download CSV to save all the settings and coverage percentages"
             "to your downloads folder.")
    st.write("This Streamlit WebApp was developed by Guy Coleman. "
             "Source code is accessible [here](https://github.com/geezacoleman/GilgaiDetection).")

    st.sidebar.write("# Upload Images and Save Results")


def app():
    st.set_page_config(layout="wide", page_title="Coverage Mapper")
    uploaded_files = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"],
                                              accept_multiple_files=True)
    setup_page()
    col1, col2 = st.columns([2, 1])

    color_space = col2.selectbox("Choose color space", options=["RGB", "HSV", "LAB"])
    image_placeholder = col1.empty()
    placeholder = np.ones((500, 500), dtype=np.uint8) * 255
    image_placeholder.image(placeholder)

    if "sliders" not in st.session_state:
        st.session_state["sliders"] = {
            f"class_{i + 1}": [(0, 180), (0, 255), (0, 255) if color_space == 'HSV' else (0, 255)] for i in range(2)
        }

    if "clicked_pixels" not in st.session_state:
        st.session_state["clicked_pixels"] = {f"class_{i + 1}": [] for i in range(2)}

    if "manual_slider_update" not in st.session_state:
        st.session_state.manual_slider_update = False

    if "clicked_location" not in st.session_state:
        st.session_state.clicked_location = None

    thresholds = {}
    for i in range(2):
        lower = []
        upper = []
        expander = col2.expander(f"Class {i + 1} {color_space} Thresholds")
        for j, ch in enumerate(color_space):
            min_value = 0
            max_value = 180 if ch == 'H' and color_space == 'HSV' else 255
            range_values = list(range(min_value, max_value + 1))
            selected_range = expander.select_slider(
                f"{ch} | (Class {i + 1})", options=range_values, value=st.session_state["sliders"][f"class_{i + 1}"][j],
                on_change=on_slider_change)
            lower.append(selected_range[0])
            upper.append(selected_range[1])
            st.session_state["sliders"][f"class_{i + 1}"][j] = selected_range

        thresholds[f"class_{i + 1}"] = {"lower": np.array(lower), "upper": np.array(upper)}

    if st.sidebar.button("Save Results"):
        if uploaded_files:
            results = []
            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)
                image = fetch_image(uploaded_file, height=400)
                coverages = []
                for i in range(2):
                    converted_image = convert_colour_space(image.copy(), colour_space=color_space)

                    _, coverage = thresholding(converted_image, image.cop(), thresholds[f"class_{i + 1}"]["lower"],
                                               thresholds[f"class_{i + 1}"]["upper"], colour=None)
                    coverages.append(coverage)
                result = {
                    "image_name": uploaded_file.name,
                    "class_1_%": coverages[0],
                    "class_2_%": coverages[1],
                }
                for i in range(2):
                    for ch, lower_value, upper_value in zip(color_space, thresholds[f"class_{i + 1}"]["lower"],
                                                            thresholds[f"class_{i + 1}"]["upper"]):
                        result[f"lower_{ch}_class_{i + 1}"] = lower_value
                        result[f"upper_{ch}_class_{i + 1}"] = upper_value
                results.append(result)

            df = pd.DataFrame(results)
            csv_file = f"segmentation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_file, index=False)

            with open(csv_file, "rb") as f:
                csv_data = f.read()
            st.sidebar.download_button(label="Download CSV", data=csv_data, file_name=csv_file, mime="text/csv")
        else:
            st.warning("No images uploaded. Please upload images to save results.")

    if uploaded_files:
        col1_columns = col1.columns(2)

        current_image_idx = st.session_state.get("current_image_idx", 0)

        uploaded_file = uploaded_files[current_image_idx]
        uploaded_file.seek(0)
        image = fetch_image(uploaded_file, height=400)
        overlay_image = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2RGB)
        colors = [(250, 43, 50), (100, 0, 255)]  # Red and blue colors for the masks
        click_expander = col2.expander(f"Automatic Thresholding")
        selected_class = click_expander.radio("Select Class", options=["Class 1", "Class 2"])

        with click_expander:
            clicked_location = streamlit_image_coordinates(cached_pil_image(image.copy()), key='pil', height=400)

            if clicked_location != st.session_state.clicked_location:
                y = clicked_location["y"]
                x = clicked_location["x"]
                if color_space == "HSV":
                    pixel_value = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[y, x]
                elif color_space == "LAB":
                    pixel_value = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)[y, x]
                else:
                    pixel_value = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)[y, x]

                st.session_state["clicked_pixels"][f"class_{selected_class[-1]}"].append(pixel_value)

                if not st.session_state.manual_slider_update:
                    mean_min, mean_max = calculate_mean_min_max(st.session_state["clicked_pixels"][f"class_{selected_class[-1]}"])

                    for i, ch in enumerate(color_space):
                        st.session_state["sliders"][f"class_{selected_class[-1]}"][i] = (int(mean_min[i]), int(mean_max[i]))

                # Reset the flag after processing
                st.session_state.manual_slider_update = False
                st.session_state.clicked_location = clicked_location

        for i in range(2):
            converted_image = convert_colour_space(overlay_image, colour_space=color_space)
            masked_image, coverage = thresholding(converted_image, overlay_image.copy(), thresholds[f"class_{i + 1}"]["lower"],
                                            thresholds[f"class_{i + 1}"]["upper"], colors[i])
            show_overlay = col1_columns[i].checkbox(f"Class {i + 1} Overlay", value=False, key=f"overlay_class_{i + 1}")
            if show_overlay:
                overlay_image = masked_image

            col1_columns[i].write(f"Coverage Class {i + 1}: {coverage:.2f}%")
            col1_columns[i].progress(int(coverage))

        image_placeholder.image(overlay_image)

        if col1_columns[0].button("Back"):
            if current_image_idx > 0:
                current_image_idx -= 1
                st.session_state.current_image_idx = current_image_idx
        if col1_columns[1].button("Next"):
            if current_image_idx < len(uploaded_files) - 1:
                current_image_idx += 1
                st.session_state.current_image_idx = current_image_idx

        if col1.button("Reset Pixel Averages"):
            st.session_state["clicked_pixels"] = {f"class_{i + 1}": [] for i in range(2)}

if __name__ == "__main__":
    app()