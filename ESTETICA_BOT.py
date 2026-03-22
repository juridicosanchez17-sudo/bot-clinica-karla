import streamlit as st
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# --- 1. CONFIGURACIÓN Y LIFTING VISUAL PREMIUM ---
st.set_page_config(page_title="Dra. Karla Soto - Clínica Estética", page_icon="✨", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Fondo global de la app (tono crema/nude muy sutil) */
    .stApp { background-color: #FDFBF7; }
    
    .encabezado-clinica {
        text-align: center; padding-bottom: 30px; padding-top: 20px;
        border-bottom: 1px solid #EAE3D9; margin-bottom: 20px;
    }
    .titulo-principal {
        color: #B9935A; /* Dorado elegante */
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 600; letter-spacing: 1px;
    }
    .subtitulo { color: #6C7A89; font-size: 1.1em; font-weight: 300; }
    
    /* Estilo del área de subida de archivos */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF; border: 1px dashed #B9935A; border-radius: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="encabezado-clinica">
        <h1 class="titulo-principal">✨ Dra. Karla Soto</h1>
        <p class="subtitulo">Medicina Estética Avanzada</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. LLAVES MAESTRAS (PRODUCCIÓN EN NUBE) ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
CORREO_MAESTRO = st.secrets["CORREO_MAESTRO"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]

client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=GEMINI_API_KEY)

# --- 3. SISTEMA DE ALERTA A GMAIL ---
def notificar_a_karla_por_correo(resumen_chat, foto_adjunta=None):
    msg = MIMEMultipart()
    msg['From'] = CORREO_MAESTRO
    msg['To'] = CORREO_MAESTRO
    msg['Subject'] = "🚨 NUEVO PROSPECTO (+FOTO) - Bot Clínico"

    msg.attach(MIMEText(resumen_chat, 'plain'))

    if foto_adjunta is not None:
        try:
            foto_adjunta.seek(0)
            image_data = foto_adjunta.read()
            image_package = MIMEImage(image_data, name=foto_adjunta.name)
            msg.attach(image_package)
        except Exception:
            pass # Silencioso en producción

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(CORREO_MAESTRO, GMAIL_APP_PASSWORD)
        texto = msg.as_string()
        server.sendmail(CORREO_MAESTRO, CORREO_MAESTRO, texto)
        server.quit()
    except Exception:
        pass 

# --- 4. CEREBRO GEMINI (Prompt Calibrado con Candado de Venta) ---
PROMPT_SISTEMA = """Eres la asistente virtual exclusiva de la Dra. Karla Soto, médica experta en medicina estética avanzada. 
Tu tono es cálido, profesional, empático y de alta gama. 

TUS REGLAS DE OPERACIÓN:
1. Conoces los tratamientos principales: Toxina Botulínica (Botox), Ácido Hialurónico (relleno de labios, ojeras, rinomodelación), Armonización Facial, Bioestimuladores de colágeno y Faciales clínicos.
2. NUNCA das diagnósticos médicos definitivos ni prometes resultados exactos. Si el paciente subió una foto, dile que la Dra. Karla la revisará personalmente.
3. Tu objetivo principal (Embudo de Ventas): Explicar brevemente los beneficios e invitarlos a una "Cita de Valoración Personalizada" con la Dra. Karla.
4. CIERRE DE VENTA: Si el paciente muestra interés, dile que con gusto le coordinas su espacio y pídele: SU NOMBRE COMPLETO y SU NÚMERO DE WHATSAPP.
5. REGLA DE ORO DEL CIERRE: SOLO CUANDO el paciente te haya dado explícitamente su número de teléfono, confírmale que la Dra. Karla lo contactará hoy mismo. 
6. GATILLO DEL SISTEMA: Inmediatamente después de despedirte en el cierre exitoso (y SOLO si ya tienes el teléfono del paciente en la conversación), DEBES escribir exactamente esta etiqueta al final de tu mensaje: [VENTA_CERRADA_2026]"""

# --- 5. INICIALIZACIÓN DE MEMORIA Y SWITCH DE SEGURIDAD ---
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [{"role": "system", "content": PROMPT_SISTEMA}]
if "correo_enviado" not in st.session_state:
    st.session_state.correo_enviado = False # El candado antispam

# --- 6. INTERFAZ DE USUARIO ---
foto_subida = st.file_uploader("Opcional: Sube una foto de la zona a tratar para la evaluación previa de la Dra.", type=["jpg", "jpeg", "png"])

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
                
                # Lógica del Candado Criptográfico
                hubo_cierre = "[VENTA_CERRADA_2026]" in texto_crudo
                
                # Limpiamos el texto para que el paciente NO vea la etiqueta técnica
                texto_final_limpio = texto_crudo.replace("[VENTA_CERRADA_2026]", "").strip()
                
                st.markdown(texto_final_limpio)
                st.session_state.mensajes.append({"role": "assistant", "content": texto_final_limpio})

                # Disparo único y extracción de historial total
                if hubo_cierre and not st.session_state.correo_enviado:
                    st.session_state.correo_enviado = True # Cierra el candado
                    
                    text_adicional = ""
                    if foto_subida is not None:
                         text_adicional = "\n\n*(FOTO ADJUNTA POR EL PACIENTE)*"
                    
                    # Armamos el historial completo para Karla
                    historial_completo = "HISTORIAL COMPLETO DE LA CONVERSACIÓN:\n" + "-"*40 + "\n"
                    for m in st.session_state.mensajes:
                        if m["role"] == "user":
                            historial_completo += f"Paciente: {m['content']}\n"
                        elif m["role"] == "assistant":
                            historial_completo += f"IA: {m['content']}\n"
                            
                    resumen_chat = f"{historial_completo}{text_adicional}"
                    
                    notificar_a_karla_por_correo(resumen_chat, foto_adjunta=foto_subida)

            except Exception as e:
                st.error("En este momento nuestros sistemas están procesando, intenta de nuevo en unos segundos.")
