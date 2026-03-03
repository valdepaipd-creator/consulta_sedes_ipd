import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Consulta sedes IPD", layout="wide")

@st.cache_data
def load_data():
    # 1. CARGA DE BASES (Asegúrate de que los nombres coincidan en GitHub)
    try:
        df_l = pd.read_csv("consolidado_lima.csv", encoding='latin-1')
        df_p = pd.read_csv("consolidado_provincias.csv", encoding='latin-1')
    except FileNotFoundError:
        # Intento de lectura por si los archivos están en mayúsculas
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
            # Función interna para limpiar y estandarizar textos
            def limpiar(campo):
                val = row.get(campo, '')
                return str(val).upper().strip() if pd.notnull(val) else ''

            # Extraer valores (Si no existe la columna, devolverá vacío en lugar de error)
            infra = limpiar('TIPO INFRAESTRUCTURA')
            uso = limpiar('USO ESPECIFICO')
            predio = limpiar('TIPO PREDIO')
            est_itse = limpiar('ESTADO ITSE')
            prob_est = limpiar('PROBLEMAS ESTRUCTURALES')
            itse_status = limpiar('ITSE')
            zona = limpiar('ZONA')
            
            # --- NUEVA REGLA: TERRENO ---
            if 'TERRENO' in [infra, uso, predio] or est_itse == 'NO APLICA':
                return "NO APLICA(TERRENO)"

            # --- REGLA GENERAL: SIN ITSE ---
            if prob_est == 'SI' or itse_status == 'SIN ITSE':
                return "SIN ITSE"
            
            # --- VIGENCIAS ---
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
        except Exception as e:
            return "ERROR REGLA"

    df['ALERTA'] = df.apply(aplicar_reglas, axis=1)
    return df.fillna("-")
