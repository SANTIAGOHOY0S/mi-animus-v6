import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
from geopy.geocoders import Nominatim
from deep_translator import GoogleTranslator

# --- 1. CONFIGURACIÓN DE IA (GEMINI ACTUALIZADO) ---
st.set_page_config(page_title="Animus OS V6", layout="wide")

# Inicializar modelo como None
model = None

if "GEMINI_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
       model = genai.GenerativeModel('gemini-pro') # Usamos Flash que es más rápido
    except Exception as e:
        st.error(f"Error configurando IA: {e}")
else:
    st.error("🔑 No se encontró la GEMINI_KEY en Secrets.")

# --- 2. SEGURIDAD: INGRESO DE CUARTEL GENERAL ---
if 'cg' not in st.session_state:
    st.title("🦅 Sistema de Sincronización Animus")
    cg_input = st.text_input("Define la ubicación de tu Cuartel General:", value="Bella Suiza, Bogota")
    if st.button("Iniciar Sincronización de ADN"):
        geoloc = Nominatim(user_agent="animus_v6_santiago")
        loc = geoloc.geocode(cg_input)
        if loc:
            st.session_state.cg = {"nombre": cg_input, "lat": loc.latitude, "lon": loc.longitude}
            st.rerun()
    st.stop()

# --- 3. BASE DE DATOS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Estado", "Pais", "Lat", "Lon", "Info"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 4. FUNCIÓN SHAUN HASTINGS (IA) ---
def reporte_shaun(lugar):
    if model:
        prompt = f"Eres Shaun Hastings de Assassin's Creed. Dame un reporte táctico/histórico de {lugar} (max 280 caracteres). Sé inteligente y sarcástico."
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error de enlace: {str(e)[:50]}..." # Esto nos dirá el error real
    return "IA no conectada."

# --- 5. INTERFAZ ---
st.sidebar.title(f"📍 CG: {st.session_state.cg['nombre']}")
with st.sidebar.form("nuevo_nodo"):
    nombre = st.text_input("Ciudad/Pueblo:")
    pais = st.text_input("País:", value="Colombia")
    if st.form_submit_button("Sincronizar Atalaya"):
        geoloc = Nominatim(user_agent="animus_v6_santiago")
        loc = geoloc.geocode(f"{nombre}, {pais}")
        if loc:
            info_ia = reporte_shaun(nombre)
            nuevo = pd.DataFrame([{"Nombre": nombre, "Pais": pais, "Lat": loc.latitude, "Lon": loc.longitude, "Info": info_ia}])
            df = pd.concat([df, nuevo], ignore_index=True)
            df.to_csv(archivo_csv, index=False)
            st.rerun()

# --- 6. MAPA ---
mapa = folium.Map(location=[st.session_state.cg['lat'], st.session_state.cg['lon']], zoom_start=12, tiles="CartoDB dark_matter")
folium.Marker([st.session_state.cg['lat'], st.session_state.cg['lon']], icon=folium.Icon(color="green", icon="home")).add_to(mapa)

for _, f in df.iterrows():
    folium.Marker([f['Lat'], f['Lon']], popup=f"<b>{f['Nombre']}</b><br>{f['Info']}", icon=folium.Icon(color="red")).add_to(mapa)

st_folium(mapa, width="100%", height=600)
