import csv
import io
from collections.abc import Mapping, Sequence


def build_csv(
    dataset_name: str,
    columns: Sequence[str],
    rows: Sequence[Mapping[str, object]],
) -> str:
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow([dataset_name])
    writer.writerow(columns)
    writer.writerows([[row[column] for column in columns] for row in rows])
    return csv_buffer.getvalue()


def build_series_csv(
    dataset_name: str,
    x_axis_name: str,
    y_axis_name: str,
    series: Sequence[Mapping[str, object]],
) -> str:
    columns = [
        column_name
        for item in series
        for column_name in (
            f"{item['name']} {x_axis_name}",
            f"{item['name']} {y_axis_name}",
        )
    ]
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow([dataset_name])
    writer.writerow(columns)
    row_count = max((len(item["points"]) for item in series), default=0)
    for row_index in range(row_count):
        row = []
        for item in series:
            points = item["points"]
            if row_index < len(points):
                row.extend((points[row_index]["x"], points[row_index]["y"]))
            else:
                row.extend(("", ""))
        writer.writerow(row)
    return csv_buffer.getvalue()


def build_single_series_csv(
    series_name: str,
    x_axis_name: str,
    y_axis_name: str,
    points: Sequence[Mapping[str, object]],
) -> str:
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow([series_name])
    writer.writerow([x_axis_name, y_axis_name])
    writer.writerows([[point["x"], point["y"]] for point in points])
    return csv_buffer.getvalue()
