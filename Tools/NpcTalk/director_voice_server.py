"""NPC voices: a hidden sidecar the game starts, like whisper-server and llama-server (docs/NPC_TALK.md).

LuxTTS (Apache-2.0, code and model) runs on the PROCESSOR - no video memory (owner 2026-10-10: "4 GB of VRAM is a
heavy tax") - and clones short reference recordings. A voice is a file in the voices folder (owner 2026-10-12:
"there should be an audio profile for them", like the text profiles):

  <Name>.wav   a 4-7 s recording of the voice, cut at a pause between sentences (a mid-word cut leaks that word
               into every line); how it was made does not matter - designed, recorded, bought
  <Name>.txt   optional settings: speed=0.92 (pace, ~ speed squared), treatment=entity|chrome|none

The Director's is "predator entity" (design, recipe and approved sample: M:/Local AI/DirectorTTS/director_voice_final).

  POST /speak   header X-Voice: <Name> (default: --default), body = the line as UTF-8 text
                200 -> raw mono PCM16 little-endian, header X-Sample-Rate (48000)
                400 empty line; 404 no such voice; 500 the model failed
  GET  /health  200 once the model is loaded and the default voice is warm
  GET  /voices  the voice names, one per line

The port opens only once the model is loaded, so a refused connection means "still waking up". One line at a
time, in arrival order. Binds 127.0.0.1 only (0.0.0.0 would raise a firewall prompt on screen). Exits by itself
when the game that started it goes away (--parent-pid), so a crashed game never strands it.

  prerender:  python director_voice_server.py <same args> --voice <Name> --prerender <lines.txt> --cache <dir>
              writes each line as the game's cache file (cache_key below), so scripted lines play the moment they
              fire, with nothing to wait for; --check <whisper /inference URL> re-says a line slower until every
              word is heard.
"""
import argparse
import hashlib
import os
import struct
import sys
import threading
import time

SR = 48000


def watch_parent(pid):
    """Leave when the game does: Windows lets a process wait on another's handle."""
    if pid <= 0 or os.name != "nt":
        return
    import ctypes

    SYNCHRONIZE = 0x00100000
    handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        os._exit(0)  # already gone

    def wait():
        ctypes.windll.kernel32.WaitForSingleObject(handle, 0xFFFFFFFF)
        os._exit(0)

    threading.Thread(target=wait, daemon=True).start()


def cache_key(reference, speed, treatment, text):
    """Same string and hash as SSNpcTalk::VoiceCacheName: a new recording, speed or treatment makes every line again."""
    material = "%s|%.2f|%s|%s" % (os.path.basename(reference), speed, treatment, text)
    return hashlib.md5(material.encode("utf-8")).hexdigest()


def read_voices(folder):
    """Every <Name>.wav in the folder, with its <Name>.txt settings. Same reading as USSNpcTalkSubsystem."""
    voices = {}
    for file in sorted(os.listdir(folder)):
        if not file.lower().endswith(".wav"):
            continue
        name = file[:-4]
        settings = {"speed": 0.92, "treatment": "none"}
        txt = os.path.join(folder, name + ".txt")
        if os.path.exists(txt):
            for line in open(txt, encoding="utf-8"):
                key, _, value = line.partition("=")
                key, value = key.strip().lower(), value.strip()
                if key == "speed":
                    try:
                        settings["speed"] = float(value)
                    except ValueError:
                        pass
                elif key == "treatment":
                    settings["treatment"] = value.lower() or "none"
        voices[name] = dict(reference=os.path.join(folder, file), **settings)
    return voices


