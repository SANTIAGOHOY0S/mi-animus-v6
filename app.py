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
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Intentamos conectar con el modelo Flash que ya vimos que te funciona
        model = genai.GenerativeModel('gemini-1.5-flash')
        st.sidebar.success("🛰️ Shaun conectado via: Gemini Flash")
    except Exception as e:
        st.sidebar.error(f"Error de enlace: {e}")

# --- 2. CARGA DEL MAPA DE DEPARTAMENTOS ---
geojson_path = "colombia.json"
geo_data = None
if os.path.exists(geojson_path):
    try:
        with open(geojson_path, encoding='utf-8') as f:
            geo_data = json.load(f)
    except: pass

# --- 3. BASE DE DATOS LOCAL ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 4. FUNCIÓN CEREBRO: SHAUN HASTINGS (MODO ESPAÑOL) ---
def obtener_reporte(ciudad, pais_nombre):
    if model:
        try:
            # Aquí forzamos el idioma Español en las instrucciones
            prompt = (
                f"Actúa como Shaun Hastings de Assassin's Creed. Dame un reporte táctico de {ciudad}, {pais_nombre}. "
                "Responde EXCLUSIVAMENTE en ESPAÑOL. Sé cínico, británico, muy inteligente y sarcástico. "
                "Máximo 300 caracteres."
            )
            response = model.generate_content(prompt)
            return response.text
        except:
            return "Error de enlace táctico. Shaun está ocupado con su té."
    return "IA fuera de línea."

# --- 5. PANEL LATERAL ---
st.sidebar.title("🦅 Sincronización Mundial")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad/Pueblo:")
    pais = st.text_input("País:", value="Colombia")
    depto_input = st.text_input("Departamento (MAYÚSCULAS para CO):").upper()
    
    if st.form_submit_button("Sincronizar Atalaya"):
        geoloc = Nominatim(user_agent="animus_v6_santiago")
        try:
            loc = geoloc.geocode(f"{nombre}, {pais}", timeout=10)
            if loc:
                info = obtener_reporte(nombre, pais)
                nuevo = pd.DataFrame([{"Nombre": nombre, "Pais": pais, "Depto": depto_input, "Lat": loc.latitude, "Lon": loc.longitude, "Info": info}])
                df = pd.concat([df, nuevo], ignore_index=True)
                df.to_csv(archivo_csv, index=False)
                st.rerun()
            else:
                st.error("Ubicación no encontrada.")
        except:
            st.error("Error de satélite.")

# --- 6. MAPA TÁCTICO ---
lat_ini = df['Lat'].iloc[-1] if not df.empty else 4.5
lon_ini = df['Lon'].iloc[-1] if not df.empty else -74.2

mapa = folium.Map(location=[lat_ini, lon_ini], zoom_start=4, tiles="CartoDB dark_matter")

if geo_data:
    conquistados = df[df['Pais'].str.lower() == 'colombia']['Depto'].unique().tolist()
    folium.GeoJson(
        geo_data,
        style_function=lambda feature: {
            'fillColor': '#ff4b4b' if feature['properties']['DPTO'] in conquistados else 'transparent',
            'color': '#444', 'weight': 1,
            'fillOpacity': 0.4 if feature['properties']['DPTO'] in conquistados else 0,
        }
    ).add_to(mapa)

for _, f in df.iterrows():
    # Popup mejorado para que no necesite tanto scroll
    html = f"""
    <div style="width: 330px; font-family: 'Courier New', Courier, monospace; color: #00ff00; background-color: #000; padding: 12px; border: 2px solid #ff4b4b; border-radius: 8px;">
        <b style="color: #ff4b4b;">> NODO: {f['Nombre'].upper()}</b><br>
        <hr style="border: 0.5px solid #333; margin: 8px 0;">
        <div style="font-size: 12px; line-height: 1.3; text-align: justify;">{f['Info']}</div>
        <div style="font-size: 9px; color: #555; margin-top: 10px; text-align: right;">[HASTINGS_DB_V6]</div>
    </div>
    """
    folium.Marker(
        [f['Lat'], f['Lon']], 
        popup=folium.Popup(folium.IFrame(html, width=350, height=190), max_width=350), 
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
    ).add_to(mapa)

st_folium(mapa, width="100%", height=600)
