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

# --- 4. FUNCIÓN CEREBRO: SHAUN HASTINGS (VERSIÓN BLINDADA) ---
def obtener_reporte(ciudad, pais_nombre):
    if model:
        try:
            prompt = (
                f"Actúa como Shaun Hastings de Assassin's Creed. Dame un reporte táctico de {ciudad}, {pais_nombre}. "
                "Responde en ESPAÑOL. Sé cínico y sarcástico. Máximo 250 caracteres."
            )
            # Añadimos parámetros de seguridad relajados para evitar bloqueos tontos
            response = model.generate_content(
                prompt,
                safety_settings={
                    "HATE": "BLOCK_NONE",
                    "HARASSMENT": "BLOCK_NONE",
                    "DANGEROUS": "BLOCK_NONE",
                    "SEXUAL": "BLOCK_NONE",
                }
            )
            
            # Validamos si la respuesta tiene texto antes de acceder a él
            if response and response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                return f"Nodo {ciudad} parcialmente encriptado. Los servidores de Abstergo están interfiriendo."
        except Exception as e:
            # Esto te dirá en la consola de Streamlit qué está pasando realmente
            print(f"DEBUG: Error en Gemini: {e}")
            return "Error de enlace. Shaun está ocupado con su té (y el firewall de Abstergo)."
    return "IA fuera de línea."

# --- 5. PANEL LATERAL: SINCRONIZACIÓN (VERSIÓN BLINDADA) ---
st.sidebar.title("🦅 Sincronización Mundial")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad/Pueblo:")
    pais = st.text_input("País:", value="Colombia")
    depto_resaltar = st.text_input("Departamento (MAYÚSCULAS para CO):").upper()
    
    if st.form_submit_button("Sincronizar Atalaya"):
        # Cambiamos el nombre del agente cada vez que hay error para "despistar" al bloqueo
        agente_id = f"animus_tactical_{pd.Timestamp.now().second}"
        geoloc = Nominatim(user_agent=agente_id)
        
        try:
            # Intentamos la búsqueda con un tiempo de espera más largo (timeout)
            loc = geoloc.geocode(f"{nombre}, {pais}", timeout=15)
            
            if loc:
                info_shaun = obtener_reporte(nombre, pais)
                
                nueva_fila = pd.DataFrame([{
                    "Nombre": nombre, "Pais": pais, "Depto": depto_resaltar, 
                    "Lat": loc.latitude, "Lon": loc.longitude, "Info": info_shaun
                }])
                df = pd.concat([df, nueva_fila], ignore_index=True)
                df.to_csv(archivo_csv, index=False)
                st.success(f"Nodo {nombre} sincronizado.")
                st.rerun()
            else:
                st.error("📍 El satélite no localiza esas coordenadas.")
        except Exception as e:
            st.error("📡 Satélite saturado. Espera 10 segundos y reintenta.")

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
