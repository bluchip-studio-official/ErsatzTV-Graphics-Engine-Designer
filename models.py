from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import uuid


class AnimType(str, Enum):
    NONE = "none"
    FADE = "fade"
    SLIDE_IN_RIGHT = "slide_in_right"
    SLIDE_IN_LEFT = "slide_in_left"
    SLIDE_IN_UP = "slide_in_up"
    SLIDE_IN_DOWN = "slide_in_down"
    POP_IN = "pop_in"
    TYPEWRITER = "typewriter"
    SHAKE = "shake"
    ROTATE = "rotate"
    PULSE = "pulse"


class AnimMode(str, Enum):
    FIXED = "fixed"
    INFINITE = "infinite"


@dataclass
class Animation:
    type: AnimType = AnimType.NONE
    mode: AnimMode = AnimMode.FIXED
    duration_s: float = 0.5

    offset_x: int = 260
    offset_y: int = 120
    overshoot: float = 0.50
    scale_from: float = 0.6


@dataclass
class BaseElement:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Element"
    kind: Literal["text", "image"] = "text"

    x: int = 0
    y: int = 0
    z: int = 0
    opacity: float = 1.0
    rotation: float = 0.0

    visible_from_s: float = 0.0
    visible_until_s: float = 4.0

    animation_in: Animation = field(default_factory=Animation)
    animation_out: Animation = field(default_factory=Animation)


@dataclass
class TextElement(BaseElement):
    kind: Literal["text"] = "text"
    name: str = "Text"
    text: str = "Hello"
    font_path: Optional[str] = None
    font_size: int = 24
    color: str = "#FFFFFF"


@dataclass
class ImageElement(BaseElement):
    kind: Literal["image"] = "image"
    name: str = "Image"
    path: str = ""
    scale: float = 1.0


@dataclass
class ShapeElement(BaseElement):
    kind: Literal["shape"] = "shape"
    name: str = "Shape"
    shape_type: Literal["rectangle", "ellipse"] = "rectangle"
    width: int = 100
    height: int = 100
    color: str = "#3B8ED0"
    border_width: int = 0
    border_color: str = "#FFFFFF"


Element = Union[TextElement, ImageElement, ShapeElement]


@dataclass
class Scene:
    width: int = 1920
    height: int = 1080
    fps: float = 60.0
    bg_color: Tuple[int, int, int, int] = (0, 0, 0, 0)

    loop_seconds: float = 4.0
    elements: List[Element] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        def anim(a: Animation) -> Dict[str, Any]:
            d = asdict(a)
            d["type"] = a.type.value
            d["mode"] = a.mode.value
            return d

        out = {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "bg_color": list(self.bg_color),
            "loop_seconds": self.loop_seconds,
            "elements": [],
        }

        for e in self.elements:
            d = asdict(e)
            d["animation_in"] = anim(e.animation_in)
            d["animation_out"] = anim(e.animation_out)
            out["elements"].append(d)

        return out

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Scene":
        scene = Scene(
            width=int(data.get("width", 640)),
            height=int(data.get("height", 360)),
            fps=float(data.get("fps", 60.0)),
            bg_color=tuple(data.get("bg_color", [0, 0, 0, 0])),
            loop_seconds=float(data.get("loop_seconds", 4.0)),
        )

        for raw in data.get("elements", []):
            def read_anim(key: str) -> Animation:
                a = raw.get(key, {}) or {}
                return Animation(
                    type=AnimType(a.get("type", "none")),
                    mode=AnimMode(a.get("mode", "fixed")),
                    duration_s=float(a.get("duration_s", 0.5)),
                    offset_x=int(a.get("offset_x", 260)),
                    offset_y=int(a.get("offset_y", 120)),
                    overshoot=float(a.get("overshoot", 0.5)),
                    scale_from=float(a.get("scale_from", 0.6)),
                )

            base = dict(
                id=raw.get("id", str(uuid.uuid4())),
                name=raw.get("name", "Element"),
                x=int(raw.get("x", 0)),
                y=int(raw.get("y", 0)),
                z=int(raw.get("z", 0)),
                opacity=float(raw.get("opacity", 1.0)),
                visible_from_s=float(raw.get("visible_from_s", 0.0)),
                visible_until_s=float(raw.get("visible_until_s", scene.loop_seconds)),
                animation_in=read_anim("animation_in"),
                animation_out=read_anim("animation_out"),
            )
            base["rotation"] = float(raw.get("rotation", 0.0))

            if raw.get("kind") == "image":
                el = ImageElement(
                    **base,
                    path=str(raw.get("path", "")),
                    scale=float(raw.get("scale", 1.0)),
                )

            elif raw.get("kind") == "shape":
                el = ShapeElement(
                    **base,
                    shape_type=str(raw.get("shape_type", "rectangle")),
                    width=int(raw.get("width", 100)),
                    height=int(raw.get("height", 100)),
                    color=str(raw.get("color", "#3B8ED0")),
                    border_width=int(raw.get("border_width", 0)),
                    border_color=str(raw.get("border_color", "#FFFFFF")),
                )
            else:
                el = TextElement(
                    **base,
                    text=str(raw.get("text", "Hello")),
                    font_path=raw.get("font_path"),
                    font_size=int(raw.get("font_size", 24)),
                    color=str(raw.get("color", "#FFFFFF")),
                )

            scene.elements.append(el)

        return scene
