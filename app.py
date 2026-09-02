import streamlit as st
from fpdf import FPDF
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def formatear_numero(valor):
    try:
        num_limpio = str(valor).replace(".", "").replace(",", "").strip()
        if not num_limpio:
            return ""
        return f"{int(num_limpio):,}".replace(",", ".")
    except ValueError:
        return valor 

def generar_pdf(operacion, nombre, dni, domicilio, tel, cobrador, total_cuotas, monto, fecha_inicio_date, frecuencia, observaciones_texto):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Grosor de las líneas y fuente general
    pdf.set_line_width(0.3)
    pdf.set_font("Arial", size=10)
    
    dni_formateado = formatear_numero(dni)
    monto_formateado = formatear_numero(monto)
    fecha_emision = datetime.now().strftime("%d/%m/%Y")
    
    # --- MÁRGENES Y ENCABEZADO ---
    margen_izq = 25
    pdf.set_y(20)
    pdf.set_x(margen_izq)
    
    pdf.cell(0, 6, f"Fecha de emision: {fecha_emision}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # Lógica de columnas con coordenadas fijas para evitar desbordes
    y_start = pdf.get_y()
    alto_linea = 6
    col_der_x = margen_izq + 95 # Columna derecha desplazada al centro
    
    # Fila 1
    pdf.set_xy(margen_izq, y_start)
    pdf.cell(38, alto_linea, "operacion:", border=0)
    pdf.cell(57, alto_linea, str(operacion), border=0)
    
    pdf.set_xy(col_der_x, y_start)
    pdf.cell(60, alto_linea, "cobrador:", border=0)
    
    # Fila 2
    pdf.set_xy(margen_izq, y_start + alto_linea)
    pdf.cell(38, alto_linea, "Apellido y nombre:", border=0)
    pdf.cell(57, alto_linea, nombre, border=0)
    
    pdf.set_xy(col_der_x, y_start + alto_linea)
    pdf.cell(60, alto_linea, cobrador, border=0)
    
    # Fila 3
    pdf.set_xy(margen_izq, y_start + alto_linea*2)
    pdf.cell(38, alto_linea, "DNI:", border=0)
    pdf.cell(57, alto_linea, dni_formateado, border=0)
    
    pdf.set_xy(col_der_x, y_start + alto_linea*2)
    pdf.cell(60, alto_linea, "plan de pago:", border=0)
    
    # Fila 4
    pdf.set_xy(margen_izq, y_start + alto_linea*3)
    pdf.cell(38, alto_linea, "Domicilio:", border=0)
    pdf.cell(57, alto_linea, domicilio, border=0)
    
    texto_plan = f"{total_cuotas} cuotas de $ {monto_formateado}" if total_cuotas > 0 else ""
    pdf.set_xy(col_der_x, y_start + alto_linea*3)
    pdf.cell(60, alto_linea, texto_plan, border=0)
    
    # Fila 5
    pdf.set_xy(margen_izq, y_start + alto_linea*4)
    pdf.cell(38, alto_linea, "Tel.:", border=0)
    pdf.cell(57, alto_linea, tel, border=0)
    
    pdf.set_xy(col_der_x, y_start + alto_linea*4)
    pdf.cell(60, alto_linea, "Frecuencia de pago:", border=0)
    
    # Fila 6 (Solo frecuencia)
    pdf.set_xy(col_der_x, y_start + alto_linea*5)
    pdf.cell(60, alto_linea, frecuencia.capitalize(), border=0)
    
    pdf.set_y(y_start + alto_linea*6 + 8)
    
    # --- CUOTAS ---
    fecha_ideal = fecha_inicio_date
        
    if frecuencia == 'quincenal':
        if fecha_ideal.day <= 5:
            fecha_ideal = fecha_ideal.replace(day=5)
        elif fecha_ideal.day <= 20:
            fecha_ideal = fecha_ideal.replace(day=20)
        else:
            fecha_ideal = (fecha_ideal + relativedelta(months=1)).replace(day=5)

    # Medidas exactas enviadas (en milímetros)
    ancho_caja, alto_caja = 52, 18 
    espacio_x, espacio_y = 3, 3
    subcaja_ancho = 10
    columnas = 3
    x_inicial, y_inicial = margen_izq, pdf.get_y()
    
    for i in range(total_cuotas):
        fecha_imprimir = fecha_ideal
        if fecha_imprimir.weekday() == 6: 
            if frecuencia in ['mensual', 'quincenal']:
                fecha_imprimir -= timedelta(days=1) 
        
        columna_actual = i % columnas
        fila_actual = i // columnas
        x = x_inicial + (ancho_caja + espacio_x) * columna_actual
        y = y_inicial + (alto_caja + espacio_y) * fila_actual
        
        # Recuadro principal
        pdf.rect(x, y, ancho_caja, alto_caja)
        # Línea divisoria de la subcaja a 1cm (10mm)
        pdf.line(x + subcaja_ancho, y, x + subcaja_ancho, y + alto_caja)
        
        # Fecha de vencimiento
        pdf.set_xy(x, y + 1)
        pdf.set_font("Arial", size=8)
        pdf.cell(subcaja_ancho, 4, fecha_imprimir.strftime("%d/%m"), border=0, align='C')
        
        # Número de cuota gigante y centrado
        pdf.set_xy(x, y + alto_caja - 8)
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(subcaja_ancho, 6, str(i + 1), border=0, align='C')
        
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
            
    # --- OBSERVACIONES ---
    y_final_cajas = y_inicial + (alto_caja + espacio_y) * (max(0, total_cuotas - 1) // columnas + 1)
    pdf.set_y(y_final_cajas + 15)
    pdf.set_font("Arial", size=10)
    pdf.set_x(margen_izq)
    
    if observaciones_texto.strip():
        pdf.multi_cell(0, 6, f"observaciones: {observaciones_texto.strip()}", border=0)
    else:
        pdf.cell(0, 6, "observaciones: ", border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(4)
    pdf.set_x(margen_izq)
    pdf.cell(0, 7, "." * 115, border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(margen_izq)
    pdf.cell(0, 7, "." * 115, border=0, new_x="LMARGIN", new_y="NEXT")
    
    return bytes(pdf.output())

# --- INTERFAZ WEB PRINCIPAL ---
st.title("📝 Generador de Planillas de Pago")
st.write("Completa los datos del cliente para generar la planilla en PDF.")

with st.form("formulario_planilla"):
    col1, col2 = st.columns(2)
    
    with col1:
        operacion = st.text_input("Nro. de Operación (Ej: 22001)")
        nombre = st.text_input("Apellido y Nombre")
        dni = st.text_input("DNI (Solo números)")
        domicilio = st.text_input("Domicilio")
        tel = st.text_input("Teléfono")
        cobrador = st.text_input("Cobrador")
        
    with col2:
        monto = st.text_input("Monto de la cuota (Solo números)")
        total_cuotas = st.number_input("Cantidad de cuotas", min_value=1, max_value=60, value=5)
        frecuencia = st.selectbox("Frecuencia de pago", ['diario', 'semanal', 'quincenal', 'mensual'])
        fecha_inicio = st.date_input("Fecha de primera cuota", format="DD/MM/YYYY")
        
    observaciones_input = st.text_area("Observaciones (Opcional)", help="Este texto aparecerá impreso. Debajo se dejarán líneas punteadas vacías.")
        
    submit_btn = st.form_submit_button("Generar Planilla PDF")
    
if submit_btn:
    if not operacion or not nombre:
        st.warning("Por favor, ingresa al menos el Número de Operación y el Nombre.")
    else:
        pdf_bytes = generar_pdf(
            operacion, nombre, dni, domicilio, tel, cobrador, 
            total_cuotas, monto, fecha_inicio, frecuencia, observaciones_input
        )
        
        nombre_limpio = "".join(nombre.split()).title()
        nombre_archivo = f"{nombre_limpio}_{operacion}.pdf"
        
        st.success(f"¡Planilla generada con éxito para {nombre}!")
        
        st.download_button(
            label="📥 Clic aquí para Descargar tu PDF",
            data=pdf_bytes,
            file_name=nombre_archivo,
            mime="application/pdf"
        )
