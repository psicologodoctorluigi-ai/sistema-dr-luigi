import streamlit as st
import pandas as pd
from datetime import datetime
import random
import string
from docx import Document
import io
from streamlit_gsheets import GSheetsConnection

# -------------------------
# CONFIGURACIÓN
# -------------------------
st.set_page_config(page_title="Consultorio del Dr. Luigi's", layout="wide")

# Nombres de las columnas exactas que tendrá tu Google Sheet
COLUMNAS = [
    "Código", "Fecha", "Hora", "Nombre", "DNI", "Edad", "Sexo", "Cargo", 
    "Área", "Tiempo servicio", "Contrato", "Teléfono", "Motivo", "Solicitante", 
    "Descripción", "Tiempo problema", "Ámbito", "Actitud", "Observaciones", 
    "Área afectada", "Orientación", "Acuerdos", "Plan acción", "Fecha seguimiento", "Conclusión"
]

# -------------------------
# CONEXIÓN A GOOGLE SHEETS (Preparación)
# -------------------------
def cargar_datos():
    try:
        # Intenta conectar a Google Sheets
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Hoja 1", usecols=list(range(len(COLUMNAS))))
        return df.dropna(how="all") # Quita filas totalmente vacías
    except Exception:
        # Si falla (porque aún no configuramos las claves), devuelve un DataFrame vacío para que la app no se rompa
        return pd.DataFrame(columns=COLUMNAS)

def guardar_datos(nuevos_datos_dict):
    df_actual = cargar_datos()
    df_nuevo = pd.DataFrame([nuevos_datos_dict])
    df_actualizado = pd.concat([df_actual, df_nuevo], ignore_index=True)
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Hoja 1", data=df_actualizado)
        return True
    except Exception as e:
        st.error(f"⚠️ Aún falta configurar la conexión a Google Sheets para guardar permanentemente.")
        return False

# -------------------------
# FUNCIONES AUXILIARES
# -------------------------
def generar_codigo():
    fecha = datetime.now().strftime("%Y%m%d")
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"HC-{fecha}-{rand}"

def obtener_codigo_por_dni(dni, df):
    if not df.empty and dni in df["DNI"].astype(str).values:
        codigo = df[df["DNI"].astype(str) == dni]["Código"].iloc[0]
        return codigo, True
    return generar_codigo(), False

def generar_word_memoria(datos):
    doc = Document()
    doc.add_heading("FICHA DE ATENCIÓN DE CONSEJERÍA PSICOLÓGICA LABORAL", 0)

    doc.add_paragraph(f"Código: {datos['Código']}")
    doc.add_paragraph(f"Fecha: {datos['Fecha']}")
    doc.add_paragraph(f"Hora: {datos['Hora']}")
    doc.add_paragraph("Subgerencia de Seguridad Ciudadana")
    doc.add_paragraph("")

    for k, v in datos.items():
        if k not in ["Código", "Fecha", "Hora"]:
            doc.add_paragraph(f"{k}: {v}")

    # Guardar en la memoria RAM, no en el disco duro
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# -------------------------
# LOGIN
# -------------------------
def login():
    st.title("🔐 Acceso al Sistema")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user == "psicologo" and password == "1234": # Más adelante cambiaremos esto por algo más seguro
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# -------------------------
# MENÚ
# -------------------------
st.sidebar.title("🧠 Menú")
menu = st.sidebar.radio("Navegación", 
                        ["🏠 Inicio", "📋 Nueva Atención", "📈 Seguimiento", "📂 Historial", "🔎 Buscar por DNI", "🚪 Cerrar sesión"])

# Cargar base de datos actual
df_atenciones = cargar_datos()

# -------------------------
# INICIO
# -------------------------
if menu == "🏠 Inicio":
    st.title("Sistema de Psicología Organizacional")
    st.write("Subgerencia de Seguridad Ciudadana")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Atenciones", len(df_atenciones))
    
    if not df_atenciones.empty:
        col2.metric("Trabajadores únicos", df_atenciones["DNI"].nunique())
        col3.metric("Última atención", df_atenciones["Fecha"].iloc[-1])
    else:
        col2.metric("Trabajadores únicos", 0)
        col3.metric("Última atención", "-")

