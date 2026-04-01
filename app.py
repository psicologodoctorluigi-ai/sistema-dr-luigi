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

# Nombres de las columnas exactas que tendrá tu Google Sheet (ACTUALIZADO A LA NUEVA FICHA)
COLUMNAS = [
    "Código", "Fecha", "Hora", "Nombres y Apellidos", "DNI", "Edad", "Sexo", "Cargo", 
    "Área", "Tiempo de servicio", "Tipo de contrato", "Teléfono", "Motivo de Atención", "Solicitante", 
    "Descripción", "Tiempo del problema", "Ámbito del problema", "Actitud", "Observaciones conductuales", 
    "Área afectada", "Orientación", "Acuerdos", "Plan de Acción", "Requiere cita", "Fecha próxima cita", "Conclusión"
]

# -------------------------
# CONEXIÓN A GOOGLE SHEETS
# -------------------------
def cargar_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Hoja 1", usecols=list(range(len(COLUMNAS))), ttl=0)
        return df.dropna(how="all") 
    except Exception:
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
        st.error(f"⚠️ Aún falta configurar la conexión a Google Sheets.")
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
    doc.add_paragraph("Subgerencia de Seguridad Ciudadana\n")

    doc.add_paragraph(f"Código HC: {datos['Código']}")
    doc.add_paragraph(f"Fecha: {datos['Fecha']}  |  Hora: {datos['Hora']}\n")

    for k, v in datos.items():
        if k not in ["Código", "Fecha", "Hora"]:
            doc.add_paragraph(f"{k}: {v}")

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
        if user == "psicologoluigi" and password == "psicologoluigi151297":
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
    st.title("📋 Ficha de Atención Psicológica Laboral")

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
            
            st.text_input("Código", value=codigo, disabled=True)
            dni_form = st.text_input("DNI (Confirmar)", value=dni_input)

            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombres y Apellidos")
                edad = st.number_input("Edad", 18, 70)
                sexo = st.selectbox("Sexo", ["Masculino","Femenino","Otro"])
                cargo = st.text_input("Cargo")
                area = st.selectbox("Área / Base", ["Serenazgo / Patrullaje", "Centro de Monitoreo / CCTV", "Guardianía / Puestos Fijos", "Administrativo", "Otro"])
            with col2:
                tiempo = st.text_input("Tiempo de servicio")
                contrato = st.selectbox("Tipo de contrato", ["CAS", "Permanente", "Nombrado", "Locador", "Otro"])
                telefono = st.text_input("Teléfono")

            st.subheader("2. Motivo de Atención")
            lista_motivos = [
                "Estrés laboral", "Conflicto con compañero", "Conflicto con jefe", "Problemas familiares", 
                "Problemas de pareja", "Problemas económicos", "Desmotivación laboral", "Problemas de conducta laboral", 
                "Dificultad de adaptación al trabajo", "Problemas de trabajo en equipo", "Problemas disciplinarios", 
                "Bajo rendimiento laboral", "Problemas personales", "Orientación laboral", "Otros"
            ]
            motivo = st.selectbox("Motivo principal", lista_motivos)
            motivo_otro = ""
            if motivo == "Otros":
                motivo_otro = st.text_input("Especifique otro motivo:")

            solicitante = st.selectbox("¿Quién solicita la atención?", ["Voluntario", "Derivado por jefe", "Recursos Humanos", "Psicología (seguimiento)", "Otro"])

            st.subheader("3. Descripción del Problema")
            descripcion = st.text_area("Descripción del problema")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                tiempo_prob = st.selectbox("Tiempo del problema", ["Días", "Semanas", "Meses", "Años"])
            with col_t2:
                ambito = st.selectbox("Ámbito del problema", ["Laboral", "Familiar", "Personal", "Económico", "Pareja", "Mixto"])

            st.subheader("4. Observación del Psicólogo")
            actitud = st.selectbox("Actitud durante la entrevista", ["Colaborador", "Reservado", "Evasivo", "Agresivo", "Ansioso", "Desmotivado", "Preocupado", "Otro"])
            observaciones = st.text_area("Observaciones conductuales")
            area_afectada = st.multiselect("Área afectada", ["Desempeño laboral", "Relaciones laborales", "Puntualidad", "Trabajo en equipo", "Trato al ciudadano", "Cumplimiento de órdenes", "Ninguna", "Otros"])

            st.subheader("5. Orientación / Consejería Brindada")
            orientacion = st.text_area("Orientación / Consejería")
            acuerdos = st.text_area("Acuerdos o compromisos")

            st.subheader("6. Plan de Acción")
            plan = st.multiselect("Plan de Acción", ["Seguimiento psicológico laboral", "Derivación a Recursos Humanos", "Derivación a jefe inmediato", "Recomendación de capacitación", "Mediación laboral", "Sin seguimiento", "Otros"])
            
            requiere_cita = st.radio("¿Próxima cita?", ["No", "Sí"])
            fecha_prox = None
            if requiere_cita == "Sí":
                fecha_prox = st.date_input("Fecha de próxima cita")

            st.subheader("7. Conclusión y Recomendaciones Laborales")
            conclusion = st.text_area("Conclusión y recomendaciones")

            guardar = st.form_submit_button("💾 Guardar Atención")

        if guardar:
            motivo_final = motivo if motivo != "Otros" else f"Otros: {motivo_otro}"
            fecha_prox_str = str(fecha_prox) if requiere_cita == "Sí" else "No requiere"

            datos = {
                "Código": codigo, "Fecha": fecha, "Hora": hora, "Nombres y Apellidos": nombre, "DNI": dni_form,
                "Edad": edad, "Sexo": sexo, "Cargo": cargo, "Área": area, "Tiempo de servicio": tiempo,
                "Tipo de contrato": contrato, "Teléfono": telefono, "Motivo de Atención": motivo_final, "Solicitante": solicitante,
                "Descripción": descripcion, "Tiempo del problema": tiempo_prob, "Ámbito del problema": ambito,
                "Actitud": actitud, "Observaciones conductuales": observaciones, "Área afectada": ", ".join(area_afectada),
                "Orientación": orientacion, "Acuerdos": acuerdos, "Plan de Acción": ", ".join(plan),
                "Requiere cita": requiere_cita, "Fecha próxima cita": fecha_prox_str, "Conclusión": conclusion
            }

            if guardar_datos(datos):
                st.success(f"✅ Atención guardada exitosamente en la nube.")
            
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
            resultado = df_atenciones[df_atenciones["DNI"].astype(str).str.replace(".0", "", regex=False).str.strip() == dni_seg.strip()]
            
            if not resultado.empty:
                ultimo_registro = resultado.iloc[-1]
                st.success(f"Paciente: {ultimo_registro['Nombres y Apellidos']} | Código: {ultimo_registro['Código']}")
                st.info(f"Último motivo: {ultimo_registro.get('Motivo de Atención', 'No registrado')}")

                with st.form("ficha_seguimiento", clear_on_submit=True):
                    st.subheader("Evolución del Caso")
                    col1, col2 = st.columns(2)
                    with col1:
                        estado_evolucion = st.selectbox("Estado actual", ["Mejoría notable", "Mejoría leve", "Estable/Sin cambios", "Retroceso/Empeoramiento"])
                        cumplimiento = st.select_slider("Cumplimiento de acuerdos previos", options=["Ninguno", "Bajo", "Medio", "Alto", "Total"])
                    with col2:
                        nueva_actitud = st.selectbox("Actitud en sesión", ["Colaborador", "Reservado", "Evasivo", "Agresivo", "Ansioso", "Desmotivado", "Preocupado", "Otro"])
                        fecha_hoy = datetime.now().strftime("%Y-%m-%d")

                    st.subheader("Detalles de la sesión")
                    evolucion_detallada = st.text_area("Descripción de la evolución (¿Qué ha pasado desde la última vez?)")
                    nuevos_acuerdos = st.text_area("Nuevos acuerdos o compromisos")
                    
                    st.subheader("Plan de Acción")
                    proximo_paso = st.multiselect("Plan de Acción (Seguimiento)", ["Seguimiento psicológico laboral", "Derivación a Recursos Humanos", "Alta administrativa", "Derivación externa", "Cierre de caso", "Otros"])
                    
                    req_cita_seg = st.radio("¿Nueva próxima cita?", ["No", "Sí"])
                    fecha_prox_seg = None
                    if req_cita_seg == "Sí":
                        fecha_prox_seg = st.date_input("Fecha sugerida")

                    guardar_seg = st.form_submit_button("💾 Registrar Seguimiento")

                if guardar_seg:
                    fecha_prox_seg_str = str(fecha_prox_seg) if req_cita_seg == "Sí" else "No requiere"
                    
                    datos_seg = {
                        "Código": ultimo_registro['Código'], "Fecha": fecha_hoy, "Hora": datetime.now().strftime("%H:%M:%S"),
                        "Nombres y Apellidos": ultimo_registro['Nombres y Apellidos'], "DNI": dni_seg,
                        "Edad": ultimo_registro['Edad'], "Sexo": ultimo_registro['Sexo'], "Cargo": ultimo_registro['Cargo'],
                        "Área": ultimo_registro['Área'], "Tiempo de servicio": ultimo_registro.get('Tiempo de servicio', '-'),
                        "Tipo de contrato": ultimo_registro.get('Tipo de contrato', '-'), "Teléfono": ultimo_registro.get('Teléfono', '-'),
                        "Motivo de Atención": f"SEGUIMIENTO: {ultimo_registro.get('Motivo de Atención', '')}",
                        "Solicitante": "Psicología (seguimiento)", "Descripción": evolucion_detallada,
                        "Tiempo del problema": "-", "Ámbito del problema": "-", "Actitud": nueva_actitud,
                        "Observaciones conductuales": "-", "Área afectada": "-", "Orientación": "-", "Acuerdos": nuevos_acuerdos,
                        "Plan de Acción": ", ".join(proximo_paso), "Requiere cita": req_cita_seg,
                        "Fecha próxima cita": fecha_prox_seg_str, "Conclusión": f"Estado: {estado_evolucion}. Cumplimiento acuerdos: {cumplimiento}"
                    }
                    
                    if guardar_datos(datos_seg):
                        st.success("✅ Seguimiento registrado con éxito.")
                        
                    doc_seg = generar_word_memoria(datos_seg)
                    st.download_button("📄 Descargar Ficha de Seguimiento", doc_seg, file_name=f"Seguimiento_{dni_seg}_{fecha_hoy}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            else:
                st.error("No se encontró ningún registro previo con ese DNI.")
        else:
            st.error("La base de datos está vacía.")

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
            resultado = df_atenciones[df_atenciones["DNI"].astype(str).str.replace(".0", "", regex=False).str.strip() == dni_buscar.strip()]
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
