from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from models import Scene


def save_project(scene: Scene, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scene.to_dict(), f, indent=2)


def load_project(path: str) -> Scene:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Scene.from_dict(data)


def export_ersatztv_script_yaml(yaml_path: str, python_script_path: str, z_index: int = 50) -> None:
    Path(yaml_path).parent.mkdir(parents=True, exist_ok=True)

    # Normalize Windows paths to forward slashes to avoid backslash escape issues
    normalized_path = python_script_path.replace("\\", "/")
    
    content = f"""z_index: {int(z_index)}
format: raw
command: python
args:
  - '{normalized_path}'
"""
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(content)


def export_python_renderer(py_path: str, scene: Scene) -> None:
    Path(py_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert scene to JSON, then fix JSON literals to Python syntax
    scene_json = json.dumps(scene.to_dict(), indent=2)
    scene_json = scene_json.replace(": null", ": None")
    scene_json = scene_json.replace(": true", ": True")
    scene_json = scene_json.replace(": false", ": False")

    content = f"""#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import sys
import time
from typing import Any, Dict, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    sys.stdout.reconfigure(encoding=None)
except Exception:
    pass

SCENE = {scene_json}

def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def _ease_out_back(t, overshoot=1.70158):
    t -= 1.0
    return t * t * ((overshoot + 1.0) * t + overshoot) + 1.0

def _parse_hex_color(s):
    try:
        s = s.lstrip("#")
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except Exception:
        return (255, 255, 255)

def _load_font(path, size):
    for p in [path, "C:\\\\Windows\\\\Fonts\\\\arial.ttf"]:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def _anim_progress(anim, elapsed, ping_pong=False):
    mode = anim.get("mode", "fixed")
    duration_s = float(anim.get("duration_s", 0.5))
    
    if mode == "fixed":
        return _clamp(elapsed / max(duration_s, 1e-6), 0.0, 1.0)
    
    # infinite
    if ping_pong:
        t = (elapsed / max(duration_s, 1e-6)) % 2.0
        return t if t <= 1.0 else 2.0 - t
    return (elapsed / max(duration_s, 1e-6)) % 1.0

def _apply_anim(anim, elapsed, invert=False):
    anim_type = anim.get("type", "none")
    
    if anim_type == "none":
        return 0, 0, 1.0, 1.0
    
    # Use ping-pong for infinite fade
    ping_pong = (anim.get("mode") == "infinite" and anim_type == "fade")
    t = _anim_progress(anim, elapsed, ping_pong=ping_pong)
    
    if invert:
        t = 1.0 - t
    
    eased = _ease_out_back(t, float(anim.get("overshoot", 0.5)))
    
    dx = dy = 0
    alpha = t
    scale = 1.0
    
    if anim_type == "pop_in":
        scale_from = float(anim.get("scale_from", 0.6))
        scale = scale_from + (1.0 - scale_from) * eased
    
    elif anim_type == "slide_in_right":
        dx = int((1.0 - eased) * int(anim.get("offset_x", 260)))
    
    elif anim_type == "slide_in_left":
        dx = -int((1.0 - eased) * int(anim.get("offset_x", 260)))
    
    elif anim_type == "slide_in_down":
        dy = int((1.0 - eased) * int(anim.get("offset_y", 120)))
    
    elif anim_type == "slide_in_up":
        dy = -int((1.0 - eased) * int(anim.get("offset_y", 120)))
    
    return dx, dy, alpha, scale

def main():
    try:
        if not sys.stdin.isatty():
            sys.stdin.read()
    except Exception:
        pass

    fps = float(SCENE.get("fps", 60.0))
    loop_seconds = float(SCENE.get("loop_seconds", 4.0))
    
    # Validate fps and loop_seconds to prevent division by zero
    if fps <= 0:
        fps = 60.0
    if loop_seconds <= 0:
        loop_seconds = 4.0
    
    frame_duration = 1.0 / fps

    running = True
    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    cache: Dict[str, Image.Image] = {{}}
    
    frame_count = 0

    while running:
        # Generate frame based on frame count, not wall clock time
        # This ensures consistent timing
        t = (frame_count * frame_duration) % loop_seconds
        w = int(SCENE.get("width", 1920))
        h = int(SCENE.get("height", 1080))
        frame = Image.new("RGBA", (w, h), tuple(SCENE["bg_color"]))
        draw = ImageDraw.Draw(frame)

        elems = sorted(SCENE["elements"], key=lambda e: (e.get("z", 0), e.get("id", "")))

        for el in elems:
            # Check visibility window
            visible_from = float(el.get("visible_from_s", 0.0))
            visible_until = float(el.get("visible_until_s", loop_seconds))
            
            if t < visible_from or t > visible_until:
                continue
            
            # Determine animation state
            anim_in = el.get("animation_in", {{}}) or {{}}
            anim_out = el.get("animation_out", {{}}) or {{}}
            anim_in_duration = float(anim_in.get("duration_s", 0.5))
            anim_out_duration = float(anim_out.get("duration_s", 0.5))
            
            if t < visible_from + anim_in_duration:
                dx, dy, a, s = _apply_anim(anim_in, t - visible_from)
            elif t > visible_until - anim_out_duration:
                # Use elapsed time from start of out animation
                dx, dy, a, s = _apply_anim(anim_out, t - (visible_until - anim_out_duration))
                # Invert alpha for fade-out
                a = 1.0 - a
            else:
                dx, dy, a, s = 0, 0, 1.0, 1.0
            
            opacity = _clamp(float(el.get("opacity", 1.0)) * a, 0.0, 1.0)
            if opacity <= 0:
                continue

            x = int(el.get("x", 0)) + dx
            y = int(el.get("y", 0)) + dy

            if el.get("kind") == "text":
                font_path = el.get("font_path")
                font_size = int(el.get("font_size", 24))
                # Apply animation scale to font
                scaled_font_size = int(font_size * s)
                font = _load_font(font_path, scaled_font_size)
                rgb = _parse_hex_color(el.get("color", "#FFFFFF"))
                draw.text((x, y), el.get("text", ""), font=font, fill=(*rgb, int(255 * opacity)))
            
            elif el.get("kind") == "image":
                img_path = el.get("path", "")
                if not img_path:
                    continue
                
                img = cache.get(img_path)
                if img is None:
                    try:
                        img = Image.open(img_path).convert("RGBA")
                        cache[img_path] = img
                    except Exception:
                        continue
                
                # Apply both animation scale and element scale
                el_scale = float(el.get("scale", 1.0))
                combined_scale = s * el_scale
                
                out = img
                if abs(combined_scale - 1.0) > 1e-3:
                    out = img.resize(
                        (max(1, int(img.width * combined_scale)), max(1, int(img.height * combined_scale))),
                        Image.Resampling.LANCZOS,
                    )
                
                if opacity < 1.0:
                    tmp = out.copy()
                    tmp.putalpha(tmp.getchannel("A").point(lambda v: int(v * opacity)))
                    out = tmp
                
                frame.alpha_composite(out, (int(x), int(y)))
            
            elif el.get("kind") == "shape":
                w = int(float(el.get("width", 100)) * s)
                h = int(float(el.get("height", 100)) * s)
                bw = int(el.get("border_width", 0))
                shape_img = Image.new("RGBA", (w + bw*2, h + bw*2), (0,0,0,0))
                d = ImageDraw.Draw(shape_img)
                
                rgb = _parse_hex_color(el.get("color", "#3B8ED0"))
                border_rgb = _parse_hex_color(el.get("border_color", "#FFFFFF"))
                fill = (*rgb, int(255 * opacity))
                outline = (*border_rgb, int(255 * opacity)) if bw > 0 else None
                
                if el.get("shape_type") == "ellipse":
                    d.ellipse((0, 0, w, h), fill=fill, outline=outline, width=bw)
                else:
                    d.rectangle((0, 0, w, h), fill=fill, outline=outline, width=bw)

                if rotation != 0:
                    shape_img = shape_img.rotate(rotation, resample=Image.BICUBIC, expand=True)
                    
                frame.alpha_composite(shape_img, (int(x), int(y)))

        arr = np.asarray(frame)
        bgra = np.ascontiguousarray(arr[:, :, [2, 1, 0, 3]])
        try:
            # Use os.write for raw binary output to avoid AttributeError/buffer issues in some envs
            if sys.platform == "win32":
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            
            os.write(sys.stdout.fileno(), bgra.tobytes())
        except (BrokenPipeError, AttributeError, ValueError):
            break
        
        frame_count += 1

if __name__ == "__main__":
    main()
"""
    with open(py_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