# -------------------------
# NUEVA ATENCIÓN
# -------------------------
if menu == "📋 Nueva Atención":
    st.title("📋 Ficha de Atención")

    fecha = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M:%S")

    dni_input = st.text_input("Ingrese DNI del trabajador para iniciar:")
    
    if dni_input:
        codigo, existe = obtener_codigo_por_dni(dni_input, df_atenciones)
        if existe:
            st.success(f"📁 Trabajador con historial previo - Código HC recuperado: {codigo}")
        else:
            st.info(f"🆕 Nuevo registro - Código HC asignado: {codigo}")

        with st.form("ficha", clear_on_submit=True):
            st.subheader("1. Datos Generales")
            
            # Campos ocultos o deshabilitados
            st.text_input("Código", value=codigo, disabled=True)
            dni_form = st.text_input("DNI (Confirmar)", value=dni_input)

            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre")
                edad = st.number_input("Edad", 18, 70)
                sexo = st.selectbox("Sexo", ["Masculino","Femenino","Otro"])
                cargo = st.text_input("Cargo")
            with col2:
                area = st.text_input("Área/Base")
                tiempo = st.text_input("Tiempo de servicio")
                contrato = st.selectbox("Tipo de contrato", ["CAS","Nombrado","Locador","Otro"])
                telefono = st.text_input("Teléfono")

            st.subheader("2. Motivo y Descripción")
            motivo = st.selectbox("Motivo", ["Estrés laboral","Conflicto con compañero","Problemas familiares","Otros"])
            solicitante = st.selectbox("Solicitante", ["Voluntario","Jefe","RRHH","Psicología","Otro"])
            descripcion = st.text_area("Descripción del problema")
            tiempo_prob = st.selectbox("Tiempo del problema", ["Días","Semanas","Meses","Años"])
            ambito = st.selectbox("Ámbito", ["Laboral","Familiar","Personal","Mixto"])

            st.subheader("3. Observación y Plan")
            actitud = st.selectbox("Actitud", ["Colaborador","Reservado","Evasivo","Ansioso","Otro"])
            observaciones = st.text_area("Observaciones clínicas")
            area_afectada = st.multiselect("Área afectada", ["Desempeño","Relaciones","Puntualidad","Ninguna"])
            orientacion = st.text_area("Orientación brindada")
            acuerdos = st.text_area("Acuerdos")
            plan = st.multiselect("Plan de Acción", ["Seguimiento","RRHH","Jefe","Sin seguimiento"])
            fecha_seg = st.date_input("Fecha de seguimiento")
            conclusion = st.text_area("Conclusión y recomendaciones")

            guardar = st.form_submit_button("💾 Guardar Atención")

        if guardar:
            datos = {
                "Código": codigo, "Fecha": fecha, "Hora": hora, "Nombre": nombre, "DNI": dni_form,
                "Edad": edad, "Sexo": sexo, "Cargo": cargo, "Área": area, "Tiempo servicio": tiempo,
                "Contrato": contrato, "Teléfono": telefono, "Motivo": motivo, "Solicitante": solicitante,
                "Descripción": descripcion, "Tiempo problema": tiempo_prob, "Ámbito": ambito,
                "Actitud": actitud, "Observaciones": observaciones, "Área afectada": ", ".join(area_afectada),
                "Orientación": orientacion, "Acuerdos": acuerdos, "Plan acción": ", ".join(plan),
                "Fecha seguimiento": str(fecha_seg), "Conclusión": conclusion
            }

            if guardar_datos(datos):
                st.success(f"✅ Atención guardada exitosamente en la nube.")
            
            # Generar Word para descargar
            archivo_word_memoria = generar_word_memoria(datos)
            st.download_button(
                label="📄 Descargar ficha en Word",
                data=archivo_word_memoria,
                file_name=f"Ficha_{codigo}_{fecha}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# -------------------------
# SEGUIMIENTO
# -------------------------
if menu == "📈 Seguimiento":
    st.title("📈 Seguimiento de Caso")

    dni_seg = st.text_input("Ingrese DNI para seguimiento:")
    
    if dni_seg:
        if not df_atenciones.empty:
            resultado = df_atenciones[df_atenciones["DNI"].astype(str) == dni_seg]
            
            if not resultado.empty:
                ultimo_registro = resultado.iloc[-1]
                st.success(f"Paciente: {ultimo_registro['Nombre']} | Código: {ultimo_registro['Código']}")
                st.info(f"Último motivo: {ultimo_registro.get('Motivo', 'No registrado')}")

                with st.form("ficha_seguimiento", clear_on_submit=True):
                    st.subheader("Evolución del Caso")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        estado_evolucion = st.selectbox("Estado actual", ["Mejoría notable", "Mejoría leve", "Estable/Sin cambios", "Retroceso/Empeoramiento"])
                        cumplimiento = st.select_slider("Cumplimiento de acuerdos previos", options=["Ninguno", "Bajo", "Medio", "Alto", "Total"])
                    
                    with col2:
                        nueva_actitud = st.selectbox("Actitud en sesión", ["Colaborador", "Resistente", "Abierto", "Ansioso", "Otro"])
                        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

                    st.subheader("Detalles de la sesión")
                    evolucion_detallada = st.text_area("Descripción de la evolución (¿Qué ha pasado desde la última vez?)")
                    nuevos_acuerdos = st.text_area("Nuevos acuerdos / Tareas")
                    
                    st.subheader("Plan de Acción")
                    proximo_paso = st.multiselect("Continuidad", ["Mantener seguimiento", "Alta administrativa", "Derivación externa", "Cierre de caso"])
                    fecha_prox = st.date_input("Próxima cita sugerida")

                    guardar_seg = st.form_submit_button("💾 Registrar Seguimiento")

                if guardar_seg:
                    datos_seg = {
                        "Código": ultimo_registro['Código'],
                        "Fecha": fecha_hoy,
                        "Hora": datetime.now().strftime("%H:%M:%S"),
                        "Nombre": ultimo_registro['Nombre'],
                        "DNI": dni_seg,
                        "Edad": ultimo_registro['Edad'],
                        "Sexo": ultimo_registro['Sexo'],
                        "Cargo": ultimo_registro['Cargo'],
                        "Área": ultimo_registro['Área'],
                        "Tiempo servicio": ultimo_registro.get('Tiempo servicio', '-'),
                        "Contrato": ultimo_registro.get('Contrato', '-'),
                        "Teléfono": ultimo_registro.get('Teléfono', '-'),
                        "Motivo": f"SEGUIMIENTO: {ultimo_registro.get('Motivo', '')}",
                        "Solicitante": ultimo_registro.get('Solicitante', '-'),
                        "Descripción": evolucion_detallada,
                        "Tiempo problema": "-",
                        "Ámbito": "-",
                        "Actitud": nueva_actitud,
                        "Observaciones": "-",
                        "Área afectada": "-",
                        "Orientación": "-",
                        "Acuerdos": nuevos_acuerdos,
                        "Plan acción": ", ".join(proximo_paso),
                        "Fecha seguimiento": str(fecha_prox),
                        "Conclusión": f"Estado: {estado_evolucion}. Cumplimiento: {cumplimiento}"
                    }
                    
                    if guardar_datos(datos_seg):
                        st.success("✅ Seguimiento registrado con éxito.")
                        
                    doc_seg = generar_word_memoria(datos_seg)
                    st.download_button("📄 Descargar Ficha de Seguimiento", doc_seg, file_name=f"Seguimiento_{dni_seg}_{fecha_hoy}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            else:
                st.error("No se encontró ningún registro previo con ese DNI. Debe crear una 'Nueva Atención' primero.")
        else:
            st.error("La base de datos está vacía. No se puede hacer seguimiento aún.")

# -------------------------
# HISTORIAL Y BÚSQUEDA
# -------------------------
if menu == "📂 Historial":
    st.title("Historial General")
    st.dataframe(df_atenciones, use_container_width=True)

if menu == "🔎 Buscar por DNI":
    st.title("Buscar paciente")
    dni_buscar = st.text_input("Ingrese DNI")
    if st.button("Buscar"):
        if not df_atenciones.empty:
            resultado = df_atenciones[df_atenciones["DNI"].astype(str) == dni_buscar]
            if not resultado.empty:
                st.dataframe(resultado, use_container_width=True)
            else:
                st.warning("No se encontraron registros para ese DNI.")
        else:
            st.info("La base de datos está vacía.")

# -------------------------
# LOGOUT
# -------------------------
if menu == "🚪 Cerrar sesión":
    st.session_state["login"] = False
    st.rerun()