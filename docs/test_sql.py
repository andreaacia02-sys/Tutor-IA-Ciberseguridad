import sqlite3
import pandas as pd
conn = sqlite3.connect('database.db')
query = "SELECT h.fecha as Fecha, u.nombre as Alumno, h.pregunta_alumno as Pregunta, h.respuesta_tutor as 'Respuesta de la IA' FROM historial h JOIN usuarios u ON h.usuario_id = u.id ORDER BY h.fecha DESC"
try:
    df = pd.read_sql_query(query, conn)
    print(df.head())
except Exception as e:
    print(e)
