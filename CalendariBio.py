import ephem
from datetime import datetime, timedelta
import math
import calendar

# Diccionaris
sign_elements = {
    'Aries': 'Foc',
    'Leo': 'Foc',
    'Sagittarius': 'Foc',
    'Taurus': 'Terra',
    'Virgo': 'Terra',
    'Capricorn': 'Terra',
    'Gemini': 'Aire',
    'Libra': 'Aire',
    'Aquarius': 'Aire',
    'Cancer': 'Aigua',
    'Scorpio': 'Aigua',
    'Pisces': 'Aigua'
}
sign_modalities = {
    'Aries': 'Cardinal',
    'Leo': 'Fixe',
    'Sagittarius': 'Mutable',
    'Taurus': 'Fixe',
    'Virgo': 'Mutable',
    'Capricorn': 'Cardinal',
    'Gemini': 'Mutable',
    'Libra': 'Cardinal',
    'Aquarius': 'Fixe',
    'Cancer': 'Cardinal',
    'Scorpio': 'Fixe',
    'Pisces': 'Mutable'
}

# Funcións
def get_zodiac_sign(longitude):
    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return zodiac_signs[int(longitude // 30)]

def find_lunar_nodes(start_date, end_date, step_hours=1):

    observer = ephem.Observer()
    observer.date = start_date
    
    lunar_nodes = []
    
    current_date = ephem.Date(start_date)
    last_latitude = None  # Última latitud eclíptica de la Lluna
    last_diff = None
    
    while current_date < ephem.Date(end_date):
        moon = ephem.Moon(current_date)
        
        # Latitud eclíptica de la Lluna (geocèntrica)
        moon_latitude = math.degrees(moon.hlat) # Convertim de radians a graus
        if last_latitude is not None:
            diff_latitude = moon_latitude - last_latitude    

            # Comprovem si ha creuat l'eclíptica (canvi de signe a hlat)
            if last_latitude < 0 and moon_latitude > 0:
                type = "Node Ascendent"
                lunar_nodes.append((current_date, type))
            elif last_latitude > 0 and moon_latitude < 0:
                type = "Node Descendent"
                lunar_nodes.append((current_date, type))

            # Detectar màxims i mínims (canvi de direcció)
            if last_diff is not None and last_diff * diff_latitude < 0:
                type = "Node Màxim" if last_diff > 0 else "Node Mínim"
                lunar_nodes.append((current_date, type))
            
            last_diff = diff_latitude

        # Actualitzar valors
        last_latitude = moon_latitude
        current_date = ephem.Date(current_date + step_hours * ephem.hour)
    
    return lunar_nodes

def track_planetary_signs(start_date, end_date, step_hours=1):
    planetes_info = []
    date = start_date
    planets = [ephem.Sun(), ephem.Moon()]
    
    last_signs = {p.name: None for p in planets}
    # Càlcul de la Lluna i el Sol
    
    while date <= end_date:
        for planet in planets:
            planet.compute(date)
                    # Obtenim el signe zodiacal i element

            # Obtenim la longitud eclíptica per tots els planetes
            if isinstance(planet, (ephem.Sun, ephem.Moon)):
                longitude = ephem.Ecliptic(planet).lon * 180 / ephem.pi  # Lluna i Sol (geocèntric)
            else:
                longitude = ephem.Ecliptic(planet).lon * 180 / ephem.pi  # Restants planetes (heliocèntric)

            sign = get_zodiac_sign(longitude)
            sign_element = sign_elements.get(sign, "Desconegut")
            sign_modalitie = sign_modalities.get(sign, "Desconegut")
            
            # Només comparem si el valor de last_signs no és None
            if last_signs[planet.name] is None:
                last_signs[planet.name] = sign
            if last_signs[planet.name] != sign:
                planetes_info.append((planet.name, sign, date.strftime('%Y-%m-%d %Hh'), sign_element, sign_modalitie, round(planet.phase), planet.hlat*10))
                last_signs[planet.name] = sign

        # Avançar al següent moment
        date += timedelta(hours=step_hours)
    
    return planetes_info

def calcular_distancia_lluna_terra(start_date, end_date):

    # Inicialitzar l'observador
    observer = ephem.Observer()

    # Inicialitzar la data actual com la data d'inici
    current_date = start_date

    distancies = []
    # Iterar per cada dia dins del període
    while current_date <= end_date:
        # Configurar la data per l'observador
        observer.date = current_date.strftime("%Y-%m-%d")  # Formatar la data per Ephem

        # Obtenir la Lluna
        moon = ephem.Moon(observer)

        # Distància entre la Lluna i la Terra (en km)
        distancia_lluna_terra = moon.earth_distance * 149597870.7  # Convertir a km
        
        # Emmagatzemar la distància i la data
        distancies.append((current_date, distancia_lluna_terra))
        
         
        # Passar al següent dia
        current_date += timedelta(days=1)

    return distancies

def determinar_tendencia(distancies):
    
    tendències = []
    tendència_precedent = None
    # data_precedent = len(distancies[0])

    # Comprovem la tendència comparant les distàncies de dos dies consecutius
    for i in range(1, len(distancies)):
        data_precedent, distancia_precedent = distancies[i-1]
        data_actual, distancia_actual = distancies[i]
        
        if distancia_actual < distancia_precedent:
            nova_tendència = "La Lluna es comença a acostar "
        elif distancia_actual > distancia_precedent:
            nova_tendència = "La Lluna es comença a allunyar"
        else:
            continue  # Si no hi ha canvi, no afegir res

        # Emmagatzemar només si la tendència és diferent de la anterior
        if tendència_precedent != nova_tendència:
            tendències.append((data_precedent, nova_tendència, distancia_precedent))
            tendència_precedent = nova_tendència

    return tendències

def lluna_plena_nova(start_date, end_date, step_hours=1):
    
    observer = ephem.Observer()
    observer.date = start_date
    
    llunes = []
    
    current_date = ephem.Date(start_date)

    while current_date < ephem.Date(end_date):
        moon = ephem.Moon(current_date)
        longitude = ephem.Ecliptic(moon).lon * 180 / ephem.pi  # Lluna i Sol (geocèntric)
        signe = get_zodiac_sign(longitude)
        
        if moon.phase > 99.5:
            type = "Lluna Plena"
            llunes.append((current_date, type, signe))
        elif moon.phase < 0.5:
            type = "Lluna Nova"
            llunes.append((current_date, type, signe))

        # Actualitzar valors
        current_date = ephem.Date(current_date + step_hours * ephem.hour)
    
    return llunes


def unir_llistes(list1, list2):
    # Fusionar les dues llistes respectant l'ordre de les dates
    merged_list = []
    i, j = 0, 0

    while i < len(list1) and j < len(list2):
        # Compara les dates
        if list1[i][0] < list2[j][0]:
            merged_list.append(list1[i])
            i += 1
        else:
            merged_list.append(list2[j])
            j += 1

    # Si queden elements a la llista 1
    while i < len(list1):
        merged_list.append(list1[i])
        i += 1

    # Si queden elements a la llista 2
    while j < len(list2):
        merged_list.append(list2[j])
        j += 1

    # Mostrar la llista fusionada
    return merged_list

# Exemple d'ús amb dates actuals
start_date = datetime.now()
# end_date = datetime.now() + timedelta(weeks=8)
end_date = datetime.now() + timedelta(days=365)
print()
print(start_date, end_date)

# Calcular 
# distancies = calcular_distancia_lluna_terra(start_date, end_date)
# tendències = determinar_tendencia(distancies)
nodes = find_lunar_nodes(start_date, end_date)
# planetes_info = track_planetary_signs(start_date, end_date)
llunes = lluna_plena_nova(start_date,end_date)
lunar_events = unir_llistes(nodes, llunes)
print(lunar_events)

# Imprimir
print()
lluna_previa = None
for data, lluna,signe in llunes:
    if lluna_previa != lluna:
        print(data, lluna, signe)
        lluna_previa = lluna
print()        

for data, tipus in nodes:
    print(data, tipus)
print()

# for data, tendència, distancia in tendències[1:]:
#     print(f"Data: {data} | {tendència} | Distancia: {round(distancia/1000)}")
# print()

# print(f"{'Planet':<10}{'Sign Entrant':<15}{'Data':<20}{'Element':<10}{'Modalitie':<12}{'Fase':<10}{'Latitutd*100'}")
# print("-" * 120)
# Formatació de cada línia
# for planeta, signe, data, element, modalitat, fase, latitud in planetes_info:
    # print(f"{planeta:<10}{signe:<15}{data:<20}{element:<10}{modalitat:<12}{fase:<10}{round(latitud, 2)}")

# Dades d'exemple (les teves dades reals)
# lunar_events = [
#     ("2025-03-01", "Node Ascendent"),
#     ("2025-03-07", "Node Màxim"),
#     ("2025-03-13", "Lluna Plena (Virgo)"),
#     ("2025-03-14", "Node Descendent"),
#     ("2025-03-22", "Node Mínim"),
#     ("2025-03-27", "Lluna Nova (Aries)"),
#     ("2025-03-28", "Node Ascendent")
# ]

# import calendar
# from datetime import datetime, timedelta
# import ephem

# # Dades d'exemple (els teus esdeveniments reals)
# lunar_events = [
#     (ephem.Date("2025-03-01"), "Node Ascendent"),
#     (ephem.Date("2025-03-07"), "Node Màxim"),
#     (ephem.Date("2025-03-13"), "Lluna Plena (Virgo)"),
#     (ephem.Date("2025-03-14"), "Node Descendent"),
#     (ephem.Date("2025-03-22"), "Node Mínim"),
#     (ephem.Date("2025-03-27"), "Lluna Nova (Aries)"),
#     (ephem.Date("2025-03-28"), "Node Ascendent"),
#     (ephem.Date("2025-04-06"), "Lluna Plena (Libra)"),
#     (ephem.Date("2025-04-19"), "Node Ascendent"),
#     # Afegeix més esdeveniments aquí
# ]

# Funció per convertir ephem.Date a string
def convert_ephem_to_str(ephem_date):
    # Si la data és un objecte ephem.Date, la convertim a string
    if isinstance(ephem_date, ephem.Date):
        return str(ephem_date)
    return ephem_date

# Funció per calcular els dies entre dos dates
def get_days_in_range(start_date, end_date):
    date_list = []
    delta = timedelta(days=1)
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += delta
    return date_list

def print_month_calendar(year, month, events):
    month_name = calendar.month_name[month]
    print(f"\n📅 {month_name.upper()} {year}")
    print("-" * 40)
    
    # Encabezado del calendari
    print("Dl Dt Dc Dj Dv Ds Dg")
    
    month_calendar = calendar.monthcalendar(year, month)
    
    # Calcular els intervals de Node Màxim a Node Mínim i de Node Mínim a Node Màxim
    max_to_min_dates = []
    min_to_max_dates = []
    
    # Buscar les dates de Node Màxim i Node Mínim per crear els intervals
    for i in range(len(events)):
        # Convertim les dates a string
        event_date = convert_ephem_to_str(events[i][0])
        event_name = events[i][1]
        
        # Convertim la data al format correcte (per exemple, '%Y-%m-%d' si no té hora)
        if isinstance(event_date, str):
            event_date = datetime.strptime(event_date, "%Y/%m/%d %H:%M:%S")
        else:
            event_date = datetime.strptime(str(event_date), "%Y-%m-%d")
        
        # Calcular interval si hi ha Node Màxim o Node Mínim
        if "Node Màxim" in event_name:
            # Busquem el següent "Node Mínim"
            for j in range(i + 1, len(events)):
                next_event_date = convert_ephem_to_str(events[j][0])
                next_event_name = events[j][1]
                
                if isinstance(next_event_date, str):
                    next_event_date = datetime.strptime(next_event_date, "%Y/%m/%d %H:%M:%S")
                else:
                    next_event_date = datetime.strptime(str(next_event_date), "%Y-%m-%d")

                if "Node Mínim" in next_event_name:
                    max_to_min_dates = get_days_in_range(event_date, next_event_date)
                    break
        
        elif "Node Mínim" in event_name:
            # Busquem el següent "Node Màxim"
            for j in range(i + 1, len(events)):
                next_event_date = convert_ephem_to_str(events[j][0])
                next_event_name = events[j][1]
                
                if isinstance(next_event_date, str):
                    next_event_date = datetime.strptime(next_event_date, "%Y/%m/%d %H:%M:%S")
                else:
                    next_event_date = datetime.strptime(str(next_event_date), "%Y-%m-%d")

                if "Node Màxim" in next_event_name:
                    min_to_max_dates = get_days_in_range(event_date, next_event_date)
                    break

    for week in month_calendar:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += "   "
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                
                # Buscar l'esdeveniment per aquesta data
                event = next((e[1] for e in events if convert_ephem_to_str(e[0]) == date_str), None)
                
                # Establir el color per aquesta data
                if event:
                    if "Node Ascendent" in event:
                        # Si l'esdeveniment és "Node Ascendent", es pinta de vermell
                        week_str += f"\033[31m{day:2d}\033[0m "
                    elif "Node Descendent" in event:
                        # Si l'esdeveniment és "Node Descendent", es pinta de vermell
                        week_str += f"\033[31m{day:2d}\033[0m "
                    elif "Lluna Nova" in event:
                        # Si l'esdeveniment és "Lluna Nova", es pinta de negre
                        week_str += f"\033[30m{day:2d}\033[0m "
                    elif "Lluna Plena" in event:
                        # Si l'esdeveniment és "Lluna Plena", es pinta de groc
                        week_str += f"\033[93m{day:2d}\033[0m "
                    else:
                        # Per altres esdeveniments, es pinta amb el color per defecte
                        week_str += f"\033[94m{day:2d}\033[0m "
                else:
                    # Aplicar el color de Node Màxim a Node Mínim (Verd)
                    if date_obj in max_to_min_dates:
                        week_str += f"\033[92m{day:2d}\033[0m "
                    # Aplicar el color de Node Mínim a Node Màxim (Blau)
                    elif date_obj in min_to_max_dates:
                        week_str += f"\033[94m{day:2d}\033[0m "
                    else:
                        # Si no hi ha esdeveniment, es pinta el dia amb el color per defecte
                        week_str += f"\033[0m{day:2d}\033[0m "
        
        print(week_str)

def print_full_year_calendar(year, events):
    for month in range(1, 13):
        print_month_calendar(year, month, events)

# Mostrar el calendari complet de l'any 2025
print_full_year_calendar(2025, lunar_events)
