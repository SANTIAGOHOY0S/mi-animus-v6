import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import requests
import re
import random
import streamlit.components.v1 as components
from gtts import gTTS

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(page_title="Animus OS V6 - Santiago", layout="wide")

st.markdown("""
    <style>
    .leaflet-tile { border: solid transparent 1px !important; }
    .stApp { background-color: #000000; }
    </style>
""", unsafe_allow_html=True)

if "ultima_transmision" not in st.session_state:
    st.session_state.ultima_transmision = None
    st.session_state.ultimo_nodo = None

model = None
if "GEMINI_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info", "Tipo"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 2. NÚCLEO LOGÍSTICO: SHAUN HASTINGS ---
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
                "3. Conecta el lugar con una conspiración de Abstergo. "
                "4. Usa formato Markdown (negritas) para resaltar puntos clave. "
                "5. Mínimo 2 párrafos."
            )
            response = model.generate_content(prompt)
            return response.text if response.text else "Nodo encriptado."
        except Exception as e:
            return f"Error de Sistema: {str(e)}"
    return "IA fuera de línea."

# --- 3. PANEL DE CONTROL (SIDEBAR) ---
st.sidebar.title("🦅 Sincronización Táctica")

# --- NUEVO MÓDULO DE MÚSICA INTELIGENTE ---
# Lista de IDs de tus videos de YouTube
soundtracks = [
    "C_n-EcznZpE", # AC2 - Ezio's Family
    "d5F9X6qeXco", # AC Revelations - Main Theme
    "NVsSrJJIzDM", # AC3 - Main Theme
    "RwDQZI_NRHA", # AC Black Flag - Main Theme
    "nyQEQM0CEBQ", # AC Rogue - Main Theme
    "NEpjh30DLas", # AC Unity - Main Theme
    "PDVnsHC3ypQ"  # AC Syndicate - Family
]

# Script de YouTube API para reproducción aleatoria sin repetición inmediata
musica_html = f"""
<div id="player"></div>
<script>
  var tag = document.createElement('script');
  tag.src = "https://www.youtube.com/iframe_api";
  var firstScriptTag = document.getElementsByTagName('script')[0];
  firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

  var player;
  var soundtracks = {soundtracks};
  var lastVideo = "";

  function onYouTubeIframeAPIReady() {{
    playRandomVideo();
  }}

  function playRandomVideo() {{
    var filtered = soundtracks.filter(function(id) {{ return id !== lastVideo; }});
    var nextVideo = filtered[Math.floor(Math.random() * filtered.length)];
    lastVideo = nextVideo;

    if (!player) {{
        player = new YT.Player('player', {{
            height: '1',
            width: '1',
            videoId: nextVideo,
            playerVars: {{ 'autoplay': 1, 'controls': 0 }},
            events: {{ 'onStateChange': onPlayerStateChange }}
        }});
    }} else {{
        player.loadVideoById(nextVideo);
    }}
  }}

  function onPlayerStateChange(event) {{
    if (event.data == YT.PlayerState.ENDED) {{
        playRandomVideo();
    }}
  }}
</script>
"""

with st.sidebar:
    st.caption("🎵 Frecuencia de la Hermandad (Shuffle activo)")
    components.html(musica_html, height=1)
    st.markdown("---")