def load_engine(args):
    """Returns speak(voice, text, pace) -> (pcm16 bytes, rate). Imports here: the parent watch and the argument
    checks run first."""
    os.environ["HF_HUB_OFFLINE"] = "1"  # everything is on disk; never reach for the network from inside the game
    # The thread budget is the game's ("the game is running beside it"): LuxTTS only hands it to ONNX, so the torch
    # vocoder and numpy would otherwise take every core. Set before the first numpy/torch import.
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[name] = str(max(1, args.threads))
    sys.path.insert(0, args.lux_repo)
    import numpy as np
    import torch
    from scipy.signal import butter, fftconvolve, lfilter
    import librosa
    from zipvoice.luxvoice import LuxTTS

    torch.set_num_threads(max(1, args.threads))
    torch.set_num_interop_threads(1)
    lux = LuxTTS("YatharthS/LuxTTS", device="cpu", threads=args.threads)
    prompts = {}

    def prompt_for(voice):
        # Encoded once per voice, on first use (~1 s), and kept.
        if voice["reference"] not in prompts:
            prompts[voice["reference"]] = lux.encode_prompt(voice["reference"], duration=1000, rms=0.01)
        return prompts[voice["reference"]]

    # "entity" (director_voice_final/speak_predator_entity.py): pitched down 3 semitones, an octave-down double, a
    # faint ghost an octave up 18 ms late, a 1.2 s dark tail. The tail's impulse is made once.
    rng = np.random.default_rng(11)
    n = int(1.2 * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (1.2 / 5 * SR))
    b, a = butter(2, 2000 / (SR / 2))
    ir = lfilter(b, a, ir)
    ir /= np.sqrt(np.sum(ir ** 2))

    def entity(y):
        down = librosa.effects.pitch_shift(y, sr=SR, n_steps=-3)
        sub = librosa.effects.pitch_shift(y, sr=SR, n_steps=-12)
        ghost = librosa.effects.pitch_shift(y, sr=SR, n_steps=12)
        lag = int(0.018 * SR)
        ghost = np.concatenate([np.zeros(lag), ghost[:-lag]])
        mixed = down + 0.3 * sub + 0.07 * ghost
        wet = fftconvolve(mixed, ir)[: len(mixed) + n // 2]
        return np.concatenate([mixed, np.zeros(len(wet) - len(mixed))]) + 0.12 * wet

    # "chrome": a faint metallic comb and a slow shimmer under the dry voice - cybernetics, lightly.
    bc, ac = butter(2, [150 / (SR / 2), 9000 / (SR / 2)], btype="band")

    def chrome(y):
        d = int(0.0021 * SR)
        comb = y.copy()
        for i in range(d, len(comb)):
            comb[i] += 0.3 * comb[i - d]
        t = np.arange(len(y)) / SR
        delay = (0.004 + 0.0015 * np.sin(2 * np.pi * 0.3 * t)) * SR
        idx = np.clip(np.arange(len(y)) - delay, 0, len(y) - 1)
        lo = np.floor(idx).astype(int)
        frac = idx - lo
        shimmer = y[lo] * (1 - frac) + y[np.minimum(lo + 1, len(y) - 1)] * frac
        return 0.7 * y + 0.2 * lfilter(bc, ac, comb) + 0.15 * shimmer

    treatments = {"entity": entity, "chrome": chrome}

    def speak(voice, text, pace=1.0):
        # A one-word line ("Fetch.") comes out shorter than the vocoder's 7-frame kernel and raises; said a little
        # slower it has room (measured 2026-10-11). Anything else that raises is a real failure.
        prompt = prompt_for(voice)
        first = voice["speed"] * pace
        for speed in (first, first * 0.7, first * 0.5):
            try:
                y = lux.generate_speech(text, prompt, num_steps=4, t_shift=0.9, speed=speed).numpy().squeeze()
                break
            except RuntimeError as error:
                if "Kernel size" not in str(error) or speed == first * 0.5:
                    raise
        y = np.asarray(y, dtype=np.float32)
        if voice["treatment"] in treatments:
            y = treatments[voice["treatment"]](y)
        y = y / max(1e-6, float(np.max(np.abs(y)))) * 0.89
        return (np.clip(y, -1.0, 1.0) * 32767.0).astype("<i2").tobytes(), SR

    return speak


def words(text):
    return "".join(c for c in text.lower() if c.isalnum() or c.isspace()).split()


def heard(url, pcm, rate):
    """What whisper-server (the game's own transcriber) hears in a clip."""
    import io
    import json
    import urllib.request
    import uuid

    import librosa
    import numpy as np
    import soundfile as sf

    y = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32767.0
    wav = io.BytesIO()
    sf.write(wav, librosa.resample(y, orig_sr=rate, target_sr=16000), 16000, format="WAV", subtype="PCM_16")
    boundary = uuid.uuid4().hex
    head = ('--%s\r\nContent-Disposition: form-data; name="file"; filename="line.wav"\r\n'
            'Content-Type: audio/wav\r\n\r\n' % boundary)
    tail = ('\r\n--%s\r\nContent-Disposition: form-data; name="response_format"\r\n\r\njson\r\n--%s--\r\n'
            % (boundary, boundary))
    body = head.encode() + wav.getvalue() + tail.encode()
    request = urllib.request.Request(url, body, {"Content-Type": "multipart/form-data; boundary=" + boundary})
    return words(json.load(urllib.request.urlopen(request, timeout=60))["text"])


def live_pace(text):
    """Short lines come out rushed ("Did that sting?" in 0.7 s, 2026-10-11); the checked prerender settled most of
    them at 0.8-0.9 of the pace, so a live one starts there."""
    count = len(text.split())
    return 0.8 if count <= 4 else 0.9 if count <= 7 else 1.0


def prerender(args, voice, speak):
    """Scripted lines, made once. With --check each take is transcribed and a line that loses words is said again,
    slower."""
    lines = [l.strip() for l in open(args.prerender, encoding="utf-8") if l.strip() and not l.startswith("#")]
    os.makedirs(args.cache, exist_ok=True)
    made = kept = failed = 0
    for text in lines:
        path = os.path.join(args.cache, cache_key(voice["reference"], voice["speed"], voice["treatment"], text) + ".pcm")
        if os.path.exists(path):
            kept += 1
            continue
        # "Acornaut" is invented: the transcriber never knows it, so it never counts against a take.
        want = [w for w in words(text) if w != "acornaut"]
        best = None
        for pace in (1.0, 0.9, 0.8, 0.72, 0.65):
            try:
                pcm, rate = speak(voice, text, pace)
                got = set(heard(args.check, pcm, rate)) if args.check else None
            except Exception as error:  # keep the best take so far rather than lose the line
                print("voice: %r at pace %.2f failed: %s" % (text, pace, error), flush=True)
                break
            missing = sum(w not in got for w in want) if got is not None else 0
            if best is None or missing < best[2]:
                best = (pcm, rate, missing, pace)
            if not missing:
                break
        if best is None:
            print("voice: %r FAILED" % text, flush=True)
            failed += 1
            continue
        pcm, rate = best[0], best[1]
        if args.check:
            print("voice: %r at pace %.2f, %d word(s) unheard" % (text, best[3], best[2]), flush=True)
        # The game's cache file: four bytes of rate, then the clip as played (with its quarter second of silence).
        with open(path, "wb") as f:
            f.write(struct.pack("<i", rate) + pcm + bytes(rate // 4 * 2))
        made += 1
        print("voice: made %r" % text, flush=True)
    print("voice: %d made, %d already there, %d failed" % (made, kept, failed), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lux-repo", required=True, help="the LuxTTS checkout (zipvoice is not pip-installed)")
    ap.add_argument("--voices", required=True, help="folder of <Name>.wav (+ <Name>.txt) voices")
    ap.add_argument("--default", default="Director", help="the voice a request without X-Voice gets")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--port", type=int, default=8703)
    ap.add_argument("--parent-pid", type=int, default=0)
    ap.add_argument("--voice", help="prerender: which voice says the lines")
    ap.add_argument("--prerender", help="a text file, one line per row: make them into --cache and exit")
    ap.add_argument("--cache")
    ap.add_argument("--check", help="whisper-server /inference URL: re-say a prerendered line slower until it is heard")
    args = ap.parse_args()
    if not args.prerender:
        # Started hidden by the game, its output would go nowhere: it goes to the project's Saved/Logs instead.
        logs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Saved", "Logs")
        os.makedirs(logs, exist_ok=True)
        sys.stdout = sys.stderr = open(os.path.join(logs, "NpcVoice.log"), "w", encoding="utf-8", buffering=1)
    watch_parent(args.parent_pid)
    for path in (args.lux_repo, args.voices):
        if not os.path.exists(path):
            print("voice: missing %s" % path, flush=True)
            sys.exit(2)
    voices = read_voices(args.voices)
    if not voices:
        print("voice: no <Name>.wav in %s" % args.voices, flush=True)
        sys.exit(2)
    started = time.time()
    print("voice: loading (threads %d, port %d, voices %s)" % (args.threads, args.port, ", ".join(voices)), flush=True)
    speak = load_engine(args)
    print("voice: model loaded after %.1f s" % (time.time() - started), flush=True)
    if args.prerender:
        if args.voice not in voices:
            sys.exit("voice: no voice named %r in %s" % (args.voice, args.voices))
        prerender(args, voices[args.voice], speak)
        return
    warm = voices.get(args.default) or next(iter(voices.values()))
    speak(warm, "Ready.")  # first-call costs (librosa, the vocoder, the reference) are paid here, not on a line
    print("voice: ready after %.1f s" % (time.time() - started), flush=True)

    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, code, body=b"", rate=0):
            try:
                self.send_response(code)
                self.send_header("Content-Type", "audio/pcm" if rate else "text/plain")
                if rate:
                    self.send_header("X-Sample-Rate", str(rate))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (ConnectionError, OSError):
                pass  # the game cancelled: the line is no longer wanted

        def do_GET(self):
            if self.path == "/health":
                self.reply(200, b"ok")
            elif self.path == "/voices":
                self.reply(200, ("\n".join(voices) + "\n").encode("utf-8"))
            else:
                self.reply(404)

        def do_POST(self):
            if self.path != "/speak":
                self.reply(404)
                return
            length = int(self.headers.get("Content-Length") or 0)
            text = self.rfile.read(length).decode("utf-8", "replace").strip() if length > 0 else ""
            if not text:
                self.reply(400, b"empty line")
                return
            name = (self.headers.get("X-Voice") or args.default).strip()
            voice = voices.get(name)
            if voice is None:
                self.reply(404, ("no voice named %s" % name).encode("utf-8", "replace"))
                return
            try:
                pcm, rate = speak(voice, text, live_pace(text))
            except Exception as error:  # a bad line must not take the voice down for the rest of the run
                print("voice: %s %r failed: %s" % (name, text[:60], error), flush=True)
                self.reply(500, str(error).encode("utf-8", "replace"))
                return
            self.reply(200, pcm, rate)

    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
