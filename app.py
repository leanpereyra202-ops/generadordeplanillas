import streamlit as st
import os
from fpdf import FPDF
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import io

# --- CONFIGURACIÓN DE SEGURIDAD ---
CONTRASEÑA_CORRECTA = "1626"

def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    if "password_correcta" not in st.session_state:
        st.session_state["password_correcta"] = False

    if not st.session_state["password_correcta"]:
        st.title("🔒 Acceso Restringido")
        pwd_ingresada = st.text_input("Ingrese la contraseña:", type="password")
        if st.button("Ingresar"):
            if pwd_ingresada == CONTRASEÑA_CORRECTA:
                st.session_state["password_correcta"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

# --- LÓGICA PARA GENERAR EL PDF ---
def generar_pdf(operacion, nombre, dni, domicilio, tel, cobrador, total_cuotas, monto, fecha_inicio_date, frecuencia):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    fecha_emision = datetime.now().strftime("%d/%m/%Y")
    
    # Encabezado
    pdf.set_y(15)
    pdf.set_x(20)
    pdf.cell(0, 6, f"Fecha de emision: {fecha_emision}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_x(20)
    pdf.cell(40, 6, "operacion:", border=0)
    pdf.cell(60, 6, str(operacion), border=0)
    pdf.cell(30, 6, "cobrador:", border=0)
    pdf.cell(40, 6, cobrador, border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(20)
    pdf.cell(40, 6, "Apellido y nombre:", border=0)
    pdf.cell(60, 6, nombre, border=0)
    pdf.cell(30, 6, "", border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(20)
    pdf.cell(40, 6, "DNI:", border=0)
    pdf.cell(60, 6, dni, border=0)
    pdf.cell(30, 6, "plan de pago:", border=0)
    
    texto_plan = f"{total_cuotas} cuotas de $ {monto}" if total_cuotas > 0 else ""
    pdf.cell(40, 6, texto_plan, border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(20)
    pdf.cell(40, 6, "Domicilio:", border=0)
    pdf.cell(60, 6, domicilio, border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(20)
    pdf.cell(40, 6, "Tel.:", border=0)
    pdf.cell(60, 6, tel, border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(15)
    
    # Lógica de fechas
    fecha_ideal = fecha_inicio_date
        
    if frecuencia == 'quincenal':
        if fecha_ideal.day <= 5:
            fecha_ideal = fecha_ideal.replace(day=5)
        elif fecha_ideal.day <= 20:
            fecha_ideal = fecha_ideal.replace(day=20)
        else:
            fecha_ideal = (fecha_ideal + relativedelta(months=1)).replace(day=5)

    ancho_caja, alto_caja = 50, 20
    espacio_x, espacio_y = 5, 5
    columnas = 3
    x_inicial, y_inicial = 20, pdf.get_y()
    
    for i in range(total_cuotas):
        fecha_imprimir = fecha_ideal
        if fecha_imprimir.weekday() == 6: # Si es domingo
            if frecuencia in ['mensual', 'quincenal']:
                fecha_imprimir -= timedelta(days=1) # Adelantar al sábado
        
        columna_actual = i % columnas
        fila_actual = i // columnas
        x = x_inicial + (ancho_caja + espacio_x) * columna_actual
        y = y_inicial + (alto_caja + espacio_y) * fila_actual
        
        pdf.rect(x, y, ancho_caja, alto_caja)
        pdf.line(x + 15, y, x + 15, y + alto_caja)
        
        pdf.set_xy(x + 1, y + 1)
        pdf.set_font("Arial", size=9)
        pdf.cell(14, 5, fecha_imprimir.strftime("%d/%m"), border=0, align='L')
        
        pdf.set_xy(x + 1, y + alto_caja - 7)
        pdf.set_font("Arial", 'B', size=13)
        pdf.cell(14, 5, str(i + 1), border=0, align='L')
        
        # Calcular siguiente fecha
        if frecuencia == 'diario':
            fecha_ideal += timedelta(days=1)
            if fecha_ideal.weekday() == 6:
                fecha_ideal += timedelta(days=1)
        elif frecuencia == 'semanal':
            fecha_ideal += timedelta(weeks=1)
        elif frecuencia == 'quincenal':
            if fecha_ideal.day == 5:
                fecha_ideal = fecha_ideal.replace(day=20)
            else:
                fecha_ideal = (fecha_ideal + relativedelta(months=1)).replace(day=5)
        elif frecuencia == 'mensual':
            fecha_ideal += relativedelta(months=1)
            
    y_final_cajas = y_inicial + (alto_caja + espacio_y) * (max(0, total_cuotas - 1) // columnas + 1)
    pdf.set_y(y_final_cajas + 20)
    pdf.set_font("Arial", size=10)
    pdf.set_x(20)
    pdf.cell(0, 8, "observaciones: " + "." * 110, border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(20)
    pdf.cell(0, 8, "." * 136, border=0, new_x="LMARGIN", new_y="NEXT")
    
    # En lugar de guardar en disco, lo guardamos en la memoria para descargarlo web
    return bytes(pdf.output())

# --- INTERFAZ WEB PRINCIPAL ---
if check_password():
    st.title("📝 Generador de Planillas de Pago")
    st.write("Completa los datos del cliente para generar la planilla en PDF.")
    
    with st.form("formulario_planilla"):
        col1, col2 = st.columns(2)
        
        with col1:
            operacion = st.text_input("Nro. de Operación (Ej: 22001)")
            nombre = st.text_input("Apellido y Nombre")
            dni = st.text_input("DNI")
            domicilio = st.text_input("Domicilio")
            tel = st.text_input("Teléfono")
            cobrador = st.text_input("Cobrador")
            
        with col2:
            monto = st.text_input("Monto de la cuota (Ej: 200.000)")
            total_cuotas = st.number_input("Cantidad de cuotas", min_value=1, max_value=60, value=5)
            frecuencia = st.selectbox("Frecuencia de pago", ['diario', 'semanal', 'quincenal', 'mensual'])
            fecha_inicio = st.date_input("Fecha de primera cuota", format="DD/MM/YYYY")
            
        submit_btn = st.form_submit_button("Generar Planilla PDF")
        
    if submit_btn:
        if not operacion or not nombre:
            st.warning("Por favor, ingresa al menos el Número de Operación y el Nombre.")
        else:
            # Generar el PDF en memoria
            pdf_bytes = generar_pdf(
                operacion, nombre, dni, domicilio, tel, cobrador, 
                total_cuotas, monto, fecha_inicio, frecuencia
            )
            
            # Formatear el nombre del archivo
            nombre_limpio = "".join(nombre.split()).title()
            nombre_archivo = f"{nombre_limpio}_{operacion}.pdf"
            
            st.success(f"¡Planilla generada con éxito para {nombre}!")
            
            # Botón de descarga web
            st.download_button(
                label="📥 Clic aquí para Descargar tu PDF",
                data=pdf_bytes,
                file_name=nombre_archivo,
                mime="application/pdf"
            )
