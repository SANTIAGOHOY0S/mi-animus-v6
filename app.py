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

# --- 1. CONFIGURACIÓN DE INTERFAZ (ELIMINACIÓN TOTAL DE BARRAS) ---
st.set_page_config(page_title="Animus OS V6.7", layout="wide", initial_sidebar_state="expanded")

# CSS AGRESIVO: Mantenemos el header transparente para no perder el botón de la barra lateral
st.markdown("""
    <style>
    #MainMenu, footer {visibility: hidden !important;}
    header {background-color: transparent !important;} 
    
    .stApp { background-color: #000000 !important; }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    .element-container, .stMarkdown { margin: 0 !important; padding: 0 !important; }
    html, body { overflow: hidden !important; background-color: #000000 !important; }
    .report-container { 
        background-color: #050505; border: 2px solid #00ff00; 
        padding: 20px; margin: 10px; border-radius: 8px; 
        font-family: 'Courier New', monospace; color: #00ff00;
    }
    </style>
""", unsafe_allow_html=True)

if "ultima_transmision" not in st.session_state:
    st.session_state.ultima_transmision = None
    st.session_state.ultimo_nodo = None

# --- 2. CONFIGURACIÓN DE IA Y DATOS ---
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

def obtener_reporte(ciudad, pais_nombre, tipo_nodo):
    if model:
        try:
            prompt = (
                f"Actúa como Shaun Hastings de Assassin's Creed. Eres un historiador británico, cínico, arrogante y extremadamente sarcástico. "
                f"Dame un reporte sobre {ciudad}, {pais_nombre} (tipo de nodo: {tipo_nodo}). "
                "Responde en ESPAÑOL. Búrlate de la seguridad y menciona a Abstergo. "
                "Mínimo 2 párrafos cargados de veneno británico."
            )
            response = model.generate_content(prompt)
            return response.text if response.text else "Datos borrados por Abstergo."
        except Exception as e: return f"Error: {str(e)}"
    return "Shaun está offline."

# --- 3. SIDEBAR Y MÚSICA (1x1 PIXEL) ---
st.sidebar.title("🦅 Sincronización Táctica")
tracks = ["C_n-EcznZpE", "d5F9X6qeXco", "NVsSrJJIzDM", "RwDQZI_NRHA", "nyQEQM0CEBQ", "NEpjh30DLas", "PDVnsHC3ypQ"]

musica_html = """
<div id="player"></div>
<script>
  var tag = document.createElement('script'); tag.src = "https://www.youtube.com/iframe_api";
  var firstScriptTag = document.getElementsByTagName('script')[0]; firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
  var player; var tracks = %s; var last = "";
  
  function onYouTubeIframeAPIReady() { playNext(); }
  
  function playNext() {
      var filtered = tracks.filter(t => t !== last);
      var next = filtered[Math.floor(Math.random() * filtered.length)]; last = next;
      
      if(!player) { 
          player = new YT.Player('player', { 
              height: '1', width: '1', videoId: next, 
              playerVars: { 'autoplay': 1, 'controls': 0, 'playsinline': 1 },
              events: { 
                  'onReady': function(e) { e.target.playVideo(); },
                  'onStateChange': (e) => { if(e.data == YT.PlayerState.ENDED) playNext(); } 
              } 
          });
      } else { player.loadVideoById(next); } 
  }

  // Activa el audio al interactuar con cualquier elemento de la página
  document.addEventListener('click', function() {
      if(player && typeof player.playVideo === 'function' && player.getPlayerState() !== 1) { player.playVideo(); }
  }, {once:true});
</script>
""" % (tracks)

with st.sidebar:
    components.html(musica_html, height=1)
    st.markdown("---")

with st.sidebar.form("atalaya"):
    nombre = st.text_input("Nombre del Punto:")
    pais = st.text_input("País:", value="Colombia")
    tipo = st.selectbox("Categoría:", ["Nodo Estándar", "Refugio (Amigos)", "Universidad", "Abandonado"])
    es_cg = st.checkbox("🛡️ Cuartel General")
    if st.form_submit_button("Sincronizar"):
        if "MAPS_KEY" in st.secrets:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={nombre},{pais}&key={st.secrets['MAPS_KEY']}&language=es"
            res = requests.get(url).json()
            if res["status"] == "OK":
                coords = res["results"][0]["geometry"]["location"]
                lat, lon = coords["lat"], coords["lng"]
                tipo_f = "CG" if es_cg else tipo
                txt_shaun = obtener_reporte(nombre, pais, tipo_f)
                audio_clean = re.sub(r'[*_#]', '', txt_shaun)
                try:
                    if "ELEVENLABS_KEY" in st.secrets:
                        url_ev = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                        h = {"xi-api-key": st.secrets["ELEVENLABS_KEY"]}
                        data_voz = {
                            "text": audio_clean, 
                            "model_id": "eleven_multilingual_v2",
                            "voice_settings": {"stability": 0.45, "similarity_boost": 0.85}
                        }
                        v_res = requests.post(url_ev, json=data_voz, headers=h)
                        if v_res.status_code == 200:
                            with open("shaun_voice.mp3", "wb") as f: f.write(v_res.content)
                except: gTTS(text=audio_clean, lang='es', tld='es').save("shaun_voice.mp3")
                if es_cg: df.loc[df['Tipo'] == 'CG', 'Tipo'] = 'Nodo Estándar'
                new_row = pd.DataFrame([{"Nombre": nombre, "Pais": pais, "Depto": "SINC", "Lat": lat, "Lon": lon, "Info": txt_shaun, "Tipo": tipo_f}])
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(archivo_csv, index=False)
                st.session_state.ultima_transmision = txt_shaun
                st.session_state.ultimo_nodo = f"{nombre.upper()} [{tipo_f}]"
                st.rerun()

# --- 4. RENDERIZADO DEL MAPA ---
if st.session_state.ultima_transmision:
    st.markdown(f'<div class="report-container"><h3>> TRANSMISIÓN: {st.session_state.ultimo_nodo}</h3><p>{st.session_state.ultima_transmision}</p></div>', unsafe_allow_html=True)
    if os.path.exists("shaun_voice.mp3"): st.audio("shaun_voice.mp3", format="audio/mp3", autoplay=True)
    if st.button("❌ Cerrar"):
        st.session_state.ultima_transmision = None
        st.rerun()

l_lat = df['Lat'].iloc[-1] if not df.empty else 4.711
l_lon = df['Lon'].iloc[-1] if not df.empty else -74.072

# CONFIGURACIÓN DEL ANCESTRO: BLOQUEO ESTRICTO DE CÁMARA
m = folium.Map(
    location=[l_lat, l_lon], 
    zoom_start=5, 
    min_zoom=4,           # Límite matemático para no ver el vacío
    max_bounds=True,      # Bloquea el desplazamiento fuera de los límites
    min_lat=-90,          # Polo Sur
    max_lat=90,           # Polo Norte
    min_lon=-180,         # Borde Oeste
    max_lon=180,          # Borde Este
    tiles=None,
    world_copy_jump=True, 
    no_wrap=False         
)

folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attr='&copy; CARTO',
    name="CartoDB Dark Matter",
    no_wrap=False 
).add_to(m)

for _, f in df.iterrows():
    c = 'green' if f['Tipo'] == 'CG' else 'blue' if f['Tipo'] == 'Universidad' else 'orange'
    folium.Marker([f['Lat'], f['Lon']], popup=f"{f['Tipo']}: {f['Nombre']}", icon=folium.Icon(color=c)).add_to(m)

st_folium(m, width="100%", height=800, returned_objects=[])
