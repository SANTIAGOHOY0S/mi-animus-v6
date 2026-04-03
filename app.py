import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import requests
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DEL CEREBRO (GEMINI & CSS) ---
st.set_page_config(page_title="Animus OS V6 - Santiago", layout="wide")

# Parche CSS para eliminar las líneas blancas del mapa
st.markdown("""
    <style>
    .leaflet-tile { border: solid transparent 1px !important; }
    </style>
""", unsafe_allow_html=True)

if "ultima_transmision" not in st.session_state:
    st.session_state.ultima_transmision = None
    st.session_state.ultimo_nodo = None

model = None
if "GEMINI_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if modelos:
            modelo_elegido = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
            model = genai.GenerativeModel(modelo_elegido)
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

# --- 2. BASE DE DATOS DE CONQUISTAS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info", "Tipo"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

if "Tipo" not in df.columns:
    df["Tipo"] = "Nodo"

# --- 3. FUNCIÓN SHAUN HASTINGS ---
def obtener_reporte(ciudad, pais_nombre, tipo_nodo):
    if model:
        try:
            extra_info = f"Este lugar es un {tipo_nodo}."
            prompt = (
                f"Actúa como Shaun Hastings (Assassin's Creed). "
                f"Dame un reporte táctico de {ciudad}, {pais_nombre}. {extra_info} "
                "REGLAS OBLIGATORIAS: "
                "1. Responde SIEMPRE en ESPAÑOL. "
                "2. Sé extremadamente cínico, británico y sarcástico. "
                "3. Desarrolla la historia del lugar conectándola con una conspiración Templaria o de Abstergo. "
                "4. Da un análisis táctico para un Asesino (puntos de salto, peligros). "
                "5. DA UNA RECOMENDACIÓN TURÍSTICA sarcástica. "
                "6. Mínimo 3 párrafos sustanciosos."
            )
            seguridad = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            ]
            response = model.generate_content(prompt, safety_settings=seguridad)
            return response.text if response.text else "Nodo encriptado."
        except Exception as e:
            return f"Error de Sistema: {str(e)}"
    return "IA fuera de línea."

# --- 4. PANEL LATERAL: CENTRO DE MANDO ---
st.sidebar.title("🦅 Sincronización Táctica")

# Módulo de música microscópico (Pixel Espía)
youtube_html = """
<iframe width="1" height="1" 
src="https://www.youtube.com/embed/dQjRTP6ANkw?autoplay=1&loop=1&playlist=dQjRTP6ANkw" 
frameborder="0" allow="autoplay; encrypted-media"></iframe>
"""
with st.sidebar:
    st.caption("🎵 Frecuencia Ezio activada (Haz clic en la pantalla si no suena)")
    components.html(youtube_html, width=1, height=1)
    st.markdown("---")

with st.sidebar.form("atalaya"):
    nombre = st.text_input("Nombre del Punto (Barrio, U, Refugio...):")
    pais = st.text_input("País:", value="Colombia")
    
    tipo_nodo = st.selectbox("Categoría del Nodo:", 
                             ["Nodo Estándar", "Refugio (Amigos)", "Universidad", "Abandonado"])
    
    with st.expander("⚙️ Opciones Avanzadas (Coordenadas / CG)"):
        es_cg = st.checkbox("🛡️ Establecer como Cuartel General (CG)")
        st.caption("Si dejas esto vacío, se usará la búsqueda de Google:")
        lat_manual = st.text_input("Latitud Manual (Ej: 4.7030):")
        lon_manual = st.text_input("Longitud Manual (Ej: -74.030
