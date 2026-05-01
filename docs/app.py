import streamlit as st
import sqlite3
import os
import glob
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv("clave.env")

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

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
    cursor.execute('SELECT id, nombre FROM usuarios WHERE email=? AND password=?', (email, hashed_pwd))
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
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    return vectorstore

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
                        st.success("Acceso concedido.")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")
    else:
        st.success(f"Sesión iniciada como:\n**{st.session_state['user_name']}**")
        if st.button("Cerrar Sesión"):
            del st.session_state['user_id']
            del st.session_state['user_name']
            if "messages" in st.session_state:
                del st.session_state["messages"]
            st.rerun()
            
    st.divider()
    st.header("Configuración del Tutor")
    st.write("El API Key se carga automáticamente desde el archivo clave.env.")
    
    api_key_env = os.environ.get("GOOGLE_API_KEY", "")
    api_key = st.text_input("Ingresa tu GOOGLE_API_KEY (Gemini)", value=api_key_env, type="password")
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    else:
        st.warning("No se encontró la API Key en clave.env ni ha sido ingresada.")

# Flujo Principal
if 'user_id' not in st.session_state:
    st.info("👋 ¡Bienvenido al portal del Tutor IA de Ciberseguridad!\n\nPor favor, **inicia sesión** o **regístrate** en el menú lateral izquierdo para comenzar a chatear.")
    st.stop()

st.markdown(f"¡Hola de nuevo, {st.session_state['user_name']}! Pregúntame sobre los temas del curso.")

# Cargar el conocimiento (RAG)
vectorstore = load_and_index_pdfs()

if vectorstore is None:
    st.error("No se encontraron documentos PDF en el directorio actual. Asegúrate de que los archivos estén en la misma carpeta que app.py.")
    st.stop()

retriever = vectorstore.as_retriever()

# Configurar LLM usando Gemini
# Usamos el modelo rápido y eficiente (Gemini 2.5 Flash)
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
