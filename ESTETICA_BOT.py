import streamlit as st
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# --- 1. CONFIGURACIÓN Y LIFTING VISUAL ---
st.set_page_config(page_title="Dra. Karla Soto - Clínica Estética", page_icon="✨", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .encabezado-clinica {
        text-align: center;
        padding-bottom: 20px;
    }
    .titulo-principal {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .subtitulo {
        color: #7f8c8d;
        font-size: 1.1em;
        font-weight: 400;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="encabezado-clinica">
        <h1 class="titulo-principal">✨ Dra. Karla Soto</h1>
        <p class="subtitulo">Medicina Estética Avanzada</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. LLAVES MAESTRAS (VERSIÓN PRODUCCIÓN NUBE) ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
CORREO_MAESTRO = st.secrets["CORREO_MAESTRO"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]

client = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=GEMINI_API_KEY)

# --- 3. SISTEMA DE ALERTA A GMAIL (CON SOPORTE MULTIMEDIA) ---
def notificar_a_karla_por_correo(resumen_chat, foto_adjunta=None):
    msg = MIMEMultipart()
    msg['From'] = CORREO_MAESTRO
    msg['To'] = CORREO_MAESTRO
    msg['Subject'] = "🚨 NUEVO PROSPECTO (+FOTO) - Bot Clínico"

    cuerpo_correo = f"El asistente virtual ha capturado un prospecto para valoración.\n\nDetalles exactos de la interacción:\n{resumen_chat}"
    msg.attach(MIMEText(cuerpo_correo, 'plain'))

    # LÓGICA DE EXTRACCIÓN Y ADJUNTO DE IMAGEN
    if foto_adjunta is not None:
        try:
            foto_adjunta.seek(0) # Aseguramos leer la imagen desde el principio
            image_data = foto_adjunta.read()
            image_package = MIMEImage(image_data, name=foto_adjunta.name)
            msg.attach(image_package)
        except Exception as e:
            pass # Operación silenciosa si la imagen falla

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(CORREO_MAESTRO, GMAIL_APP_PASSWORD)
        texto = msg.as_string()
        server.sendmail(CORREO_MAESTRO, CORREO_MAESTRO, texto)
        server.quit()
        st.toast("✔️ Alerta y foto enviadas a la bandeja de Karla", icon="📧")
    except Exception as e:
        st.error(f"Error técnico bloqueando el correo: {e}")

# --- 4. CEREBRO GEMINI (Prompt Maestro) ---
PROMPT_SISTEMA = """Eres la asistente virtual exclusiva de la Dra. Karla Soto, médica experta en medicina estética avanzada. 
Tu tono es cálido, profesional, empático y de alta gama. 

TUS REGLAS DE OPERACIÓN:
1. Conoces los tratamientos principales: Toxina Botulínica (Botox), Ácido Hialurónico (relleno de labios, ojeras, rinomodelación), Armonización Facial, Bioestimuladores de colágeno y Faciales clínicos.
2. NUNCA das diagnósticos médicos definitivos ni prometes resultados exactos, ya que cada rostro es único. Si el paciente menciona que subió una foto, dile que la Dra. Karla la revisará personalmente.
3. Tu objetivo principal (Embudo de Ventas): Explicar brevemente los beneficios del tratamiento que pregunten y SIEMPRE invitarlos a una "Cita de Valoración Personalizada" con la Dra. Karla.
4. CIERRE DE VENTA: Si el paciente muestra interés en agendar, pregunta precios o disponibilidad, dile que con gusto le coordinas su espacio y pídele: SU NOMBRE COMPLETO y SU NÚMERO DE WHATSAPP.
5. Una vez que el paciente escriba su número de teléfono, confírmale amablemente que has registrado sus datos y que la Dra. Karla Soto (o su equipo) le escribirá por WhatsApp hoy mismo. Despídete cordialmente."""

if "mensajes" not in st.session_state:
    st.session_state.mensajes = [{"role": "system", "content": PROMPT_SISTEMA}]

# --- 5. INTERFAZ DE USUARIO ---

# Componente de subida de imagen
foto_subida = st.file_uploader("Opcional: Sube una foto de la zona a tratar para que la Dra. la evalúe (Privacidad 100% garantizada).", type=["jpg", "jpeg", "png"])

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
                texto_final = respuesta.choices[0].message.content
                st.markdown(texto_final)
                st.session_state.mensajes.append({"role": "assistant", "content": texto_final})

                # GATILLO DE CIERRE RECONFIGURADO
                if "comunicará" in texto_final.lower() or "cita" in texto_final.lower() or "contacto" in texto_final.lower() or "teléfono" in user_input.lower():
                    
                    text_adicional = ""
                    if foto_subida is not None:
                         text_adicional = "\n\n*(¡Atención! El paciente ha adjuntado una FOTO en este correo para evaluación previa)*"
                    
                    resumen_chat = f"Paciente dice: {user_input}\n\nIA respondió: {texto_final}{text_adicional}"
                    
                    # Disparo del correo pasando la foto como argumento
                    notificar_a_karla_por_correo(resumen_chat, foto_adjunta=foto_subida)

            except Exception as e:
                st.error("En este momento nuestros sistemas están procesando, intenta de nuevo en unos segundos.")