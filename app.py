import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import requests
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DEL CEREBRO (GEMINI & CSS) ---
st.set_page_config(page_title="Animus OS V6 - Santiago", layout="wide")

# Parche CSS para eliminar las líneas blancas del mapa
st.markdown("""
    <style>
    .leaflet-tile { border: solid transparent 1px !important; }
    </style>
""", unsafe_allow_html=True)

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
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

# --- 2. BASE DE DATOS DE CONQUISTAS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info", "Tipo"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

if "Tipo" not in df.columns:
    df["Tipo"] = "Nodo"

# --- 3. FUNCIÓN SHAUN HASTINGS ---
def obtener_reporte(ciudad, pais_nombre, tipo_nodo):
    if model:
        try:
            extra_info = f"Este lugar es un {tipo_nodo}."
            prompt = (
                f"Actúa como Shaun Hastings (Assassin's Creed). "
                f"Dame un reporte táctico de {ciudad}, {pais_nombre}. {extra_info} "
                "REGLAS OBLIGATORIAS: "
                "1. Responde SIEMPRE en ESPAÑOL. "
                "2. Sé extremadamente cínico, británico y sarcástico. "
                "3. Desarrolla la historia del lugar conectándola con una conspiración Templaria o de Abstergo. "
                "4. Da un análisis táctico para un Asesino (puntos de salto, peligros). "
                "5. DA UNA RECOMENDACIÓN TURÍSTICA sarcástica. "
                "6. Mínimo 3 párrafos sustanciosos."
            )
            seguridad = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            ]
            response = model.generate_content(prompt, safety_settings=seguridad)
            return response.text if response.text else "Nodo encriptado."
        except Exception as e:
            return f"Error de Sistema: {str(e)}"
    return "IA fuera de línea."

# --- 4. PANEL LATERAL: CENTRO DE MANDO ---
st.sidebar.title("🦅 Sincronización Táctica")

# Módulo de música microscópico (Pixel Espía)
youtube_html = """
<iframe width="1" height="1" 
src="https://www.youtube.com/embed/dQjRTP6ANkw?autoplay=1&loop=1&playlist=dQjRTP6ANkw" 
frameborder="0" allow="autoplay; encrypted-media"></iframe>
"""
with st.sidebar:
    st.caption("🎵 Frecuencia Ezio activada (Haz clic en la pantalla si no suena)")
    components.html(youtube_html, width=1, height=1)
    st.markdown("---")

