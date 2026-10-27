"""Local MotionBoard files and revision-checked private project storage."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = Path(__file__).resolve().parent
PRIVATE = ROOT / "SourceAssets" / "MotionBoard"
PRIVATE = Path(os.environ.get("MOTION_BOARD_ASSETS", str(PRIVATE))).resolve()
STATE = Path(os.environ.get("MOTION_BOARD_STATE", str(PRIVATE / "state"))).resolve()
MAX_BYTES = 2 * 1024 * 1024
MAX_REVISION = 2**53 - 1
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,95}\Z")
STATIC = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js",
          "/style.css": "style.css", "/model.js": "model.js"}
VENDOR = {"build/three.module.js", "build/three.core.js",
          "examples/jsm/loaders/GLTFLoader.js", "examples/jsm/controls/OrbitControls.js",
          "examples/jsm/loaders/FBXLoader.js", "examples/jsm/libs/fflate.module.js",
          "examples/jsm/curves/NURBSCurve.js", "examples/jsm/curves/NURBSUtils.js",
          "examples/jsm/utils/BufferGeometryUtils.js", "examples/jsm/utils/SkeletonUtils.js"}


class Invalid(ValueError):
    pass


class Conflict(Exception):
    def __init__(self, revision):
        self.revision = revision


def integer(value, minimum=0, maximum=MAX_REVISION):
    return type(value) is int and minimum <= value <= maximum


def string(value, maximum, empty=True):
    return isinstance(value, str) and (empty or bool(value)) and len(value) <= maximum


def number(value, maximum=36000, positive=False):
    return (type(value) in (int, float)
            and (value > 0 if positive else value >= 0) and value <= maximum
            and math.isfinite(value))


def decode_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Invalid("Duplicate JSON keys are not allowed.")
            result[key] = value
        return result

    def invalid_constant(value):
        raise Invalid("Non-finite JSON numbers are not allowed.")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Invalid("Invalid JSON document.") from exc


def validate_project(project, expected_revision=None):
    if not isinstance(project, dict) or set(project) - {"version", "title", "items", "revision", "libraries"}:
        raise Invalid("Unsupported project fields.")
    if type(project.get("version")) is not int or project["version"] != 1:
        raise Invalid("Project version must be 1.")
    if not string(project.get("title"), 240):
        raise Invalid("Project title must be text, at most 240 characters.")
    if "revision" in project and (not integer(project["revision"]) or
            (expected_revision is not None and project["revision"] != expected_revision)):
        raise Invalid("Project revision must match its request revision.")
    libraries = project.get("libraries", [])
    if not isinstance(libraries, list) or len(libraries) > 128:
        raise Invalid("At most 128 library records are allowed.")
    library_ids = set()
    for library in libraries:
        if not isinstance(library, dict) or set(library) - {"id", "name", "fileName", "sourceHash"}:
            raise Invalid("Unsupported library metadata.")
        if not string(library.get("id"), 96, False) or not ID.fullmatch(library["id"]) or library["id"] in library_ids:
            raise Invalid("Library IDs must be distinct safe identifiers.")
        library_ids.add(library["id"])
        for field, limit in (("name", 240), ("fileName", 512), ("sourceHash", 128)):
            if field in library and not string(library[field], limit):
                raise Invalid("Invalid library metadata text.")
    items = project.get("items")
    if not isinstance(items, list) or len(items) > 8:
        raise Invalid("Project must contain an items list with at most eight occupied slots.")
    ids = set()
    slots = set()
    required = {"id", "clip", "start", "end", "duration", "reverse", "note"}
    for item in items:
        if not isinstance(item, dict) or not required <= set(item) or set(item) - (required | {"library", "slot", "playbackMode", "playbackSpeed", "repeatCount"}):
            raise Invalid("Each item needs id, clip, start, end, duration, reverse and note.")
        if "slot" in item:
            if not integer(item["slot"], maximum=7) or item["slot"] in slots:
                raise Invalid("Explicit slots must be distinct integers from zero through seven.")
            slots.add(item["slot"])
        if not string(item["id"], 128, False) or item["id"] in ids:
            raise Invalid("Item IDs must be distinct nonempty strings.")
        ids.add(item["id"])
        if item["clip"] is not None and not string(item["clip"], 512, False):
            raise Invalid("Clip must be its source name or null for a transition note.")
        if "library" in item and (not string(item["library"], 96, False) or not ID.fullmatch(item["library"])):
            raise Invalid("Invalid item library identifier.")
        if not all(number(item[key]) for key in ("start", "end")) or item["end"] < item["start"]:
            raise Invalid("Source trim times must be finite, nonnegative and ordered.")
        if item["clip"] is not None and item["end"] <= item["start"]:
            raise Invalid("An animation trim must have positive length.")
        if not number(item["duration"], maximum=3600, positive=True):
            raise Invalid("Item duration must be greater than zero and at most 3600 seconds.")
        mode = item.get("playbackMode", "stretch")
        if mode not in ("stretch", "repeat-duration", "repeat-count"):
            raise Invalid("Unsupported playback mode.")
        speed = item.get("playbackSpeed", 1)
        if not number(speed, maximum=8, positive=True) or speed < 0.05:
            raise Invalid("Playback speed must be between 0.05 and 8.")
        count = item.get("repeatCount")
        if "repeatCount" in item and not number(count, maximum=10000, positive=True):
            raise Invalid("Repeat count must be greater than zero and at most 10000.")
        if mode != "stretch":
            if item["clip"] is None:
                raise Invalid("A transition note cannot repeat an animation.")
            cycle_duration = (item["end"] - item["start"]) / speed
            if cycle_duration <= 0:
                raise Invalid("Repeat trim is too short for this playback speed.")
            if mode == "repeat-count":
                if count is None or not math.isclose(item["duration"], cycle_duration * count, rel_tol=1e-7, abs_tol=1e-7):
                    raise Invalid("Repeat count and total duration disagree.")
            if item["duration"] / cycle_duration > 10000 + 1e-9:
                raise Invalid("Use at most 10000 repeats per slot.")
        if type(item["reverse"]) is not bool or not string(item["note"], 4000):
            raise Invalid("Reverse must be boolean and note text at most 4000 characters.")
    return project


class BoardStore:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()

    def _read(self):
        if not self.path.exists():
            return {"revision": 0, "project": None}
        if self.path.stat().st_size > MAX_BYTES:
            raise Invalid("Saved board exceeds the size limit; the file was left unchanged.")
        data = decode_json(self.path.read_bytes())
        if not isinstance(data, dict) or set(data) != {"revision", "project"} or not integer(data["revision"]):
            raise Invalid("Saved board format is invalid; the file was left unchanged.")
        validate_project(data["project"], data["revision"])
        return data

    def read(self):
        with self.lock:
            return self._read()

    def save(self, request):
        if not isinstance(request, dict) or set(request) != {"revision", "project"} or not integer(request["revision"], maximum=MAX_REVISION - 1):
            raise Invalid("Save requires a nonnegative revision and project.")
        project = validate_project(request["project"], request["revision"])
        with self.lock:
            current = self._read()
            if request["revision"] != current["revision"]:
                raise Conflict(current["revision"])
            revision = current["revision"] + 1
            project = dict(project)
            if "revision" in project:
                project["revision"] = revision
            data = json.dumps({"revision": revision, "project": project}, ensure_ascii=False, allow_nan=False).encode("utf-8")
            if len(data) > MAX_BYTES:
                raise Invalid("Saved board exceeds the 2 MiB limit.")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix=".board-", suffix=".tmp", delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            return {"revision": revision, "saved": True}


def request_allowed(headers, port, require_origin=False):
    hosts = headers.get_all("Host", [])
    if len(hosts) != 1 or hosts[0] not in (f"127.0.0.1:{port}", f"localhost:{port}"):
        return False
    origins = headers.get_all("Origin", [])
    if len(origins) > 1 or (require_origin and not origins):
        return False
    if origins and origins[0] != "http://" + hosts[0]:
        return False
    return headers.get("Sec-Fetch-Site", "none") in ("none", "same-origin")


def contained_file(base, relative):
    base = Path(base).resolve()
    path = (base / relative).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        return None
    return path


def read_info(private):
    manifest = contained_file(private, "manifest.json")
    if manifest:
        if manifest.stat().st_size > MAX_BYTES:
            raise Invalid("Library manifest is too large.")
        info = decode_json(manifest.read_bytes())
        if not isinstance(info, dict) or not isinstance(info.get("libraries", []), list):
            raise Invalid("Library manifest is invalid.")
        # The manifest is local configuration; it never supplies a filesystem path.
        result = {"version": 1, "libraries": [], "sourceHash": info.get("sourceHash", "")}
        for entry in info.get("libraries", []):
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not ID.fullmatch(entry["id"]):
                raise Invalid("Library manifest identifier is invalid.")
            expected = "/model.glb" if entry["id"] == "meshy" else f"/libraries/{entry['id']}.glb"
            if entry.get("url", expected) != expected:
                raise Invalid("Library manifest URLs must use the private allowlisted routes.")
            library = {key: entry[key] for key in ("id", "name", "fileName", "sourceHash") if key in entry} | {"url": expected}
            if "clips" in entry:
                clips = entry["clips"]
                if not isinstance(clips, list) or len(clips) > 4096:
                    raise Invalid("Library clip metadata must contain at most 4096 records.")
                library["clips"] = []
                for clip in clips:
                    if (not isinstance(clip, dict) or
                            not string(clip.get("name"), 512, False) or
                            not number(clip.get("duration"), positive=True)):
                        raise Invalid("Library clips need a name and a finite positive duration.")
                    library["clips"].append({"name": clip["name"], "duration": clip["duration"]})
            result["libraries"].append(library)
        return result
    model = contained_file(private, "Meshy_Reference.glb")
    if not model:
        return {"version": 1, "libraries": [], "sourceHash": ""}
    with model.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"version": 1, "sourceHash": digest, "libraries": [
        {"id": "meshy", "name": "Meshy reference", "url": "/model.glb", "fileName": model.name, "sourceHash": digest}]}


def asset_path(path, frontend, private):
    decoded = unquote(path)
    if decoded != path or "\\" in path or any(part in (".", "..") for part in path.split("/")):
        return None
    if path in STATIC:
        return contained_file(frontend, STATIC[path])
    if path == "/model.glb":
        return contained_file(private, "Meshy_Reference.glb")
    if path.startswith("/vendor/") and path[len("/vendor/"):] in VENDOR:
        return contained_file(Path(private) / "vendor", path[len("/vendor/"):])
    match = re.fullmatch(r"/libraries/([a-zA-Z0-9][a-zA-Z0-9_-]{0,95})\.glb", path)
    if match and match[1] in {entry["id"] for entry in read_info(private)["libraries"]}:
        return contained_file(Path(private) / "libraries", match[1] + ".glb")
    return None


def handler_class(store, frontend=FRONTEND, private=PRIVATE, container=False):
    class Handler(BaseHTTPRequestHandler):
        server_version = "MotionBoard/1"
        protocol_version = "HTTP/1.0"

        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self, format, *args):
            # Avoid logging query strings or arbitrary request headers.
            return

        def _guard(self, write=False):
            # Docker bridge forwarding uses a non-loopback peer inside the container.
            # The supplied Compose file publishes only host 127.0.0.1; Host/Origin
            # checks remain mandatory in both modes. Never publish a LAN port.
            if ((not container and not ipaddress.ip_address(self.client_address[0]).is_loopback)
                    or not request_allowed(self.headers, self.server.server_port, write)):
                self._json(403, {"error": "Only same-origin loopback requests are allowed."})
                return False
            return True

        def _headers(self, status, length, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()

        def _json(self, status, data):
            raw = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self._headers(status, len(raw), "application/json; charset=utf-8")
            if self.command != "HEAD":
                self.wfile.write(raw)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            if not self._guard():
                return
            try:
                path = urlsplit(self.path).path
                if path == "/api/project":
                    self._json(200, store.read())
                elif path == "/api/info":
                    self._json(200, read_info(private))
                else:
                    asset = asset_path(path, frontend, private)
                    if asset is None:
                        self._json(404, {"error": "Not found."})
                        return
                    kind = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                            ".css": "text/css; charset=utf-8", ".glb": "model/gltf-binary"}[asset.suffix]
                    with asset.open("rb") as stream:
                        self._headers(200, os.fstat(stream.fileno()).st_size, kind)
                        if self.command != "HEAD":
                            shutil.copyfileobj(stream, self.wfile, length=64 * 1024)
            except Invalid as exc:
                self._json(422, {"error": str(exc)})
            except OSError:
                self._json(500, {"error": "Could not read local MotionBoard data."})

        def do_PUT(self):
            if not self._guard(write=True):
                return
            if self.path != "/api/project":
                self._json(404, {"error": "Not found."})
                return
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                self._json(415, {"error": "Use application/json."})
                return
            lengths = self.headers.get_all("Content-Length", [])
            if self.headers.get("Transfer-Encoding") or len(lengths) != 1 or not lengths[0].isdigit():
                self._json(400, {"error": "A single Content-Length is required."})
                return
            length = int(lengths[0])
            if not 0 < length <= MAX_BYTES:
                self._json(413, {"error": "Save limit is 2 MiB."})
                return
            try:
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise Invalid("Incomplete request body.")
                self._json(200, store.save(decode_json(raw)))
            except Conflict as exc:
                self._json(409, {"error": "Another tab saved first. Reload before saving.", "revision": exc.revision})
            except Invalid as exc:
                self._json(422, {"error": str(exc)})
            except OSError:
                self._json(500, {"error": "Save failed; the previous board was preserved."})

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8769)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    container = os.environ.get("MOTION_BOARD_CONTAINER") == "1"
    address = "0.0.0.0" if container else "127.0.0.1"
    server = ThreadingHTTPServer((address, args.port), handler_class(BoardStore(STATE / "board.json"), container=container))
    server.daemon_threads = True
    print(f"MotionBoard: http://127.0.0.1:{args.port} (use the loopback-only Compose port in container mode)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
