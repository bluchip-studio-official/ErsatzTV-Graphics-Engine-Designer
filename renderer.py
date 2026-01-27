from __future__ import annotations

import os
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont
import math
import random

from models import AnimMode, AnimType, Animation, ImageElement, Scene, TextElement, ShapeElement


def _clamp(v: float | None, lo: float, hi: float) -> float:
    v = v or 0.0
    return lo if v < lo else hi if v > hi else v


def _ease_out_back(t: float, overshoot: float = 1.70158) -> float:
    t -= 1.0
    return t * t * ((overshoot + 1.0) * t + overshoot) + 1.0


def _parse_hex_color(s: str) -> Tuple[int, int, int]:
    try:
        s = s.lstrip("#")
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except Exception:
        return (255, 255, 255)


def _load_font(path: str | None, size: int) -> ImageFont.ImageFont:
    for p in [path, "C:\\Windows\\Fonts\\arial.ttf"]:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _anim_progress(anim: Animation, elapsed: float, ping_pong: bool = False) -> float:
    if anim.mode == AnimMode.FIXED:
        return _clamp(elapsed / max(anim.duration_s, 1e-6), 0.0, 1.0)
    # infinite → ping-pong (smoother for fade effects)
    if ping_pong:
        t = (elapsed / max(anim.duration_s, 1e-6)) % 2.0
        return t if t <= 1.0 else 2.0 - t
    # infinite → loop 0..1
    return (elapsed / max(anim.duration_s, 1e-6)) % 1.0


def _apply(anim: Animation, elapsed: float, invert: bool = False) -> Tuple[int, int, float, float, float]:
    if anim.type == AnimType.NONE:
        return 0, 0, 1.0, 1.0, 0.0

    # Use ping-pong for infinite fade animations (smoother)
    ping_pong = (anim.mode == AnimMode.INFINITE and anim.type == AnimType.FADE)
    t = _anim_progress(anim, elapsed, ping_pong=ping_pong)
    if invert:
        t = 1.0 - t

    eased = _ease_out_back(t, anim.overshoot)

    dx = dy = 0
    alpha = t
    scale = 1.0
    rot = 0.0

    if anim.type == AnimType.POP_IN:
        scale = anim.scale_from + (1.0 - anim.scale_from) * eased

    elif anim.type == AnimType.SLIDE_IN_RIGHT:
        dx = int((1.0 - eased) * anim.offset_x)

    elif anim.type == AnimType.SLIDE_IN_LEFT:
        dx = -int((1.0 - eased) * anim.offset_x)

    elif anim.type == AnimType.SLIDE_IN_DOWN:
        dy = int((1.0 - eased) * anim.offset_y)

    elif anim.type == AnimType.SLIDE_IN_UP:
        dy = -int((1.0 - eased) * anim.offset_y)

    elif anim.type == AnimType.SHAKE:
        # Shake effect: random jitter or sinewave
        intensity = 1.0 - t if anim.mode == AnimMode.FIXED else 1.0
        # Use sine waves for smoother shake
        dx = int(math.sin(elapsed * 50) * 5 * intensity)
        dy = int(math.cos(elapsed * 42) * 5 * intensity)
        alpha = 1.0  # Shake doesn't affect alpha by default

    elif anim.type == AnimType.ROTATE:
        # 360 degrees over duration
        rot = (elapsed / max(anim.duration_s, 0.1)) * 360.0
        if anim.mode == AnimMode.INFINITE:
            rot = rot % 360.0
        alpha = 1.0

    elif anim.type == AnimType.PULSE:
        # Pulse scale around 1.0
        # t is 0..1..0 (ping-pong)
        scale = 1.0 + (anim.scale_from - 1.0) * t
        alpha = 1.0

    elif anim.type == AnimType.TYPEWRITER:
        # Special case handled in render loop for TextElement text slicing
        # Here we just return alpha 1 so it is visible
        alpha = 1.0

    return dx, dy, alpha, scale, rot


