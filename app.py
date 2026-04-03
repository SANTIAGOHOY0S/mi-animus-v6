import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import requests

# --- 1. CONFIGURACIÓN DEL CEREBRO (GEMINI) ---
st.set_page_config(page_title="Animus OS V6 - Santiago", layout="wide")

if "ultima_transmision" not in st.session_state:
    st.session_state.ultima_transmision = None
    st.session_state.ultimo_nodo = None

model = None
if "GEMINI_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if modelos:
            modelo_elegido = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
            model = genai.GenerativeModel(modelo_elegido)
            st.sidebar.success(f"🛰️ Shaun en línea")
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

# --- 2. BASE DE DATOS DE CONQUISTAS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info", "Tipo"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 3. FUNCIÓN SHAUN HASTINGS ---
def obtener_reporte(ciudad, pais_nombre, tipo_nodo):
    if model:
        try:
            extra_info = f"Este lugar es un {tipo_nodo}."
            prompt = (
                f"Actúa como Shaun Hastings (Assassin's Creed). "
                f"Dame un reporte táctico de {ciudad}, {pais_nombre}. {extra_info} "
                "REGLAS: Responde en ESPAÑOL, sé cínico, británico, sarcástico. "
                "Menciona conspiraciones o a los nazis. Máximo 3 párrafos."
            )
            response = model.generate_content(prompt)
            return response.text if response.text else "Nodo encriptado."
        except: return "Error de enlace."
    return "IA fuera de línea."

# --- 4. PANEL LATERAL: CENTRO DE MANDO ---
st.sidebar.title("🦅 Sincronización Táctica")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Nombre del Punto (Barrio, U, Refugio...):")
    pais = st.text_input("País:", value="Colombia")
    
    # Selector de Tipo de Nodo
    tipo_nodo = st.selectbox("Categoría del Nodo:", 
                             ["Nodo Estándar", "Refugio (Amigos)", "Universidad", "Abandonado"])
    
    with st.expander("⚙️ Opciones Avanzadas (Coordenadas / CG)"):
        es_cg = st.checkbox("🛡️ Establecer como Cuartel General (CG)")
        st.caption("Si dejas esto vacío, se usará la búsqueda de Google:")
        lat_manual = st.text_input("Latitud Manual (Ej: 4.7030):")
        lon_manual = st.text_input("Longitud Manual (Ej: -74.0300):")

    if st.form_submit_button("Sincronizar Atalaya"):
        lat, lon = None, None
        
        # Lógica de Coordenadas: ¿Manual o Automática?
        if lat_manual and lon_manual:
            try:
                lat, lon = float(lat_manual), float(lon_manual)
            except: st.error("Formato de coordenadas inválido.")
        
        if not lat and "MAPS_KEY" in st.secrets:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={nombre},{pais}&key={st.secrets['MAPS_KEY']}&language=es"
            res = requests.get(url).json()
            if res["status"] == "OK":
                coords = res["results"][0]["geometry"]["location"]
                lat, lon = coords["lat"], coords["lng"]
            else: st.error("No se encontró la ubicación.")

        if lat and lon:
            # Sincronización con Shaun
            tipo_final = "CG" if es_cg else tipo_nodo
            info_shaun = obtener_reporte(nombre, pais, tipo_final)
            
            if es_cg: df.loc[df['Tipo'] == 'CG', 'Tipo'] = 'Nodo Estándar'
            
            nueva_fila = pd.DataFrame([{"Nombre": nombre, "Pais": pais, "Depto": "SINC", "Lat": lat, "Lon": lon, "Info": info_shaun, "Tipo": tipo_final}])
            df = pd.concat([df, nueva_fila], ignore_index=True)
            df.to_csv(archivo_csv, index=False)
            
            st.session_state.ultima_transmision = info_shaun
            st.session_state.ultimo_nodo = f"{nombre.upper()} [{tipo_final}]"
            st.rerun()

# --- 5. INTERFAZ Y MAPA ---
if st.session_state.ultima_transmision:
    st.markdown(f"""<div style="background-color: #050505; border: 2px solid #00ff00; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h3 style="color: #00ff00; font-family: monospace;">> TRANSMISIÓN ENTRANTE: {st.session_state.ultimo_nodo}</h3>
        <div style="color: #00ff00; font-family: monospace; font-size: 14px; white-space: pre-wrap;">{st.session_state.ultima_transmision}</div>
    </div>""", unsafe_allow_html=True)
    if st.button("❌ Cerrar"):
        st.session_state.ultima_transmision = None
        st.rerun()

lat_ini = df['Lat'].iloc[-1] if not df.empty else 4.703
mapa = folium.Map(location=[lat_ini, df['Lon'].iloc[-1] if not df.empty else -74.030], zoom_start=13, tiles="CartoDB dark_matter")

# Lógica de Iconos por Categoría
for _, f in df.iterrows():
    tipo = f['Tipo']
    if tipo == 'CG': 
        color, icono = 'green', 'home'
    elif tipo == 'Universidad': 
        color, icono = 'blue', 'graduation-cap'
    elif tipo == 'Refugio (Amigos)': 
        color, icono = 'orange', 'users'
    elif tipo == 'Abandonado': 
        color, icono = 'lightgray', 'trash'
    else: 
        color, icono = 'red', 'crosshairs'

    html = f"""<div style="width: 300px; color: #00ff00; background: #000; padding: 10px; border: 1px solid {color};">
        <b>{f['Nombre'].upper()}</b><br><hr>{f['Info']}</div>"""
    
    folium.Marker([f['Lat'], f['Lon']], 
                  popup=folium.Popup(folium.IFrame(html, width=320, height=250), max_width=320),
                  icon=folium.Icon(color=color, icon=icono, prefix='fa')).add_to(mapa)

st_folium(mapa, width="100%", height=600)
