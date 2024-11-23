from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

# def is_extra(type):
#     # decimal_part = Decimal(str(numero)).as_tuple().exponent
#     # return abs(decimal_part) > 1
#     if 'DIESEL' in type or 'INFINIA' in type:
#         return False
#     return True

@login_required
def select_patent(request):
    nro_remmit = request.GET.get('nro_remmit')
    owner_id = request.GET.get('owner_id')

    print(f"nro_remmit: {nro_remmit}, owner_id: {owner_id}")
    with connection.cursor() as cursor:
        cursor.execute("select patent from truck where id_owner = %s;", [owner_id])
        columnas = [col[0] for col in cursor.description]
        patents = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        cursor.execute("select truck_patent from transaction where nro_remmit = %s and truck_id is null;", [nro_remmit])
        columnas = [col[0] for col in cursor.description]
        patent = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        print(patent[0]['truck_patent'])
    return render(request, 'select_patents.html', {'nro_remmit': nro_remmit, 'owner_id' : owner_id, 'patents': patents, 'patent': patent[0]['truck_patent']})


@login_required
def unknown_references(request):
    remitos = ""
    with connection.cursor() as cursor:
        cursor.execute("select * from transaction where truck_id is null;")
        columnas = [col[0] for col in cursor.description]
        remitos = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    return render(request, 'unknown_references.html', {'remitos': remitos})

@login_required
def add_remmit(request):
    nro_remmit = request.GET.get('nro_remmit')
    owner_id = request.GET.get('owner_id')
    patent = request.GET.get('patent')
    print(f"nro_remmit: {nro_remmit}, owner_id: {owner_id}")
    with connection.cursor() as cursor:
        cursor.execute("select id_truck from truck where id_owner = %s and patent = %s;", [owner_id, patent])
        columnas = [col[0] for col in cursor.description]
        truck = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        id_truck = truck[0]['id_truck']
        print(f"Truck id: {id_truck}, patent: {patent}")
        cursor.execute("update transaction set truck_id = %s, truck_patent = %s where nro_remmit = %s;", [id_truck, patent, nro_remmit])
    return redirect('index')


@login_required
def select_owner(request):
    nro_remmit = request.GET.get('nro_remmit')
    with connection.cursor() as cursor:
        cursor.execute("select * from owner ORDER BY name ASC;")
        columnas = [col[0] for col in cursor.description]
        owners = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    return render(request, 'select_owner.html', {'nro_remmit': nro_remmit, 'owners': owners})

@login_required
def index(request):
    query = request.GET.get('query', '')  # Captura el valor de búsqueda
    with connection.cursor() as cursor:
        # Si no hay búsqueda, muestra todos los datos; si hay, aplica un filtro
        if query:
            cursor.execute("""
                SELECT * FROM owner
                WHERE name ILIKE %s
                ORDER BY name ASC;
            """, [f"%{query}%"])
        else:
            cursor.execute("SELECT * FROM owner ORDER BY name ASC;")
        
        columnas = [col[0] for col in cursor.description]
        owners = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

    return render(request, 'index.html', {'carriers': owners, 'query': query})


def patents(request):
    id = request.GET.get('id')
    with connection.cursor() as cursor:
        # Escribe la consulta SQL que necesitas
        cursor.execute("select patent from truck where id_owner = %s;", [id])
        columnas = [col[0] for col in cursor.description]
        patents = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        for patent in patents:
            print(patent)

    return render(request, 'patents.html', {'patents': patents, 'id': id})

@login_required
def add_user(request):
    return render(request, 'add_carrier.html')

@login_required
@csrf_exempt
def insert_patent(request):
    if request.method == 'POST':
        patent = request.POST.get('patent')
        
        id = request.POST.get('id')

        print (f"Insertando patent {patent} para el carrier con ID: {id}")
        with connection.cursor() as cursor:
            # Escribe la consulta SQL que necesitas
            cursor.execute("INSERT INTO truck (patent, id_owner) VALUES (%s, %s);", [patent, id])
    return redirect('index')