def render_frame(scene: Scene, t: float, cache: Dict[str, Image.Image]) -> Image.Image:
    w = int(scene.width or 1920)
    h = int(scene.height or 1080)
    frame = Image.new("RGBA", (w, h), tuple(scene.bg_color))
    draw = ImageDraw.Draw(frame)

    for el in sorted(scene.elements, key=lambda e: (e.z or 0, e.id)):
        if t < (el.visible_from_s or 0.0) or t > (el.visible_until_s or 999.0):
            continue

        if t < (el.visible_from_s or 0.0) + (el.animation_in.duration_s or 0.0):
            dx, dy, a, s, r = _apply(el.animation_in, t - (el.visible_from_s or 0.0))
            
            # Special Typewriter logic for IN animation
            typewriter_progress = None
            if el.animation_in.type == AnimType.TYPEWRITER:
                # 0.0 to 1.0 progress
                typewriter_progress = _anim_progress(el.animation_in, t - el.visible_from_s)

        elif t > (el.visible_until_s or 4.0) - (el.animation_out.duration_s or 0.0):
            # Use elapsed time from start of out animation (no invert needed)
            dx, dy, a, s, r = _apply(el.animation_out, t - ((el.visible_until_s or 4.0) - (el.animation_out.duration_s or 0.0)))
            # Invert alpha for fade-out effect
            a = 1.0 - a
            typewriter_progress = None
        else:
            dx = dy = 0
            a = 1.0
            s = 1.0
            r = 0.0
            typewriter_progress = None

        opacity = _clamp((el.opacity or 1.0) * a, 0.0, 1.0)
        if opacity <= 0:
            continue

        x = el.x + dx
        y = el.y + dy

        x = (el.x or 0) + dx
        y = (el.y or 0) + dy
        rotation = (el.rotation or 0.0) + r

        if isinstance(el, TextElement):
            text_to_render = el.text
            if typewriter_progress is not None:
                # Calculate how many chars to show
                char_count = int(len(el.text) * typewriter_progress)
                text_to_render = el.text[:char_count]

            font = _load_font(el.font_path, int(el.font_size * s))
            rgb = _parse_hex_color(el.color)
            
            # Create a separate image for text to handle rotation
            # Estimate size
            bbox = font.getbbox(el.text) # use full text for consistent size
            w, h = bbox[2], bbox[3] + bbox[1] # rough estimate
            # Expand for rotation/scale
            w = int(w * 1.5) + 50
            h = int(h * 1.5) + 50
            
            txt_img = Image.new("RGBA", (w, h), (0,0,0,0))
            d = ImageDraw.Draw(txt_img)
            d.text((25, 25), text_to_render, font=font, fill=(*rgb, int(255 * opacity)))
            
            if rotation != 0:
                txt_img = txt_img.rotate(rotation, resample=Image.BICUBIC, expand=True)
            
            frame.alpha_composite(txt_img, (int((x or 0) - 25), int((y or 0) - 25))) # Adjust for padding

        elif isinstance(el, ShapeElement):
            w = int(el.width * s)
            h = int(el.height * s)
            shape_img = Image.new("RGBA", (w + int(el.border_width*2), h + int(el.border_width*2)), (0,0,0,0))
            d = ImageDraw.Draw(shape_img)
            
            rgb = _parse_hex_color(el.color)
            border_rgb = _parse_hex_color(el.border_color)
            fill = (*rgb, int(255 * opacity))
            outline = (*border_rgb, int(255 * opacity)) if el.border_width > 0 else None
            
            if el.shape_type == "ellipse":
                d.ellipse((0, 0, w, h), fill=fill, outline=outline, width=el.border_width)
            else:
                d.rectangle((0, 0, w, h), fill=fill, outline=outline, width=el.border_width)

            if rotation != 0:
                shape_img = shape_img.rotate(rotation, resample=Image.BICUBIC, expand=True)
                
            frame.alpha_composite(shape_img, (int(x or 0), int(y or 0)))

        elif isinstance(el, ImageElement) and el.path:
            img = cache.get(el.path)
            if img is None:
                try:
                    img = Image.open(el.path).convert("RGBA")
                    cache[el.path] = img
                except Exception:
                    continue

            # Apply both animation scale (s) and element scale (el.scale)
            combined_scale = s * el.scale
            out = img
            if abs(combined_scale - 1.0) > 1e-3:
                out = img.resize(
                    (max(1, int(img.width * combined_scale)), max(1, int(img.height * combined_scale))),
                    Image.Resampling.LANCZOS,
                )

                tmp = out.copy()
                tmp.putalpha(tmp.getchannel("A").point(lambda v: int(v * opacity)))
                out = tmp
            
            if rotation != 0:
                out = out.rotate(rotation, resample=Image.BICUBIC, expand=True)

            frame.alpha_composite(out, (int(x or 0), int(y or 0)))

    return frame
