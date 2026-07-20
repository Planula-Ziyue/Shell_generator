import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import struct
import base64
import html
import re
import os
import hashlib

try:
    import kaleido  # noqa: F401
    kaleido_available = True
except ImportError:
    kaleido_available = False

st.set_page_config(page_title="Mollusc Shell Generator", layout="wide")

# ============ Dark or Light or Matrix? ============
if "theme" not in st.session_state:
    st.session_state.theme = "dark" if st.get_option("theme.base") == "dark" else "light"
if "matrix_rain_enabled" not in st.session_state:
    st.session_state.matrix_rain_enabled = True

def toggle_theme(new_theme):
    st.session_state.theme = new_theme

font_family = 'Courier, "Courier New", monospace' if st.session_state.theme == "matrix" else "inherit"

matrix_background_css = ""

# 
@st.cache_data(show_spinner=False)
def get_matrix_rain_html():
    # A fixed seed keeps the cached markup stable across reruns.
    rng = np.random.default_rng(2025)
    char_bank = list("｡｢｣､･ｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ!#$%&()*+,-./:;<=>?@[]^_{|}~")
    # Keep the effect decorative: a few text nodes animated only with transform.
    # This is substantially cheaper than thousands of <br> nodes plus blur filters.
    total_columns = 30
    column_spans = []
    
    for idx in range(total_columns):
        left = rng.uniform(-8, 108)
        row_count = int(rng.integers(34, 58))
        chars_raw = rng.choice(char_bank, row_count)
        chars = "".join(html.escape(c) for c in chars_raw)
        
        if not chars:
            continue
        duration = rng.uniform(10.0, 17.0)
        delay = rng.uniform(-20.0, 0.0)
        intensity = rng.uniform(0.35, 0.9)
        depth_class = "matrix-column matrix-column--near" if rng.random() > 0.4 else "matrix-column matrix-column--far"
        
        column_spans.append(
            f"<span class=\"{depth_class}\" style=\"left:{left:.2f}vw; --duration:{duration:.2f}s; --delay:{delay:.2f}s; --intensity:{intensity:.2f};\">{chars}</span>"
        )
    
    streams_html = "".join(column_spans)
    
    matrix_overlay = f"""
    <style>
        body {{
            background-color: #010101 !important;
        }}
        .matrix-rain {{
            position: fixed;
            inset: 0;
            overflow: hidden;
            pointer-events: none;
            z-index: 0;
            background-color: #000;
            background-image:
                radial-gradient(circle at 20% 20%, rgba(0, 80, 0, 0.35), transparent 55%),
                radial-gradient(circle at 80% 0%, rgba(0, 120, 60, 0.35), transparent 55%),
                radial-gradient(circle at 70% 85%, rgba(0, 60, 40, 0.35), transparent 55%),
                linear-gradient(180deg, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.55) 100%);
        }}
        .matrix-column {{
            position: absolute;
            top: -80vh;
            writing-mode: vertical-rl;
            text-orientation: upright;
            white-space: nowrap;
            font-family: Courier, "Courier New", monospace;
            font-size: clamp(11px, 1.35vw, 20px);
            line-height: 1;
            letter-spacing: 0.02em;
            color: rgba(0, 255, 190, 0.55);
            text-shadow: 0 0 5px rgba(0,255,150,0.55);
            opacity: var(--intensity, 0.6);
            contain: layout paint style;
            will-change: transform;
            animation: matrixFall var(--duration, 12s) linear infinite;
            animation-delay: var(--delay, 0s);
        }}
        .matrix-column--far {{
            font-size: clamp(10px, 1.05vw, 16px);
            opacity: calc(var(--intensity, 0.6) * 0.45);
        }}
        @keyframes matrixFall {{
            from {{ transform: translate3d(0, -90vh, 0); }}
            to {{ transform: translate3d(0, 210vh, 0); }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            .matrix-column {{ animation: none; opacity: 0.18; }}
        }}
    </style>
    <div class="matrix-rain">
        {streams_html}
    </div>
    """
    return matrix_overlay

# ----------------------- End of Optimization -----------------------

if st.session_state.theme == "dark":
    bg_color     = "#000000"   
    text_color   = "#FFFFFF"   
    input_bg     = "#1A1A1A"   
    button_bg    = "#000000"
    button_hover = "#333333"
elif st.session_state.theme == "matrix":
    bg_color     = "rgba(0, 0, 0, 0.25)" if st.session_state.matrix_rain_enabled else "#050505"
    text_color   = "#00FF00"   
    input_bg     = "rgba(0, 26, 0, 0.85)"   
    button_bg    = "rgba(0, 0, 0, 0.9)"
    button_hover = "#003300"
    if not st.session_state.matrix_rain_enabled:
        matrix_background_css = """
        background-color: #000000 !important;
        background-image:
            radial-gradient(circle at 20% 20%, rgba(0, 80, 0, 0.35), transparent 55%),
            radial-gradient(circle at 80% 0%, rgba(0, 120, 60, 0.35), transparent 55%),
            radial-gradient(circle at 70% 85%, rgba(0, 60, 40, 0.35), transparent 55%),
            linear-gradient(180deg, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.55) 100%) !important;
        """
