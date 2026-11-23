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
