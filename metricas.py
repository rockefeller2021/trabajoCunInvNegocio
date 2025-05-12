import networkx as nx
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString
import contextily as ctx
import pandas as pd # Importar pandas para tablas

# --- Datos simulados (los mismos que en el código de visualización del mapa) ---
# Estos datos definen los nodos (ubicaciones) y las aristas (rutas) con sus pesos (tiempo en minutos).
nodos_simulados_geo = {
    "Centro Distribucion CEDI - Sur": (3.34, -76.53), # Sur de Cali
    "Punto Entrega 1 - Tequendama": (3.43, -76.52), # Tequendama
    "Punto Entrega 2 - Granada": (3.45, -76.51),   # Granada
    "Punto Entrega 3 - San Antonio": (3.44, -76.52), # San Antonio
    "Punto Entrega 4 - Ciudad Jardin": (3.36, -76.53), # Ciudad Jardín
    "Punto Entrega 5 - Menga": (3.51, -76.47)      # Menga (norte)
}

aristas_simuladas = [
    ("Centro Distribucion CEDI - Sur", "Punto Entrega 1 - Tequendama", {'weight': 20}), # weight = tiempo en minutos
    ("Centro Distribucion CEDI - Sur", "Punto Entrega 4 - Ciudad Jardin", {'weight': 10}),
    ("Punto Entrega 1 - Tequendama", "Centro Distribucion CEDI - Sur", {'weight': 25}),
    ("Punto Entrega 1 - Tequendama", "Punto Entrega 2 - Granada", {'weight': 15}),
    ("Punto Entrega 1 - Tequendama", "Punto Entrega 3 - San Antonio", {'weight': 5}),
    ("Punto Entrega 2 - Granada", "Punto Entrega 1 - Tequendama", {'weight': 18}),
    ("Punto Entrega 2 - Granada", "Punto Entrega 5 - Menga", {'weight': 30}),
    ("Punto Entrega 3 - San Antonio", "Punto Entrega 1 - Tequendama", {'weight': 7}),
    ("Punto Entrega 3 - San Antonio", "Punto Entrega 4 - Ciudad Jardin", {'weight': 20}),
    ("Punto Entrega 4 - Ciudad Jardin", "Centro Distribucion CEDI - Sur", {'weight': 12}),
    ("Punto Entrega 4 - Ciudad Jardin", "Punto Entrega 3 - San Antonio", {'weight': 22}),
    ("Punto Entrega 5 - Menga", "Centro Distribucion CEDI - Sur", {'weight': 40})
]

# Crear el grafo dirigido de NetworkX
G = nx.DiGraph()
for nodo, (lat, lon) in nodos_simulados_geo.items():
    G.add_node(nodo, geometry=Point(lon, lat), pos=(lon, lat)) # Añadir geometría y posición
G.add_edges_from(aristas_simuladas)

# --- Definir una ruta de ejemplo para el análisis ---
# Esta ruta es una lista de tuplas (nodo_origen, nodo_destino)
ruta_ejemplo = [
    ("Centro Distribucion CEDI - Sur", "Punto Entrega 4 - Ciudad Jardin"),
    ("Punto Entrega 4 - Ciudad Jardin", "Punto Entrega 3 - San Antonio"),
    ("Punto Entrega 3 - San Antonio", "Punto Entrega 1 - Tequendama"),
    ("Punto Entrega 1 - Tequendama", "Centro Distribucion CEDI - Sur")
]

# --- Código para calcular el tiempo total de una ruta ---
def calcular_tiempo_total(grafo, ruta):
    """Calcula el tiempo total de una ruta sumando los pesos (tiempo) de las aristas."""
    tiempo_total = 0
    for origen, destino in ruta:
        if grafo.has_edge(origen, destino):
            tiempo_total += grafo[origen][destino]['weight']
        else:
            print(f"Advertencia: La arista ({origen}, {destino}) no existe en el grafo.")
            return None # Retornar None si una arista no existe
    return tiempo_total

