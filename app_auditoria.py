import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. CONFIGURACIÓN DE LA PÁGINA (Debe ser la primera línea de Streamlit)
st.set_page_config(
    page_title="Sistema Avanzado de Auditoría",
    page_icon="🔍",
    layout="wide"
)

# Estilo personalizado para mantener la estética ejecutiva oscura
st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .kpi-box {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        text-align: center;
        margin-bottom: 20px;
    }
    .kpi-box.alert { border-color: #ef4444; background-color: #1e1b1b; }
    h1, h2, h3 { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. OPTIMIZACIÓN A: CARGA DE DATOS CON CACHÉ (Para soportar las 12,000 filas al instante)
@st.cache_data
def cargar_datos(ruta):
    try:
        # Cargamos el archivo de Excel de forma eficiente
        df = pd.read_excel(ruta)
        # Aseguramos que los nombres de columnas estén limpios y en mayúsculas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpieza rápida: Asegurar que VALOR EN LIBROS sea numérico
        if 'VALOR EN LIBROS' in df.columns:
            df['VALOR EN LIBROS'] = pd.to_numeric(df['VALOR EN LIBROS'], errors='coerce').fillna(0)
        
        # Creamos la lógica automática de alertas por naturaleza invertida
        # Ejemplo: Cuenta de Activo (empieza por 1) con saldo Crédito o valor menor a 0
        if 'CUENTA' in df.columns and 'VALOR EN LIBROS' in df.columns:
            df['ALERTA_NATURALEZA'] = df.apply(
                lambda row: "Alerta Crítica" if (str(row['CUENTA']).startswith('1') and row['VALOR EN LIBROS'] < 0) else "Normal", 
                axis=1
            )
        else:
            df['ALERTA_NATURALEZA'] = "Normal"
            
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo de Excel: {e}")
        return pd.DataFrame()

# Llamado a la base de datos (Python la lee una sola vez y la guarda en memoria caché)
df_original = cargar_datos("Base datos.xlsx")

if not df_original.empty:
    
    # === TÍTULO PRINCIPAL ===
    st.title("Propuesta de Nazly Diagnóstico Automático de Auditoría")
    st.subheader("Cuentas por Pagar y Cuentas por Cobrar - Análisis de Terceros en Masa")
    st.write("---")

    # =========================================================================
    # SECCIÓN: FILTROS AVANZADOS Y SEGMENTACIÓN (Barra Lateral Izquierda)
    # =========================================================================
    st.sidebar.header("🔍 Panel de Filtros Avanzados")
    
    # Filtro 1: Buscador de Tercero o NIT
    busqueda = st.sidebar.text_input("Buscar por Nombre de Tercero o NIT:", "").strip().upper()
    
    # Filtro 2: Segmentación por Año (Dinámico según el Excel)
    lista_anios = ["Todos"] + sorted(list(df_original['AÑO'].dropna().unique()), reverse=True)
    anio_sel = st.sidebar.selectbox("Filtrar por Año Contable:", lista_anios)
    
    # Filtro 3: Segmentación por Estado de Alerta
    lista_alertas = ["Todos", "Solo Alertas Críticas", "Solo Normales"]
    alerta_sel = st.sidebar.selectbox("Filtrar por Estado de Alerta:", lista_alertas)

    # Filtro 4: Control del volumen de datos a mostrar en pantalla (Paginación visual)
    max_filas = st.sidebar.slider("Filas máximas a visualizar en la tabla:", 10, 500, 50)

    # APLICACIÓN DE FILTROS EN CADENA (Sobre la memoria caché, veloz)
    df_filtrado = df_original.copy()
    
    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado['TERCERO'].astype(str).str.contains(busqueda) | 
            df_filtrado['NIT'].astype(str).str.contains(busqueda)
        ]
    if anio_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['AÑO'] == anio_sel]
        
    if alerta_sel == "Solo Alertas Críticas":
        df_filtrado = df_filtrado[df_filtrado['ALERTA_NATURALEZA'] == "Alerta Crítica"]
    elif alerta_sel == "Solo Normales":
        df_filtrado = df_filtrado[df_filtrado['ALERTA_NATURALEZA'] == "Normal"]

    # =========================================================================
    # SECCIÓN: TARJETAS KPI DE CONTROL GENERAL
    # =========================================================================
    total_libros = df_filtrado['VALOR EN LIBROS'].sum()
    total_inconsistencias = (df_filtrado['ALERTA_NATURALEZA'] == "Alerta Crítica").sum()
    total_terceros = df_filtrado['TERCERO'].nunique()

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="kpi-box">
                <div style="font-size: 14px; color: #94a3b8; font-weight: bold;">TOTAL EN LIBROS FILTRADO</div>
                <div style="font-size: 24px; font-weight: bold; color: #38bdf8;">${total_libros:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Si hay inconsistencias, la tarjeta se pone en rojo automáticamente
        clase_alerta = "kpi-box alert" if total_inconsistencias > 0 else "kpi-box"
        color_texto = "#ef4444" if total_inconsistencias > 0 else "#38bdf8"
        st.markdown(f"""
            <div class="{clase_alerta}">
                <div style="font-size: 14px; color: #94a3b8; font-weight: bold;">ALERTAS DE NATURALEZA</div>
                <div style="font-size: 24px; font-weight: bold; color: {color_texto};">{total_inconsistencias} Inconsistencias</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="kpi-box">
                <div style="font-size: 14px; color: #94a3b8; font-weight: bold;">TERCEROS SELECCIONADOS</div>
                <div style="font-size: 24px; font-weight: bold; color: #38bdf8;">{total_terceros}</div>
            </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # SECCIÓN NUEVA 1: GRÁFICOS ESTADÍSTICOS DEL IMPACTO (Módulo de Tendencias)
    # =========================================================================
    st.write("## 📊 Módulo de Tendencias y Análisis Estadístico")
    graf_col1, graf_col2 = st.columns(2)

    with graf_col1:
        st.write("### Top 10 Terceros con Mayor Saldo en Libros")
        # Agrupamos por tercero para consolidar montos totales reales
        top_terceros = df_filtrado.groupby('TERCERO')['VALOR EN LIBROS'].sum().reset_index()
        top_terceros = top_terceros.sort_values(by='VALOR EN LIBROS', ascending=False).head(10)
        
        if not top_terceros.empty:
            fig_bar = px.bar(
                top_terceros,
                x='VALOR EN LIBROS',
                y='TERCERO',
                orientation='h',
                template='plotly_dark',
                color='VALOR EN LIBROS',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos para graficar.")

    with graf_col2:
        st.write("### Proporción de Registros Críticos vs Normales")
        conteo_alertas = df_filtrado['ALERTA_NATURALEZA'].value_counts().reset_index()
        conteo_alertas.columns = ['Estado', 'Cantidad']
        
        if not conteo_alertas.empty:
            fig_pie = px.pie(
                conteo_alertas,
                values='Cantidad',
                names='Estado',
                template='plotly_dark',
                color='Estado',
                color_discrete_map={'Normal': '#0284c7', 'Alerta Crítica': '#ef4444'}
            )
            fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos para graficar.")

    # =========================================================================
    # SECCIÓN: REGISTROS CONTABLES ENCONTRADOS (DATAFRAME)
    # =========================================================================
    st.write("## 📋 Registros Contables Detectados")
    st.write(f"Mostrando los primeros {max_filas} registros de acuerdo a tus filtros aplicados:")
    
    # Mostramos la tabla formateada y limpia en pantalla de forma optimizada
    st.dataframe(df_filtrado.head(max_filas), use_container_width=True)

    # =========================================================================
    # SECCIÓN NUEVA 2: DESCARGA Y REPORTES EJECUTIVOS
    # =========================================================================
    st.write("---")
    st.write("## 📥 Exportación y Reportes Ejecutivos")
    st.write("Descarga los resultados del diagnóstico actual filtrado para tus informes de auditoría:")

    # Generamos el archivo de descarga en memoria sin escribir en el disco (Garantiza velocidad)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtrado.to_excel(writer, index=False, sheet_name='Hallazgos_Auditoria')
    
    st.download_button(
        label="📥 Descargar Diagnóstico Actual en Excel",
        data=buffer.getvalue(),
        file_name="Reporte_Diagnostico_Auditoria.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.warning("Asegúrate de tener el archivo 'Base datos.xlsx' dentro de la misma carpeta 'Monstruo'.")