with st.sidebar.form("atalaya"):
    nombre = st.text_input("Nombre del Punto (Barrio, U, Refugio...):")
    pais = st.text_input("País:", value="Colombia")
    
    tipo_nodo = st.selectbox("Categoría del Nodo:", 
                             ["Nodo Estándar", "Refugio (Amigos)", "Universidad", "Abandonado"])
    
    with st.expander("⚙️ Opciones Avanzadas (Coordenadas / CG)"):
        es_cg = st.checkbox("🛡️ Establecer como Cuartel General (CG)")
        st.caption("Si dejas esto vacío, se usará la búsqueda de Google:")
        lat_manual = st.text_input("Latitud Manual (Ej: 4.7030):")
        lon_manual = st.text_input("Longitud Manual (Ej: -74.0300):")

    if st.form_submit_button("Sincronizar Atalaya"):
        lat, lon = None, None
        
        if lat_manual and lon_manual:
            try:
                lat, lon = float(lat_manual), float(lon_manual)
            except: st.error("Formato de coordenadas inválido.")
        
        if not lat and "MAPS_KEY" in st.secrets:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={nombre},{pais}&key={st.secrets['MAPS_KEY']}&language=es"
            try:
                res = requests.get(url).json()
                if res["status"] == "OK":
                    coords = res["results"][0]["geometry"]["location"]
                    lat, lon = coords["lat"], coords["lng"]
                    
                    # Limpieza automática del departamento
                    depto_auto = "DESCONOCIDO"
                    for comp in res["results"][0]["address_components"]:
                        if "administrative_area_level_1" in comp["types"]:
                            depto_auto = comp["long_name"].upper()
                            palabras_basura = [" DEPARTMENT", " DEPARTAMENTO", " PROVINCE", " STATE", " DISTRITO CAPITAL", " D.C."]
                            for palabra in palabras_basura: depto_auto = depto_auto.replace(palabra, "")
                            tildes = {"Á":"A", "É":"E", "Í":"I", "Ó":"O", "Ú":"U"}
                            for a, sa in tildes.items(): depto_auto = depto_auto.replace(a, sa)
                            
                            if "BOGOTA" in depto_auto or "CUNDINAMARCA" in depto_auto:
                                if nombre.upper() in ["BOGOTA", "BOGOTÁ"] or "BOGOTA" in url.upper():
                                    depto_auto = "SANTAFE DE BOGOTA D.C" 
                            depto_auto = depto_auto.strip()
                            break
                else:
                    st.error(f"Error de GPS: {res['status']}")
            except Exception as e:
                st.error(f"Falla de satélite: {e}")

        if lat and lon:
            tipo_final = "CG" if es_cg else tipo_nodo
            info_shaun = obtener_reporte(nombre, pais, tipo_final)
            
            if es_cg: df.loc[df['Tipo'] == 'CG', 'Tipo'] = 'Nodo Estándar'
            
            nueva_fila = pd.DataFrame([{
                "Nombre": nombre, "Pais": pais, "Depto": depto_auto if not (lat_manual and lon_manual) else "MANUAL", 
                "Lat": lat, "Lon": lon, "Info": info_shaun, "Tipo": tipo_final
            }])
            
            df = pd.concat([df, nueva_fila], ignore_index=True)
            df.to_csv(archivo_csv, index=False)
            
            st.session_state.ultima_transmision = info_shaun
            st.session_state.ultimo_nodo = f"{nombre.upper()} [{tipo_final}]"
            st.rerun()

# --- 5. INTERFAZ Y MAPA ---
if st.session_state.ultima_transmision:
    st.markdown(f"""<div style="background-color: #050505; border: 2px solid #00ff00; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h3 style="color: #00ff00; font-family: monospace; margin-top:0;">> TRANSMISIÓN ENTRANTE: {st.session_state.ultimo_nodo}</h3>
        <hr style="border-color:#333;">
        <div style="color: #00ff00; font-family: monospace; font-size: 14px; white-space: pre-wrap;">{st.session_state.ultima_transmision}</div>
    </div>""", unsafe_allow_html=True)
    if st.button("❌ Cerrar Transmisión"):
        st.session_state.ultima_transmision = None
        st.rerun()

lat_ini = df['Lat'].iloc[-1] if not df.empty else 4.703
lon_ini = df['Lon'].iloc[-1] if not df.empty else -74.030

# Mapa Cilíndrico
mapa = folium.Map(
    location=[lat_ini, lon_ini], 
    zoom_start=4, 
    min_zoom=3, 
    max_bounds=True,
    tiles="CartoDB dark_matter"
)

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

    titulo = f"> {tipo.upper()}: {f['Nombre'].upper()}"
    
    html = f"""
    <div style="width: 100%; font-family: 'Courier New', monospace; color: {color}; background-color: #000; padding: 5px;">
        <b style="color: {color};">{titulo}</b><br>
        <hr style="border: 0.5px solid #333; margin: 8px 0;">
        <div style="font-size: 12px; line-height: 1.4; text-align: justify;">
            {f['Info']}
        </div>
    </div>
    """
    
    folium.Marker([f['Lat'], f['Lon']], 
                  popup=folium.Popup(folium.IFrame(html, width=380, height=350), max_width=380),
                  icon=folium.Icon(color=color, icon=icono, prefix='fa')).add_to(mapa)

st_folium(mapa, width="100%", height=700)
