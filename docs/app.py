import streamlit as st
import sqlite3
import os
import glob
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import requests

# Función global para conectar con Make
def enviar_resumen_por_email(email_alumno, nombre_alumno, texto_resumen):
    MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "https://hook.eu1.make.com/v6993o44itau6f4hpmntcdnp2s6i1dpg")
    
    payload = {
        "email": email_alumno,
        "nombre": nombre_alumno,
        "resumen": texto_resumen
    }
    
    try:
        response = requests.post(MAKE_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"Error enviando a Make: {e}")
        return False


# Cargar variables de entorno
load_dotenv("clave.env")

api_key_env = os.getenv("GOOGLE_API_KEY")
if not api_key_env:
    print("Error crítico: GOOGLE_API_KEY no encontrada en clave.env")
    st.error("Error de configuración del servidor.")
    st.stop()

st.set_page_config(page_title="Tutor IA: Ciberseguridad", page_icon="🛡️", initial_sidebar_state="expanded")

# Configuración de Base de Datos
DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Crear tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Añadir columna rol si no existe (Migración)
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT DEFAULT 'alumno'")
    except sqlite3.OperationalError:
        pass # La columna ya existe
    # Crear tabla de historial
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            fecha TEXT,
            pregunta_alumno TEXT,
            respuesta_tutor TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(nombre, email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)
    try:
        cursor.execute('INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)', (nombre, email, hashed_pwd))
        conn.commit()
        return True, "Registro exitoso. Ahora puedes iniciar sesión."
    except sqlite3.IntegrityError:
        return False, "El correo electrónico ya está registrado."
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)
    cursor.execute('SELECT id, nombre, rol FROM usuarios WHERE email=? AND password=?', (email, hashed_pwd))
    user = cursor.fetchone()
    conn.close()
    return user

