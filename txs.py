from flask import Flask, request, jsonify
from sklearn.cluster import DBSCAN
import numpy as np
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Clave de API de Google Maps
API_KEY = os.getenv("GOOGLE_API_KEY", "TU_API_KEY")

# 🔧 Redondea una hora al bloque de 30 minutos más cercano
def redondear_a_media_hora(hora_str):
    hora = datetime.strptime(hora_str, "%H:%M")
    minutos = (hora.minute + 15) // 30 * 30
    if minutos == 60:
        hora += timedelta(hours=1)
        minutos = 0
    return hora.replace(minute=minutos, second=0).strftime("%H:%M")

# 🔧 Genera una ruta optimizada usando Google Directions API
def generar_ruta_google(grupo):
    if len(grupo) < 2:
        return grupo
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
        return grupo

# 🚀 Endpoint principal
@app.route('/optimizar', methods=['POST'])
def optimizar_rutas():
    empleados = request.json
    eventos = []

    # 📌 Crear eventos separados por entrada y salida
    for e in empleados:
        if e.get("Hora entrada"):
            eventos.append({
                **e,
                "Hora": redondear_a_media_hora(e["Hora entrada"]),
                "TipoEvento": "entrada",
                "EventoID": f"{e['Work Email']}_entrada"
            })
        if e.get("Hora Salida"):
            eventos.append({
                **e,
                "Hora": redondear_a_media_hora(e["Hora Salida"]),
                "TipoEvento": "salida",
                "EventoID": f"{e['Work Email']}_salida"
            })

    # 📦 Agrupar eventos por hora y tipo
    grupos_por_hora = {}
    for evento in eventos:
        clave = (evento["Hora"], evento["TipoEvento"])
        grupos_por_hora.setdefault(clave, []).append(evento)

    resultados = []
    grupo_id = 1

    # 🔁 Procesar cada grupo horario
    for (hora, tipo), grupo in grupos_por_hora.items():
        coords = np.radians([[e["DirecciónLAT"], e["DirecciónLONG"]] for e in grupo])
        kms_per_radian = 6371.0088
        epsilon = 5 / kms_per_radian
        db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine')
        labels = db.fit_predict(coords)

        # 🧩 Agrupar por etiquetas de DBSCAN
        subgrupos = {}
        for label, emp in zip(labels, grupo):
            subgrupos.setdefault(label, []).append(emp)

        # 🚐 Generar rutas optimizadas por subgrupo
        for subgrupo in subgrupos.values():
            for i in range(0, len(subgrupo), 4):
                chunk = subgrupo[i:i+4]
                ruta = generar_ruta_google(chunk) if len(chunk) > 1 else chunk
                for orden, emp in enumerate(ruta, start=1):
                    resultados.append({
                        "Grupo": grupo_id,
                        "Orden": orden,
                        "Nombre": f"{emp['First Name']} {emp['Last Name']}",
                        "Email": emp["Work Email"],
                        "Lat": emp["DirecciónLAT"],
                        "Lon": emp["DirecciónLONG"],
                        "Fecha": emp["Fecha"],
                        "Hora": emp["Hora"],
                        "TipoEvento": emp["TipoEvento"],
                        "Title": emp["Title"]
                    })
                grupo_id += 1

    return jsonify(resultados)

# 🔥 Necesario para correr localmente
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