@login_required
def insert(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        patent = request.POST.get('patent')
        print (f"Insertando carrier con nombre {name} y patent {patent}")
        with connection.cursor() as cursor:
            # Escribe la consulta SQL que necesitas
            cursor.execute("insert into owner (name) values (%s);", [name])
            cursor.execute("insert into truck (patent, id_owner) values (%s, (select id_owner from owner where name = %s));", [patent, name])
    return redirect('index')

@login_required
def balance(request):
    id = request.GET.get('id')
    start_date = request.GET.get('start_date')  # Fecha inicial
    end_date = request.GET.get('end_date')  # Fecha final
    
    with connection.cursor() as cursor:
        if start_date and end_date:
            # Filtra los remitos por rango de fechas
            cursor.execute("""
                SELECT * FROM transaction 
                WHERE (truck_id, truck_patent) IN (
                    SELECT id_truck, patent 
                    FROM truck 
                    WHERE id_owner IN (
                        SELECT id_owner FROM owner WHERE id_owner = %s
                    )
                )
                AND date BETWEEN %s AND %s
                ORDER BY date ASC;
            """, [id, start_date, end_date])
        else:
            # Si no se proporcionan fechas, muestra todos los remitos
            cursor.execute("""
                SELECT * FROM transaction 
                WHERE (truck_id, truck_patent) IN (
                    SELECT id_truck, patent 
                    FROM truck 
                    WHERE id_owner IN (
                        SELECT id_owner FROM owner WHERE id_owner = %s
                    )
                )
                ORDER BY date ASC;
            """, [id])
        
        columnas = [col[0] for col in cursor.description]
        remitos = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        
        dieselQuantity = 0
        infiniaQuantity = 0
        extraQuantity = 0

        for remito in remitos:
            quantity = remito['quantity'] if remito['quantity'] is not None else 0
            type = remito['type']
            
            if 'DIESEL' in type: 
                dieselQuantity += quantity
            elif 'INFINIA' in type:
                infiniaQuantity += quantity
            else:
                extraQuantity += quantity

        # Truncar a 4 decimales
        dieselQuantity = round(dieselQuantity, 4)
        infiniaQuantity = round(infiniaQuantity, 4)
        extraQuantity = round(extraQuantity, 4)



    with connection.cursor() as cursor:
        cursor.execute("select name from owner where id_owner = %s", [id])
        columnas = [col[0] for col in cursor.description]
        name = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

    return render(request, 'balance.html', {
        'remitos': remitos,
        'dieselQuantity': dieselQuantity,
        'infiniaQuantity': infiniaQuantity,
        'extraQuantity': extraQuantity,
        'start_date': start_date,
        'end_date': end_date,
        'name': name[0]['name']
    })


@login_required
def edit_carrier(request):
    id = request.GET.get('id')  # Obtén el valor del parámetro 'id' de la query string
    if id:
        print(f"Editando carrier con ID: {id}")
    else:
        return HttpResponse("ID no proporcionado", status=400)
    # carrier = Carrier.objects.get(id=id)
    with connection.cursor() as cursor:
        # Escribe la consulta SQL que necesitas
        cursor.execute("select * from owner where id_owner = %s;", [id])
        columnas = [col[0] for col in cursor.description]
        carrier = [dict(zip(columnas, fila)) for fila in cursor.fetchall()][0]
        print(carrier)


    with connection.cursor() as cursor:
        # Escribe la consulta SQL que necesitas
        cursor.execute("select patent from truck where id_owner = %s;", [id])
        columnas = [col[0] for col in cursor.description]
        patents = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        for patent in patents:
            print(patent)

    return render(request, 'edit_carrier.html', {'carrier': carrier, 'patents': patents})

@login_required
@csrf_exempt
def update_patent(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        name = request.POST.get('name')
        patents = request.POST.getlist('patent')

        print(f"Actualizando carrier con ID: {id} y nombre {name} ")
        print(f"Nuevas patents: {patents}")

        with connection.cursor() as cursor:
            # Escribe la consulta SQL que necesitas
            cursor.execute("UPDATE owner set name = %s where id_owner = %s;", [name, id])
            for patent in patents:
                cursor.execute("UPDATE truck set patent = %s where id_owner = %s;", [patent, id])
            
    return redirect('index')

@login_required
def delete(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        print(f"Eliminando carrier con ID: {id}")
        with connection.cursor() as cursor:
            # Escribe la consulta SQL que necesitas
            cursor.execute("delete from ownertruck_owner where id_owner = %s;", [id])

    return redirect('index')

def add_patent(request):
    
    id = request.GET.get('id')
    return render(request, 'add_patent.html', {'id': id})