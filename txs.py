import requests
from sklearn.cluster import DBSCAN
import numpy as np

# Tu API Key de Google Maps
API_KEY = "AIzaSyCAWjGEbd8ZG83YANokmBpmPFUKIqkP0p8"

def optimizar_rutas_empleados(empleados):
    # Convertir coordenadas a radianes para DBSCAN con haversine
    coords = np.radians([[e["DirecciónLAT"], e["DirecciónLONG"]] for e in empleados])

    # Agrupar con DBSCAN (5 km de radio)
    kms_per_radian = 6371.0088
    epsilon = 5 / kms_per_radian
    db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine')
    labels = db.fit_predict(coords)

    # Agrupar empleados por cluster
    grupos = {}
    for label, emp in zip(labels, empleados):
        grupos.setdefault(label, []).append(emp)

    # Limitar a máximo 4 personas por grupo
    grupos_finales = []
    for grupo in grupos.values():
        for i in range(0, len(grupo), 4):
            grupos_finales.append(grupo[i:i+4])

    # Función para generar ruta optimizada con Google Directions API
    def generar_ruta_google(grupo):
        if len(grupo) < 2:
            return None

        origen = f"{grupo[0]['DirecciónLAT']},{grupo[0]['DirecciónLONG']}"
        waypoints = "|".join([f"{e['DirecciónLAT']},{e['DirecciónLONG']}" for e in grupo[1:]])
        url = (
            f"https://maps.googleapis.com/maps/api/directions/json?"
            f"origin={origen}&destination={origen}&waypoints=optimize:true|{waypoints}&key={API_KEY}"
        )

        response = requests.get(url)
        data = response.json()

        if data["status"] == "OK":
            orden = data["routes"][0]["waypoint_order"]
            ruta = [grupo[0]] + [grupo[1:][i] for i in orden]
            return ruta
        else:
            print("❌ Error en Directions API:", data)
            return None

    # Generar lista de resultados para SharePoint
    resultados = []
    grupo_id = 1
    for grupo in grupos_finales:
        if len(grupo) > 1:
            ruta = generar_ruta_google(grupo)
            if ruta:
                for orden, emp in enumerate(ruta, start=1):
                    resultados.append({
                        "Grupo": grupo_id,
                        "Orden": orden,
                        "Nombre": f"{emp['First Name']} {emp['Last Name']}",
                        "Email": emp["Work Email"],
                        "Lat": emp["DirecciónLAT"],
                        "Lon": emp["DirecciónLONG"],
                        "Fecha": emp["Fecha"],
                        "Hora": emp["Hora entrada"],
			"Title": emp["Title"]
                    })
            else:
                for emp in grupo:
                    resultados.append({
                        "Grupo": grupo_id,
                        "Orden": 1,
                        "Nombre": f"{emp['First Name']} {emp['Last Name']}",
                        "Email": emp["Work Email"],
                        "Lat": emp["DirecciónLAT"],
                        "Lon": emp["DirecciónLONG"],
                        "Fecha": emp["Fecha"],
                        "Hora": emp["Hora entrada"],
			"Title": emp["Title"]
                    })
        else:
            emp = grupo[0]
            resultados.append({
                "Grupo": grupo_id,
                "Orden": 1,
                "Nombre": f"{emp['First Name']} {emp['Last Name']}",
                "Email": emp["Work Email"],
                "Lat": emp["DirecciónLAT"],
                "Lon": emp["DirecciónLONG"],
                "Fecha": emp["Fecha"],
                "Hora": emp["Hora entrada"],
		"Title": emp["Title"]
            })
        grupo_id += 1

    return resultados

# Ejemplo de datos recibidos desde Power Automate
empleados = [
    {
        "Title": "Empleado A",
        "First Name": "Juan",
        "Last Name": "Pérez",
        "Work Email": "juan@empresa.com",
        "Hora entrada": "18:00",
        "Hora Salida": "22:00",
        "Fecha": "2025-05-30",
        "Razon de Asignacion": "Overtime",
        "Asignado por": "Supervisor X",
        "DirecciónLAT": 10.0143,
        "DirecciónLONG": -83.9769
    },
    {
        "Title": "Empleado B",
        "First Name": "Ana",
        "Last Name": "Gómez",
        "Work Email": "ana@empresa.com",
        "Hora entrada": "18:00",
        "Hora Salida": "22:00",
        "Fecha": "2025-05-30",
        "Razon de Asignacion": "Overtime",
        "Asignado por": "Supervisor Y",
        "DirecciónLAT": 10.0147,
        "DirecciónLONG": -83.9766
    },
    {
        "Title": "Empleado C",
        "First Name": "Luis",
        "Last Name": "Martínez",
        "Work Email": "luis@empresa.com",
        "Hora entrada": "18:00",
        "Hora Salida": "22:00",
        "Fecha": "2025-05-30",
        "Razon de Asignacion": "Overtime",
        "Asignado por": "Supervisor Z",
        "DirecciónLAT": 10.0715,
        "DirecciónLONG": -84.1183
    },
    {
        "Title": "Empleado D",
        "First Name": "María",
        "Last Name": "Rodríguez",
        "Work Email": "maria@empresa.com",
        "Hora entrada": "18:00",
        "Hora Salida": "22:00",
        "Fecha": "2025-05-30",
        "Razon de Asignacion": "Overtime",
        "Asignado por": "Supervisor X",
        "DirecciónLAT": 10.0736,
        "DirecciónLONG": -84.1226
    },
    {
        "Title": "Empleado E",
        "First Name": "Carlos",
        "Last Name": "Fernández",
        "Work Email": "carlos@empresa.com",
        "Hora entrada": "18:00",
        "Hora Salida": "22:00",
        "Fecha": "2025-05-30",
        "Razon de Asignacion": "Overtime",
        "Asignado por": "Supervisor Y",
        "DirecciónLAT": 10.0140,
        "DirecciónLONG":  -83.9763
    }
]

# Llamar a la función y obtener los resultados
resultados = optimizar_rutas_empleados(empleados)

# Imprimir los resultados
import json
print(json.dumps(resultados, indent=2))


import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5555))
    app.run(host='0.0.0.0', port=port)