else:
    bg_color     = "#FFFFFF"   
    text_color   = "#000000"  
    input_bg     = "#F0F0F0"
    button_bg    = "#FFFFFF"
    button_hover = "#E0E0E0"

text_glow_css = "text-shadow: 0 0 6px #00FF00, 0 0 14px #00FF00 !important;" if st.session_state.theme == "matrix" else ""

# ============ Main region ============
st.markdown(f"""
<style>
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], 
    .stApp > div, section.main, .block-container, .stMarkdown {{
        background: {bg_color} !important;
        color: {text_color} !important;
        font-family: {font_family} !important;
        {text_glow_css}
        {matrix_background_css}
    }}

    h1, h2, h3, h4, h5, h6, p, label,
    .stMarkdown, .stCaption, .stExpander, 
    [data-testid="caption"], [data-testid="stMetricLabel"] {{
        color: {text_color} !important;
        font-family: {font_family} !important;
        {text_glow_css}
    }}

    input, textarea, select, button,
    [data-baseweb="select"], [data-baseweb="slider"],
    .js-plotly-plot text {{
        font-family: {font_family} !important;
    }}

    .stExpander > div > div > div > div {{
        color: {text_color} !important;
    }}
    .stExpander png {{
        fill: {bg_color} !important;
        color: {bg_color} !important;
    }}


    .stExpander {{
        background: {bg_color} !important;
    }}
    .stExpander > details {{
        background: {bg_color} !important;
        border: 1px solid {text_color}30 !important;
    }}
    .stExpander > details:hover {{
        background: {bg_color} !important;
    }}
    .stExpander > details > summary {{
        background: {bg_color} !important;
        color: {text_color} !important;
    }}
    .stExpander > details[open] {{
        background: {bg_color} !important;
    }}
    .stExpander > details > div {{
        background: {bg_color} !important;
        color: {text_color} !important;
    }}


    input, textarea, select, 
    .stNumberInput > div > input,
    [data-baseweb="select"] > div {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 3px solid {text_color}30 !important;
        {text_glow_css}
    }}


    button, .stButton > button, .stDownloadButton > button {{
        background-color: {button_bg} !important;
        color: {text_color} !important;
        border: 1px solid {text_color}60 !important;
        {text_glow_css}
    }}
    button:hover, .stButton > button:hover, .stDownloadButton > button:hover {{
        background-color: {button_hover} !important;
        border-color: {text_color} !important;
    }}


    .js-plotly-plot .plotly, .plot-container, .modebar {{
        background: {bg_color} !important;
    }}


    [data-testid="stFileUploaderDropzone"] {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px dashed {text_color}60 !important;
    }}
    [data-testid="stFileUploaderDropzone"] > small {{
        color: {text_color} !important;
    }}
    [data-testid="stFileUploaderDropzone"] > div > small {{
        color: {text_color} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ============ sidebar ============
st.markdown(f"""
<style>
    [data-testid="stSidebar"], .sidebar .sidebar-content {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        {text_glow_css}
    }}

    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {{
        color: {text_color} !important;
        {text_glow_css}
    }}

    [data-testid="stSidebar"] button[kind="secondary"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        border: 1px solid {text_color}60 !important;
        {text_glow_css}
    }}
    [data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background-color: {button_hover} !important;
        border-color: {text_color} !important;
    }}

    [data-testid="stSidebar"] .stSlider {{
        color: {text_color} !important;
    }}
    [data-testid="stSidebar"] .stSlider > div > div {{
        background-color: {text_color}40 !important;
    }}
    [data-testid="stSidebar"] .stSlider > div > div > div[role="slider"] {{
        background-color: {text_color} !important;
        border: 2px solid {bg_color} !important;
    }}

    [data-testid="stSidebar"] [data-testid="stColorPicker"] > div {{
        background-color: {input_bg} !important;
        border: 1px solid {text_color}30 !important;
    }}

    [data-testid="stHeader"] {{
        background-color: {bg_color} !important;
    }}
    [data-testid="stAppViewContainer"] > div:first-child {{
        background-color: {bg_color} !important;
    }}

    [data-testid="stSidebar"] .stSlider > div > div > div[role="slider"] {{
        background-color: {text_color} !important;   /* 滑块圆点：黑夜白 / 白天黑 */
        border: 2px solid {bg_color} !important;
        box-shadow: 0 0 8px {text_color}40 !important;
    }}
    [data-testid="stSidebar"] .stSlider > div > div > div[role="slider"]:focus {{
        box-shadow: 0 0 0 3px {text_color}60 !important;
    }}
    
    [data-testid="stSidebar"] .stSlider > div > div {{
        background: transparent !important;
    }}
    [data-testid="stSidebar"] .stSlider > div > div::before,
    [data-testid="stSidebar"] .stSlider > div > div::after {{
        background: {text_color}30 !important;   /* 轨道细线：淡淡黑白 */
    }}

    /* Hide file uploader default texts */
    [data-testid="stFileUploader"] small {{
        display: none !important;
    }}
    section[data-testid="stFileUploader"] p {{
        display: none !important;
    }}
    
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
        border: 1px dashed {text_color}60 !important;
    }}

    [data-testid="stSidebar"] .stRadio > div > label > div:first-child {{
        background-color: {bg_color} !important;
        border: 1px solid {text_color}60 !important;
    }}
    [data-testid="stSidebar"] .stRadio > div > label > input:checked ~ div:first-child {{
        box-shadow: inset 0 0 0 0.35rem {text_color} !important;
        background-color: {bg_color} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ============ code rain ============
if st.session_state.theme == "matrix" and st.session_state.matrix_rain_enabled:
    matrix_overlay = get_matrix_rain_html()
    st.markdown(matrix_overlay, unsafe_allow_html=True)
    
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebar"] .stSlider > div > div,
            .stSlider > div > div {{
                background: linear-gradient(90deg, rgba(0,255,120,0.15), rgba(0,255,120,0.05)) !important;
                border-radius: 999px !important;
            }}
            [data-testid="stSidebar"] .stSlider > div > div::before,
            [data-testid="stSidebar"] .stSlider > div > div::after,
            .stSlider > div > div::before,
            .stSlider > div > div::after {{
                background: rgba(0,255,120,0.35) !important;
            }}
            [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div:first-child,
            .stSlider [data-baseweb="slider"] > div:first-child {{
                background: linear-gradient(90deg, rgba(0,255,120,0.12), rgba(0,255,120,0.05)) !important;
                border-radius: 999px !important;
            }}
            [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div:nth-child(2),
            .stSlider [data-baseweb="slider"] > div:nth-child(2),
            [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div:nth-child(3),
            .stSlider [data-baseweb="slider"] > div:nth-child(3) {{
                background: rgba(0,255,120,0.15) !important;
                border-radius: 999px !important;
            }}
            [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] > div:first-child > div,
            .stSlider [data-baseweb="slider"] > div:first-child > div {{
                background-color: rgba(0,255,150,0.65) !important;
            }}
            [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"],
            .stSlider [data-baseweb="slider"] [role="slider"],
            [data-testid="stSidebar"] .stSlider > div > div > div[role="slider"],
            .stSlider > div > div > div[role="slider"] {{
                background-color: #00ff99 !important;
                border: 2px solid rgba(0,20,0,0.9) !important;
                box-shadow: 0 0 12px rgba(0,255,150,0.75), inset 0 0 2px rgba(0,0,0,0.6) !important;
            }}
            [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"]:focus,
            .stSlider [data-baseweb="slider"] [role="slider"]:focus {{
                box-shadow: 0 0 16px rgba(0,255,200,0.95), 0 0 3px rgba(0,255,150,0.9) inset !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
# ----------------------- function -----------------------
def frenet_frame(t, b, d, z):
    denom = np.sqrt((b**2 + 1) * d**2 + b**2 * z**2)
    xi1 = (1 / denom) * np.array([
        d * (b * np.sin(t) + np.cos(t)),
        d * (b * np.cos(t) - np.sin(t)),
        b * z
    ])
    xi2 = 1/np.sqrt(b**2 + 1) * np.array([
        b*np.cos(t) - np.sin(t),
        -b*np.sin(t) - np.cos(t),
        0
    ])
    denom3 = np.sqrt((b**2 + 1) * ((b**2 + 1)*d**2 + b**2*z**2))
    xi3 = 1/denom3 * np.array([
        b*z*(b*np.sin(t)+np.cos(t)),
        b*z*(b*np.cos(t)-np.sin(t)),
        -d*(b**2 + 1)
    ])
    return xi1, xi2, xi3

def rotation_matrix_psi(psi):
    return np.array([[np.cos(psi), -np.sin(psi), 0],
                     [np.sin(psi),  np.cos(psi), 0],
                     [0,          0,         1]])

def rotation_matrix_delta(delta):
    return np.array([[np.cos(delta), 0, np.sin(delta)],
                     [0, 1, 0],
                     [-np.sin(delta), 0, np.cos(delta)]])

def generating_curve(theta, a, phi, psi, delta, xi1, xi2, xi3):
    u = a*np.sin(theta)*np.cos(phi) + np.cos(theta)*np.sin(phi)
    v = a*np.sin(theta)*np.sin(phi) - np.cos(theta)*np.cos(phi)
    local_vec = np.array([0, u, v])
    rot_delta = rotation_matrix_delta(delta)
    local_rot = rot_delta @ local_vec
    rot_psi = rotation_matrix_psi(psi)
    local_rot2 = rot_psi @ local_rot
    return local_rot2[0]*xi1 + local_rot2[1]*xi2 + local_rot2[2]*xi3

def model(t, theta, b, d, z, a, phi, psi, delta, m1=0, n1=0, m2=0, n2=0):
    gamma = np.exp(b * t) * np.array([d*np.sin(t), d*np.cos(t), z])
    xi1, xi2, xi3 = frenet_frame(t, b, d, z)
    s = np.exp(b * t) - 1/(t + 1 + 1e-6)
    if m2 and n2: s *= (1 + m2 * np.sin(n2 * t))
    c_base = generating_curve(theta, a, phi, psi, delta, xi1, xi2, xi3)
    c = (1 + m1*np.sin(n1*theta))*s*c_base if m1 and n1 else s*c_base
    return gamma + c

@st.cache_data(show_spinner=False, max_entries=32)
def compute_shell_geometry(b, d, z, a, phi, psi, delta, m1, n1, m2, n2,
                           num_turns, t_count=180, theta_count=70):
    """Compute the complete shell with NumPy broadcasting instead of Python loops."""
    t = np.linspace(0.0, num_turns * 2.0 * np.pi, t_count)
    theta = np.linspace(0.0, 2.0 * np.pi, theta_count, endpoint=False)

    sin_t, cos_t = np.sin(t), np.cos(t)
    exp_bt = np.exp(b * t)
    gamma = exp_bt[:, None] * np.column_stack((d * sin_t, d * cos_t, np.full_like(t, z)))

    denom = np.maximum(np.sqrt((b**2 + 1.0) * d**2 + b**2 * z**2), 1e-12)
    xi1 = np.column_stack((
        d * (b * sin_t + cos_t) / denom,
        d * (b * cos_t - sin_t) / denom,
        np.full_like(t, b * z / denom),
    ))
    xi2_scale = 1.0 / np.sqrt(b**2 + 1.0)
    xi2 = np.column_stack((
        (b * cos_t - sin_t) * xi2_scale,
        (-b * sin_t - cos_t) * xi2_scale,
        np.zeros_like(t),
    ))
    denom3 = np.maximum(np.sqrt((b**2 + 1.0) * ((b**2 + 1.0) * d**2 + b**2 * z**2)), 1e-12)
    xi3 = np.column_stack((
        b * z * (b * sin_t + cos_t) / denom3,
        b * z * (b * cos_t - sin_t) / denom3,
        np.full_like(t, -d * (b**2 + 1.0) / denom3),
    ))
    basis = np.stack((xi1, xi2, xi3), axis=1)  # (t, local-axis, xyz)

    sin_theta, cos_theta = np.sin(theta), np.cos(theta)
    u = a * sin_theta * np.cos(phi) + cos_theta * np.sin(phi)
    v = a * sin_theta * np.sin(phi) - cos_theta * np.cos(phi)
    local = np.column_stack((np.zeros_like(theta), u, v))
    local = local @ rotation_matrix_delta(delta).T
    local = local @ rotation_matrix_psi(psi).T
    curve = np.einsum("ok,tkc->otc", local, basis, optimize=True)

    scale_t = exp_bt - 1.0 / (t + 1.0 + 1e-6)
    if m2 and n2:
        scale_t *= 1.0 + m2 * np.sin(n2 * t)
    scale_theta = 1.0 + m1 * np.sin(n1 * theta) if m1 and n1 else np.ones_like(theta)
    points = gamma[None, :, :] + curve * scale_theta[:, None, None] * scale_t[None, :, None]
    return t, theta, points[:, :, 0], points[:, :, 1], points[:, :, 2]

@st.cache_data(show_spinner=False, max_entries=16)
def compute_inner_surface(X, Y, Z, theta_step, t_step, thickness):
    dX_dtheta, dX_dt = np.gradient(X, theta_step, t_step)
    dY_dtheta, dY_dt = np.gradient(Y, theta_step, t_step)
    dZ_dtheta, dZ_dt = np.gradient(Z, theta_step, t_step)
    normals = np.cross(
        np.stack((dX_dtheta, dY_dtheta, dZ_dtheta), axis=-1),
        np.stack((dX_dt, dY_dt, dZ_dt), axis=-1),
    )
    normals /= np.maximum(np.linalg.norm(normals, axis=-1, keepdims=True), 1e-12)
    if np.mean(X) > 0:
        normals *= -1.0
    return X - thickness * normals[..., 0], Y - thickness * normals[..., 1], Z - thickness * normals[..., 2]

def wireframe_coordinates(X, Y, Z):
    """Join the whole grid into one WebGL trace using NaN separators."""
    def joined(values):
        rows = np.pad(values, ((0, 0), (0, 1)), constant_values=np.nan).ravel()
        columns = np.pad(values.T, ((0, 0), (0, 1)), constant_values=np.nan).ravel()
        return np.concatenate((rows, columns))
    return joined(X), joined(Y), joined(Z)

@st.cache_data(show_spinner=False, max_entries=16)
def build_binary_stl(X, Y, Z, inner_X=None, inner_Y=None, inner_Z=None):
    """Build all STL triangles and normals in vectorized form."""
    outer_vertices = np.stack((X, Y, Z), axis=-1).reshape(-1, 3).astype("<f4")
    ntheta, nt = X.shape
    i, j = np.meshgrid(np.arange(ntheta), np.arange(nt - 1), indexing="ij")
    i1 = (i + 1) % ntheta
    a_idx = i * nt + j
    b_idx = a_idx + 1
    c_idx = i1 * nt + j
    d_idx = c_idx + 1
    outer_faces = np.stack((
        np.stack((a_idx, b_idx, d_idx), axis=-1),
        np.stack((a_idx, d_idx, c_idx), axis=-1),
    ), axis=-2).reshape(-1, 3)

    vertices = outer_vertices
    faces = outer_faces
    if inner_X is not None:
        inner_vertices = np.stack((inner_X, inner_Y, inner_Z), axis=-1).reshape(-1, 3).astype("<f4")
        offset = len(outer_vertices)
        inner_faces = np.stack((
            np.stack((a_idx + offset, d_idx + offset, b_idx + offset), axis=-1),
            np.stack((a_idx + offset, c_idx + offset, d_idx + offset), axis=-1),
        ), axis=-2).reshape(-1, 3)
        vertices = np.vstack((outer_vertices, inner_vertices))
        faces = np.vstack((outer_faces, inner_faces))

    triangles = vertices[faces]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    valid = lengths > 1e-12
    normals[valid] /= lengths[valid, None]
    normals[~valid] = (0.0, 0.0, 1.0)

    records = np.empty(len(faces), dtype=[
        ("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")
    ])
    records["normal"] = normals
    records["vertices"] = triangles
    records["attribute"] = 0
    header = b"Mollusc shell generated by Ziyue Xu @ HKUST - 2025".ljust(80, b" ")
    return header + struct.pack("<I", len(faces)) + records.tobytes()

@st.cache_data(show_spinner=False, max_entries=8)
def export_png(fig_json):
    if not kaleido_available:
        return None, "PNG export requires the kaleido package (`pip install -U kaleido`)."
    try:
        export_fig = pio.from_json(fig_json)
        export_fig.update_layout(
            scene=dict(bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False),
                       yaxis=dict(visible=False), zaxis=dict(visible=False)),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            width=2000, height=2000,
        )
        return export_fig.to_image(format="png", engine="kaleido"), None
    except Exception as err:
        return None, f"PNG export failed: {err}"

# ----------------------- default -----------------------
defaults = {"b":0.10, "d":1.0, "z":1.0, "a":1.0, "phi_deg":0.0, "psi_deg":0.0, "delta_deg":0.0,
            "m1":0.0, "n1":0, "m2":0.0, "n2":0, "num_turns":5.0,
            "render_mode": "Surface",
            "side_light_intensity": 1.0, "surface_opacity": 1.0}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

if "show_theory" not in st.session_state:
    st.session_state.show_theory = False

if "show_spiral" not in st.session_state:
    st.session_state.show_spiral = False

if "show_frenet" not in st.session_state:
    st.session_state.show_frenet = False

if "show_grid" not in st.session_state:
    st.session_state.show_grid = True

st.title("Mollusc Shell 3D Generator")

# ----------------------- SIDE BAR-----------------------
with st.sidebar:
    col1, col2, col3 = st.sidebar.columns([1,1,1])
    with col1:
        if st.button("Night", use_container_width=True):
            toggle_theme("dark")
            st.rerun()
    with col2:
        if st.button("Day", use_container_width=True):
            toggle_theme("light")
            st.rerun()
    with col3:
        if st.button("Matrix", use_container_width=True):
            toggle_theme("matrix")
            st.rerun()
    if st.session_state.theme == "matrix":
        rain_label = "Code Rain: ON" if st.session_state.matrix_rain_enabled else "Code Rain: OFF"
        if st.button(rain_label, use_container_width=True):
            st.session_state.matrix_rain_enabled = not st.session_state.matrix_rain_enabled
            st.rerun()
    sidecol1, sidecol2 = st.sidebar.columns([1,2])
    with sidecol1:
        shell_color = st.color_picker("**Color**", "#DCDCDC")
    with sidecol2:
        thickness = st.number_input("**Thickness (mm)**", 0.0, 10.0, 0.0, 0.05, key="thickness")
    st.markdown("**Render Mode**")
    render_mode = st.radio(
        label="render_mode",
        options=["Surface", "Wireframe", "Points"],
        index=["Surface", "Wireframe", "Points"].index(st.session_state.render_mode),
        horizontal=True,
        label_visibility="collapsed",
        key="render_mode"
        )
    st.number_input("Opacity", min_value=0.0, max_value=1.0, step=0.1, key="surface_opacity")   
    if st.button("Show Logarithmic Spiral",use_container_width=True):
        st.session_state.show_spiral = not st.session_state.show_spiral
    if st.session_state.show_spiral:
        if st.button("Show Frenet-Serret Frame", use_container_width=True):
            st.session_state.show_frenet = not st.session_state.show_frenet

        
    grid_label = "Hide Grid" if st.session_state.show_grid else "Show Grid"
    if st.button(grid_label,use_container_width=True):
        st.session_state.show_grid = not st.session_state.show_grid

    st.markdown("**Overlay Image**")
    uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    if uploaded_file is not None:
        image_opacity = st.slider("Transparency", 0.0, 1.0, 0.5, 0.05)
        image_size = st.slider("Image Size (relative to canvas)", 0.1, 1.0, 0.5, 0.05)


    if st.sidebar.button("Read Mathematical Background",use_container_width=True):
        st.session_state.show_theory = not st.session_state.show_theory

def embed_images(md_content, base_dir):
    def replace_img(match):
        tag = match.group(0)
        src_match = re.search(r'src="([^"]+)"', tag, re.IGNORECASE)
        if src_match:
            src = src_match.group(1)
            if src.startswith('./assets/'):
                img_path = os.path.join(base_dir, src[2:])
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                    ext = os.path.splitext(src)[1][1:].lower()
                    if ext in ['jpg', 'jpeg', 'png', 'gif']:
                        new_src = f'data:image/{ext};base64,{img_data}'
                        new_tag = re.sub(r'src="[^"]+"', f'src="{new_src}"', tag, flags=re.IGNORECASE)
                        return new_tag
        return tag

    embedded = re.sub(r'<img[^>]*>', replace_img, md_content, flags=re.IGNORECASE | re.DOTALL)
    return embedded

if not st.session_state.show_theory:
    # ----------------------- Left and right -----------------------
    left_col, right_col = st.columns([1,1.2])

    with left_col:
        # parameter estimation from measurement
        with st.expander("Estimate from measurements", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                p = st.number_input("p (inner chord)", 1.0, step=0.1, key="p")
                q = st.number_input("q (outer chord)", 3.0, step=0.1, key="q")
                if q > p:
                    b_calc = (np.log(q)-np.log(p))/(2*np.pi)
                    st.success(f"b ≈ {b_calc:.5f}")
            with c2:
                w = st.number_input("w (width)", min_value=0.1, value=3.0, step=0.1, key="w")
                h = st.number_input("h (height)", min_value=0.1, value=2.0, step=0.1, key="h_ap")  
                a_calc = w/h
                st.success(f"a ≈ {a_calc:.4f}")

            c1, c2 = st.columns(2)
            with c1:
                he = st.number_input("hₑ (later)", min_value=0.1, value=2.0, step=0.1, key="he")
                hi = st.number_input("hᵢ (earlier)", min_value=0.1, value=0.5, step=0.1, key="hi")
                if abs(he-hi)>1e-6:
                    z_calc = (he+hi)/(he-hi) if he>hi else -(he+hi)/(hi-he)
                    st.success(f"z ≈ {z_calc:.4f}")
            with c2:
                re = st.number_input("rₑ (outer)", value=5.0, step=0.1, key="re")
                ri = st.number_input("rᵢ (inner)", value=1.0, step=0.1, key="ri")
                if re > ri:
                    d_calc = (re+ri)/(re-ri) * a_calc
                    st.success(f"d ≈ {d_calc:.4f}")

            if st.button("Apply estimates", use_container_width=True):
                st.session_state.b = b_calc
                st.session_state.a = a_calc
                st.session_state.z = z_calc
                st.session_state.d = d_calc
                st.success("Applied!")
                st.rerun()

        st.markdown("**Fine-tune parameters**")
        c1, c2 = st.columns(2)
        with c1:
            st.number_input("b (expansion)", min_value=0.0, step=0.01, format="%.4f", key="b")
            st.number_input("d (displacement)", min_value=0.0, step=0.01, format="%.4f", key="d")
            st.number_input("z (transition)", step=0.01, format="%.4f", key="z")
            st.number_input("a (ellipticity, w/h ratio)", min_value=0.0, step=0.01, format="%.4f", key="a")
            st.number_input("φ tan. rot. [°]", -90.0, 90.0, step=1.0, key="phi_deg")
            st.number_input("δ normal rot. [°]", -90.0, 90.0, step=1.0, key="delta_deg")
        with c2:
            st.number_input("ψ binormal rot. [°]", 0.0, 90.0, step=1.0, key="psi_deg")
            st.number_input("m1 (curve osc. amp.) [0,+∞)", 0.0, step=0.01, format="%.3f", key="m1")
            st.number_input("n1 (curve osc. freq.)", 0.0, step=1.0, key="n1")
            st.number_input("m2 (radius osc. amp.) [0,+∞)", 0.0, step=0.01, format="%.3f", key="m2")
            st.number_input("n2 (radius osc. freq.)", 0.0, step=1.0, key="n2")
            st.number_input("Number of Turns", 0.01, 20.0, step=0.5, key="num_turns")

        generate = True

    # ----------------------- RIGHT -----------------------
    with right_col:
        if generate:
            with st.spinner("Generating..."):
                phi = np.deg2rad(st.session_state.phi_deg)
                psi = np.deg2rad(st.session_state.psi_deg)
                delta = np.deg2rad(st.session_state.delta_deg)
                # Reverse the direction by negating z without changing the input
                z_used = -st.session_state.z
                t, theta, X, Y, Z = compute_shell_geometry(
                    st.session_state.b, st.session_state.d, z_used,
                    st.session_state.a, phi, psi, delta,
                    st.session_state.m1, st.session_state.n1,
                    st.session_state.m2, st.session_state.n2,
                    st.session_state.num_turns,
                )

                inner_X = inner_Y = inner_Z = None
                if thickness > 0:
                    inner_X, inner_Y, inner_Z = compute_inner_surface(
                        X, Y, Z, theta[1] - theta[0], t[1] - t[0], thickness
                    )

                # Plotly 
                fig = go.Figure()
                render_mode = st.session_state.render_mode
                if render_mode == "Surface":
                    fig.add_trace(go.Surface(x=X, y=Y, z=Z,
                                            colorscale=[[0, shell_color], [1, shell_color]],
                                            showscale=False,
                                            lighting=dict(ambient=0.7, diffuse=0.8, specular=0.1),
                                            lightposition=dict(x=-1e5, y=0, z=-50),
                                            opacity=st.session_state.surface_opacity))
                    if thickness > 0:
                        fig.add_trace(go.Surface(x=inner_X, y=inner_Y, z=inner_Z,
                                                colorscale=[[0, shell_color], [1, shell_color]],
                                                opacity=0.65, showscale=False,
                                                lighting=dict(ambient=0.7, diffuse=0.8, specular=0.1),
                                                lightposition=dict(x=-1e5, y=0, z=-50)))
                elif render_mode == "Wireframe":
                    wire_x, wire_y, wire_z = wireframe_coordinates(X, Y, Z)
                    fig.add_trace(go.Scatter3d(
                        x=wire_x, y=wire_y, z=wire_z, mode="lines",
                        line=dict(color=shell_color, width=1), showlegend=False,
                    ))
                    if thickness > 0:
                        wire_x, wire_y, wire_z = wireframe_coordinates(inner_X, inner_Y, inner_Z)
                        fig.add_trace(go.Scatter3d(
                            x=wire_x, y=wire_y, z=wire_z, mode="lines",
                            line=dict(color=shell_color, width=1), showlegend=False,
                        ))
                elif render_mode == "Points":
                    fig.add_trace(go.Scatter3d(x=X.flatten(), y=Y.flatten(), z=Z.flatten(), mode='markers', marker=dict(size=1, color=shell_color), showlegend=False))
                    if thickness > 0:
                        fig.add_trace(go.Scatter3d(x=inner_X.flatten(), y=inner_Y.flatten(), z=inner_Z.flatten(), mode='markers', marker=dict(size=1, color=shell_color), showlegend=False))


                if st.session_state.show_spiral:
                    gamma_x = np.exp(st.session_state.b * t) * st.session_state.d * np.sin(t)
                    gamma_y = np.exp(st.session_state.b * t) * st.session_state.d * np.cos(t)
                    gamma_z = np.exp(st.session_state.b * t) * z_used
                    if st.session_state.theme == "light":
                        spiral_color = "#000000"  # 黑色
                    elif st.session_state.theme == "dark":
                        spiral_color = "#FFFFFF"  # 白色
                    else:  # matrix
                        spiral_color = "#00FF00"  # 绿色
                    fig.add_trace(go.Scatter3d(x=gamma_x, y=gamma_y, z=gamma_z, mode='lines', line=dict(color=spiral_color, width=4), name="Logarithmic Spiral"))


                    if st.session_state.show_frenet:
                        t_end = t[-1]
                        gamma_end = np.exp(st.session_state.b * t_end) * np.array([st.session_state.d * np.sin(t_end), st.session_state.d * np.cos(t_end), z_used])
                        xi1, xi2, xi3 = frenet_frame(t_end, st.session_state.b, st.session_state.d, z_used)
                        scale = np.exp(st.session_state.b * t_end) * 0.5  # 调整规模以匹配大小
                        vectors = [xi1, xi2, xi3]
                        labels = ["T", "N", "B"]
                        if st.session_state.theme == "light":
                            colors = ['#8B0000', '#00008B', '#006400']  # 深红、深蓝、深绿
                        elif st.session_state.theme == "dark":
                            colors = ['#FF4500', '#ADD8E6', '#90EE90']  # 橙红、浅蓝、浅绿
                        else:  # matrix
                            colors = ['#00FF00', '#00CC00', '#009900']  # 不同绿色调
                        arrow_length = scale * 0.1
                        angle = 30 * np.pi / 180
                        for vec, label, color in zip(vectors, labels, colors):
                            vec_norm = vec / np.linalg.norm(vec) if np.linalg.norm(vec) > 0 else vec
                            end_point = gamma_end + scale * vec_norm
                            x = [gamma_end[0], end_point[0]]
                            y = [gamma_end[1], end_point[1]]
                            z = [gamma_end[2], end_point[2]]
                            fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color=color, width=5), showlegend=False))
                            # 计算垂直向量
                            if abs(vec_norm[0]) > 0.1 or abs(vec_norm[1]) > 0.1:
                                perp1 = np.array([-vec_norm[1], vec_norm[0], 0])
                            else:
                                perp1 = np.array([0, -vec_norm[2], vec_norm[1]])
                            perp1 /= np.linalg.norm(perp1) if np.linalg.norm(perp1) > 0 else 1
                            back_vec = -vec_norm * arrow_length * np.cos(angle)
                            side = arrow_length * np.sin(angle)
                            # barb1
                            bx1 = [end_point[0], end_point[0] + back_vec[0] + side * perp1[0]]
                            by1 = [end_point[1], end_point[1] + back_vec[1] + side * perp1[1]]
                            bz1 = [end_point[2], end_point[2] + back_vec[2] + side * perp1[2]]
                            fig.add_trace(go.Scatter3d(x=bx1, y=by1, z=bz1, mode='lines', line=dict(color=color, width=3), showlegend=False))
                            # barb2
                            bx2 = [end_point[0], end_point[0] + back_vec[0] - side * perp1[0]]
                            by2 = [end_point[1], end_point[1] + back_vec[1] - side * perp1[1]]
                            bz2 = [end_point[2], end_point[2] + back_vec[2] - side * perp1[2]]
                            fig.add_trace(go.Scatter3d(x=bx2, y=by2, z=bz2, mode='lines', line=dict(color=color, width=3), showlegend=False))

                            fig.add_trace(go.Scatter3d(x=[end_point[0]], y=[end_point[1]], z=[end_point[2]], mode='text', text=[label], textfont=dict(color=color, size=14), showlegend=False))

                plot_bg = "#000000" if st.session_state.theme in ["dark", "matrix"] else "white"
                grid_color = "#444444" if st.session_state.theme in ["dark", "matrix"] else "#E5E5E5"
                show_grid = st.session_state.show_grid
                fig.update_layout(
                    font=dict(family=font_family),
                    uirevision="shell-camera-v1",
                    scene=dict(aspectmode='data',
                               camera={'eye': {'x': 1.25, 'y': 1.25, 'z': 1.25}},
                               bgcolor=plot_bg,
                               xaxis=dict(backgroundcolor="rgba(0,0,0,0)" if not show_grid else plot_bg,
                                          showbackground=show_grid,
                                          gridcolor=grid_color if show_grid else "rgba(0,0,0,0)",
                                          showgrid=show_grid,
                                          showline=show_grid,
                                          ticks='' if not show_grid else 'outside',
                                          showticklabels=show_grid,
                                          zeroline=show_grid,
                                          zerolinecolor=grid_color if show_grid else "rgba(0,0,0,0)",
                                          title=None,
                                          visible=show_grid),
                               yaxis=dict(backgroundcolor="rgba(0,0,0,0)" if not show_grid else plot_bg,
                                          showbackground=show_grid,
                                          gridcolor=grid_color if show_grid else "rgba(0,0,0,0)",
                                          showgrid=show_grid,
                                          showline=show_grid,
                                          ticks='' if not show_grid else 'outside',
                                          showticklabels=show_grid,
                                          zeroline=show_grid,
                                          zerolinecolor=grid_color if show_grid else "rgba(0,0,0,0)",
                                          title=None,
                                          visible=show_grid),
                               zaxis=dict(backgroundcolor="rgba(0,0,0,0)" if not show_grid else plot_bg,
                                          showbackground=show_grid,
                                          gridcolor=grid_color if show_grid else "rgba(0,0,0,0)",
                                          showgrid=show_grid,
                                          showline=show_grid,
                                          ticks='' if not show_grid else 'outside',
                                          showticklabels=show_grid,
                                          zeroline=show_grid,
                                          zerolinecolor=grid_color if show_grid else "rgba(0,0,0,0)",
                                          title=None,
                                          visible=show_grid)
                               ),
                               paper_bgcolor=plot_bg,
                               plot_bgcolor=plot_bg,
                               margin=dict(l=0, r=0, t=0, b=0),
                               height=550
                               )

                if uploaded_file is not None:
                    img_bytes = uploaded_file.read()
                    base64_img = base64.b64encode(img_bytes).decode('utf-8')
                    mime_type = uploaded_file.type
                    source = f"data:{mime_type};base64,{base64_img}"
                    fig.add_layout_image(
                        dict(
                            source=source,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            sizex=image_size,
                            sizey=image_size,
                            xanchor="center",
                            yanchor="middle",
                            opacity=image_opacity,
                            layer="above"
                        )
                    )

                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

                # STL is also vectorized; PNG is generated only when requested.
                stl_bytes = build_binary_stl(X, Y, Z, inner_X, inner_Y, inner_Z)
                fig_json = fig.to_json()
                png_signature = hashlib.sha256(fig_json.encode("utf-8")).hexdigest()
                if st.session_state.get("png_signature") != png_signature:
                    st.session_state.pop("png_bytes", None)
                    st.session_state.pop("png_error", None)

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="Download STL",
                        data=stl_bytes,
                        file_name="mollusc_shell.stl",
                        mime="model/stl",
                        use_container_width=True
                    )
                with col_dl2:
                    if st.button("Prepare PNG", use_container_width=True):
                        with st.spinner("Preparing PNG..."):
                            png_bytes, png_error = export_png(fig_json)
                        st.session_state.png_signature = png_signature
                        st.session_state.png_bytes = png_bytes
                        st.session_state.png_error = png_error
                    if st.session_state.get("png_bytes"):
                        st.download_button(
                            label="Download PNG",
                            data=st.session_state.png_bytes,
                            file_name="mollusc_shell.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    elif st.session_state.get("png_error"):
                        st.info(st.session_state.png_error)
        else:
            st.markdown("<div style='text-align:center; margin-top:250px; color:#666; font-size:1.3rem;'>"
                        "Adjust parameters on the left<br><br>"
                        "then click <strong>Generate Shell</strong></div>",
                        unsafe_allow_html=True)
else:
    try:
        base_dir = os.path.dirname(__file__)
        with open("Theory.md", "r", encoding="utf-8") as f:
            theory_content = f.read()
        theory_content = embed_images(theory_content, base_dir)
        st.markdown(theory_content, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("Theory.md file not found in the same directory.")

st.caption("App by Ziyue Xu, OCES, HKUST")
st.caption("Contact: Ziyue-Xu@outlook.com")
