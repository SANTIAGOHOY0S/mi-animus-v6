# --- PROCESAMIENTO DE VOZ NEURONAL (SHAUN HASTINGS) ---
            try:
                if "ELEVENLABS_KEY" in st.secrets and "VOICE_ID" in st.secrets:
                    api_url = f"https://api.elevenlabs.io/v1/text-to-speech/{st.secrets['VOICE_ID']}"
                    headers = {
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": st.secrets["ELEVENLABS_KEY"]
                    }
                    data = {
                        "text": info_audio,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.45,       # Menos estable = más emocional/sarcástico
                            "similarity_boost": 0.85, # Máximo parecido al clon de Fernando de Luis
                            "style": 0.5,             # Añade un poco de exageración al hablar
                            "use_speaker_boost": True
                        }
                    }
                    
                    v_res = requests.post(api_url, json=data, headers=headers)
                    
                    if v_res.status_code == 200:
                        with open("shaun_voice.mp3", "wb") as f:
                            f.write(v_res.content)
                    else:
                        st.sidebar.warning(f"ElevenLabs Error {v_res.status_code}. Usando respaldo gTTS.")
                        gTTS(text=info_audio, lang='es', tld='es').save("shaun_voice.mp3")
                else:
                    gTTS(text=info_audio, lang='es', tld='es').save("shaun_voice.mp3")
            except Exception as e:
                st.sidebar.error(f"Falla en el enlace vocal: {e}")
                gTTS(text=info_audio, lang='es', tld='es').save("shaun_voice.mp3")
