from __future__ import annotations

import base64
import io
import time
from typing import Dict, Optional, List

from nicegui import ui, app
from PIL import Image

from models import AnimMode, Animation, ImageElement, Scene, TextElement, Element, ShapeElement
from animation_presets import IN_ANIMATION_PRESETS, OUT_ANIMATION_PRESETS
from renderer import render_frame
from exporters import (
    save_project,
    load_project,
    export_python_renderer,
    export_ersatztv_script_yaml,
)

# ================= CUSTOMER THEME =================
# We inject global CSS to override some defaults and create the "Sleek" look.
ui.add_head_html('''
<style>
    body {
        font-family: 'Inter', sans-serif;
        background-color: #0f172a; /* Slate 900 */
        color: #e2e8f0; /* Slate 200 */
    }
    .sleek-panel {
        background-color: rgba(30, 41, 59, 0.7); /* Slate 800 with opacity */
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
    }
    .sleek-input .q-field__control {
        border-radius: 8px !important;
        background: rgba(0, 0, 0, 0.2) !important;
    }
    .sleek-btn {
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    /* Window Drag Controls */
    body {
        -webkit-app-region: no-drag;
        overflow: hidden; /* Prevent body scroll */
    }
    .drag-handle {
        -webkit-app-region: drag;
    }
    .no-drag {
        -webkit-app-region: no-drag;
    }
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a; 
    }
    ::-webkit-scrollbar-thumb {
        background: #334155; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569; 
    }
</style>
''')

# ================= STATE =================
class AppState:
    def __init__(self):
        self.scene: Scene = Scene()
        self.selected_id: Optional[str] = None
        self.image_cache: Dict[str, object] = {}
        self.preview_start = time.perf_counter()
        
state = AppState()

def get_selected_element() -> Optional[Element]:
    if not state.selected_id: return None
    for e in state.scene.elements:
        if getattr(e, "id", None) == state.selected_id: return e
    return None

# ================= PREVIEW LOOP =================
# We use ui.interactive_image which handles frequent updates better than ui.image
preview_interactive: ui.interactive_image = None
preview_card: ui.card = None

async def update_preview():
    if not preview_interactive: return
        
    t = (time.perf_counter() - state.preview_start) % max(float(state.scene.loop_seconds or 4.0), 0.01)
    
    # Catch any potential NoneTypes here before rendering
    for el in state.scene.elements:
        if el.visible_from_s is None: el.visible_from_s = 0.0
        if el.visible_until_s is None: el.visible_until_s = 4.0
    
    try:
        # Update aspect ratio if changed
        if preview_card:
            aspect = f"{state.scene.width}/{state.scene.height}"
            preview_card.style(f"aspect-ratio: {aspect}; max-width: 100%; max-height: 100%; width: auto; height: auto;")

        frame = render_frame(state.scene, t, state.image_cache)
        
        buffered = io.BytesIO()
        frame.save(buffered, format="PNG") # PNG handles RGBA
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # interactive_image expects a URL or base64.
        # To avoid flicker, we push the content directly.
        preview_interactive.set_source(f"data:image/png;base64,{img_str}")
        
    except Exception as e:
        print(f"Render Error: {e}")

# ================= ACTIONS =================

def select_element(eid: str):
    state.selected_id = eid
    refresh_ui()

def delete_selected():
    if not state.selected_id: return
    state.scene.elements = [e for e in state.scene.elements if e.id != state.selected_id]
    state.selected_id = None
    refresh_ui()

def show_scene_settings():
    state.selected_id = None
    refresh_ui()

def add_element(kind: str):
    if kind == "text":
        el = TextElement(x=0, y=0, text="NEW TEXT")
    elif kind == "shape":
        el = ShapeElement(x=0, y=0)
    elif kind == "image":
        # Native file picker hack
        import tkinter as tk; from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        path = filedialog.askopenfilename()
        root.destroy()
        if not path: return
        el = ImageElement(x=0, y=0, path=path)
        
    state.scene.elements.append(el)
    select_element(el.id)

