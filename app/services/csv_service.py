import csv
from io import StringIO

from fastapi.responses import StreamingResponse


def create_csv_response(
    filename: str,
    fieldnames: list[str],
    rows: list[dict],
) -> StreamingResponse:
    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(rows)

    stream.seek(0)

    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
    )

    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
