import fitz # PyMuPDF
import re
import pg8000.dbapi
from datetime import datetime

def get_data_cruce(pdf, url):
    for page_num in range(pdf.page_count):
        page = pdf[page_num]
        text = page.get_text()

    print(text)
    # Patrones regex
    fecha_pattern = r"Fecha:\s*(\d{2}/\d{2}/\d{4})" 
    remito_pattern1 =   r"Fecha:\s*\d{2}/\d{2}/\d{4}\s*(\d{8})" 
    remito_pattern2 = r"CANTIDAD\s*(\d{4}\s*-)" 
    descripcion_pattern = r"(?:DESCRIPCION\s*|(?:\d+,\d+)\s+)((?:(?!C\.U\.I\.T\.|^\d+,\d+)[\s\S])+?)(?=\s*\d+,\d+|\s*C\.U\.I\.T)"
    cantidad_pattern = r"(\d{1,},\d{0,})"
    nombre_retira_pattern = r"Retira:\s*([A-Za-zÀ-ÿ\s\(\)\-]+)(?=\nPatente)"

    patente_pattern = r"Patente:\s*([A-Za-z]{2,3}\s?[0-9]{3}[A-Za-z]{0,2})"


    # Buscar los datos en el texto usando regex
    patente = re.search(patente_pattern, text)
    nombre_retira = re.search(nombre_retira_pattern, text)
    cantidad = re.findall(cantidad_pattern, text)
    descripcion = re.findall(descripcion_pattern, text, re.DOTALL)
    fecha = re.search(fecha_pattern, text)
    remito1 = re.search(remito_pattern1, text)
    remito2 = re.search(remito_pattern2, text)

    print(f"Cantidad de coincidencias encontradas para descripcion: {len(descripcion)}")
    print( descripcion )
    print(f"Cantidad de coincidencias encontradas para cantidad: {len(cantidad)}")
    print( cantidad )

    patente = patente.group(1) if patente else "No encontrado"
    nombre_retira = nombre_retira.group(1).strip() if nombre_retira else "No encontrado"
    fecha = fecha.group(1) if fecha else "No encontrado"
    fecha = datetime.strptime(fecha, "%d/%m/%Y")
    remito1 = remito1.group(1) if remito1 else "No encontrado"
    remito2 = remito2.group(1) if remito2 else "No encontrado"

    # CONEXION

    
    cursor = con.cursor()
    patente = patente.upper().replace(" ", "")
    for i in range(len(cantidad)):
        print("DATOS SCRAPEADOS")
        print("Fecha:", fecha)
        print("Remito:", remito2+ " " + remito1)
        print(f"Se compro {cantidad[i]} lts de {descripcion[i]} ")
        print("Nombre del que retira:", nombre_retira)
        print("Patente:", patente)
        cursor.execute("select COALESCE(id_truck, NULL) from truck where patent=%s;", [patente])
        id_truck = cursor.fetchone()
        print("URL2:", url)
        if id_truck is None:
            print(id_truck)
            cursor.execute("insert into transaction(quantity, type, name_driver, date, nro_remmit, truck_id, truck_patent, url) values(%s,%s,%s,%s,%s,%s,%s, %s);",[float(cantidad[i].replace(',', '.')), str(descripcion[i]), str(nombre_retira), fecha, remito2+ " " + remito1, None, patente, url])
            con.commit()
        else:
            cursor.execute("insert into transaction(quantity, type, name_driver, date, nro_remmit, truck_id, truck_patent, url) values(%s,%s,%s,%s,%s,%s,%s, %s);",[float(cantidad[i].replace(',', '.')), str(descripcion[i]), str(nombre_retira), fecha, remito2+ " " + remito1, id_truck[0], patente, url])
            con.commit()
    # [1]
    con.close()


# with fitz.open("../remmits/cruce/boss.pdf") as pdf:
#     get_data_cruce(pdf)