# ================= UI COMPONENTS =================

def render_element_list():
    ui.label("LAYERS").classes("text-xs font-bold text-slate-500 tracking-wider mb-2")
    
    # Add Actions Row
    with ui.row().classes("w-full gap-2 mb-4"):
        def add_btn(label, icon, kind, color="blue-700"):
            ui.button(label, icon=icon, on_click=lambda: add_element(kind)).classes("flex-grow sleek-btn").props(f"unelevated color={color} size=sm")
        
        add_btn("Text", "text_fields", "text")
        add_btn("Shape", "category", "shape")
        ui.button(icon="image", on_click=lambda: add_element("image")).props("unelevated color=slate-700 size=sm").classes("rounded-lg").tooltip("Add Image")
    
    with ui.column().classes("w-full gap-1"):
        for el in state.scene.elements:
            is_selected = el.id == state.selected_id
            
            # Styling for the list item
            base_class = "w-full p-2 rounded-lg flex items-center cursor-pointer transition-colors duration-200"
            bg_class = "bg-blue-600/20 border-blue-500/50 border" if is_selected else "hover:bg-white/5 border border-transparent"
            
            with ui.row().classes(f"{base_class} {bg_class}").on("click", lambda e=el: select_element(e.id)):
                # Icon
                icon_name = "text_fields" if isinstance(el, TextElement) else "image" if isinstance(el, ImageElement) else "category"
                ui.icon(icon_name).classes("mr-3 text-slate-400")
                
                # Name
                ui.label(el.name or "Element").classes("text-sm font-medium flex-grow truncate")
                
                # Visibility Toggle (Fake for now, just visual)
                ui.icon("visibility").classes("text-slate-600 hover:text-white text-xs")

