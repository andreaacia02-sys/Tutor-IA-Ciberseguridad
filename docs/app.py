import streamlit as st
import sqlite3
import os
import glob
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Cargar variables de entorno
load_dotenv("clave.env")

api_key_env = os.getenv("GOOGLE_API_KEY")
if not api_key_env:
    print("Error crítico: GOOGLE_API_KEY no encontrada en clave.env")
    st.error("Error de configuración del servidor.")
    st.stop()

st.set_page_config(page_title="Tutor IA: Ciberseguridad", page_icon="🛡️")

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

st.title("🛡️ Tutor IA: Ciberseguridad")

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
                        st.success("Acceso concedido.")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")
    else:
        st.success(f"Sesión iniciada como:\n**{st.session_state['user_name']}**\n*(Rol: {st.session_state.get('user_rol', 'alumno')})*")
        if st.button("Cerrar Sesión"):
            for key in ['user_id', 'user_name', 'user_rol', 'messages']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

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
st.markdown("Pregúntame sobre los temas del curso.")

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

rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Inicializar el estado de la sesión para el historial de chat de la UI
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores en la UI
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Interfaz de entrada del chat
if user_input := st.chat_input("Escribe tu pregunta sobre ciberseguridad aquí..."):
    # Mostrar mensaje del usuario
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Mostrar respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("Consultando la base de conocimiento oficial..."):
            try:
                answer = rag_chain.invoke(user_input)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Guardar en SQLite (Requisito) con el ID del usuario
                save_to_db(st.session_state['user_id'], user_input, answer)
            except Exception as e:
                st.error(f"Error de conexión con el modelo: {str(e)}")
