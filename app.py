import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import json
import requests

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Animus OS V6 - Santiago", layout="wide")

model = None
if "GEMINI_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        modelos_disponibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if modelos_disponibles:
            modelo_elegido = 'models/gemini-pro' if 'models/gemini-pro' in modelos_disponibles else modelos_disponibles[0]
            model = genai.GenerativeModel(modelo_elegido)
            st.sidebar.success(f"🛰️ Shaun en línea ({modelo_elegido.replace('models/', '')})")
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

# --- 2. CARGA DE GEODATOS (COLOMBIA) ---
geojson_path = "colombia.json"
geo_data = None
if os.path.exists(geojson_path):
    with open(geojson_path, encoding='utf-8') as f:
        geo_data = json.load(f)

# --- 3. BASE DE DATOS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 4. FUNCIÓN SHAUN HASTINGS ---
def obtener_reporte(ciudad, pais_nombre):
    if model:
        try:
            prompt = (
                f"Eres Shaun Hastings de Assassin's Creed. Dame un reporte táctico de {ciudad}, {pais_nombre}. "
                "Responde SIEMPRE en ESPAÑOL. Sé cínico, sarcástico y muy inteligente. Máximo 280 caracteres."
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error de Sistema: {str(e)}"
    return "IA fuera de línea."

# --- 5. PANEL LATERAL: SINCRONIZACIÓN AUTOMÁTICA ---
st.sidebar.title("🦅 Sincronización Mundial")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad/Pueblo:")
    pais = st.text_input("País:", value="Colombia")
    # ¡Casilla de departamento eliminada!
    
    if st.form_submit_button("Sincronizar Atalaya"):
        if "MAPS_KEY" in st.secrets:
            api_key = st.secrets["MAPS_KEY"]
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={nombre},{pais}&key={api_key}&language=es"
            
            try:
                res = requests.get(url).json()
                if res["status"] == "OK":
                    # Coordenadas
                    coords = res["results"][0]["geometry"]["location"]
                    lat, lon = coords["lat"], coords["lng"]
                    
                    # --- AUTO-DETECCIÓN DE DEPARTAMENTO/ESTADO ---
                    depto_auto = "DESCONOCIDO"
                    for componente in res["results"][0]["address_components"]:
                        if "administrative_area_level_1" in componente["types"]:
                            depto_auto = componente["long_name"].upper()
                            # Limpiamos tildes para que coincida con colombia.json
                            tildes = {"Á":"A", "É":"E", "Í":"I", "Ó":"O", "Ú":"U"}
                            for acento, sin_acento in tildes.items():
                                depto_auto = depto_auto.replace(acento, sin_acento)
                            
                            # Ajuste especial para Bogotá según el estándar del DANE/IGAC
                            if "BOGOTA" in depto_auto or "CUNDINAMARCA" in depto_auto:
                                if nombre.upper() in ["BOGOTA", "BOGOTÁ"]:
                                    depto_auto = "SANTAFE DE BOGOTA D.C" 
                            break
                    
                    # Llamada a Shaun
                    info_shaun = obtener_reporte(nombre, pais)
                    
                    # Guardamos la info con el departamento automático
                    nueva_fila = pd.DataFrame([{
                        "Nombre": nombre, "Pais": pais, "Depto": depto_auto, 
                        "Lat": lat, "Lon": lon, "Info": info_shaun
                    }])
                    df = pd.concat([df, nueva_fila], ignore_index=True)
                    df.to_csv(archivo_csv, index=False)
                    st.success(f"Nodo {nombre} ({depto_auto}) sincronizado.")
                    st.rerun()
                else:
                    st.error(f"Google Maps Error: {res['status']}")
            except Exception as e:
                st.error(f"Falla en el satélite: {e}")
        else:
            st.error("🔑 Falta MAPS_KEY en los Secrets.")

# --- 6. RENDERIZADO DEL MAPA ---
lat_c = df['Lat'].iloc[-1] if not df.empty else 4.5
lon_c = df['Lon'].iloc[-1] if not df.empty else -74.2

mapa = folium.Map(location=[lat_c, lon_c], zoom_start=5, tiles="CartoDB dark_matter")

# Pintar departamentos de Colombia automáticamente
if geo_data:
    conquistados = df['Depto'].unique().tolist()
    folium.GeoJson(
        geo_data,
        style_function=lambda f: {
            'fillColor': '#ff4b4b' if str(f['properties'].get('DPTO', '')).upper() in conquistados else 'transparent',
            'color': '#444', 'weight': 1,
            'fillOpacity': 0.35 if str(f['properties'].get('DPTO', '')).upper() in conquistados else 0,
        }
    ).add_to(mapa)

for _, f in df.iterrows():
    # Añadí el departamento/estado al título del popup para que veas qué detectó
    html = f"""
    <div style="width: 330px; font-family: 'Courier New', Courier, monospace; color: #00ff00; background-color: #000; padding: 12px; border: 2px solid #ff4b4b; border-radius: 8px;">
        <b style="color: #ff4b4b;">> NODO: {f['Nombre'].upper()} | {str(f['Depto']).upper()}</b><br>
        <hr style="border: 0.5px solid #333; margin: 8px 0;">
        <div style="font-size: 12px; line-height: 1.3; text-align: justify;">{f['Info']}</div>
        <div style="font-size: 9px; color: #555; margin-top: 10px; text-align: right;">[HASTINGS_DB_V6]</div>
    </div>
    """
    folium.Marker(
        [f['Lat'], f['Lon']], 
        popup=folium.Popup(folium.IFrame(html, width=350, height=200), max_width=350), 
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
    ).add_to(mapa)

st_folium(mapa, width="100%", height=700)
