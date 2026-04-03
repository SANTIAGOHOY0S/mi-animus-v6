import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import json
import requests

# --- 1. CONFIGURACIÓN DEL CEREBRO (GEMINI) ---
st.set_page_config(page_title="Animus OS V6 - Santiago", layout="wide")

model = None
if "GEMINI_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if modelos:
            modelo_elegido = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
            model = genai.GenerativeModel(modelo_elegido)
            st.sidebar.success(f"🛰️ Shaun en línea ({modelo_elegido.split('/')[-1]})")
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

# --- 2. CARGA DE GEODATOS (COLOMBIA) ---
geojson_path = "colombia.json"
geo_data = None
if os.path.exists(geojson_path):
    with open(geojson_path, encoding='utf-8') as f:
        geo_data = json.load(f)

# --- 3. BASE DE DATOS DE CONQUISTAS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info", "Tipo"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# Asegurar que la columna 'Tipo' exista en bases de datos viejas
if "Tipo" not in df.columns:
    df["Tipo"] = "Nodo"

# --- 4. FUNCIÓN SHAUN HASTINGS (SIN CENSURA NI LÍMITES) ---
def obtener_reporte(ciudad, pais_nombre):
    if model:
        try:
            prompt = (
                f"Actúa como Shaun Hastings (Assassin's Creed). "
                f"Dame un reporte táctico y geográfico DETALLADO de {ciudad}, {pais_nombre}. "
                "REGLAS OBLIGATORIAS: "
                "1. Responde SIEMPRE en ESPAÑOL. "
                "2. Sé extremadamente cínico, británico y sarcástico. "
                "3. Desarrolla la historia del lugar conectándola profundamente con una conspiración de los Templarios, Abstergo o los nazis. "
                "4. Da un análisis táctico del terreno para un Asesino (puntos de salto, escondites, peligros). "
                "5. DA UNA RECOMENDACIÓN TURÍSTICA sarcástica. "
                "6. Mínimo 3 párrafos sustanciosos. No te guardes información."
            )
            seguridad = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            ]
            response = model.generate_content(prompt, safety_settings=seguridad)
            return response.text if response.text else "Nodo encriptado por Abstergo."
        except Exception as e:
            return f"Error de Sistema: {str(e)}"
    return "IA fuera de línea."

# --- 5. PANEL LATERAL: SINCRONIZACIÓN MUNDIAL ---
st.sidebar.title("🦅 Centro de Mando")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad, Barrio o Punto de Interés:")
    pais = st.text_input("País:", value="Colombia")
    es_cg = st.checkbox("🛡️ Establecer como Cuartel General (CG)")
    
    if st.form_submit_button("Sincronizar Atalaya"):
        if "MAPS_KEY" in st.secrets:
            api_key = st.secrets["MAPS_KEY"]
            url =