def render_inspector():
    el = get_selected_element()
    if not el:
        with ui.column().classes("w-full h-full items-center justify-center opacity-30"):
            ui.icon("settings", size="48px")
            ui.label("Scene Settings").classes("mt-2 font-bold")
        
        # Show scene settings when nothing is selected
        with ui.column().classes("w-full gap-4 mt-8"):
            ui.separator().classes("bg-slate-700")
            ui.label("GLOBAL SETTINGS").classes("text-xs font-bold text-slate-500 tracking-wider")
            
            with ui.grid(columns=2).classes("w-full gap-2"):
                ui.number("Width", value=state.scene.width).bind_value(state.scene, "width").props("outlined dense dark").classes("w-full")
                ui.number("Height", value=state.scene.height).bind_value(state.scene, "height").props("outlined dense dark").classes("w-full")
                ui.number("FPS", value=state.scene.fps).bind_value(state.scene, "fps").props("outlined dense dark").classes("w-full")
                ui.number("Duration (s)", value=state.scene.loop_seconds).bind_value(state.scene, "loop_seconds").props("outlined dense dark").classes("w-full")
        return
        
    with ui.column().classes("w-full gap-4"):
        # Header
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(el.name).classes("text-lg font-bold text-slate-100")
            ui.button(icon="delete", on_click=delete_selected).props("flat dense round color=red")
            
        ui.separator().classes("bg-slate-700")
        
        # --- PROPERTIES ---
        with ui.expansion("Properties", value=True).classes("w-full"):
            with ui.grid(columns=2).classes("w-full gap-2"):
                ui.number("X", value=el.x).bind_value(el, "x").props("outlined dense dark").classes("w-full")
                ui.number("Y", value=el.y).bind_value(el, "y").props("outlined dense dark").classes("w-full")
                ui.number("Z Index", value=el.z).bind_value(el, "z").props("outlined dense dark").classes("w-full")
                ui.number("Rotation", value=el.rotation).bind_value(el, "rotation").props("outlined dense dark").classes("w-full")
                ui.number("Opacity", value=el.opacity, min=0.0, max=1.0, step=0.1).bind_value(el, "opacity").props("outlined dense dark").classes("w-full")
                
                if isinstance(el, TextElement):
                    ui.input("Text").bind_value(el, "text").props("outlined dense dark").classes("col-span-2")
                    ui.number("Font Size").bind_value(el, "font_size").props("outlined dense dark")
                    ui.color_input("Color", value=el.color).bind_value(el, "color").props("outlined dense dark").classes("w-full")

                elif isinstance(el, ShapeElement):
                    ui.select(["rectangle", "ellipse"], value=el.shape_type).bind_value(el, "shape_type").props("outlined dense dark").classes("col-span-2")
                    ui.number("W").bind_value(el, "width").props("outlined dense dark")
                    ui.number("H").bind_value(el, "height").props("outlined dense dark")
                    ui.color_input("Fill", value=el.color).bind_value(el, "color").props("outlined dense dark")
                    ui.color_input("Border", value=el.border_color).bind_value(el, "border_color").props("outlined dense dark")

                elif isinstance(el, ImageElement):
                    ui.number("Scale", step=0.1).bind_value(el, "scale").props("outlined dense dark").classes("col-span-2")

        # --- TIMING ---
        with ui.expansion("Timing", value=True).classes("w-full"):
            with ui.row().classes("w-full gap-2"):
                 ui.number("Start", max=state.scene.loop_seconds).bind_value(el, "visible_from_s").props("outlined dense dark").classes("w-1/2")
                 # Calc duration proxy
                 dur = el.visible_until_s - el.visible_from_s
                 def set_dur(v): el.visible_until_s = el.visible_from_s + float(v or 0)
                 ui.number("Duration", value=dur).on_value_change(lambda e: set_dur(e.value)).props("outlined dense dark").classes("w-1/2")

        # --- ANIMATIONS ---
        with ui.expansion("Animations").classes("w-full"):
             def render_anim(label, anim, is_in):
                 ui.label(label).classes("text-xs font-bold text-slate-500 mt-2")
                 
                 # Preset Selection
                 presets = IN_ANIMATION_PRESETS if is_in else OUT_ANIMATION_PRESETS
                 current = next((k for k,v in presets.items() if v.type == anim.type and v.mode == anim.mode), "Custom")
                 
                 def apply(e):
                     if e.value in presets:
                         anim.__dict__.update(presets[e.value].__dict__)
                         refresh_ui()
                 
                 ui.select(list(presets.keys()), value=current, label="Preset").on_value_change(apply).props("outlined dense dark").classes("w-full")
                 
                 # Manual Controls
                 with ui.grid(columns=2).classes("w-full gap-2 mt-2"):
                     ui.number("Duration (s)", value=anim.duration_s, step=0.1).bind_value(anim, "duration_s").props("outlined dense dark")
                     ui.select([m.value for m in AnimMode], value=anim.mode.value).bind_value(anim, "mode").props("outlined dense dark")
                 
             render_anim("ENTRANCE", el.animation_in, True)
             ui.separator().classes("bg-slate-700 my-2")
             render_anim("EXIT", el.animation_out, False)

# ================= MAIN LAYOUT =================

def refresh_ui():
    left_drawer.clear()
    with left_drawer:
        render_element_list()
        
    right_drawer.clear()
    with right_drawer:
        render_inspector()

# Background
ui.query("body").classes("bg-slate-900")

