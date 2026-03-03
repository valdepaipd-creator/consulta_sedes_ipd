import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Consulta sedes IPD", layout="wide")

@st.cache_data
def load_data():
    # 1. CARGA DE BASES
    try:
        df_l = pd.read_csv("consolidado_lima.csv", encoding='latin-1')
        df_p = pd.read_csv("consolidado_provincias.csv", encoding='latin-1')
    except:
        df_l = pd.read_csv("CONSOLIDADO_LIMA.csv", encoding='latin-1')
        df_p = pd.read_csv("CONSOLIDADO_PROVINCIAS.csv", encoding='latin-1')
    
    df_l['ZONA'] = 'LIMA'
    df_p['ZONA'] = 'PROVINCIAS'
    
    # 2. UNIFICACIÓN
    df = pd.concat([df_l, df_p], ignore_index=True, sort=False)
    
    # 3. LÓGICA DE ALERTAS
    hoy = pd.Timestamp(datetime.now().date())
    
    def aplicar_reglas(row):
        try:
            def limpiar(campo):
                val = row.get(campo, '')
                return str(val).upper().strip() if pd.notnull(val) else ''

            infra = limpiar('TIPO INFRAESTRUCTURA')
            uso = limpiar('USO ESPECIFICO')
            predio = limpiar('TIPO PREDIO')
            est_itse = limpiar('ESTADO ITSE')
            prob_est = limpiar('PROBLEMAS ESTRUCTURALES')
            itse_status = limpiar('ITSE')
            zona = limpiar('ZONA')
            
            if 'TERRENO' in [infra, uso, predio] or est_itse == 'NO APLICA':
                return "NO APLICA(TERRENO)"

            if prob_est == 'SI' or itse_status == 'SIN ITSE':
                return "SIN ITSE"
            
            if zona == 'LIMA':
                f_limite = pd.to_datetime(row.get('FECHA LIMITE'), errors='coerce')
                if pd.notnull(f_limite):
                    return "VIGENTE" if (f_limite - hoy).days > 0 else "VENCIDO"
            elif zona == 'PROVINCIAS':
                f_ven_itse = pd.to_datetime(row.get('FVEN ITSE'), errors='coerce')
                f_limite_p = pd.to_datetime(row.get('FECHA LIMITE'), errors='coerce')
                if pd.notnull(f_ven_itse):
                    return "ITSE VIGENTE" if (f_ven_itse - hoy).days > 0 else "ITSE VENCIDO"
                elif pd.notnull(f_limite_p):
                    return "VIGENTE" if (f_limite_p - hoy).days > 0 else "VENCIDO"
            return "SIN DATOS"
        except:
            return "ERROR REGLA"

    df['ALERTA'] = df.apply(aplicar_reglas, axis=1)
    return df.fillna("-")

# --- INTERFAZ ---
df = load_data()

st.title("🇵🇪 Sistema de Consulta Nacional ITSE")

busqueda = st.text_input("🔍 Buscar por local, dirección, código o ubigeo:", "")
st.sidebar.header("Filtros")
filtro_zona = st.sidebar.multiselect("Zona:", df['ZONA'].unique(), default=df['ZONA'].unique())
filtro_alerta = st.sidebar.multiselect("Estado Alerta:", df['ALERTA'].unique(), default=df['ALERTA'].unique())

df_res = df[(df['ZONA'].isin(filtro_zona)) & (df['ALERTA'].isin(filtro_alerta))]

if busqueda:
    mask = df_res.apply(lambda r: r.astype(str).str.contains(busqueda, case=False).any(), axis=1)
    df_res = df_res[mask]

def style_alerta(val):
    color = 'white'
    if "VENCIDO" in val or "SIN ITSE" in val: color = '#FFCCCC'
    elif "VIGENTE" in val: color = '#CCFFCC'
    elif "TERRENO" in val: color = '#E0E0E0'
    return f'background-color: {color}'

st.write(f"Mostrando {len(df_res)} registros.")
st.dataframe(df_res.style.applymap(style_alerta, subset=['ALERTA']), use_container_width=True)

