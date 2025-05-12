import networkx as nx
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString
import contextily as ctx

# Datos simulados para nodos (ubicaciones) con coordenadas geográficas (latitud, longitud)
nodos_simulados_geo = {
    "Centro Distribucion CEDI - Sur": (3.34, -76.53), # Sur de Cali
    "Punto Entrega 1 - Tequendama": (3.43, -76.52), # Tequendama
    "Punto Entrega 2 - Granada": (3.45, -76.51),   # Granada
    "Punto Entrega 3 - San Antonio": (3.44, -76.52), # San Antonio
    "Punto Entrega 4 - Ciudad Jardin": (3.36, -76.53), # Ciudad Jardín
    "Punto Entrega 5 - Menga": (3.51, -76.47)      # Menga (norte)
}

# Datos simulados para aristas (rutas) con pesos (tiempo de viaje en minutos)
aristas_simuladas = [
    ("Centro Distribucion CEDI - Sur", "Punto Entrega 1 - Tequendama", {'weight': 20}),
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

# Crear el grafo dirigido
G = nx.DiGraph()

# Añadir nodos con sus coordenadas geográficas como atributos 'geometry' y 'pos'
# Geopandas trabaja mejor con la columna 'geometry'
# NetworkX para dibujar aún necesita 'pos' en (x, y) si usaras nx.draw
for nodo, (lat, lon) in nodos_simulados_geo.items():
    G.add_node(nodo, geometry=Point(lon, lat), pos=(lon, lat)) # Nota: Geopandas usa (lon, lat)

# Añadir aristas con sus pesos
G.add_edges_from(aristas_simuladas)

# --- Preparar datos para Geopandas ---
# Crear un GeoDataFrame para los nodos
nodos_gdf = gpd.GeoDataFrame.from_dict(nodos_simulados_geo, orient='index', columns=['lat', 'lon'])
nodos_gdf['geometry'] = nodos_gdf.apply(lambda row: Point(row['lon'], row['lat']), axis=1)

# Crear un GeoDataFrame para las aristas (rutas)
# Necesitamos crear LineString geometries para las aristas
aristas_list = []
for u, v, data in G.edges(data=True):
    point_u = nodos_gdf.loc[u]['geometry']
    point_v = nodos_gdf.loc[v]['geometry']
    # Asegurarse de que ambos puntos son válidos antes de crear la LineString
    if point_u.is_valid and point_v.is_valid:
        line = LineString([point_u, point_v])
        if line.is_valid: # Verificar que la línea creada es válida
             aristas_list.append({'source': u, 'target': v, 'weight': data['weight'], 'geometry': line})
        else:
             print(f"Advertencia: No se pudo crear LineString para el borde {u} -> {v}")
    else:
        print(f"Advertencia: Puntos inválidos para el borde {u} -> {v}")


aristas_gdf = gpd.GeoDataFrame(aristas_list, crs="EPSG:4326") # Asignar CRS (Sistema de Coordenadas de Referencia)

# Si Contextily falla, puede intentar reproyectar a Web Mercator (EPSG:3857)
# nodos_gdf = nodos_gdf.to_crs(epsg=3857)
# aristas_gdf = aristas_gdf.to_crs(epsg=3857)

# --- Visualización con Mapa Base ---
fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# Dibujar las aristas en el mapa
aristas_gdf.plot(ax=ax, color='gray', linewidth=1, alpha=0.7)

# Dibujar los nodos en el mapa
nodos_gdf.plot(ax=ax, marker='o', color='red', markersize=50, zorder=5) # zorder para asegurar que los puntos estén encima de las líneas

# Añadir etiquetas a los nodos usando las posiciones (lon, lat)
for x, y, label in zip(nodos_gdf.geometry.x, nodos_gdf.geometry.y, nodos_gdf.index):
    ax.annotate(label, xy=(x, y), xytext=(5, 5), textcoords="offset points", fontsize=9, weight='bold')

# Añadir etiquetas a las aristas (pesos) usando interpolate(0.5)
for idx, row in aristas_gdf.iterrows():
    # Usar interpolate(0.5, normalized=True) para obtener el punto medio
    midpoint = row['geometry'].interpolate(0.5, normalized=True)
    ax.annotate(f"{row['weight']}", (midpoint.x, midpoint.y), textcoords="offset points", xytext=(0,5), ha='center', fontsize=8, color='blue') # Cambié a azul para contraste

# Añadir el mapa base usando Contextily
# Es importante que tus datos estén en un CRS que Contextily entienda (EPSG:3857 o EPSG:4326)
# Usamos el crs del GeoDataFrame de aristas
ctx.add_basemap(ax, crs=aristas_gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)

# Configurar límites del mapa para que se ajusten a tus datos
# ax.set_extent([aristas_gdf.total_bounds[0] - 0.01, aristas_gdf.total_bounds[2] + 0.01, # Añadir un pequeño margen
#                aristas_gdf.total_bounds[1] - 0.01, aristas_gdf.total_bounds[3] + 0.01])


plt.title("Red de Distribución Simulada sobre Mapa de Cali", size=16)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.show()

# --- Ejemplo de cómo resaltar una ruta optimizada sobre el mapa ---
fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# Una ruta de ejemplo (Centro -> Punto 4 -> Punto 3 -> Punto 1 -> Centro)
ruta_ejemplo_edges = [
    ("Centro Distribucion CEDI - Sur", "Punto Entrega 4 - Ciudad Jardin"),
    ("Punto Entrega 4 - Ciudad Jardin", "Punto Entrega 3 - San Antonio"),
    ("Punto Entrega 3 - San Antonio", "Punto Entrega 1 - Tequendama"),
    ("Punto Entrega 1 - Tequendama", "Centro Distribucion CEDI - Sur")
]

# Filtrar las aristas que forman la ruta de ejemplo para dibujarlas de forma diferente
ruta_gdf = aristas_gdf[aristas_gdf.apply(lambda row: (row['source'], row['target']) in ruta_ejemplo_edges, axis=1)]
otras_aristas_gdf = aristas_gdf[~aristas_gdf.apply(lambda row: (row['source'], row['target']) in ruta_ejemplo_edges, axis=1)]


# Dibujar las otras aristas (en gris)
otras_aristas_gdf.plot(ax=ax, color='gray', linewidth=1, alpha=0.7)

# Dibujar las aristas de la ruta resaltada (en rojo y más gruesas)
ruta_gdf.plot(ax=ax, color='red', linewidth=3, zorder=3) # zorder para que esté por encima de las otras líneas

# Dibujar los nodos
nodos_gdf.plot(ax=ax, marker='o', color='blue', markersize=70, zorder=5) # Nodos en azul para contraste

# Añadir etiquetas a los nodos
for x, y, label in zip(nodos_gdf.geometry.x, nodos_gdf.geometry.y, nodos_gdf.index):
    ax.annotate(label, xy=(x, y), xytext=(5, 5), textcoords="offset points", fontsize=9, weight='bold')

# Añadir etiquetas de pesos a las aristas (puedes optar por solo poner los de la ruta)
for idx, row in aristas_gdf.iterrows(): # O iterar solo sobre ruta_gdf si prefieres
    # Usar interpolate(0.5, normalized=True) para obtener el punto medio
    midpoint = row['geometry'].interpolate(0.5, normalized=True)
    color_etiqueta = 'darkred' if (row['source'], row['target']) in ruta_ejemplo_edges else 'blue' # Color diferente para las etiquetas de la ruta
    ax.annotate(f"{row['weight']}", (midpoint.x, midpoint.y), textcoords="offset points", xytext=(0,5), ha='center', fontsize=8, color=color_etiqueta)


# Añadir el mapa base
ctx.add_basemap(ax, crs=aristas_gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)

# Ajustar límites
# ax.set_extent([aristas_gdf.total_bounds[0] - 0.01, aristas_gdf.total_bounds[2] + 0.01,
#                aristas_gdf.total_bounds[1] - 0.01, aristas_gdf.total_bounds[3] + 0.01])

plt.title("Red de Distribución con Ruta de Ejemplo Resaltada sobre Mapa", size=16)
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.show()