with st.sidebar.form("atalaya"):
    nombre = st.text_input("Nombre del Punto:")
    pais = st.text_input("País:", value="Colombia")
    tipo_nodo = st.selectbox("Categoría:", ["Nodo Estándar", "Refugio (Amigos)", "Universidad", "Abandonado"])
    
    es_cg = st.checkbox("🛡️ Establecer como Cuartel General")
    lat_manual = st.text_input("Latitud (Opcional):")
    lon_manual = st.text_input("Longitud (Opcional):")

    if st.form_submit_button("Sincronizar Atalaya"):
        lat, lon = None, None
        
        if lat_manual and lon_manual:
            lat, lon = float(lat_manual), float(lon_manual)
        elif "MAPS_KEY" in st.secrets:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={nombre},{pais}&key={st.secrets['MAPS_KEY']}&language=es"
            res = requests.get(url).json()
            if res["status"] == "OK":
                coords = res["results"][0]["geometry"]["location"]
                lat, lon = coords["lat"], coords["lng"]

        if lat and lon:
            tipo_final = "CG" if es_cg else tipo_nodo
            info_shaun = obtener_reporte(nombre, pais, tipo_final)
            
            info_audio = re.sub(r'[*_#]', '', info_shaun)
            
            try:
                if "ELEVENLABS_KEY" in st.secrets and "VOICE_ID" in st.secrets:
                    api_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                    headers = {{
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": st.secrets["ELEVENLABS_KEY"]
                    }}
                    data = {{
                        "text": info_audio,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {{"stability": 0.45, "similarity_boost": 0.8}}
                    }}
                    v_res = requests.post(api_url, json=data, headers=headers)
                    if v_res.status_code == 200:
                        with open("shaun_voice.mp3", "wb") as f:
                            f.write(v_res.content)
                    else:
                        raise Exception("Fallo en ElevenLabs")
                else:
                    gTTS(text=info_audio, lang='es', tld='es').save("shaun_voice.mp3")
            except:
                gTTS(text=info_audio, lang='es', tld='es').save("shaun_voice.mp3")

            if es_cg: df.loc[df['Tipo'] == 'CG', 'Tipo'] = 'Nodo Estándar'
            nueva_fila = pd.DataFrame([{"Nombre": nombre, "Pais": pais, "Depto": "SINC", "Lat": lat, "Lon": lon, "Info": info_shaun, "Tipo": tipo_final}])
            df = pd.concat([df, nueva_fila], ignore_index=True)
            df.to_csv(archivo_csv, index=False)
            
            st.session_state.ultima_transmision = info_shaun
            st.session_state.ultimo_nodo = f"{{nombre.upper()}} [{{tipo_final}}]"
            st.rerun()

# --- 4. INTERFAZ DE USUARIO Y MAPA ---
if st.session_state.ultima_transmision:
    st.markdown(f"""
    <div style="background-color: #050505; border: 2px solid #00ff00; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h3 style="color: #00ff00; font-family: monospace; margin-top:0;">> TRANSMISIÓN ENTRANTE: {{st.session_state.ultimo_nodo}}</h3>
        <hr style="border-color:#333;">
        <div style="color: #00ff00; font-family: monospace; font-size: 15px; white-space: pre-wrap;">{{st.session_state.ultima_transmision}}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if os.path.exists("shaun_voice.mp3"):
        st.audio("shaun_voice.mp3", format="audio/mp3", autoplay=True)
        
    if st.button("❌ Terminar Transmisión"):
        st.session_state.ultima_transmision = None
        st.rerun()

lat_ini = df['Lat'].iloc[-1] if not df.empty else 4.703
lon_ini = df['Lon'].iloc[-1] if not df.empty else -74.030
mapa = folium.Map(location=[lat_ini, lon_ini], zoom_start=13, tiles="CartoDB dark_matter")

for _, f in df.iterrows():
    colores = {'CG': 'green', 'Universidad': 'blue', 'Refugio (Amigos)': 'orange', 'Abandonado': 'lightgray'}
    color = colores.get(f['Tipo'], 'red')
    
    html = f"""<div style="font-family: monospace; color: {{color}}; background: #000; padding: 10px; border: 1px solid {{color}};">
               <b>{{f['Tipo']}}: {{f['Nombre']}}</b><br><br>{{f['Info']}}</div>"""
    folium.Marker([f['Lat'], f['Lon']], popup=folium.Popup(html, max_width=300), icon=folium.Icon(color=color)).add_to(mapa)

st_folium(mapa, width="100%", height=700)
