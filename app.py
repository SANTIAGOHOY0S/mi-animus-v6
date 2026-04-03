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
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if modelos:
            modelo_elegido = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
            model = genai.GenerativeModel(modelo_elegido)
            st.sidebar.success(f"🛰️ Shaun en línea ({modelo_elegido.split('/')[-1]})")
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

# --- 2. CARGA DE GEODATOS (COLOMBIA) ---
geojson_path = "colombia.json"
geo_data = None
if os.path.exists(geojson_path):
    with open(geojson_path, encoding='utf-8') as f:
        geo_data = json.load(f)

# --- 3. BASE DE DATOS DE CONQUISTAS ---
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info", "Tipo"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# Asegurar que la columna 'Tipo' exista en bases de datos viejas
if "Tipo" not in df.columns:
    df["Tipo"] = "Nodo"

# --- 4. FUNCIÓN SHAUN HASTINGS (SIN CENSURA NI LÍMITES) ---
def obtener_reporte(ciudad, pais_nombre):
    if model:
        try:
            prompt = (
                f"Actúa como Shaun Hastings (Assassin's Creed). "
                f"Dame un reporte táctico y geográfico DETALLADO de {ciudad}, {pais_nombre}. "
                "REGLAS OBLIGATORIAS: "
                "1. Responde SIEMPRE en ESPAÑOL. "
                "2. Sé extremadamente cínico, británico y sarcástico. "
                "3. Desarrolla la historia del lugar conectándola profundamente con una conspiración de los Templarios, Abstergo o los nazis. "
                "4. Da un análisis táctico del terreno para un Asesino (puntos de salto, escondites, peligros). "
                "5. DA UNA RECOMENDACIÓN TURÍSTICA sarcástica. "
                "6. Mínimo 3 párrafos sustanciosos. No te guardes información."
            )
            seguridad = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            ]
            response = model.generate_content(prompt, safety_settings=seguridad)
            return response.text if response.text else "Nodo encriptado por Abstergo."
        except Exception as e:
            return f"Error de Sistema: {str(e)}"
    return "IA fuera de línea."

# --- 5. PANEL LATERAL: SINCRONIZACIÓN MUNDIAL ---
st.sidebar.title("🦅 Centro de Mando")
with st.sidebar.form("atalaya"):
    nombre = st.text_input("Ciudad, Barrio o Punto de Interés:")
    pais = st.text_input("País:", value="Colombia")
    es_cg = st.checkbox("🛡️ Establecer como Cuartel General (CG)")
    
    if st.form_submit_button("Sincronizar Atalaya"):
        if "MAPS_KEY" in st.secrets:
            api_key = st.secrets["MAPS_KEY"]
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={nombre},{pais}&key={api_key}&language=es"
            
            try:
                res = requests.get(url).json()
                if res["status"] == "OK":
                    coords = res["results"][0]["geometry"]["location"]
                    lat, lon = coords["lat"], coords["lng"]
                    
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
                    
                    info_shaun = obtener_reporte(nombre, pais)
                    
                    # Lógica para establecer el nuevo CG y degradar el anterior
                    if es_cg:
                        df.loc[df['Tipo'] == 'CG', 'Tipo'] = 'Nodo'
                        tipo_actual = "CG"
                    else:
                        tipo_actual = "Nodo"
                        
                    nueva_fila = pd.DataFrame([{
                        "Nombre": nombre, "Pais": pais, "Depto": depto_auto, 
                        "Lat": lat, "Lon": lon, "Info": info_shaun, "Tipo": tipo_actual
                    }])
                    
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

# Mapa en loop cilíndrico (tiles por defecto sin no_wrap)
mapa = folium.Map(location=[lat_c, lon_c], zoom_start=5, min_zoom=2, tiles="CartoDB dark_matter")

# Relleno automático de regiones (Colombia)
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

# Pines Dinámicos (CG vs NODO) y Popups agrandados
for _, f in df.iterrows():
    es_base = f['Tipo'] == 'CG'
    color_borde = "#00ff00" if es_base else "#ff4b4b"
    color_icono = "green" if es_base else "red"
    icono = "home" if es_base else "crosshairs"
    titulo = f"> CUARTEL GENERAL: {f['Nombre'].upper()}" if es_base else f"> NODO: {f['Nombre'].upper()}"
    
    html = f"""
    <div style="width: 350px; font-family: 'Courier New', monospace; color: #00ff00; background-color: #000; padding: 12px; border: 2px solid {color_borde}; border-radius: 5px;">
        <b style="color: {color_borde};">{titulo} | {str(f.get('Depto', 'DESCONOCIDO')).upper()}</b><br>
        <hr style="border: 0.5px solid #333; margin: 8px 0;">
        <div style="font-size: 12px; line-height: 1.4; text-align: justify; max-height: 300px; overflow-y: auto;">
            {f['Info']}
        </div>
    </div>
    """
    folium.Marker(
        [f['Lat'], f['Lon']], 
        popup=folium.Popup(folium.IFrame(html, width=380, height=380), max_width=380), 
        icon=folium.Icon(color=color_icono, icon=icono, prefix="fa")
    ).add_to(mapa)

st_folium(mapa, width="100%", height=700)