# --- HEADER (Floating) ---
with ui.header().classes("bg-transparent pointer-events-auto drag-handle"):
    with ui.row().classes("w-full justify-between items-center p-4 pointer-events-auto"):
        # Logo Area
        with ui.row().classes("items-center gap-3"):
            with ui.card().classes("w-10 h-10 flex items-center justify-center bg-blue-600 rounded-xl shadow-lg"):
                ui.icon("movie_filter", size="24px").classes("text-white")
            ui.label("Overlay Designer").classes("text-xl font-bold tracking-tight text-white")

        # Actions Area
        with ui.row().classes("gap-2"):
            # We use small icon buttons for a cleaner look
            def btn(icon, func, tooltip):
                ui.button(icon=icon, on_click=func).props("flat round dense color=white").tooltip(tooltip).classes("no-drag")
            
            btn("save", lambda: action_save(), "Save Project")
            btn("folder_open", lambda: action_load(), "Load Project")
            btn("code", lambda: action_export_py(), "Export Python")
            ui.separator().props("vertical").classes("mx-2 h-6 bg-slate-700")
            btn("settings", lambda: show_scene_settings(), "Scene Settings")

# --- LEFT PANEL (Floating Glass) ---
left_drawer = ui.left_drawer(value=True).classes("bg-transparent shadow-none border-none p-4").props("width=320")
# We inject a content div inside the drawer to give the floating glass look
with left_drawer:
    with ui.column().classes("w-full h-full sleek-panel p-4"):
        render_element_list()


# --- RIGHT PANEL (Floating Glass) ---
right_drawer = ui.right_drawer(value=True).classes("bg-transparent shadow-none border-none p-4").props("width=360")
with right_drawer:
    with ui.column().classes("w-full h-full sleek-panel p-4 overflow-y-auto"):
        render_inspector()


# --- CENTER PREVIEW ---
with ui.column().classes("w-full h-screen items-center justify-center p-8 bg-black"):
    # The canvas container - aspect-ratio will be set dynamically
    # We use flex justify-center to handle window resizing, but the card itself should be rigid ratio
    preview_card = ui.card().classes("shadow-2xl rounded-none border border-slate-700 overflow-hidden relative bg-transparent").style("width: 100%; height: 100%; max-width: 100%; max-height: 100%;")
    with preview_card:
        
        # Checkerboard background for transparency
        ui.html('<div style="position:absolute;top:0;left:0;right:0;bottom:0;background-image: linear-gradient(45deg, #1e293b 25%, transparent 25%), linear-gradient(-45deg, #1e293b 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #1e293b 75%), linear-gradient(-45deg, transparent 75%, #1e293b 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px; opacity: 0.5;"></div>', sanitize=False)
        
        # Live Preview Image - Use fill to stretch to the aspect-ratio constrained card
        preview_interactive = ui.interactive_image().classes("w-full h-full absolute top-0 left-0").style("object-fit: fill")
        
        # Overlay Info
        with ui.column().classes("absolute bottom-4 left-4 z-20"):
            with ui.row().classes("bg-black/50 backdrop-blur px-2 py-1 rounded text-xs gap-4 font-mono text-slate-400"):
                ui.label().bind_text_from(state.scene, "width", backward=lambda w: f"{w}x{state.scene.height}")
                ui.label().bind_text_from(state.scene, "fps", backward=lambda f: f"{f} FPS")


# Initial Render
refresh_ui()

# Helpers for file actions (re-implemented to avoid Tkinter threading issues if possible, but keeping simple for now)
async def action_save():
    import tkinter as tk; from tkinter import filedialog
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Overlay Project", "*.json")])
    root.destroy()
    if path: save_project(state.scene, path); ui.notify(f"Saved to {path}")

async def action_load():
    import tkinter as tk; from tkinter import filedialog
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    path = filedialog.askopenfilename(filetypes=[("Overlay Project", "*.json")])
    root.destroy()
    if path:
        state.scene = load_project(path)
        state.selected_id = None
        state.image_cache.clear()
        refresh_ui()

async def action_export_py():
    import tkinter as tk; from tkinter import filedialog
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Script", "*.py")])
    root.destroy()
    if path: export_python_renderer(path, state.scene); ui.notify("Exported Python Script")

# Start Loop (20ms = 50fps for smoother feel)
ui.timer(0.02, update_preview)

ui.run(title="ErsatzTV Overlay Designer", native=True, window_size=(1600, 950), dark=True, frameless=False)
