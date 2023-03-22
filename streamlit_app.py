from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import imutils
import cv2


def thresholding(image, lower, upper, color_space):
    if color_space == "HSV":
        converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    elif color_space == "LAB":
        converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    else:
        converted_image = image

    mask = cv2.inRange(converted_image, lower, upper)
    result = cv2.bitwise_and(image, image, mask=mask)
    coverage = np.count_nonzero(mask) / (mask.shape[0] * mask.shape[1]) * 100

    return result, coverage


def apply_mask(image, lower, upper, color, color_space, alpha=0.5):
    if color_space == "HSV":
        converted_image = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2HSV)
    elif color_space == "LAB":
        converted_image = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2Lab)
    else:
        converted_image = image.copy()

    mask = cv2.inRange(converted_image, lower, upper)
    colored_mask = np.zeros_like(image)
    colored_mask[mask > 0] = color

    # Create a mask of the inverse of the original mask
    inverse_mask = cv2.bitwise_not(mask)

    # Merge the colored mask with the original image only in the masked areas
    masked_image = cv2.bitwise_and(image, image, mask=inverse_mask)
    masked_image = cv2.add(masked_image, colored_mask)

    return cv2.addWeighted(masked_image, 1 - alpha, image, alpha, 0), mask

def app():
    st.set_page_config(layout="wide", page_title="Coverage Mapper")
    st.title("Coverage Mapping")
    st.write("Find out the coverage of two separate classes in your photos using colour-based thresholding. Select from"
             "RGB (red, green, blue), HSV (hue, saturation, value) or L*a*b to segment each image.")
    st.write("Once you are happy "
             "with the results, click Save Results and Download CSV to save all the settings and coverage percentages"
             "to your downloads folder.")
    st.write("This WebApp is entirely open-source and was developed by Guy Coleman. "
             "All the source code is accessible [here](https://github.com/geezacoleman/GilgaiDetection).")

    st.sidebar.write("# Upload Images and Save Results")

    col1, col2 = st.columns([2, 1])
    image_placeholder = col1.empty()
    placeholder = np.ones((600, 600), dtype=np.uint8) * 255
    image_placeholder.image(placeholder)

    uploaded_files = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    color_space = col2.selectbox("Choose color space", options=["RGB", "HSV", "LAB"])

    thresholds = {}
    for i in range(2):
        # col2.write(f"### Class {i + 1} {color_space} Thresholds")
        lower = []
        upper = []
        expander = col2.expander(f"Class {i + 1} {color_space} Thresholds")
        for ch in color_space:
            min_value = 0
            max_value = 180 if ch == 'H' and color_space == 'HSV' else 255
            range_values = list(range(min_value, max_value + 1))
            selected_range = expander.select_slider(
                f"{ch} | (Class {i + 1})", options=range_values, value=(min_value, max_value)
            )
            lower.append(selected_range[0])
            upper.append(selected_range[1])
        thresholds[f"class_{i + 1}"] = {"lower": np.array(lower), "upper": np.array(upper)}

    if st.sidebar.button("Save Results"):
        if uploaded_files:
            results = []
            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)
                file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                image = cv2.imdecode(file_bytes, 1)
                coverages = []
                for i in range(2):
                    _, coverage = thresholding(image, thresholds[f"class_{i + 1}"]["lower"],
                                               thresholds[f"class_{i + 1}"]["upper"], color_space)
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
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        image = imutils.resize(image.copy(), height=600)

        overlay_image = image.copy()
        colors = [(200, 43, 104), (0, 0, 255)]  # Red and blue colors for the masks
        for i in range(2):
            masked_image, mask = apply_mask(overlay_image, thresholds[f"class_{i + 1}"]["lower"],
                                            thresholds[f"class_{i + 1}"]["upper"], colors[i], color_space, alpha=0.1)
            show_overlay = col1_columns[i].checkbox(f"Class {i + 1} Overlay", value=False, key=f"overlay_class_{i + 1}")
            if show_overlay:
                overlay_image = masked_image

            coverage = np.count_nonzero(mask) / (mask.shape[0] * mask.shape[1]) * 100

            col1_columns[i].write(f"Coverage Class {i + 1}: {coverage:.2f}%")
            col1_columns[i].progress(int(coverage))

        display_image = cv2.cvtColor(overlay_image.copy(), cv2.COLOR_BGR2RGB)
        image_placeholder.image(display_image)

        if col1_columns[0].button("Back"):
            if current_image_idx > 0:
                current_image_idx -= 1
                st.session_state.current_image_idx = current_image_idx
        if col1_columns[1].button("Next"):
            if current_image_idx < len(uploaded_files) - 1:
                current_image_idx += 1
                st.session_state.current_image_idx = current_image_idx


if __name__ == "__main__":
    app()