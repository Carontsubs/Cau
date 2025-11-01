import ephem



# Entrada: data, hora i lloc
data = '1978/09/29'  # Any/Mes/Dia
hora = '13:30:00'    # Hora en format HH:MM:SS
lloc = 'Barcelona'   # Nom de la ciutat per obtenir les coordenades

# Crear un objecte de data amb el format de ephem
data_hora = f'{data} {hora}'
print(data_hora)
observador = ephem.Observer()
observador.date = data_hora

# Coordenades de Barcelona (per exemple)
observador.lat = '41.3784'   # Latitud de Barcelona
observador.lon = '2.1925'    # Longitud de Barcelona

# Calcular les cúspides de les cases
ascendent = observador.radec_of(0, ephem.degrees('0'))  # Ascendent a 0°
ascendent_raj = ascendent[0]  # Ascensió recta de l'ascendent

# Generar les cúspides de les cases en graus amb un desplaçament de -90 graus (per desplaçar cap a l'est)
cases = []
for i in range(12):
    cusp = (ascendent_raj + ephem.degrees(i * 30) - ephem.degrees(90))  # Restem 90° per desplaçar cap a l'est
    cases.append(cusp % 360)  # Ens assegurem que estigui entre 0 i 360°

# Posicions dels planetes
planetes = {
    'Sol': ephem.Sun(observador),
    'Lluna': ephem.Moon(observador),
    'Mercuri': ephem.Mercury(observador),
    'Venus': ephem.Venus(observador),
    'Marte': ephem.Mars(observador),
    'Júpiter': ephem.Jupiter(observador),
    'Saturn': ephem.Saturn(observador),
    # 'Uranus': ephem.Uranus(observador),
    # 'Neptú': ephem.Neptune(observador),
    # 'Plutó': ephem.Pluto(observador)
}

# Funció per assignar els planetes a les cases
def assignar_casa(planeta_ra, cases):
    for i in range(12):
        # Cas 1: Comprovem si el planeta està dins del rang de dues cúspides consecutives
        if i == 11:  # Última casa (Casa 12)
            if (cases[i] <= planeta_ra < 360) or (0 <= planeta_ra < cases[0]):
                return i + 1
        else:  # Per a totes les altres cases
            if cases[i] <= planeta_ra < cases[i + 1]:
                return i + 1
    return None  # Si no es pot assignar

# Assignar planetes a les cases
for planeta, obj_planeta in planetes.items():
    ra_planeta = obj_planeta.ra  # Ascensió recta del planeta
    ra_planeta = ra_planeta * 180 / ephem.pi  # Convertir de radians a graus (ephem treballa en radians)
    
    casa = assignar_casa(ra_planeta, cases)
    
    if casa is None:
        print(f"{planeta} no es pot assignar a cap casa")
    else:
        print(f'{planeta} està a la Casa {casa}')
