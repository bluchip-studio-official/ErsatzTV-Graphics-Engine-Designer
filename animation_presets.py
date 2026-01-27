from models import Animation, AnimType, AnimMode

# =====================================================
# IN ANIMATION PRESETS
# =====================================================

IN_ANIMATION_PRESETS = {
    # ---------- None ----------
    "None": Animation(
        type=AnimType.NONE,
        mode=AnimMode.FIXED,
        duration_s=0.0,
    ),

    # ---------- Standard ----------
    "Fade In": Animation(
        type=AnimType.FADE,
        mode=AnimMode.FIXED,
        duration_s=0.35,
    ),

    "Slide In Right": Animation(
        type=AnimType.SLIDE_IN_RIGHT,
        mode=AnimMode.FIXED,
        duration_s=0.4,
    ),

    "Slide In Left": Animation(
        type=AnimType.SLIDE_IN_LEFT,
        mode=AnimMode.FIXED,
        duration_s=0.4,
    ),

    "Slide In Up": Animation(
        type=AnimType.SLIDE_IN_UP,
        mode=AnimMode.FIXED,
        duration_s=0.4,
    ),

    "Slide In Down": Animation(
        type=AnimType.SLIDE_IN_DOWN,
        mode=AnimMode.FIXED,
        duration_s=0.4,
    ),

    # ---------- Special ----------
    "Pop In": Animation(
        type=AnimType.POP_IN,
        mode=AnimMode.FIXED,
        duration_s=0.3,
        scale_from=0.6,
    ),

    # Floating is approximated as slow infinite fade modulation
    "Floating (Infinite)": Animation(
        type=AnimType.FADE,
        mode=AnimMode.INFINITE,
        duration_s=3.0,
    ),

    # Pulsing is a faster infinite fade
    "Pulsing (Fade)": Animation(
        type=AnimType.FADE,
        mode=AnimMode.INFINITE,
        duration_s=1.0,
    ),

    "Pulsing (Scale)": Animation(
        type=AnimType.PULSE,
        mode=AnimMode.INFINITE,
        duration_s=0.6,
        scale_from=1.1,
    ),

    "Shake (Fixed)": Animation(
        type=AnimType.SHAKE,
        mode=AnimMode.FIXED,
        duration_s=0.5,
    ),

    "Shake (Infinite)": Animation(
        type=AnimType.SHAKE,
        mode=AnimMode.INFINITE,
        duration_s=0.2, # fast jitter
    ),

    "Spin (Infinite)": Animation(
        type=AnimType.ROTATE,
        mode=AnimMode.INFINITE,
        duration_s=2.0,
    ),

    "Typewriter": Animation(
        type=AnimType.TYPEWRITER,
        mode=AnimMode.FIXED,
        duration_s=2.0,
    ),
}

# =====================================================
# OUT ANIMATION PRESETS
# =====================================================

OUT_ANIMATION_PRESETS = {
    # ---------- None ----------
    "None": Animation(
        type=AnimType.NONE,
        mode=AnimMode.FIXED,
        duration_s=0.0,
    ),

    # ---------- Standard ----------
    "Fade Out": Animation(
        type=AnimType.FADE,
        mode=AnimMode.FIXED,
        duration_s=0.35,
    ),

    "Slide Out Right": Animation(
        type=AnimType.SLIDE_IN_RIGHT,
        mode=AnimMode.FIXED,
        duration_s=0.35,
    ),

    "Slide Out Left": Animation(
        type=AnimType.SLIDE_IN_LEFT,
        mode=AnimMode.FIXED,
        duration_s=0.35,
    ),

    "Slide Out Up": Animation(
        type=AnimType.SLIDE_IN_UP,
        mode=AnimMode.FIXED,
        duration_s=0.35,
    ),

    "Slide Out Down": Animation(
        type=AnimType.SLIDE_IN_DOWN,
        mode=AnimMode.FIXED,
        duration_s=0.35,
    ),

    "Spin Out": Animation(
        type=AnimType.ROTATE,
        mode=AnimMode.FIXED,
        duration_s=0.5,
    ),
}
