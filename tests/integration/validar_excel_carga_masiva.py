import pandas as pd
import sys
from pathlib import Path

def validar_excel_carga_masiva(ruta_archivo):
    """
    Valida un archivo Excel para carga masiva de clientes sin afectar la base de datos.
    
    Args:
        ruta_archivo (str): Ruta al archivo Excel a validar
        
    Returns:
        dict: Resumen de la validación
    """
    print(f"🔍 Validando archivo: {ruta_archivo}")
    
    # Verificar si el archivo existe
    if not Path(ruta_archivo).exists():
        return {"error": f"❌ El archivo {ruta_archivo} no existe"}
    
    try:
        # Leer el archivo Excel
        df = pd.read_excel(ruta_archivo)
        print(f"📊 Archivo leído correctamente. Registros encontrados: {len(df)}")
        
    except Exception as e:
        return {"error": f"❌ Error al leer el archivo Excel: {str(e)}"}
    
    # Columnas requeridas
    columnas_requeridas = [
        'nombre', 'apellido', 'email', 'password', 'tipo_documento',
        'num_doc', 'numero_telefono', 'id_departamento', 'id_distrito',
        'direccion', 'fecha_nac', 'genero', 'talla', 'peso'
    ]
    
    # Verificar estructura
    columnas_faltantes = []
    for col in columnas_requeridas:
        if col not in df.columns:
            columnas_faltantes.append(col)
    
    if columnas_faltantes:
        return {
            "error": f"❌ Faltan las siguientes columnas: {', '.join(columnas_faltantes)}",
            "columnas_encontradas": df.columns.tolist()
        }
    
    print("✅ Estructura de columnas correcta")
    
    # Validar datos
    resumen_validacion = {
        "total_registros": len(df),
        "registros_validos": 0,
        "problemas_encontrados": [],
        "registros_con_problemas": []
    }
    
    print("\n🔍 Validando datos registro por registro...")
    
    for idx, fila in df.iterrows():
        problemas_fila = []
        
        # Validar campos obligatorios
        if pd.isna(fila['email']) or str(fila['email']).strip() == '':
            problemas_fila.append("Email vacío")
        elif '@' not in str(fila['email']):
            problemas_fila.append("Email inválido")
            
        if pd.isna(fila['num_doc']) or str(fila['num_doc']).strip() == '':
            problemas_fila.append("Número de documento vacío")
            
        if pd.isna(fila['nombre']) or str(fila['nombre']).strip() == '':
            problemas_fila.append("Nombre vacío")
            
        if pd.isna(fila['apellido']) or str(fila['apellido']).strip() == '':
            problemas_fila.append("Apellido vacío")
            
        if pd.isna(fila['password']) or str(fila['password']).strip() == '':
            problemas_fila.append("Password vacío")
        
        # Validar tipos de datos numéricos
        try:
            if not pd.isna(fila['talla']):
                float(fila['talla'])
        except (ValueError, TypeError):
            problemas_fila.append("Talla no es un número válido")
            
        try:
            if not pd.isna(fila['peso']):
                float(fila['peso'])
        except (ValueError, TypeError):
            problemas_fila.append("Peso no es un número válido")
            
        try:
            if not pd.isna(fila['id_departamento']):
                int(fila['id_departamento'])
        except (ValueError, TypeError):
            problemas_fila.append("ID Departamento no es un número válido")
            
        try:
            if not pd.isna(fila['id_distrito']):
                int(fila['id_distrito'])
        except (ValueError, TypeError):
            problemas_fila.append("ID Distrito no es un número válido")
        
        # Validar tipo de documento
        if not pd.isna(fila['tipo_documento']) and str(fila['tipo_documento']) not in ['DNI', 'CARNET DE EXTRANJERIA']:
            problemas_fila.append("Tipo de documento debe ser 'DNI' o 'CARNET DE EXTRANJERIA'")
        
        if problemas_fila:
            resumen_validacion["registros_con_problemas"].append({
                "fila": idx + 2,  # +2 porque Excel empieza en 1 y tiene header
                "problemas": problemas_fila,
                "datos": fila.to_dict()
            })
        else:
            resumen_validacion["registros_validos"] += 1
    
    # Mostrar resumen
    print(f"\n📈 RESUMEN DE VALIDACIÓN:")
    print(f"   📊 Total de registros: {resumen_validacion['total_registros']}")
    print(f"   ✅ Registros válidos: {resumen_validacion['registros_validos']}")
    print(f"   ⚠️  Registros con problemas: {len(resumen_validacion['registros_con_problemas'])}")
    
    if resumen_validacion["registros_con_problemas"]:
        print(f"\n❌ PROBLEMAS ENCONTRADOS:")
        for problema in resumen_validacion["registros_con_problemas"]:
            print(f"   🔸 Fila {problema['fila']}: {', '.join(problema['problemas'])}")
    
    # Verificar duplicados dentro del archivo
    print(f"\n🔍 Verificando duplicados...")
    emails_duplicados = df[df['email'].duplicated(keep=False)]
    docs_duplicados = df[df['num_doc'].duplicated(keep=False)]
    
    if len(emails_duplicados) > 0:
        print(f"   ⚠️  Emails duplicados encontrados:")
        for idx, row in emails_duplicados.iterrows():
            print(f"      🔸 Fila {idx + 2}: {row['email']}")
    
    if len(docs_duplicados) > 0:
        print(f"   ⚠️  Documentos duplicados encontrados:")
        for idx, row in docs_duplicados.iterrows():
            print(f"      🔸 Fila {idx + 2}: {row['num_doc']}")
    
    if len(emails_duplicados) == 0 and len(docs_duplicados) == 0:
        print("   ✅ No se encontraron duplicados")
    
    # Mostrar muestra de datos
    print(f"\n📋 MUESTRA DE LOS PRIMEROS 3 REGISTROS:")
    print(df.head(3).to_string())
    
    return resumen_validacion

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Uso: python validar_excel_carga_masiva.py <ruta_al_archivo.xlsx>")
        print("📝 Ejemplo: python validar_excel_carga_masiva.py mi_archivo_clientes.xlsx")
        sys.exit(1)
    
    ruta_archivo = sys.argv[1]
    resultado = validar_excel_carga_masiva(ruta_archivo)
    
    if "error" in resultado:
        print(f"\n{resultado['error']}")
        if "columnas_encontradas" in resultado:
            print(f"📋 Columnas encontradas: {resultado['columnas_encontradas']}")
        sys.exit(1)
    
    print(f"\n🎯 CONCLUSIÓN:")
    if resultado["registros_validos"] == resultado["total_registros"]:
        print("   ✅ ¡Tu archivo Excel está perfecto para la carga masiva!")
    elif resultado["registros_validos"] > 0:
        print(f"   ⚠️  Tu archivo tiene {resultado['registros_validos']} registros válidos de {resultado['total_registros']}")
        print("   🔧 Corrige los problemas encontrados para mejorar la carga")
    else:
        print("   ❌ Tu archivo tiene problemas que deben corregirse antes de la carga masiva")
    
    print("\n📁 Para usar este archivo en carga masiva:")
    print("   📤 Endpoint: POST /api/usuarios/clientes/carga-masiva")
    print("   🔑 Requiere: Token de administrador")
    print("   📝 Campo: 'archivo' (multipart/form-data)") 