import mimetypes
import re
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.utils._os import safe_join


_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)$")
_CHUNK_SIZE = 64 * 1024


def _file_chunks(file_path, start, length):
    remaining = length
    with open(file_path, "rb") as media_file:
        media_file.seek(start)
        while remaining > 0:
            chunk = media_file.read(min(_CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


def ranged_media(request, path):
    """Serve local media with single-range support required by native players."""
    try:
        file_path = Path(safe_join(settings.MEDIA_ROOT, path)).resolve()
        media_root = Path(settings.MEDIA_ROOT).resolve()
    except (ValueError, TypeError):
        raise Http404

    if not file_path.is_relative_to(media_root) or not file_path.is_file():
        raise Http404

    file_size = file_path.stat().st_size
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    range_header = request.headers.get("Range", "").strip()
    match = _RANGE_RE.fullmatch(range_header)

    start = 0
    end = max(file_size - 1, 0)
    status = 200

    if range_header:
        if not match or file_size == 0:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{file_size}"
            return response

        start_text, end_text = match.groups()
        if not start_text:
            suffix_length = int(end_text or 0)
            if suffix_length <= 0:
                response = HttpResponse(status=416)
                response["Content-Range"] = f"bytes */{file_size}"
                return response
            start = max(file_size - suffix_length, 0)
        else:
            start = int(start_text)
            if end_text:
                end = min(int(end_text), file_size - 1)

        if start >= file_size or start > end:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{file_size}"
            return response
        status = 206

    content_length = end - start + 1 if file_size else 0
    if request.method == "HEAD":
        response = HttpResponse(status=status, content_type=content_type)
    else:
        response = StreamingHttpResponse(
            _file_chunks(file_path, start, content_length),
            status=status,
            content_type=content_type,
        )

    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(content_length)
    response["Content-Disposition"] = f'inline; filename="{file_path.name}"'
    if status == 206:
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    return response
