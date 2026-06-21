# 🛡️ Tutor IA de Ciberseguridad con Arquitectura RAG y Automatización Event-Driven

Este proyecto consiste en un **Portal Educativo y Tutor Virtual Inteligente** especializado en ciberseguridad, desarrollado como Trabajo de Fin de Máster (TFM) en Inteligencia Artificial. La plataforma implementa una arquitectura **RAG (Retrieval-Augmented Generation)** descentralizada para interactuar con el temario oficial del curso y cuenta con un bus de automatización externo mediante webhooks para la distribución de contenido personalizado.

---

## 🚀 Características Principales

* **Autenticación y Control de Roles:** Sistema de inicio de sesión y registro respaldado por una base de datos relacional local (**SQLite**). Separa estrictamente las vistas y privilegios entre `alumno` y `profesor`.
* **Tutoría Inteligente basada en RAG:** Ventana de chat interactiva que consume documentos PDF de ciberseguridad (criptografía, redes, amenazas, etc.). Utiliza **LangChain** y los modelos de última generación de Google (**Gemini 2.5 Flash** y **Gemini Embeddings**).
* **Mitigación de Alucinaciones:** El *System Prompt* restringe las respuestas del LLM únicamente al contexto de los archivos adjuntos, garantizando rigor educativo.
* **Biblioteca e Interoperabilidad (Make.com):** Panel dedicado donde el alumno puede descargar el material original o solicitar un resumen estructurado con un solo clic. El resumen se genera mediante la IA y se despacha a través de un webhook hacia un escenario automatizado en **Make**, el cual da formato HTML y lo envía directamente al correo electrónico del alumno.
* **Panel de Seguimiento Docente:** Interfaz exclusiva para el rol `profesor` que permite auditar el listado de usuarios y monitorizar el historial completo de consultas/respuestas de los alumnos en tiempo real.

---

## 📐 Arquitectura del Sistema

El proyecto está diseñado bajo un enfoque híbrido *Pro-Code / Low-Code* enfocado en la eficiencia de cómputo y el desacoplamiento de servicios:

[ Interfaz Web: Streamlit ]
│
├─► [ Base de Datos Local: SQLite ] (Usuarios e Historial)
│
├─► [ Núcleo RAG: LangChain + FAISS Vector Store ] ◄── [ PDFs Locales ]
│         │
│         └─► [ Modelos de IA: Gemini API ]
│
└─► [ Webhook Outbound ] ──► [ Automatización: Make.com ] ──► [ Notificación: Gmail ]


1. **Ingesta y Segmentación:** Los PDFs se procesan con `RecursiveCharacterTextSplitter` en fragmentos (*chunks*) de 1000 caracteres con un solapamiento de 200 caracteres para preservar el contexto lineal.
2. **Indexación:** Se generan vectores semánticos mediante el modelo nativo de embeddings de Google y se almacenan temporalmente en una base de datos vectorial de alto rendimiento indexada por **FAISS**.
3. **Flujo de Ejecución Dirigido:** Al solicitar un resumen, se parametriza la cadena de LangChain mediante un mapeo de claves estrictas (`"question"`) forzando una consulta sintética enfocada en el documento seleccionado.

---

## 🛠️ Tecnologías Utilizadas

* **Framework de UI:** Streamlit
* **Orquestación de IA:** LangChain
* **Modelos de Lenguaje (LLM) y Embeddings:** Google Gemini API (`gemini-2.5-flash` y `models/gemini-embedding-2`)
* **Base de Datos Vectorial:** FAISS (Facebook AI Similarity Search)
* **Base de Datos Relacional:** SQLite3
* **Integración y Automatización Externa:** Make (antiguo Integromat) junto con la API de Gmail.
* **Procesamiento de Archivos:** PyPDF / PyPDFLoader y Glob.

---

## 📦 Instalación y Configuración

Sigue estos pasos para desplegar y probar la aplicación en tu entorno local:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/andreaacia02-sys/Tutor-IA-Ciberseguridad.git](https://github.com/andreaacia02-sys/Tutor-IA-Ciberseguridad.git)
cd Tutor-IA-Ciberseguridad
2. Instalar las dependencias requeridas
Se recomienda utilizar un entorno virtual de Python (venv):

Bash
pip install -r requirements.txt
(Asegúrate de que tu requirements.txt incluya: streamlit, langchain, langchain-community, langchain-google-genai, faiss-cpu, pypdf, python-dotenv y requests).

3. Configurar las variables de entorno
Crea un archivo llamado clave.env en la raíz del proyecto y añade tus credenciales privadas:

Fragmento de código
GOOGLE_API_KEY=tu_api_key_de_google_gemini_aqui
4. Lanzar la aplicación
Ejecuta el servidor local de Streamlit:

Bash
streamlit run app.py
