import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import pandas as pd
import os
import requests
import re
import streamlit.components.v1 as components
from gtts import gTTS

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(page_title="Animus OS V6.1 - Santiago", layout="wide")

# Forzar el tema oscuro del Animus
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #00ff00; }
    .leaflet-tile { border: solid transparent 1px !important; }
    </style>
""", unsafe_allow_html=True)

if "ultima_transmision" not in st.session_state:
    st.session_state.ultima_transmision = None
    st.session_state.ultimo_nodo = None

# Configuración de IA (Shaun Hastings Core)
model = None
if "GEMINI_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        st.sidebar.error(f"Error de enlace IA: {e}")

# Base de datos
archivo_csv = "animus_data.csv"
if not os.path.exists(archivo_csv):
    pd.DataFrame(columns=["Nombre", "Pais", "Depto", "Lat", "Lon", "Info", "Tipo"]).to_csv(archivo_csv, index=False)
df = pd.read_csv(archivo_csv)

# --- 2. PERSONALIDAD DE SHAUN (BLINDADA) ---
def obtener_reporte(ciudad, pais_nombre, tipo_nodo):
    if model:
        try:
            prompt = (
                f"SISTEMA: Actúa ÚNICAMENTE como Shaun Hastings de Assassin's Creed. "
                f"LUGAR: {ciudad}, {pais_nombre}. TIPO DE NODO: {tipo_nodo}. "
                "INSTRUCCIONES: Responde en ESPAÑOL. Sé extremadamente sarcástico, pedante, británico y cínico. "
                "Búrlate de la seguridad del lugar y conéctalo con una conspiración de Abstergo o los Templarios. "
                "Usa negritas para enfatizar tu arrogancia. Mínimo 2 párrafos de puro veneno británico."
            )
            response = model.generate_content(prompt)
            return response.text if response.text else "Nodo encriptado por Abstergo."
        except Exception as e:
            return f"Error de Sistema: {str(e)}"
    return "IA fuera de línea."

# --- 3. SIDEBAR Y MÚSICA ALEATORIA ---
st.sidebar.title("🦅 Sincronización Táctica")

soundtracks = ["C_n-EcznZpE", "d5F9X6qeXco", "NVsSrJJIzDM", "RwDQZI_NRHA", "nyQEQM0CEBQ", "NEpjh30DLas", "PDVnsHC3ypQ"]

# Usamos %s para inyectar la lista sin romper las llaves {} del JavaScript
musica_js = """
<div id="player"></div>
<script>
  var tag = document.createElement('script');
  tag.src = "https://www.youtube.com/iframe_api";
  var firstScriptTag = document.getElementsByTagName('script')[0];
  firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
  var player;
  var soundtracks = %s;
  var lastVideo = "";
  function onYouTubeIframeAPIReady() { playRandomVideo(); }
  function playRandomVideo() {
    var filtered = soundtracks.filter(function(id) { return id !== lastVideo; });
    var nextVideo = filtered[Math.floor(Math.random() * filtered.length)];
    lastVideo = nextVideo;
    if (!player) {
        player = new YT.Player('player', {
            height: '1', width: '1', videoId: nextVideo,
            playerVars: { 'autoplay': 1, 'controls': 0 },
            events: { 'onStateChange': onPlayerStateChange }
        });
    } else { player.loadVideoById(nextVideo); }
  }
  function onPlayerStateChange(event) { if (event.data == YT.PlayerState.ENDED) { playRandomVideo(); } }
</script>
""" % (soundtracks)

with st.sidebar:
    st.caption("🎵 Frecuencia de la Hermandad (Shuffle)")
    components.html(musica_js, height=1)
    st.markdown("---")

with st.sidebar.form("atalaya"):
    nombre = st.text_input("Nombre del Punto:")
    pais = st.text_input("País:", value="Colombia")
    tipo_nodo = st.selectbox("Categoría:", ["Nodo Estándar", "Refugio (Amigos)", "Universidad", "Abandonado"])
    es_cg = st.checkbox("🛡️ Establecer como Cuartel General")
    
    if st.form_submit_button("Sincronizar Atalaya"):
        if "MAPS_KEY" in st.secrets:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={nombre},{pais}&key={st.secrets['MAPS_KEY']}&language=es"
            res = requests.get(url).json()
            if res["status"] == "OK":
                coords = res["results"][0]["geometry"]["location"]
                lat, lon = coords["lat"], coords["lng"]
                
                tipo_final = "CG" if es_cg else tipo_nodo
                info_shaun = obtener_reporte(nombre, pais, tipo_final)
                
                # Limpiar asteriscos para la voz de ElevenLabs
                info_audio = re.sub(r'[*_#]', '', info_shaun)
                
                # Gestión de Voz
                try:
                    if "ELEVENLABS_KEY" in st.secrets and "VOICE_ID" in st.secrets:
                        api_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                        v_res = requests.post(api_url, json={"text": info_audio, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.4, "similarity_boost": 0.8}}, headers={"xi-api-key": st.secrets["ELEVENLABS_KEY"]})
                        if v_res.status_code == 200:
                            with open("shaun_voice.mp3", "wb") as f: f.write(v_res.content)
                    else: gTTS(text=info_audio, lang='es', tld='es').save("shaun_voice.mp3")
                except: gTTS(text=info_audio, lang='es', tld='es').save("shaun_voice.mp3")

                # Lógica de CG único (Solo puede haber uno)
                if es_cg: df.loc[df['Tipo'] == 'CG', 'Tipo'] = 'Nodo Estándar'
                
                nueva_fila = pd.DataFrame([{"Nombre": nombre, "Pais": pais, "Depto": "SINC", "Lat": lat, "Lon": lon, "Info": info_shaun, "Tipo": tipo_final}])
                df = pd.concat([df, nueva_fila], ignore_index=True)
                df.to_csv(archivo_csv, index=False)
                
                st.session_state.ultima_transmision = info_shaun
                st.session_state.ultimo_nodo = f"{nombre.upper()} [{tipo_final}]"
                st.rerun()

# --- 4. MAPA Y TRANSMISIONES ---
if st.session_state.ultima_transmision:
    st.markdown(f"""<div style="background-color: #050505; border: 2px solid #00ff00; padding: 20px; border-radius: 8px;">
        <h3 style="color: #00ff00; font-family: monospace;">> TRANSMISIÓN ENTRANTE: {st.session_state.ultimo_nodo}</h3>
        <p style="color: #00ff00; font-family: monospace;">{st.session_state.ultima_transmision}</p>
    </div>""", unsafe_allow_html=True)
    if os.path.exists("shaun_voice.mp3"): st.audio("shaun_voice.mp3", format="audio/mp3", autoplay=True)
    if st.button("❌ Cerrar Transmisión"):
        st.session_state.ultima_transmision = None
        st.rerun()

# Mapa corregido
if not df.empty:
    lat_ini, lon_ini = df['Lat'].iloc[-1], df['Lon'].iloc[-1]
    mapa = folium.Map(location=[lat_ini, lon_ini], zoom_start=13, tiles="CartoDB dark_matter")
    for _, f in df.iterrows():
        col = 'green' if f['Tipo'] == 'CG' else 'blue' if f['Tipo'] == 'Universidad' else 'orange'
        folium.Marker([f['Lat'], f['Lon']], popup=f"{f['Tipo']}: {f['Nombre']}", icon=folium.Icon(color=col)).add_to(mapa)
    st_folium(mapa, width="100%", height=600)
