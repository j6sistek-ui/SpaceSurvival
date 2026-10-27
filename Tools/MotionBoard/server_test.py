"""MotionBoard backend regression tests; all assets/state are temporary fixtures."""
from __future__ import annotations

import copy
from email.message import Message
import http.client
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import server


def project(items=None):
    return {"version": 1, "title": "Temporary test board", "items": items or []}


def item(index=0, **changes):
    value = {"id": f"item-{index}", "slot": index, "library": "test",
             "clip": "Source_Clip", "start": 0, "end": 2,
             "duration": 3, "reverse": False, "note": ""}
    return value | changes


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="motionboard-test-")
        self.root = Path(self.temporary.name)
        self.frontend = self.root / "frontend"
        self.assets = self.root / "assets"
        self.state = self.root / "state" / "board.json"
        self.frontend.mkdir()
        self.assets.mkdir()
        (self.frontend / "index.html").write_text("<p>test fixture</p>")
        (self.assets / "Meshy_Reference.glb").write_bytes(b"fixture model")
        self.store = server.BoardStore(self.state)
        handler = server.handler_class(self.store, self.frontend, self.assets)
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.http.daemon_threads = True
        self.thread = threading.Thread(
            target=lambda: self.http.serve_forever(poll_interval=0.01), daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(self, method="GET", path="/api/project", body=None,
                headers=(), origin=True):
        raw = body if isinstance(body, bytes) else (
            json.dumps(body).encode() if body is not None else None)
        fields = list(headers)
        names = {key.lower() for key, _ in fields}
        host = f"127.0.0.1:{self.http.server_port}"
        if "host" not in names:
            fields.append(("Host", host))
        if method == "PUT":
            if origin and "origin" not in names:
                fields.append(("Origin", "http://" + host))
            if "content-type" not in names:
                fields.append(("Content-Type", "application/json"))
        if raw is not None and "content-length" not in names:
            fields.append(("Content-Length", str(len(raw))))
        connection = http.client.HTTPConnection("127.0.0.1", self.http.server_port,
                                                timeout=3)
        try:
            connection.putrequest(method, path, skip_host=True)
            for key, value in fields:
                connection.putheader(key, value)
            connection.endheaders(raw)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def save(self, revision=0, value=None):
        return self.request("PUT", body={"revision": revision,
                                         "project": value or project()})

    def manifest(self, libraries):
        (self.assets / "manifest.json").write_text(json.dumps(
            {"version": 1, "sourceHash": "source-hash", "libraries": libraries}))

    def test_01_empty_store_and_first_save(self):
        status, _, raw = self.request()
        self.assertEqual((status, json.loads(raw)), (200, {"revision": 0, "project": None}))
        self.assertFalse(self.state.exists())
        self.assertEqual(self.save()[0], 200)
        self.assertEqual(self.store.read(), {"revision": 1, "project": project()})

    def test_02_embedded_revision_and_caller_are_preserved(self):
        value = project([item()]) | {"revision": 0}
        original = copy.deepcopy(value)
        self.assertEqual(self.save(value=value)[0], 200)
        self.assertEqual(value, original)
        saved = self.store.read()
        self.assertEqual((saved["revision"], saved["project"]["revision"]), (1, 1))
        self.assertEqual(self.save(1, saved["project"])[0], 200)
        self.assertEqual(self.store.read()["project"]["revision"], 2)

    def test_03_stale_tab_gets_409_without_overwrite(self):
        self.assertEqual(self.save()[0], 200)
        before = self.state.read_bytes()
        status, _, raw = self.save(0, project([item()]))
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(raw)["revision"], 1)
        self.assertEqual(self.state.read_bytes(), before)

    def test_04_reject_ambiguous_or_nonfinite_json(self):
        for raw in (b'{"revision":0,"revision":1,"project":{}}', b'{"x":NaN}',
                    b'{"x":Infinity}', b'{"x":-Infinity}', b'\xff', b'{'):
            with self.subTest(raw=raw):
                self.assertEqual(self.request("PUT", body=raw)[0], 422)
                self.assertFalse(self.state.exists())

    def test_05_corrupt_save_is_never_replaced(self):
        self.state.parent.mkdir()
        corruptions = [b'{broken', b'{"revision":true,"project":{}}',
                       json.dumps({"revision": 1, "project": project() | {"revision": 0}}).encode()]
        for raw in corruptions:
            with self.subTest(raw=raw):
                self.state.write_bytes(raw)
                self.assertEqual(self.request()[0], 422)
                self.assertEqual(self.save()[0], 422)
                self.assertEqual(self.state.read_bytes(), raw)

    def test_06_atomic_save_uses_sibling_fsynced_replacement(self):
        self.store.save({"revision": 0, "project": project()})
        before = self.state.read_bytes()
        real_replace = os.replace
        observations = []

        def inspect_replace(source, destination):
            self.assertEqual(Path(source).parent, self.state.parent)
            self.assertEqual(Path(destination), self.state)
            self.assertEqual(self.state.read_bytes(), before)
            self.assertEqual(json.loads(Path(source).read_bytes())["revision"], 2)
            observations.append(True)
            return real_replace(source, destination)

        with patch.object(server.os, "replace", side_effect=inspect_replace), \
                patch.object(server.os, "fsync", wraps=os.fsync) as fsync:
            self.store.save({"revision": 1, "project": project([item()])})
        self.assertEqual(observations, [True])
        fsync.assert_called_once()
        self.assertEqual(self.store.read()["revision"], 2)
        self.assertEqual(list(self.state.parent.glob(".board-*.tmp")), [])

    def test_07_failed_atomic_replace_preserves_save_and_cleans_temp(self):
        self.save()
        before = self.state.read_bytes()
        with patch.object(server.os, "replace", side_effect=OSError("test failure")):
            self.assertEqual(self.save(1, project([item()]))[0], 500)
        self.assertEqual(self.state.read_bytes(), before)
        self.assertEqual(list(self.state.parent.glob(".board-*.tmp")), [])

    def test_08_exact_eight_slot_schema(self):
        self.assertEqual(server.validate_project(project([item(i) for i in range(8)]))["items"][-1]["slot"], 7)
        server.validate_project(project([item(0), item(7)]))
        unnumbered = item()
        del unnumbered["slot"]
        server.validate_project(project([unnumbered]))
        invalid = [[item(slot=value)] for value in (-1, 8, True, False, 1.0, "1", None)]
        invalid += [[item(0), item(1, slot=0)], [item(i) for i in range(9)], [None]]
        for items in invalid:
            with self.subTest(items=items), self.assertRaises(server.Invalid):
                server.validate_project(project(items))

    def test_09_trim_types_ranges_and_transition_notes(self):
        server.validate_project(project([item(clip=None, start=0, end=0)]))
        for changes in ({"start": -1}, {"end": 0}, {"end": -1}, {"start": True},
                        {"duration": 0}, {"duration": 3601}, {"duration": float("nan")},
                        {"end": float("inf")}, {"reverse": 1}, {"clip": ""},
                        {"note": "x" * 4001}):
            with self.subTest(changes=changes), self.assertRaises(server.Invalid):
                server.validate_project(project([item(**changes)]))
        with self.assertRaises(server.Invalid):
            server.validate_project(project() | {"version": True})

    def test_10_library_metadata_and_identity_bounds(self):
        libraries = [{"id": f"lib-{i}"} for i in range(128)]
        server.validate_project(project() | {"libraries": libraries})
        for records in (libraries + [{"id": "extra"}], [{"id": "../private"}],
                        [{"id": "same"}, {"id": "same"}], [{"id": "test", "path": "/secret"}]):
            with self.subTest(records=records[-2:]), self.assertRaises(server.Invalid):
                server.validate_project(project() | {"libraries": records})
        with self.assertRaises(server.Invalid):
            server.validate_project(project([item(), item(1, id="item-0")]))

    def test_19_repeat_modes_roundtrip_preserve_legacy_and_exact_trims(self):
        legacy = item(0, start=4.87, end=10.9333, duration=8)
        counted = item(1, end=0.5, duration=5, playbackMode="repeat-count",
                       repeatCount=10, playbackSpeed=1)
        timed = item(2, start=2, end=2.5, duration=1.125,
                     playbackMode="repeat-duration", playbackSpeed=1, reverse=True)
        value = project([legacy, counted, timed])
        original = copy.deepcopy(value)
        self.assertEqual(self.save(value=value)[0], 200)
        self.assertEqual(value, original)
        status, _, raw = self.request()
        self.assertEqual(status, 200)
        readback = json.loads(raw)
        self.assertEqual(readback["project"], original)
        self.assertNotIn("playbackMode", readback["project"]["items"][0])
        self.assertEqual(server.BoardStore(self.state).read(), readback)
        self.assertEqual(self.save(1, readback["project"])[0], 200)
        before = self.state.read_bytes()
        self.assertEqual(self.save(1, value)[0], 409)
        self.assertEqual(self.state.read_bytes(), before)

    def test_20_repeat_schema_and_duration_consistency(self):
        good = item(end=0.5, duration=5, playbackMode="repeat-count",
                    repeatCount=10, playbackSpeed=1)
        server.validate_project(project([good]))
        server.validate_project(project([good | {"repeatCount": 2.5, "duration": 1.25}]))
        for changes in ({"playbackMode": None}, {"playbackMode": "loop"},
                        {"playbackMode": []}, {"playbackSpeed": 0},
                        {"playbackSpeed": True}, {"playbackSpeed": 9},
                        {"playbackSpeed": float("nan")}, {"repeatCount": None},
                        {"repeatCount": 0}, {"repeatCount": "10"}, {"repeatCount": True},
                        {"repeatCount": 10001}, {"duration": 6}, {"clip": None},
                        {"end": 5e-324, "playbackSpeed": 8},
                        {"playbackMode": "repeat-duration", "duration": 3600, "playbackSpeed": 8}):
            with self.subTest(changes=changes), self.assertRaises(server.Invalid):
                server.validate_project(project([good | changes]))
        missing = good.copy()
        del missing["repeatCount"]
        with self.assertRaises(server.Invalid):
            server.validate_project(project([missing]))
        self.assertEqual(self.save(value=project([good]))[0], 200)
        before = self.state.read_bytes()
        self.assertEqual(self.save(1, project([good | {"duration": 6}]))[0], 422)
        self.assertEqual(self.state.read_bytes(), before)

    def test_11_manifest_cannot_select_arbitrary_paths(self):
        (self.assets / "libraries").mkdir()
        (self.assets / "libraries" / "test.glb").write_bytes(b"approved library")
        self.manifest([{"id": "test", "name": "Test", "path": "/not/trusted",
                        "url": "/libraries/test.glb", "sourceHash": "hash"}])
        status, _, raw = self.request(path="/api/info")
        self.assertEqual(status, 200)
        info = json.loads(raw)
        self.assertEqual(info["sourceHash"], "source-hash")
        self.assertNotIn("path", info["libraries"][0])
        self.assertEqual(self.request(path="/libraries/test.glb")[2], b"approved library")
        for entry in ({"id": "../outside"}, {"id": "test", "url": "https://example.test/data"},
                      {"id": "test", "url": "/model.glb"}):
            with self.subTest(entry=entry):
                self.manifest([entry])
                self.assertEqual(self.request(path="/api/info")[0], 422)

    def test_18_optional_manifest_clip_metadata_is_bounded(self):
        entry = {"id": "test", "name": "Test", "fileName": "test.glb", "sourceHash": "hash"}
        self.manifest([entry])
        self.assertNotIn("clips", json.loads(self.request(path="/api/info")[2])["libraries"][0])
        self.manifest([entry | {"clips": [{"name": "Walk", "duration": 2.5, "path": "/private/source"}]}])
        status, _, raw = self.request(path="/api/info")
        self.assertEqual(status, 200)
        library = json.loads(raw)["libraries"][0]
        self.assertEqual(library, entry | {"url": "/libraries/test.glb", "clips": [{"name": "Walk", "duration": 2.5}]})
        invalid = [None, {}, [{"name": "", "duration": 1}], [{"name": "x" * 513, "duration": 1}],
                   [{"name": "Walk"}], [None], [{"name": "Walk", "duration": 1}] * 4097]
        invalid.extend([[{"name": "Walk", "duration": value}] for value in (0, -1, True, "2", float("nan"), float("inf"), 36001)])
        for clips in invalid:
            with self.subTest(clips=str(clips)[:100]):
                self.manifest([entry | {"clips": clips}])
                self.assertEqual(self.request(path="/api/info")[0], 422)

    def test_12_routes_and_symlinks_cannot_escape_allowlist(self):
        outside = self.root / "secret.glb"
        outside.write_bytes(b"must not be served")
        (self.assets / "libraries").mkdir()
        (self.assets / "libraries" / "unlisted.glb").write_bytes(b"unlisted")
        self.manifest([])
        for path in ("/../secret.glb", "/%2e%2e/secret.glb", "/libraries/../secret.glb",
                     "/libraries/unlisted.glb", "/vendor/not-approved.js", "/server.py",
                     "/state/board.json", "/libraries\\secret.glb"):
            with self.subTest(path=path):
                self.assertIsNone(server.asset_path(path, self.frontend, self.assets))
        link = self.assets / "libraries" / "escape.glb"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"Symlink unavailable on this host: {exc}")
        self.manifest([{"id": "escape"}])
        self.assertEqual(self.request(path="/libraries/escape.glb")[0], 404)

    def test_13_origin_host_and_fetch_site_guards(self):
        cases = [[("Host", "attacker.test")], [("Host", "localhost:1")],
                 [("Host", f"127.0.0.1:{self.http.server_port}"), ("Host", "attacker.test")],
                 [("Origin", "https://attacker.test")], [("Origin", "null")],
                 [("Origin", f"http://127.0.0.1:{self.http.server_port}"), ("Origin", "null")],
                 [("Sec-Fetch-Site", "cross-site")]]
        for headers in cases:
            with self.subTest(headers=headers):
                self.assertEqual(self.request("PUT", body={"revision": 0, "project": project()}, headers=headers)[0], 403)
        self.assertEqual(self.request("PUT", body={}, origin=False)[0], 403)
        self.assertFalse(self.state.exists())

    def test_14_http_body_type_size_and_length_guards(self):
        cases = [([("Content-Type", "text/plain")], 415),
                 ([("Content-Length", str(server.MAX_BYTES + 1))], 413),
                 ([("Content-Length", "0")], 413),
                 ([("Content-Length", "-1")], 400),
                 ([("Content-Length", "2"), ("Content-Length", "2")], 400),
                 ([("Transfer-Encoding", "chunked")], 400)]
        for headers, expected in cases:
            with self.subTest(headers=headers):
                self.assertEqual(self.request("PUT", body=b"{}", headers=headers)[0], expected)
        self.assertEqual(self.request("PUT", body=None)[0], 400)
        self.assertFalse(self.state.exists())

    def test_15_static_head_and_vendor_routes(self):
        vendor = self.assets / "vendor/examples/jsm/utils/SkeletonUtils.js"
        vendor.parent.mkdir(parents=True)
        vendor.write_bytes(b"// test fixture")
        status, headers, body = self.request(path="/")
        self.assertEqual((status, body), (200, b"<p>test fixture</p>"))
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Cross-Origin-Resource-Policy"], "same-origin")
        self.assertEqual(self.request("HEAD", "/model.glb")[2], b"")
        status, headers, body = self.request(path="/vendor/examples/jsm/utils/SkeletonUtils.js")
        self.assertEqual((status, body), (200, b"// test fixture"))
        self.assertTrue(headers["Content-Type"].startswith("text/javascript"))
        self.assertEqual(self.request("PUT", "/model.glb", body={})[0], 404)

    def test_16_explicit_asset_and_state_mount_paths(self):
        environment = os.environ.copy()
        environment.update(MOTION_BOARD_ASSETS=str(self.assets),
                           MOTION_BOARD_STATE=str(self.state.parent),
                           PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-c",
            "import json,server; print(json.dumps([str(server.PRIVATE),str(server.STATE)]))"],
            cwd=Path(server.__file__).parent, env=environment, check=True,
            capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), [str(self.assets.resolve()),
                                                    str(self.state.parent.resolve())])
        self.assertFalse(self.state.exists())
        self.assertFalse((self.assets / "board.json").exists())

    def test_17_container_forwarding_keeps_origin_checks(self):
        headers = Message()
        headers["Host"] = "127.0.0.1:8769"
        headers["Origin"] = "http://127.0.0.1:8769"
        for container, expected in ((False, False), (True, True)):
            handler_type = server.handler_class(self.store, self.frontend, self.assets,
                                                container=container)
            handler = handler_type.__new__(handler_type)
            handler.client_address = ("172.18.0.1", 12345)
            handler.headers = headers
            handler.server = SimpleNamespace(server_port=8769)
            handler._json = lambda *_: None
            self.assertEqual(handler._guard(write=True), expected)
            headers.replace_header("Origin", "http://attacker.test")
            self.assertFalse(handler._guard(write=True))
            headers.replace_header("Origin", "http://127.0.0.1:8769")


if __name__ == "__main__":
    unittest.main()