def save_to_db(usuario_id, pregunta, respuesta):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO historial (usuario_id, fecha, pregunta_alumno, respuesta_tutor)
        VALUES (?, ?, ?, ?)
    ''', (usuario_id, fecha, pregunta, respuesta))
    conn.commit()
    conn.close()

# Inicializar Base de Datos
init_db()


st.markdown("""
<style>
    /* 1. Fondo general: Gradiente suave Azul Cielo y Lavanda */
    .stApp {
        background: linear-gradient(135deg, #E0F2FE 0%, #F5F3FF 100%) !important;
        color: #1E293B !important; /* Gris oscuro para lectura fácil */
    }
    
    /* 2. Títulos y textos generales (Protegiendo iconos) */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Courier New', Courier, monospace !important;
        color: #F472B6 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Aplicar fuente a textos, pero EXCLUIR los iconos de Material Design */
    p, label, span:not(.material-icons):not(.notranslate) {
        font-family: 'Courier New', Courier, monospace !important;
        color: #334155 !important;
    }
    
    /* 3. Sidebar: Gris claro profesional */
    [data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        border-right: 1px solid #E2E8F0 !important;
    }


    /* 4. Botones: Rosa Chicle Vibrante con Texto Blanco */
    .stButton > button {
        background-color: #F472B6 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 2rem !important;
        transition: all 0.3s ease !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px -1px rgba(244, 114, 182, 0.3) !important;
    }

    .stButton > button:hover {
        background-color: #DB2777 !important; /* Un rosa un poco más oscuro al pasar el ratón */
        box-shadow: 0 10px 15px -3px rgba(244, 114, 182, 0.4) !important;
        transform: translateY(-1px);
    }
    
    /* 5. Inputs (Email, Contraseña, Chat): Blancos y limpios */
    input, textarea, [data-testid="stChatInput"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
    }

    input:focus, textarea:focus {
        border-color: #38BDF8 !important; /* Azul brillante al escribir */
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    }
    
    /* 6. Burbujas de Chat y Formularios: Estilo "Glassmorphism" */
    [data-testid="stForm"], .stChatMessage {
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        background-color: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-radius: 12px !important;
    }

    /* 7. Pestañas y selectores: Rosa y Azul */
    .stTabs [aria-selected="true"] {
        color: #F472B6 !important;
        border-bottom: 2px solid #F472B6 !important;
    }

    /* Control de la barra lateral (flechita) */
    [data-testid="collapsedControl"] {
        color: #F472B6 !important;
        background-color: #FFFFFF !important;
    }
</style>

""", unsafe_allow_html=True)

st.markdown(r"""
<div style="text-align: center; color: #F472B6; text-shadow: 0 0 5px #F472B6; font-family: monospace; white-space: pre; font-size: 14px; font-weight: bold;">
  _____            _             ___  ___ 
 |_   _|   _ | |_  ___  _ _   |_ _||   \
   | |  | || ||  _|/ _ \| '_|   | | | |) |
   |_|   \_,_| \__|\___/|_|    |___||___/ 
                                          
      C I B E R S E G U R I D A D         
</div>
<hr style="border-top: 1px dashed #F472B6;">
""", unsafe_allow_html=True)

# Sidebar de Autenticación y Configuración
with st.sidebar:
    st.header("🔑 Autenticación")
    
    if 'user_id' not in st.session_state:
        auth_mode = st.radio("Elige una opción", ["Iniciar Sesión", "Registrarse"])
        
        if auth_mode == "Registrarse":
            with st.form("register_form"):
                st.subheader("Crear Cuenta nueva")
                new_name = st.text_input("Nombre completo")
                new_email = st.text_input("Email")
                new_password = st.text_input("Contraseña", type="password")
                submit_register = st.form_submit_button("Registrarse")
                if submit_register:
                    if new_name and new_email and new_password:
                        success, msg = register_user(new_name, new_email, new_password)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Por favor completa todos los campos.")
                        
        elif auth_mode == "Iniciar Sesión":
            with st.form("login_form"):
                st.subheader("Iniciar Sesión")
                login_email = st.text_input("Email")
                login_password = st.text_input("Contraseña", type="password")
                submit_login = st.form_submit_button("Entrar")
                if submit_login:
                    user = authenticate_user(login_email, login_password)
                    if user:
                        st.session_state['user_id'] = user[0]
                        st.session_state['user_name'] = user[1]
                        st.session_state['user_rol'] = user[2]
                        st.session_state['user_email'] = login_email  # <-- ¡ESTA LÍNEA ES CLAVE!
                        st.success("Acceso concedido.")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")
    else:
        st.success(f"Sesión iniciada como:\n**{st.session_state['user_name']}**\n*(Rol: {st.session_state.get('user_rol', 'alumno')})*")
        if st.button("Cerrar Sesión"):
            for key in ['user_id', 'user_name', 'user_rol', 'messages', 'student_nav']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        # Selector de navegación para el alumno
        if st.session_state.get('user_rol', 'alumno') == 'alumno':
            st.write("---")
            st.radio(
                "Menú de Navegación",
                ["💬 Chat con el Tutor", "📚 Biblioteca y Resúmenes"],
                key="student_nav"
            )

# Flujo Principal
if 'user_id' not in st.session_state:
    st.info("👋 ¡Bienvenido al portal del Tutor IA de Ciberseguridad!\n\nPor favor, **inicia sesión** o **regístrate** en el menú lateral izquierdo para comenzar a chatear.")
    st.stop()

st.markdown(f"¡Hola de nuevo, {st.session_state['user_name']}!")

# --------------------------------------------------------------------------------
# PANEL DE PROFESOR (Aislado de cualquier librería de IA)
# --------------------------------------------------------------------------------
if st.session_state.get('user_rol') == 'profesor':
    st.header("📋 Panel de Seguimiento")
    st.write("Visualización de métricas y consultas de los alumnos.")
    
    # Creamos las dos pestañas solicitadas
    tab1, tab2 = st.tabs(["Listado de Usuarios", "Historial de Consultas"])
    
    with tab1:
        conn = sqlite3.connect(DB_NAME)
        df_users = pd.read_sql_query("SELECT id, nombre, email, rol FROM usuarios", conn)
        conn.close()
        st.dataframe(df_users, use_container_width=True)
        
    with tab2:
        conn = sqlite3.connect(DB_NAME)
        query = '''
            SELECT h.fecha as Fecha, u.nombre as Alumno, h.pregunta_alumno as Pregunta, h.respuesta_tutor as 'Respuesta de la IA'
            FROM historial h
            JOIN usuarios u ON h.usuario_id = u.id
            ORDER BY h.fecha DESC
        '''
        df_history = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df_history.empty:
            df_clean = df_history.astype(str)
            st.dataframe(df_clean, use_container_width=True)
        else:
            st.info("Aún no hay actividad de alumnos registrada.")
            
    # Finaliza la ejecución para el profesor, garantizando que el resto del código (IA) NO se evalúe ni cargue en memoria.
    st.stop()


# --------------------------------------------------------------------------------
# PANEL DE ALUMNO (Carga las librerías de IA bajo demanda)
# --------------------------------------------------------------------------------
with st.spinner("Cargando librerías de Inteligencia Artificial..."):
    # Movimos TODAS las importaciones de IA aquí para que solo ocurran si el usuario es un alumno.
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser

@st.cache_resource(show_spinner="Indexando documentos (esto puede tardar la primera vez)...")
def load_and_index_pdfs():
    pdf_files = glob.glob("*.pdf")
    documents = []
    for pdf_file in pdf_files:
        try:
            loader = PyPDFLoader(pdf_file)
            documents.extend(loader.load())
        except Exception as e:
            st.warning(f"Error cargando {pdf_file}: {e}")
    
    if not documents:
        return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    
    import time
    vectorstore = None
    
    progress_text = "Indexando documentos (evitando límites de API)..."
    progress_bar = st.progress(0, text=progress_text)
    
    # Procesar en lotes para no saturar la API
    batch_size = 25
    
    for i in range(0, len(splits), batch_size):
        batch = splits[i:i+batch_size]
        
        retries = 3
        while retries > 0:
            try:
                # 1. Extraemos textos y metadatos para controlar nosotros mismos el proceso
                texts = [doc.page_content for doc in batch]
                metadatas = [doc.metadata for doc in batch]
                
                # 2. Llamada nativa a la API para forzar que devuelva la lista correcta de embeddings
                import google.generativeai as genai
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                res = genai.embed_content(model="models/gemini-embedding-2", content=texts)
                batch_embeddings = res["embedding"]
                
                # 3. Verificamos que la longitud coincida (Solución al ValueError)
                if len(texts) != len(batch_embeddings):
                    raise ValueError(f"Desajuste: documents={len(texts)}, embeddings={len(batch_embeddings)}")
                
                # 4. Inyectamos en FAISS manualmente emparejando texto y vector
                text_embeddings = list(zip(texts, batch_embeddings))
                batch_vectorstore = FAISS.from_embeddings(text_embeddings, embeddings, metadatas=metadatas)
                
                if vectorstore is None:
                    vectorstore = batch_vectorstore
                else:
                    vectorstore.merge_from(batch_vectorstore)
                    
                break # Si tiene éxito, salir del bucle de reintento
                
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    time.sleep(15) # Esperar 15 segundos extra si la cuota explota
                    retries -= 1
                else:
                    # Robustez solicitada: atrapar error, no crashear, y decir qué documento falló
                    source_doc = batch[0].metadata.get('source', 'Desconocido') if batch else 'Desconocido'
                    st.warning(f"Error procesando lote cerca del documento '{source_doc}'. Detalle: {str(e)}")
                    break # Abortar este lote específico y seguir con el siguiente
                    
        # Respetar el límite de 15 Requests Per Minute (~4 segundos por request)
        time.sleep(4)
        
        # Actualizar progreso en la UI
        current_progress = min(1.0, (i + batch_size) / len(splits))
        progress_bar.progress(current_progress, text=f"Indexando conocimiento: {min(i + batch_size, len(splits))} de {len(splits)} fragmentos...")

    progress_bar.empty()
    return vectorstore

# Cargar el conocimiento (RAG)
vectorstore = load_and_index_pdfs()

if vectorstore is None:
    st.error("No se encontraron documentos PDF en el directorio actual. Asegúrate de que los archivos estén en la misma carpeta que app.py.")
    st.stop()

retriever = vectorstore.as_retriever()

# Configurar LLM usando Gemini
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

system_prompt = (
    "Eres un Profesor Virtual de Ciberseguridad. "
    "Tu única base de conocimiento oficial es el contexto proporcionado, el cual proviene de los documentos PDF del curso. "
    "Responde SIEMPRE basándote EXCLUSIVAMENTE en este conocimiento. "
    "Si la pregunta no está relacionada con el contexto o no puedes encontrar la respuesta en él, "
    "indica amablemente que la pregunta está fuera del temario oficial del curso y que solo puedes responder basándote en el material proporcionado. "
    "No intentes adivinar ni uses información externa. Mantén un tono profesional, educativo y alentador.\n\n"
    "Contexto oficial de los documentos:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Función helper para extraer la query de forma segura si se pasa un diccionario o string
def obtener_texto_query(x):
    if isinstance(x, dict):
        return x.get("input", x.get("question", x.get("query", "")))
    return str(x)

rag_chain = (
    {"context": obtener_texto_query | retriever | format_docs, "input": obtener_texto_query}
    | prompt
    | llm
    | StrOutputParser()
)

# Obtener la navegación del alumno
nav_option = st.session_state.get('student_nav', '💬 Chat con el Tutor')

if nav_option == "💬 Chat con el Tutor":
    st.markdown("Pregúntame sobre los temas del curso.")
    
    # Inicializar el estado de la sesión para el historial de chat de la UI
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar mensajes anteriores en la UI
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Interfaz de entrada del chat sin comando /resumen
    if user_input := st.chat_input("Escribe tu pregunta sobre ciberseguridad aquí..."):
        # Mostrar mensaje del usuario en la interfaz
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            with st.spinner("Consultando la base de conocimiento oficial..."):
                try:
                    answer = rag_chain.invoke(user_input)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    # Guardar en SQLite con el ID del usuario
                    save_to_db(st.session_state['user_id'], user_input, answer)
                except Exception as e:
                    st.error(f"Error de conexión con el modelo: {str(e)}")

elif nav_option == "📚 Biblioteca y Resúmenes":
    st.header("📚 Biblioteca de Apuntes")
    st.write("Aquí puedes descargar los documentos oficiales del curso o solicitar un resumen estructurado por correo electrónico.")
    
    pdf_files = glob.glob("*.pdf")
    
    if not pdf_files:
        st.info("No se encontraron documentos PDF en el directorio del curso.")
    else:
        for idx, pdf_file in enumerate(sorted(pdf_files)):
            try:
                size_bytes = os.path.getsize(pdf_file)
                size_kb = size_bytes / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            except Exception:
                size_str = "Tamaño desconocido"
            
            with st.container():
                st.markdown(f"### 📄 {pdf_file}  `({size_str})`")
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    try:
                        with open(pdf_file, "rb") as f:
                            pdf_data = f.read()
                        st.download_button(
                            label="⬇️ Descargar PDF",
                            data=pdf_data,
                            file_name=pdf_file,
                            mime="application/pdf",
                            key=f"download_{idx}_{pdf_file}"
                        )
                    except Exception as e:
                        st.error(f"Error al leer el archivo para descarga: {e}")
                        
                with col2:
                    if st.button("Solicitar Resumen por Email", key=f"res_{pdf_file}"):
                        with st.spinner("Generando resumen..."):
                            try:
                                # 1. Creamos la petición en el formato de diccionario con la clave exacta que exige la cadena ("question")
                                peticion_dict = {"question": f"Por favor, haz un resumen detallado, estructurado y educativo basado en el documento: {pdf_file}"}
                                
                                # 2. Invocamos la cadena original pasándole el diccionario correcto
                                answer = rag_chain.invoke(peticion_dict)
                                
                                # 3. Convertimos la respuesta en un string limpio y quitamos espacios en blanco
                                texto_final_resumen = str(answer).strip()
                                
                                # 4. Validamos que no esté vacío y disparamos a Make
                                if texto_final_resumen and len(texto_final_resumen) > 10:
                                    email_actual = st.session_state.get('user_email', 'alumno@correo.com')
                                    nombre_actual = st.session_state.get('user_name', 'Alumno')
                                    
                                    exito = enviar_resumen_por_email(email_actual, nombre_actual, texto_final_resumen)
                                    
                                    if exito:
                                        st.success(f"¡Resumen enviado con éxito por email a {email_actual}!")
                                    else:
                                        st.error("El resumen se generó pero hubo un problema al conectarse con Make. Comprueba la URL de tu webhook.")
                                else:
                                    st.error("El modelo devolvió una respuesta vacía o con un formato incorrecto.")
                                    
                            except Exception as e:
                                st.error(f"Error al invocar el modelo RAG: {str(e)}")
            st.write("---")
