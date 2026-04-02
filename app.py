import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
from geopy.geocoders import Nominatim
from deep_translator import GoogleTranslator

# --- 1. CONFIGURACIÓN DE IA (GEMINI) ---
st.set_page_config(page_title="Animus OS V6", layout="wide")

# Conexión con los Secretos del Servidor
if "GEMINI_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("🔑 Falta la GEMINI_KEY en los Secrets de Streamlit.")
    model = None

# --- 2. SEGURIDAD: INGRESO DE CUARTEL GENERAL ---
if 'cg' not in st.session_state:
    st.title("🦅 Sistema de Sincronización Animus")
    cg_input = st.text_input("Define la ubicación de tu Cuartel General (Ej: Bella Suiza, Bogota):")
    if st.button("Iniciar Sincronización de ADN"):
        geoloc = Nominatim(user_agent="animus_v6")
        loc = geoloc.geocode(cg_input)
        if loc:
            st.session_state.cg = {"nombre": cg_input, "lat": loc.latitude, "lon": loc.longitude}
            st.rerun()
        else:
            st.error("No se encontró la ubicación. Revisa la conexión satelital.")
    st.stop()

# --- 3. BASE DE DATOS AUTO-GENERADA ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    # Creamos el archivo con el árbol: País -> Estado -> Ciudad
    df_inicial = pd.DataFrame(columns=["Nombre", "Tipo", "Estado", "Pais", "Lat", "Lon", "Info"])
    df_inicial.to_csv(archivo_csv, index=False)

df = pd.read_csv(archivo_csv)

# --- 4. FUNCIÓN SHAUN HASTINGS (IA) ---
def reporte_shaun(lugar):
    if model:
        prompt = f"Actúa como Shaun Hastings de Assassin's Creed. Dame un reporte táctico/histórico de {lugar} (máximo 280 caracteres). Usa un tono inteligente y sarcástico."
        try:
            return model.generate_content(prompt).text
        except:
            return "Error de comunicación con el satélite."
    return "IA no configurada."

# --- 5. INTERFAZ DE MANDO ---
st.sidebar.title(f"📍 CG: {st.session_state.cg['nombre']}")
with st.sidebar.form("nuevo_nodo"):
    st.write("🌳 Árbol de Jerarquía")
    nombre = st.text_input("Ciudad/Pueblo:")
    estado = st.text_input("Departamento/Estado:")
    pais = st.text_input("País (Español):")
    
    if st.form_submit_button("Sincronizar Atalaya"):
        geoloc = Nominatim(user_agent="animus_v6")
        loc = geoloc.geocode(f"{nombre}, {pais}")
        if loc:
            info_ia = reporte_shaun(nombre)
            # Traducción para consistencia en el mapa
            pais_en = GoogleTranslator(source='es', target='en').translate(pais)
            
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "Tipo": "Ciudad", "Estado": estado.upper(),
                "Pais": pais_en, "Lat": loc.latitude, "Lon": loc.longitude, "Info": info_ia
            }])
            df = pd.concat([df, nueva_fila], ignore_index=True)
            df.to_csv(archivo_csv, index=False)
            st.success(f"¡{nombre} sincronizado!")
            st.rerun()

# --- 6. MAPA TÁCTICO (NIEBLA DE GUERRA) ---
mapa = folium.Map(
    location=[st.session_state.cg['lat'], st.session_state.cg['lon']], 
    zoom_start=12, 
    tiles="CartoDB dark_matter"
)

# Dibujar Cuartel General
folium.Marker(
    [st.session_state.cg['lat'], st.session_state.cg['lon']],
    popup="🏠 MI CUARTEL GENERAL",
    icon=folium.Icon(color="green", icon="shield", prefix="fa")
).add_to(mapa)

# Dibujar Nodos Sincronizados
for _, fila in df.iterrows():
    folium.Marker(
        [fila['Lat'], fila['Lon']],
        popup=f"<b>{fila['Nombre']}</b><br>{fila['Info']}",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
    ).add_to(mapa)

st_folium(mapa, width="100%", height=600)