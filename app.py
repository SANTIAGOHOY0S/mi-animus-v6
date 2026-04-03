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
        # Protocolo de auto-descubrimiento de modelos
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if modelos:
            modelo_elegido = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
            model = genai.GenerativeModel(modelo_elegido)
            st.sidebar.success(f"🛰️ Shaun en línea ({modelo_elegido.split('/')[-1]})")
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

# --- 2. CARGA DE GEODATOS (ESTRUCTURA TERRITORIAL) ---
geojson_path = "colombia.json"
geo_data = None
if os.path.exists(geojson_path):
    with open(geojson_path, encoding='utf-8') as f:
        geo_data = json.load(f)

# --- 3. BASE DE DATOS DE CONQUISTAS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 4. FUNCIÓN SHAUN HASTINGS (PERSONA) ---
def obtener_reporte(ciudad, pais_nombre):
    if model:
        try:
            prompt = (
                f"Eres Shaun Hastings de Assassin's Creed. Dame un reporte táctico de {ciudad}, {pais_nombre}. "
                "Responde SIEMPRE en ESPAÑOL. Sé cínico, sarcástico y muy inteligente. Máximo 280 caracteres."
            )
            # Desactivamos filtros pesados para evitar el "té compulsivo"
            seguridad = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            ]
            response = model.generate_content(prompt, safety_settings=seguridad)
            return response.text if response.text else "Nodo encriptado por Abstergo."
        except:
            return "Error de enlace. Shaun está ocupado con su té y el firewall."
    return "IA fuera de línea."

# --- 5. PANEL LATERAL: SINCRONIZACIÓN MUNDIAL ---
st.sidebar.title("🦅 Centro de Mando")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad o Punto de Interés:")
    pais = st.text_input("País:", value="Colombia")
    
    if st.form_submit_button("Sincronizar Atalaya"):
        if "MAPS_KEY" in st.secrets:
            api_key = st.secrets["MAPS_KEY"]
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={nombre},{pais}&key={api_key}&language=es"
            
            try:
                res = requests.get(url).json()
                if res["status"] == "OK":
                    # Coordenadas de precisión Google
                    coords = res["results"][0]["geometry"]["location"]
                    lat, lon = coords["lat"], coords["lng"]
                    
                    # --- AUTO-DETECCIÓN DE DEPARTAMENTO ---
                    depto_auto = "DESCONOCIDO"
                    for comp in res["results"][0]["address_components"]:
                        if "administrative_area_level_1" in comp["types"]:
                            depto_auto = comp["long_name"].upper()
                            # Normalizar para el JSON (Quitar tildes)
                            tildes = {"Á":"A", "É":"E", "Í":"I", "Ó":"O", "Ú":"U"}
                            for a, sa in tildes.items(): depto_auto = depto_auto.replace(a, sa)
                            break
                    
                    # Sincronización con Shaun
                    info_shaun = obtener_reporte(nombre, pais)
                    
                    # Actualizar DB
                    nueva_fila = pd.DataFrame([{"Nombre": nombre, "Pais": pais, "Depto": depto_auto, "Lat": lat, "Lon": lon, "Info": info_shaun}])
                    df = pd.concat([df, nueva_fila], ignore_index=True)
                    df.to_csv(archivo_csv, index=False)
                    st.rerun()
                else:
                    st.error(f"Error de GPS: {res['status']}")
            except Exception as e:
                st.error(f"Falla de satélite: {e}")
        else:
            st.error("🔑 MAPS_KEY no encontrada.")

# --- 6. RENDERIZADO DEL ANÍMUS ---
lat_c = df['Lat'].iloc[-1] if not df.empty else 4.703
lon_c = df['Lon'].iloc[-1] if not df.empty else -74.030

# Ajustes de mapa para evitar repetición (no_wrap)
mapa = folium.Map(
    location=[lat_c, lon_c], 
    zoom_start=3, 
    min_zoom=2,
    tiles=None # Lo definimos abajo con no_wrap
)
folium.TileLayer('CartoDB dark_matter', no_wrap=True).add_to(mapa)

# --- CUARTEL GENERAL (BELLA SUIZA) ---
folium.Marker(
    [4.7030, -74.0300], 
    popup="<b style='color: #00ff00; font-family: monospace;'>> CUARTEL GENERAL (CG)</b>",
    icon=folium.Icon(color="green", icon="home", prefix="fa")
).add_to(mapa)

# Relleno automático de regiones (Solo si el JSON coincide con el Depto detectado)
if geo_data:
    conquistados = df[df['Pais'].str.lower() == 'colombia']['Depto'].unique().tolist()
    folium.GeoJson(
        geo_data,
        style_function=lambda f: {
            'fillColor': '#ff4b4b' if str(f['properties'].get('DPTO', '')).upper() in conquistados else 'transparent',
            'color': '#444', 'weight': 1,
            'fillOpacity': 0.35 if str(f['properties'].get('DPTO', '')).upper() in conquistados else 0,
        }
    ).add_to(mapa)

# Pines de Conquista
for _, f in df.iterrows():
    html = f"""
    <div style="width: 320px; font-family: 'Courier New', monospace; color: #00ff00; background-color: #000; padding: 10px; border: 2px solid #ff4b4b; border-radius: 5px;">
        <b style="color: #ff4b4b;">> NODO: {f['Nombre'].upper()}</b><br>
        <hr style="border: 0.5px solid #333;">
        <div style="font-size: 12px;">{f['Info']}</div>
    </div>
    """
    folium.Marker(
        [f['Lat'], f['Lon']], 
        popup=folium.Popup(folium.IFrame(html, width=340, height=180), max_width=340), 
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
    ).add_to(mapa)

st_folium(mapa, width="100%", height=700)
