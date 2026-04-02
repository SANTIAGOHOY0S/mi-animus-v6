import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import json
from geopy.geocoders import Nominatim

# --- 1. CONFIGURACIÓN DE IA ---
st.set_page_config(page_title="Animus OS V6", layout="wide")

model = None
if "GEMINI_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. CARGA DEL MAPA (GIST JOHN GUERRA) ---
geojson_path = "colombia.json"
geo_data = None
if os.path.exists(geojson_path):
    with open(geojson_path, encoding='utf-8') as f:
        geo_data = json.load(f)

# --- 3. BASE DE DATOS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Depto", "Lat", "Lon", "Info"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 4. FUNCIÓN SHAUN HASTINGS ---
def reporte_shaun(lugar):
    if model:
        prompt = f"Actúa como Shaun Hastings de AC. Reporte táctico de {lugar} (max 280 chars). Sé cínico y sarcástico."
        try:
            return model.generate_content(prompt).text
        except: return "Error de enlace táctico."
    return "Shaun fuera de línea."

# --- 5. PANEL LATERAL ---
if 'cg' not in st.session_state:
    st.session_state.cg = {"lat": 4.703, "lon": -74.030} # Bella Suiza por defecto

st.sidebar.title("🦅 Panel del Animus")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad/Lugar:")
    depto_input = st.text_input("Departamento (Escríbelo tal cual: Antioquia, Cundinamarca, etc.):")
    if st.form_submit_button("Sincronizar"):
        geoloc = Nominatim(user_agent="animus_v6")
        loc = geoloc.geocode(f"{nombre}, Colombia")
        if loc:
            info = reporte_shaun(nombre)
            nuevo = pd.DataFrame([{"Nombre": nombre, "Depto": depto_input, "Lat": loc.latitude, "Lon": loc.longitude, "Info": info}])
            df = pd.concat([df, nuevo], ignore_index=True)
            df.to_csv(archivo_csv, index=False)
            st.rerun()

# --- 6. MAPA TÁCTICO ---
mapa = folium.Map(location=[4.5708, -74.2973], zoom_start=6, tiles="CartoDB dark_matter")

# RESALTADO DE TERRITORIOS
if geo_data:
    deptos_conquistados = df['Depto'].unique().tolist()
    folium.GeoJson(
        geo_data,
        style_function=lambda feature: {
            'fillColor': '#ff4b4b' if feature['properties']['DPTO'] in deptos_conquistados else 'transparent',
            'color': '#444',
            'weight': 1,
            'fillOpacity': 0.4 if feature['properties']['DPTO'] in deptos_conquistados else 0,
        }
    ).add_to(mapa)

# PINES CON POPUP HORIZONTAL (ESTILO CONSOLA)
for _, f in df.iterrows():
    html = f"""
    <div style="width: 350px; font-family: 'Courier New', Courier, monospace; color: #00ff00; background-color: #000; padding: 15px; border: 2px solid #ff4b4b; border-radius: 8px;">
        <b style="font-size: 16px; color: #ff4b4b;">> UBICACIÓN: {f['Nombre'].upper()}</b><br>
        <hr style="border: 0.5px solid #333;">
        <p style="font-size: 13px; line-height: 1.5; text-align: justify;">{f['Info']}</p>
        <p style="font-size: 10px; color: #666; margin-top: 10px;">// REPORTE DE HASTINGS, S. //</p>
    </div>
    """
    iframe = folium.IFrame(html, width=380, height=220)
    popup = folium.Popup(iframe, max_width=380)
    
    folium.Marker([f['Lat'], f['Lon']], popup=popup, icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(mapa)

st_folium(mapa, width="100%", height=650)
