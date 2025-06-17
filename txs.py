from flask import Flask, request, jsonify
from sklearn.cluster import DBSCAN
import numpy as np
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("GOOGLE_API_KEY", "TU_API_KEY_AQUI")

@app.route('/')
def home():
    return "¡API de optimización de rutas funcionando!"

@app.route('/optimizar', methods=['POST'])
def optimizar_rutas():
    empleados = request.json

    coords = np.radians([[e["DirecciónLAT"], e["DirecciónLONG"]] for e in empleados])
    kms_per_radian = 6371.0088
    epsilon = 5 / kms_per_radian
    db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine')
    labels = db.fit_predict(coords)

    grupos = {}
    for label, emp in zip(labels, empleados):
        grupos.setdefault(label, []).append(emp)

    grupos_finales = []
    for grupo in grupos.values():
        for i in range(0, len(grupo), 4):
            grupos_finales.append(grupo[i:i+4])

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
            return None

    resultados = []
    grupo_id = 1
    for grupo in grupos_finales:
        ruta = generar_ruta_google(grupo) if len(grupo) > 1 else None
        ruta = ruta if ruta else grupo
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
        grupo_id += 1

    return jsonify(resultados)

# 🔥 Esta parte es CRUCIAL para que funcione en Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

@app.route('/')
def home():
    return "¡API funcionando
