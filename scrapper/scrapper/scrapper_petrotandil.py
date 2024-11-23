import fitz # PyMuPDF
import re
import pg8000.dbapi
from datetime import datetime


def get_data_petro(pdf, url):
    for page_num in range(pdf.page_count):
        page = pdf[page_num]
        text = page.get_text()

    print(text)
    remito_pattern = r"(\d{4}-\d{8})" 
    patente_pattern = r"Patente\s*([A-Za-z]{2,3}\s?[0-9]{3}[A-Za-z]{0,2})"
    nombre_chofer_pattern = r"Chofer\s+(.+)(?=\nKilometraje)"
    descripcion_pattern = r'\(\d+\)(.*?)\n\d+,\d+'
    cantidad_pattern = r"(\d{1,},\d{0,})"
    fecha_emision_pattern = r'(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}:\d{2}'

    # Extraer los datos
    patente = re.search(patente_pattern, text)
    remito = re.search(remito_pattern, text)
    nombre_chofer = re.search(nombre_chofer_pattern, text)
    cantidad = re.findall(cantidad_pattern, text)
    descripcion = re.findall(descripcion_pattern, text, re.DOTALL)  
    fecha_emision = re.search(fecha_emision_pattern, text)

    # print(f"Cantidad de coincidencias encontradas para descripcion: {len(descripcion)}")
    # print(f"Cantidad de coincidencias encontradas para cantidad: {len(cantidad)}")

    remito = remito.group(1) if remito else "No encontrado"
    patente = patente.group(1) if patente else "No encontrado"
    nombre_chofer = nombre_chofer.group(1).strip() if nombre_chofer else "No encontrado"
    fecha_emision = fecha_emision.group(1) if fecha_emision else "No encontrado"
    fecha = datetime.strptime(fecha_emision, "%d/%m/%Y")

    # CONEXION

    cursor = con.cursor()
    patente = patente.upper().replace(" ", "")
    for i in range(len(descripcion)):
        print("DATOS SCRAPEADOS")
        print("Fecha de emisión:", fecha_emision)
        print("remito", remito)
        print(f"Se compro {cantidad[i]} de {descripcion[i]} ")
        print("Nombre del chofer:", nombre_chofer)
        print("Patente:", patente)
        
        cursor.execute("select COALESCE(id_truck, NULL) from truck where patent=%s;", [patente])
        id_truck = cursor.fetchone()
        if id_truck is None:
            print(id_truck)
            cursor.execute("insert into transaction(quantity, type, name_driver, date, nro_remmit, truck_id, truck_patent, url) values(%s,%s,%s,%s,%s,%s,%s,%s);",[float(cantidad[i].replace(',', '.')), str(descripcion[i]), str(nombre_chofer), fecha, remito, None, patente, url])
            con.commit()
        else:
            print(id_truck)
            cursor.execute("insert into transaction(quantity, type, name_driver, date, nro_remmit, truck_id, truck_patent, url) values(%s,%s,%s,%s,%s,%s,%s, %s);",[float(cantidad[i].replace(',', '.')), str(descripcion[i]), str(nombre_chofer), fecha, remito, id_truck[0], patente, url])
            con.commit()
    con.close()


# with fitz.open("../remmits/petro/petro4.pdf") as pdf:
#     get_data_petro(pdf)