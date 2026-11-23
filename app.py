import base64
import hashlib
import io
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, UnidentifiedImageError

from calibration import AxisCalibration, default_calibration_points, pixel_to_data
from data_export import build_csv


image_click_component = components.declare_component(
    "graph_image_click",
    path=str(Path(__file__).parent / "image_click_component"),
)


st.set_page_config(page_title="Graph Interpreter")
st.title("Graph Interpreter")
st.write("Calibrate the axes, then click the graph to extract data points.")

image_file = st.file_uploader(
    "Choose a graph image",
    type=["jpg", "jpeg", "png", "webp", "bmp", "gif", "tif", "tiff"],
)

if image_file is not None:
    image_bytes = image_file.getvalue()
    image_id = hashlib.sha256(image_bytes).hexdigest()

    if st.session_state.get("image_id") != image_id:
        st.session_state.image_id = image_id
        st.session_state.calibration_points = {}
        st.session_state.data_points = []
        st.session_state.last_click_event_id = None
        st.session_state.image_click_generation = (
            st.session_state.get("image_click_generation", 0) + 1
        )

    try:
        with Image.open(io.BytesIO(image_bytes)) as source_image:
            image = source_image.convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        st.error(f"Could not read the selected image: {error}")
    else:
        max_width = 1000
        if image.width > max_width:
            resized_height = round(image.height * max_width / image.width)
            image = image.resize((max_width, resized_height))

        calibration_points = st.session_state.calibration_points
        for role, point in default_calibration_points(
            image.width, image.height
        ).items():
            calibration_points.setdefault(role, point)

        input_generation = st.session_state.image_click_generation
        st.subheader("Name the data set and axes")
        dataset_name_column, x_name_column, y_name_column = st.columns(3)
        with dataset_name_column:
            dataset_name = st.text_input(
                "Data set name",
                value=Path(image_file.name).stem,
                key=f"dataset-name-{input_generation}",
            )
        with x_name_column:
            x_axis_name = st.text_input(
                "X-axis name",
                value="X",
                key=f"x-axis-name-{input_generation}",
            )
        with y_name_column:
            y_axis_name = st.text_input(
                "Y-axis name",
                value="Y",
                key=f"y-axis-name-{input_generation}",
            )

        st.subheader("1. Calibrate axes")
        st.write(
            "The four markers start near the image corners. Drag them onto "
            "the known axis points, then enter their values. Neither starting "
            "value needs to be zero. Changing a value updates all extracted "
            "points. A marker's tip shows its exact location while dragging; "
            "x-axis tips face up and y-axis tips face right."
        )
        x_column, y_column = st.columns(2)
        with x_column:
            st.markdown("**X-axis references**")
            x_scale = st.selectbox(
                "X-axis scale",
                options=["linear", "logarithmic"],
                format_func=lambda scale: scale.capitalize(),
                key=f"x-scale-{input_generation}",
            )
            x_start_value = st.number_input(
                "X value at the first point",
                value=None,
                placeholder="For example, 2",
                key=f"x-start-{input_generation}",
            )
            x_end_value = st.number_input(
                "X value at the second point",
                value=None,
                placeholder="For example, 10",
                key=f"x-end-{input_generation}",
            )
        with y_column:
            st.markdown("**Y-axis references**")
            y_scale = st.selectbox(
                "Y-axis scale",
                options=["linear", "logarithmic"],
                format_func=lambda scale: scale.capitalize(),
                key=f"y-scale-{input_generation}",
            )
            y_start_value = st.number_input(
                "Y value at the first point",
                value=None,
                placeholder="For example, 3",
                key=f"y-start-{input_generation}",
            )
            y_end_value = st.number_input(
                "Y value at the second point",
                value=None,
                placeholder="For example, 12",
                key=f"y-end-{input_generation}",
            )

        roles = (
            ("x_start", "First known point on the x-axis"),
            ("x_end", "Second known point on the x-axis"),
            ("y_start", "First known point on the y-axis"),
            ("y_end", "Second known point on the y-axis"),
        )
        next_role = next(
            (role for role, _ in roles if role not in calibration_points),
            None,
        )
        reference_to_reposition = None
        if next_role is not None:
            label = dict(roles)[next_role]
            st.info(f"Click the image to mark: **{label}**.")
        else:
            role_labels = dict(roles)
            reference_to_reposition = st.selectbox(
                "Reference point to reposition",
                options=[None] + [role for role, _ in roles],
                format_func=lambda role: (
                    "Do not reposition a reference"
                    if role is None
                    else role_labels[role]
                ),
                key=f"reference-to-reposition-{input_generation}",
            )

        values = (x_start_value, x_end_value, y_start_value, y_end_value)
        has_all_references = all(role in calibration_points for role, _ in roles)
        calibration = None
        calibration_error = None
        if has_all_references and all(value is not None for value in values):
            try:
                calibration = {
                    "x_axis": AxisCalibration(
                        pixel_start=calibration_points["x_start"],
                        value_start=x_start_value,
                        pixel_end=calibration_points["x_end"],
                        value_end=x_end_value,
                        scale=x_scale,
                    ),
                    "y_axis": AxisCalibration(
                        pixel_start=calibration_points["y_start"],
                        value_start=y_start_value,
                        pixel_end=calibration_points["y_end"],
                        value_end=y_end_value,
                        scale=y_scale,
                    ),
                }
                pixel_to_data(
                    calibration["x_axis"],
                    calibration["y_axis"],
                    calibration_points["x_start"],
                )
            except ValueError as error:
                calibration = None
                calibration_error = error

        if calibration_error is not None:
            st.error(f"Cannot calibrate this graph: {calibration_error}")
        if reference_to_reposition is not None:
            st.info(
                f"Click the image to reposition "
                f"**{role_labels[reference_to_reposition]}**. "
                "Choose **Do not reposition a reference** to add data points."
            )
        elif calibration is not None:
            st.success(
                "Axes calibrated. Click the image to add points. "
                f"X: {x_start_value:g} to {x_end_value:g} ({x_scale}); "
                f"Y: {y_start_value:g} to {y_end_value:g} ({y_scale})."
            )
        elif has_all_references:
            st.info("Enter all four known values to finish calibration.")

        image_buffer = io.BytesIO()
        image.save(image_buffer, format="PNG")
        image_source = "data:image/png;base64," + base64.b64encode(
            image_buffer.getvalue()
        ).decode("ascii")
        click = image_click_component(
            src=image_source,
            calibration_points=calibration_points,
            dataset_name=dataset_name,
            x_axis_name=x_axis_name,
            y_axis_name=y_axis_name,
            key=f"graph-image-{st.session_state.image_click_generation}",
            default=None,
            height=650,
        )
        if (
            click is not None
            and "x" in click
            and "y" in click
            and click.get("id") != st.session_state.last_click_event_id
        ):
            st.session_state.last_click_event_id = click.get("id")
            current_click = (int(click["x"]), int(click["y"]))
            if click.get("type") == "reference":
                role = click.get("role")
                if role in calibration_points:
                    calibration_points[role] = current_click
                    st.rerun()
            elif next_role is not None:
                calibration_points[next_role] = current_click
                st.rerun()
            elif reference_to_reposition is not None:
                calibration_points[reference_to_reposition] = current_click
                st.rerun()
            elif calibration is not None:
                st.session_state.data_points.append(
                    {
                        "Pixel X": current_click[0],
                        "Pixel Y": current_click[1],
                    }
                )
                st.rerun()

        if calibration_points:
            st.caption(
                "Drag a labeled marker to reposition it. Calibration marks: "
                + ", ".join(
                    f"{label} at ({calibration_points[role][0]}, "
                    f"{calibration_points[role][1]})"
                    for role, label in roles
                    if role in calibration_points
                )
            )

        if calibration is not None:
            st.subheader("2. Extract data points")

        data_points = st.session_state.data_points
        if data_points:
            reserved_column_names = {"Point", "Pixel X", "Pixel Y"}
            axis_names_valid = (
                bool(x_axis_name.strip())
                and bool(y_axis_name.strip())
                and x_axis_name.strip() != y_axis_name.strip()
                and x_axis_name.strip() not in reserved_column_names
                and y_axis_name.strip() not in reserved_column_names
            )
            if not axis_names_valid:
                st.error(
                    "Choose distinct, non-empty axis names that are not "
                    "Point, Pixel X, or Pixel Y."
                )
            dataset_name_valid = bool(dataset_name.strip())
            if not dataset_name_valid:
                st.error("Enter a data set name before downloading the CSV.")

            displayed_points = []
            for index, point in enumerate(data_points, start=1):
                row = {"Point": index}
                if calibration is not None:
                    (
                        row[x_axis_name.strip()],
                        row[y_axis_name.strip()],
                    ) = pixel_to_data(
                        calibration["x_axis"],
                        calibration["y_axis"],
                        (point["Pixel X"], point["Pixel Y"]),
                    )
                else:
                    row[x_axis_name.strip()] = None
                    row[y_axis_name.strip()] = None
                row["Pixel X"] = point["Pixel X"]
                row["Pixel Y"] = point["Pixel Y"]
                displayed_points.append(row)

            if axis_names_valid:
                st.dataframe(displayed_points, hide_index=True, width="stretch")
            point_to_remove = st.selectbox(
                "Point to remove",
                options=range(1, len(data_points) + 1),
                format_func=lambda point: f"Point {point}",
                key=f"remove-point-{input_generation}-{len(data_points)}",
            )
            if st.button("Remove selected point"):
                del data_points[point_to_remove - 1]
                st.rerun()

            if calibration is not None:
                st.download_button(
                    "Download points as CSV",
                    data=build_csv(
                        dataset_name.strip(),
                        list(displayed_points[0].keys()),
                        displayed_points,
                    ),
                    file_name="digitized-points.csv",
                    mime="text/csv",
                    disabled=not axis_names_valid or not dataset_name_valid,
                )
        elif calibration is not None:
            st.caption("No data points selected yet.")

else:
    st.info("Upload a graph image to get started.")
