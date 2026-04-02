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

# (Aquí va tu lógica de conexión de Gemini que ya funciona...)

# --- 2. CARGA DE MAPA BASE (SOLO COLOMBIA) ---
geojson_path = "colombia.json"
geo_data = None
if os.path.exists(geojson_path):
    try:
        with open(geojson_path, encoding='utf-8') as f:
            geo_data = json.load(f)
    except: pass

# --- 3. BASE DE DATOS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 4. PANEL LATERAL ---
st.sidebar.title("🦅 Sincronización Mundial")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad/Pueblo:")
    pais = st.text_input("País:", value="Colombia")
    # El Depto es opcional, solo para resaltar el mapa de Colombia
    depto_opcional = st.text_input("Depto (Solo para resaltar en CO):")
    
    if st.form_submit_button("Sincronizar Atalaya"):
        geoloc = Nominatim(user_agent="animus_v6_global")
        loc = geoloc.geocode(f"{nombre}, {pais}")
        if loc:
            # Shaun genera el reporte basado en Ciudad + País
            prompt = f"Eres Shaun Hastings de AC. Reporte táctico de {nombre}, {pais}. Sarcástico y cínico (max 280 chars)."
            info = model.generate_content(prompt).text if model else "Sin conexión."
            
            nuevo = pd.DataFrame([{"Nombre": nombre, "Pais": pais, "Depto": depto_opcional, "Lat": loc.latitude, "Lon": loc.longitude, "Info": info}])
            df = pd.concat([df, nuevo], ignore_index=True)
            df.to_csv(archivo_csv, index=False)
            st.rerun()

# --- 5. EL MAPA ---
mapa = folium.Map(location=[df['Lat'].iloc[-1] if not df.empty else 4.5, 
                           df['Lon'].iloc[-1] if not df.empty else -74.2], 
                  zoom_start=5, tiles="CartoDB dark_matter")

# RESALTADO DINÁMICO (Solo si hay datos de Colombia)
if geo_data:
    conquistados = df[df['Pais'].str.lower() == 'colombia']['Depto'].unique().tolist()
    folium.GeoJson(
        geo_data,
        style_function=lambda feature: {
            'fillColor': '#ff4b4b' if feature['properties']['DPTO'] in conquistados else 'transparent',
            'color': '#333',
            'weight': 1,
            'fillOpacity': 0.3 if feature['properties']['DPTO'] in conquistados else 0,
        }
    ).add_to(mapa)

# DIBUJAR PINES (Global)
for _, f in df.iterrows():
    html = f"""
    <div style="width: 320px; font-family: monospace; color: #00ff00; background-color: #000; padding: 10px; border: 1px solid #ff4b4b;">
        <b style="color: #ff4b4b;">> {f['Nombre'].upper()}, {f['Pais'].upper()}</b><br>
        <p style="font-size: 12px;">{f['Info']}</p>
    </div>
    """
    folium.Marker([f['Lat'], f['Lon']], 
                  popup=folium.Popup(folium.IFrame(html, width=340, height=180), max_width=340),
                  icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(mapa)

st_folium(mapa, width="100%", height=600)
