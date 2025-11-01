import ephem
from datetime import datetime, timedelta
import math

# Exemple d'ús amb dates actuals
start_date = datetime.now()
end_date = datetime.now() + timedelta(weeks=4)
print(start_date, end_date)
# print()
# Funció per obtenir el signe zodiacal a partir de la longitud eclíptica
def get_zodiac_sign(longitude):
    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return zodiac_signs[int(longitude // 30)]

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
# Diccionari de les modalitats per a cada signe
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
# Dictionary of planetary dignities
planet_dignities = {
    'Sun': {
        'Rulership': 'Leo',
        'Exaltation': 'Aries',
        'Fall': 'Aquarius',
        'Exile': 'Libra'
    },
    'Moon': {
        'Rulership': 'Cancer',
        'Exaltation': 'Taurus',
        'Fall': 'Scorpio',
        'Exile': 'Capricorn'
    },
    'Mercury': {
        'Rulership': ['Gemini', 'Virgo'],
        'Exaltation': 'Virgo',
        'Fall': 'Pisces',
        'Exile': 'Sagittarius'
    },
    'Venus': {
        'Rulership': ['Taurus', 'Libra'],
        'Exaltation': 'Pisces',
        'Fall': 'Virgo',
        'Exile': 'Aries'
    },
    'Mars': {
        'Rulership': ['Aries', 'Scorpio'],
        'Exaltation': 'Capricorn',
        'Fall': 'Cancer',
        'Exile': 'Libra'
    },
    'Jupiter': {
        'Rulership': ['Sagittarius', 'Pisces'],
        'Exaltation': 'Cancer',
        'Fall': 'Capricorn',
        'Exile': 'Libra'
    },
    'Saturn': {
        'Rulership': ['Capricorn', 'Libra'],
        'Exaltation': 'Libra',
        'Fall': 'Aries',
        'Exile': 'Cancer'
    },
    'Uranus': {
        'Rulership': 'Aquarius',
        'Exaltation': 'Scorpio',
        'Fall': 'Taurus',
        'Exile': 'Leo'
    },
    'Neptune': {
        'Rulership': 'Pisces',
        'Exaltation': 'Cancer',
        'Fall': 'Virgo',
        'Exile': 'Sagittarius'
    },
    'Pluto': {
        'Rulership': 'Scorpio',
        'Exaltation': 'Pisces',
        'Fall': 'Taurus',
        'Exile': 'Leo'
    }
}

# Funció per obtenir dignitat i categoria del signe per qualsevol planeta
def get_planet_dignity(planet_obj, sign):
    # Obtenim el nom del planeta (com a cadena de text)
    planet = planet_obj.name  # Exemple: "Moon", "Venus", etc.
    
    # Obtenim les dignitats del planeta
    planet_dignity = planet_dignities.get(planet)
    
    if not planet_dignity:
        return f"Planet {planet} not found in the dignities list."
    
    # Comprovem si el planeta està en alguna dignitat
    dignity_info = []
    
    # Si el signe està en la regència del planeta (considerant múltiples signes per regència)
    if isinstance(planet_dignity['Rulership'], list):  # Si la regència és una llista de signes
        if sign in planet_dignity['Rulership']:
            dignity_info.append("Ruler")
    else:
        if sign == planet_dignity['Rulership']:
            dignity_info.append("Ruler")
    
    if sign == planet_dignity['Exaltation']:
        dignity_info.append("Exalt")
    if sign == planet_dignity['Fall']:
        dignity_info.append("Fall")
    if sign == planet_dignity['Exile']:
        dignity_info.append("Exile")
    
    # Retornem la llista de dignitats trobades
    return dignity_info

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

planetes_info = []

def track_planetary_signs(start_date, end_date, step_hours=1):
    date = start_date
    planets = [ephem.Sun(), ephem.Moon(), ephem.Mercury(), ephem.Venus(),
               ephem.Mars(), ephem.Jupiter(), ephem.Saturn()]
    # planets = [ephem.Jupiter(), ephem.Saturn()]
    
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
            # degrees_in_sign = get_degrees_within_sign(longitude)
            
            # print(f"{planet.name} es a {sign} at {date.strftime('%Y-%m-%d %H:%M')} UTC")
            # last_signs[planet.name] = sign

            # Només comparem si el valor de last_signs no és None
            if last_signs[planet.name] is None:
                print(f"{planet.name} is at {sign} {sign_element}")
                last_signs[planet.name] = sign
            if last_signs[planet.name] != sign:
                # print(f"{planet.name} enters {sign} at {date.strftime('%Y-%m-%d %H:%M')} UTC {sign_element} {sign_modalitie} {round(planet.phase)} {', '.join(get_planet_dignity(planet, sign))} {planet.hlat}")
                planetes_info.append((planet.name, sign, date.strftime('%Y-%m-%d %Hh'), sign_element, sign_modalitie, round(planet.phase),', '.join(get_planet_dignity(planet, sign)), round(planet.hlat, 2)*100))
                last_signs[planet.name] = sign

        # Avançar al següent moment
        date += timedelta(hours=step_hours)

def calcular_distancia_lluna_terra(start_date, end_date):
    """Calcula la distància entre la Lluna i la Terra diàriament entre dues dates."""

    # Inicialitzar l'observador
    observer = ephem.Observer()

    # # Convertir les dates d'inici i final a objects datetime
    # start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    # end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

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
    """Determina si la Lluna s'acosta o s'allunya de la Terra i emmagatzema només els canvis de tendència."""
    
    tendències = []
    tendència_precedent = None

    # Comprovem la tendència comparant les distàncies de dos dies consecutius
    for i in range(1, len(distancies)):
        data_precedent, distancia_precedent = distancies[i-1]
        data_actual, distancia_actual = distancies[i]
        
        if distancia_actual < distancia_precedent:
            nova_tendència = "La Lluna s'acosta a la Terra"
        elif distancia_actual > distancia_precedent:
            nova_tendència = "La Lluna s'allunya de la Terra"
        else:
            continue  # Si no hi ha canvi, no afegir res

        # Emmagatzemar només si la tendència és diferent de la anterior
        if tendència_precedent != nova_tendència:
            tendències.append((data_actual, nova_tendència, distancia_actual))
            tendència_precedent = nova_tendència

    return tendències

print()
# Calcular les distàncies
distancies = calcular_distancia_lluna_terra(start_date, end_date)
# Determinar i mostrar només les tendències canviants
tendències = determinar_tendencia(distancies)
nodes = find_lunar_nodes(start_date, end_date)

for data, tipus in nodes:
    print(data, tipus)
# Mostrar les tendències
print()
for data, tendència, distancia in tendències:
    print(f"Data: {data} | Tendència: {tendència} | Distancia: {round(distancia/1000)}")
print()
track_planetary_signs(start_date, end_date, step_hours=1)
print()
print(f"{'Planet':<10}{'Sign Entrant':<15}{'Data':<20}{'Element':<10}{'Modalitie':<12}{'Fase':<10}{'Dignities':<15}{'Latitutd*100'}")
print("-" * 120)

# Formatació de cada línia
for planeta, signe, data, element, modalitat, fase, digniti, latitud in planetes_info:
    print(f"{planeta:<10}{signe:<15}{data:<20}{element:<10}{modalitat:<12}{fase:<10}{digniti:<15}{latitud}")


# # Definir el període de temps
# start_date = "2025-01-01"
# end_date = "2025-01-10"

