import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import json
from geopy.geocoders import Nominatim

# --- 1. CONFIGURACIÓN DE IA (ESTABLECIENDO ENLACE) ---
st.set_page_config(page_title="Animus OS V6", layout="wide")

# Inicializamos la variable del modelo para evitar el NameError
model = None

if "GEMINI_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Intentamos detectar modelos disponibles
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if modelos:
            # Elegimos Flash si está disponible, si no el primero de la lista
            model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
            model = genai.GenerativeModel(model_name)
            st.sidebar.success(f"🛰️ Shaun conectado via: {model_name.split('/')[-1]}")
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")
else:
    st.sidebar.warning("🔑 No se detectó GEMINI_KEY en Secrets.")

# --- 2. CARGA DEL MAPA DE DEPARTAMENTOS (COLOMBIA) ---
geojson_path = "colombia.json"
geo_data = None
if os.path.exists(geojson_path):
    try:
        with open(geojson_path, encoding='utf-8') as f:
            geo_data = json.load(f)
    except:
        st.error("⚠️ Error al leer colombia.json")

# --- 3. BASE DE DATOS LOCAL ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 4. FUNCIÓN CEREBRO: SHAUN HASTINGS ---
def obtener_reporte(ciudad, pais_nombre):
    if model:
        try:
            prompt_texto = f"Actúa como Shaun Hastings de Assassin's Creed. Dame un reporte táctico/histórico breve de {ciudad}, {pais_nombre}. Sé cínico, británico y muy sarcástico (máximo 280 caracteres)."
            response = model.generate_content(prompt_texto)
            return response.text
        except:
            return "Error de transmisión. Shaun está ocupado con su té."
    return "IA fuera de línea. Consulta la base de datos manual."

# --- 5. PANEL LATERAL: SINCRONIZACIÓN ---
st.sidebar.title("🦅 Sincronización Mundial")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad/Pueblo:")
    pais = st.text_input("País:", value="Colombia")
    # Este campo debe coincidir con el nombre en el JSON (ej: ANTIOQUIA, CUNDINAMARCA)
    depto_resaltar = st.text_input("Departamento (Para resaltar en CO):").upper()
    
    if st.form_submit_button("Sincronizar Atalaya"):
        geoloc = Nominatim(user_agent="animus_v6_santiago")
        try:
            loc = geoloc.geocode(f"{nombre}, {pais}", timeout=10)
            if loc:
                info_shaun = obtener_reporte(nombre, pais)
                
                nueva_fila = pd.DataFrame([{
                    "Nombre": nombre, "Pais": pais, "Depto": depto_resaltar, 
                    "Lat": loc.latitude, "Lon": loc.longitude, "Info": info_shaun
                }])
                df = pd.concat([df, nueva_fila], ignore_index=True)
                df.to_csv(archivo_csv, index=False)
                st.rerun()
            else:
                st.error("📍 Ubicación no encontrada en el satélite.")
        except:
            st.error("📡 Tiempo de espera agotado. Reintenta.")

# --- 6. RENDERIZADO DEL MAPA TÁCTICO ---
# Centramos el mapa en la última conquista o en Colombia por defecto
lat_ini = df['Lat'].iloc[-1] if not df.empty else 4.5708
lon_ini = df['Lon'].iloc[-1] if not df.empty else -74.2973

mapa = folium.Map(location=[lat_ini, lon_ini], zoom_start=6, tiles="CartoDB dark_matter")

# CAPA DE RESALTADO (COLOMBIA)
if geo_data:
    conquistados = df[df['Pais'].str.lower() == 'colombia']['Depto'].unique().tolist()
    folium.GeoJson(
        geo_data,
        style_function=lambda feature: {
            'fillColor': '#ff4b4b' if feature['properties']['DPTO'] in conquistados else 'transparent',
            'color': '#444',
            'weight': 1,
            'fillOpacity': 0.35 if feature['properties']['DPTO'] in conquistados else 0,
        }
    ).add_to(mapa)

# PINES TÁCTICOS CON POPUP HORIZONTAL
for _, f in df.iterrows():
    # HTML Personalizado para el Popup (Estilo Terminal)
    html_popup = f"""
    <div style="width: 320px; font-family: 'Courier New', Courier, monospace; color: #00ff00; background-color: #000; padding: 15px; border: 2px solid #ff4b4b; border-radius: 5px;">
        <b style="font-size: 14px; color: #ff4b4b;">> NODO: {f['Nombre'].upper()}</b><br>
        <hr style="border: 0.5px solid #333;">
        <p style="font-size: 12px; line-height: 1.4; text-align: justify;">{f['Info']}</p>
        <p style="font-size: 9px; color: #555; margin-top: 10px; text-align: right;">[HASTINGS_DB_V6]</p>
    </div>
    """
    iframe = folium.IFrame(html_popup, width=340, height=200)
    popup = folium.Popup(iframe, max_width=340)
    
    folium.Marker(
        [f['Lat'], f['Lon']], 
        popup=popup, 
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
    ).add_to(mapa)

# Mostrar el mapa en pantalla completa
st_folium(mapa, width="100%", height=650)
