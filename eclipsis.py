import ephem
import math

def find_lunar_nodes(start_date, end_date, step_hours=5):
    """ Troba els moments en què la Lluna creua la línia de l'eclíptica (nodes lunars) """

    observer = ephem.Observer()
    observer.date = start_date
    
    lunar_nodes = []
    
    current_date = ephem.Date(start_date)
    last_latitude = None  # Última latitud eclíptica de la Lluna
    
    while current_date < ephem.Date(end_date):
        moon = ephem.Moon(current_date)
        
        # Latitud eclíptica de la Lluna (geocèntrica)
        moon_latitude = math.degrees(moon.hlat)  # Convertim de radians a graus
        
        if last_latitude is not None:
            # Comprovem si ha creuat l'eclíptica (canvi de signe a hlat)
            if last_latitude < 0 and moon_latitude > 0:
                node_type = "Node Ascendent"
                lunar_nodes.append((current_date, node_type))
            elif last_latitude > 0 and moon_latitude < 0:
                node_type = "Node Descendent"
                lunar_nodes.append((current_date, node_type))

        # Actualitzar valors
        last_latitude = moon_latitude
        current_date = ephem.Date(current_date + step_hours * ephem.hour)

    return lunar_nodes

# import ephem

def find_moon_phases(start_date, end_date, step_hours=1, tolerance=2):
    """ Troba les fases de la Lluna (Lluna Nova i Lluna Plena) durant un període de temps """

    observer = ephem.Observer()
    observer.date = start_date
    full_and_new_moons = []

    # Càlcul de la Lluna i el Sol
    current_date = ephem.Date(start_date)

    while current_date < ephem.Date(end_date):
        moon = ephem.Moon(current_date)
        sun = ephem.Sun(current_date)

        # Calcular la longitud eclíptica de la Lluna i del Sol en graus
        moon_longitude_deg = moon.hlong * 180 / 3.14159265358979  # Convertir a graus
        # sun_longitude_deg = sun.hlong * 180 / 3.14159265358979    # Convertir a graus
        # Longitud heliocèntrica de la Terra (equivalent a la geocèntrica del Sol + 180°)
        long_heliocentric_earth_rad = float(sun.hlong)  
        sun_longitude_deg = (math.degrees(long_heliocentric_earth_rad) + 180) % 360

        # Diferència angular entre la Lluna i el Sol
        angular_difference = abs(moon_longitude_deg - sun_longitude_deg)

        # Ajustem la diferència angular per tenir en compte el cicle complet (0º a 360º)
        if angular_difference > 180:
            angular_difference = 360 - angular_difference

        # Busquem Lluna Nova (aproximadament 0º) o Lluna Plena (aproximadament 180º)
        if angular_difference < tolerance:
            full_and_new_moons.append((current_date, "Lluna Nova"))
            # print(f'{current_date} Lluna Nova')
        elif abs(angular_difference - 180) < tolerance:
            full_and_new_moons.append((current_date, "Lluna Plena"))
            # print(f'{current_date} Lluna Plena')

        # Incrementar la data
        current_date = ephem.Date(current_date + step_hours * ephem.hour)

    return full_and_new_moons


# Definir el període de cerca
start_date = "2025/01/01"
end_date = "2035/12/31"

# Executar la funció
phases = find_moon_phases(start_date, end_date)
nodes = find_lunar_nodes(start_date, end_date)

coincidencies = []    
for data, moon_type in phases:
    for date, node_type in nodes:
        # Comprovar si les dates estan dins de 1 dia de diferència
        if abs(data - date) <= 0.1:
            coincidencies.append((date, node_type, data, moon_type))

print(len(nodes))
print(len(phases))
print(len(coincidencies))
dia = 1
for dia1, node, dia2, fase in coincidencies:
    # print(dia1, node, dia2, fase)
    if round(dia1) != round(dia):
        print(dia1, node, fase)
        dia = dia1