# --- Código para estimar la distancia total de una ruta ---
# NOTA: Esta es una estimación simplificada usando el tiempo y una velocidad promedio.
# En un caso real, podrías tener los pesos de las aristas como distancia directamente.
def estimar_distancia_total(grafo, ruta, velocidad_promedio_km_min=0.5):
    """Estima la distancia total de una ruta basándose en el tiempo y una velocidad promedio."""
    tiempo_total = calcular_tiempo_total(grafo, ruta)
    if tiempo_total is not None:
        # Distancia = Velocidad * Tiempo
        distancia_km = tiempo_total * velocidad_promedio_km_min
        return distancia_km
    return None

# --- Código para estimar el consumo de combustible ---
# NOTA: Esta es una estimación muy simplificada.
def estimar_consumo_combustible(distancia_km, eficiencia_combustible_km_litro=10):
    """Estima el consumo de combustible basándose en la distancia y la eficiencia."""
    if distancia_km is not None and eficiencia_combustible_km_litro > 0:
        consumo_litros = distancia_km / eficiencia_combustible_km_litro
        return consumo_litros
    return None

# --- Código para contar el número de entregas en una ruta ---
# Asumimos que una entrega ocurre en cada nodo de destino de la ruta, excepto si es el nodo de origen inicial.
def contar_entregas(ruta, nodo_origen):
    """Cuenta el número de entregas en una ruta."""
    puntos_visitados_entrega = set() # Usamos un set para no contar el mismo punto varias veces
    entregas = 0
    # Iteramos sobre las aristas de la ruta
    for origen, destino in ruta:
        # Si el destino no es el nodo de origen inicial y no lo hemos contado ya como entrega
        if destino != nodo_origen and destino not in puntos_visitados_entrega:
            entregas += 1
            puntos_visitados_entrega.add(destino)
    return entregas

# --- Realizar los cálculos para la ruta de ejemplo ---
tiempo_ruta_ejemplo = calcular_tiempo_total(G, ruta_ejemplo)
distancia_ruta_ejemplo = estimar_distancia_total(G, ruta_ejemplo)
consumo_ruta_ejemplo = estimar_consumo_combustible(distancia_ruta_ejemplo)
entregas_ruta_ejemplo = contar_entregas(ruta_ejemplo, "Centro Distribucion CEDI - Sur")

# --- Presentar los resultados en una tabla (usando pandas) ---
if tiempo_ruta_ejemplo is not None and distancia_ruta_ejemplo is not None and consumo_ruta_ejemplo is not None:
    datos_analisis = {
        'Métrica': ['Tiempo Total', 'Distancia Estimada', 'Consumo Estimado Combustible', 'Número de Entregas'],
        'Valor': [f"{tiempo_ruta_ejemplo} minutos", f"{distancia_ruta_ejemplo:.2f} km", f"{consumo_ruta_ejemplo:.2f} litros", entregas_ruta_ejemplo]
    }
    df_analisis = pd.DataFrame(datos_analisis)

    print("--- Análisis de la Ruta de Ejemplo ---")
    print(df_analisis.to_string(index=False)) # Imprimir la tabla sin el índice de pandas

    # --- Opcional: Visualización simple de las métricas (ej. con barras) ---
    # Este gráfico es solo para mostrar los valores calculados.
    # Para el proyecto, sería más relevante graficar comparaciones (ej. ruta actual vs. ruta optimizada).
    metricas_a_graficar = {
        'Tiempo (min)': tiempo_ruta_ejemplo,
        'Distancia (km)': distancia_ruta_ejemplo,
        'Consumo (litros)': consumo_ruta_ejemplo
    }

    plt.figure(figsize=(8, 5))
    plt.bar(metricas_a_graficar.keys(), metricas_a_graficar.values(), color=['skyblue', 'lightgreen', 'salmon'])
    plt.ylabel("Valor")
    plt.title("Métricas Calculadas para la Ruta de Ejemplo")
    plt.show()

else:
    print("No se pudieron calcular las métricas debido a un error en la ruta o el grafo.")
