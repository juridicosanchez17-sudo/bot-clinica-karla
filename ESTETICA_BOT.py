import streamlit as st
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN Y ARQUITECTURA VISUAL ULTRA PREMIUM ---
st.set_page_config(page_title="Karla Soto | Clínica Estética", page_icon="✨", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,600&family=Montserrat:wght@300;400;500&display=swap');
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #FAFAFA; background-image: radial-gradient(circle at 50% 0%, #FFFFFF 0%, #F4F1EA 100%); font-family: 'Montserrat', sans-serif; }
    
    .encabezado-clinica { text-align: center; padding-top: 3rem; padding-bottom: 1rem; }
    .titulo-principal { font-family: 'Playfair Display', serif !important; color: #1A1A1A !important; font-size: 3.5rem !important; margin-bottom: 0px !important; letter-spacing: -1px; }
    .subtitulo { font-family: 'Montserrat', sans-serif; color: #A68A64; text-transform: uppercase; letter-spacing: 3px; font-size: 0.9rem; margin-top: 5px; font-weight: 500; }
    .linea-separadora { width: 50px; height: 2px; background-color: #A68A64; margin: 20px auto 40px auto; }
    
    /* Estilo del botón de lujo para entrar al chat */
    .stButton>button {
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        border: none !important;
        padding: 15px 30px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        letter-spacing: 1px !important;
        border-radius: 30px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: #A68A64 !important;
        box-shadow: 0 4px 15px rgba(166, 138, 100, 0.4) !important;
    }

    [data-testid="stFileUploader"] { background-color: rgba(255, 255, 255, 0.6) !important; border: 1px solid #D9D2C5 !important; border-radius: 12px !important; padding: 1.5rem !important; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px; }
    .stChatMessage { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LLAVES MAESTRAS ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
CORREO_MAESTRO = st.secrets["CORREO_MAESTRO"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 3. SISTEMA DE ALERTA ---
def notificar_a_karla_por_correo(resumen_chat, foto_adjunta=None):
    msg = MIMEMultipart()
    msg['From'] = CORREO_MAESTRO
    msg['To'] = CORREO_MAESTRO
    msg['Subject'] = "🚨 NUEVO PROSPECTO (+FOTO) - Bot Clínico"
    msg.attach(MIMEText(resumen_chat, 'plain'))
    if foto_adjunta is not None:
        try:
            foto_adjunta.seek(0)
            image_package = MIMEImage(foto_adjunta.read(), name=foto_adjunta.name)
            msg.attach(image_package)
        except Exception:
            pass 
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(CORREO_MAESTRO, GMAIL_APP_PASSWORD)
        server.sendmail(CORREO_MAESTRO, CORREO_MAESTRO, msg.as_string())
        server.quit()
    except Exception:
        pass 

# --- 4. CEREBRO GEMINI ---
PROMPT_SISTEMA = """Eres la asistente virtual exclusiva de la Dra. Karla Soto, médica experta en medicina estética avanzada. 
Tu tono es cálido, profesional, empático y de alta gama. 
TUS REGLAS DE OPERACIÓN:
1. Conoces los tratamientos principales: Toxina Botulínica (Botox), Ácido Hialurónico (relleno de labios, ojeras, rinomodelación), Armonización Facial, Bioestimuladores de colágeno y Faciales clínicos.
2. NUNCA das diagnósticos médicos definitivos ni prometes resultados exactos. Si el paciente subió una foto, dile que la Dra. Karla la revisará personalmente.
3. Tu objetivo principal (Embudo de Ventas): Explicar brevemente los beneficios e invitarlos a una "Cita de Valoración Personalizada" con la Dra. Karla.
4. CIERRE DE VENTA: Si el paciente muestra interés, dile que con gusto le coordinas su espacio y pídele: SU NOMBRE COMPLETO y SU NÚMERO DE WHATSAPP.
5. REGLA DE ORO DEL CIERRE: SOLO CUANDO el paciente te haya dado explícitamente su número de teléfono, confírmale que la Dra. Karla lo contactará hoy mismo. 
6. GATILLO DEL SISTEMA: Inmediatamente después de despedirte en el cierre exitoso (y SOLO si ya tienes el teléfono del paciente en la conversación), DEBES escribir exactamente esta etiqueta al final de tu mensaje: [VENTA_CERRADA_2026]"""

if "mensajes" not in st.session_state:
    st.session_state.mensajes = [{"role": "system", "content": PROMPT_SISTEMA}]
if "correo_enviado" not in st.session_state:
    st.session_state.correo_enviado = False
if "mostrar_chat" not in st.session_state:
    st.session_state.mostrar_chat = False # Switch para la vista de la página

# --- 5. ENRUTADOR VISUAL (LANDING PAGE VS CHAT) ---

if not st.session_state.mostrar_chat:
    # VISTA 1: PORTADA ELEGANTE (Sin cuadros de texto estorbosos)
    st.markdown("""
        <div class="encabezado-clinica">
            <h1 class="titulo-principal">Karla Soto</h1>
            <p class="subtitulo">Medicina Estética Avanzada</p>
            <div class="linea-separadora"></div>
            <p style="color: #6C7A89; font-size: 1.1rem; line-height: 1.6; margin-bottom: 40px; font-weight: 300;">
                Armonía, ciencia y vanguardia para resaltar tu mejor versión. <br>
                Evaluación médica personalizada.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Botón de enlace hacia la zona de conversión
    if st.button("✨ Sección de Preguntas y Citas"):
        st.session_state.mostrar_chat = True
        st.rerun()

else:
    # VISTA 2: EL ASISTENTE VIRTUAL (Solo visible cuando se solicita)
    st.markdown("""
        <div style="text-align: center; padding-top: 1rem;">
            <p class="subtitulo" style="font-size: 0.8rem;">Dra. Karla Soto</p>
            <div class="linea-separadora" style="margin: 10px auto 20px auto;"></div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⬅️ Volver a la portada"):
            st.session_state.mostrar_chat = False
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    foto_subida = st.file_uploader("Sube una foto de la zona a tratar para la evaluación previa de la Dra.", type=["jpg", "jpeg", "png"])

    for msj in st.session_state.mensajes:
        if msj["role"] != "system":
            avatar_icono = "👩‍⚕️" if msj["role"] == "assistant" else "👤"
            with st.chat_message(msj["role"], avatar=avatar_icono):
                st.markdown(msj["content"])

    user_input = st.chat_input("Escribe tu duda o solicita tu cita aquí...")

    if user_input:
        st.session_state.mensajes.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="👩‍⚕️"):
            with st.spinner("Procesando..."):
                try:
                    respuesta = client.chat.completions.create(
                        model="gemini-2.5-flash",
                        messages=st.session_state.mensajes
                    )
                    texto_crudo = respuesta.choices[0].message.content
                    hubo_cierre = "[VENTA_CERRADA_2026]" in texto_crudo
                    texto_final_limpio = texto_crudo.replace("[VENTA_CERRADA_2026]", "").strip()
                    
                    st.markdown(texto_final_limpio)
                    st.session_state.mensajes.append({"role": "assistant", "content": texto_final_limpio})

                    if hubo_cierre and not st.session_state.correo_enviado:
                        st.session_state.correo_enviado = True 
                        
                        historial_completo = ""
                        for m in st.session_state.mensajes:
                            if m["role"] == "user":
                                historial_completo += f"Paciente: {m['content']}\n"
                            elif m["role"] == "assistant":
                                historial_completo += f"IA: {m['content']}\n"
                                
                        resumen_chat = f"HISTORIAL COMPLETO:\n{'-'*40}\n{historial_completo}"
                        if foto_subida:
                            resumen_chat += "\n\n*(FOTO ADJUNTA)*"
                        
                        notificar_a_karla_por_correo(resumen_chat, foto_adjunta=foto_subida)
                        
                        try:
                            supabase.table("conversaciones").insert({
                                "historial": historial_completo, 
                                "cierre_exitoso": True
                            }).execute()
                        except Exception:
                            pass

                except Exception:
                    st.error("✨ Nuestras líneas están procesando múltiples solicitudes. Por favor, espera 2 minutos y vuelve a enviar tu mensaje.")
