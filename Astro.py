from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const, props, object
import flatlib.aspects as aspects
from flatlib.protocols.temperament import Temperament
from flatlib.dignities import essential

# Creació de la carta astral
data_naixement = Datetime('2025/02/12', '00:00', '+00:00')
lloc_naixement = GeoPos('41n23', '2e10')
carta_astral = Chart(data_naixement, lloc_naixement, IDs=const.LIST_SEVEN_PLANETS, hsys=const.HOUSES_PLACIDUS)
print(data_naixement, lloc_naixement)
print()
sun = carta_astral.getObject(const.SUN)
moon = carta_astral.getObject(const.MOON)
print(sun.lon)
print(moon.lon)
# Llistar tots els angles (AC,DC)
# for angle in carta_astral.angles:
#     print(f'{angle.id} en el signe {angle.sign}')
print(f"Ascendent és {carta_astral.get(const.ASC).sign}")

# Obtenir la fase de la Lluna
print()
fase_lluna = carta_astral.getMoonPhase()
print(f'Fase de la Lluna: {fase_lluna}')
print()

planetes = []
# Llistar tots els objectes
for obj in carta_astral.objects:
    # Obtenir la casa on està cada planeta
    casa = carta_astral.houses.getObjectHouse(obj)
    # print(f"{obj.id} en el signe de {obj.sign} ({round(obj.signlon)}°). Casa {casa.id} {object.Object.movement(obj)} {', '.join(essential.EssentialInfo(obj).getDignities())}")
    planetes.append((obj.id, obj.sign, round(obj.signlon), casa.id, object.Object.movement(obj), "; ".join(essential.EssentialInfo(obj).getDignities())))

aspectes = []
# Buscar aspectes entre planetes
for obj1 in carta_astral.objects:
    for obj2 in carta_astral.objects:
        if obj1.id != obj2.id:  # Evitem comparar un planeta amb si mateix
            # Obtenim les posicions en graus (longitud dels planetes)
            lon_obj1 = obj1.signlon
            lon_obj2 = obj2.signlon
            
            # Calcularem la separació angular
            separacio = abs(lon_obj1 - lon_obj2)  # Restem les longituds
            if separacio > 180:
                separacio = 360 - separacio  # Ens quedem amb l'angle més petit
                
            # Obtenim l'aspecte
            aspecte = aspects.getAspect(obj1, obj2, const.MAJOR_ASPECTS)
            
            # Mostrar aspectes principals i la separació (graus)
            if aspecte:
                # aspecte_nom = aspecte_noms.get(aspecte.type, "Desconegut")
                if aspecte.type != -1 and separacio <= 8:
                    # Imprimir aspecte amb el nom i els graus exactes de separació
                    # print(f"{obj1.id} i {obj2.id} tenen un {props.aspect.name[aspecte.type]} a {separacio:.1f}°")
                    aspectes.append((obj1.id, obj2.id, props.aspect.name[aspecte.type], round(separacio, 1)))

# print(planetes)

print(f"{'Planet':<10}{'Sign':<10}{'dgr':<5}{'House':<10}{'Movement':<10}{'Dignities'}")
print("-" * 60)

# Formatació de cada línia
for planeta, signe, grau, casa, moviment, dignitat in planetes:
    print(f"{planeta:<10}{signe:<10}{grau:<5}{casa:<10}{moviment:<10}{dignitat}")

# print(aspectes)
print()
# print('Aspectes Majors:')
print(f"{'Planet':<10}{'Planet':<10}{'Aspecte':<10}{'dgr':<5}")
print("-" * 42)
for planeta1, planeta2, aspecte, grau in aspectes:
    print(f"{planeta1:<10}{planeta2:<10}{aspecte:<10}{grau:<5}")


temperament = Temperament(carta_astral)
score = temperament.getScore()
# print(score)

# Extreure els dos diccionaris de dins
temperaments = score['temperaments']
qualities = score['qualities']

# Imprimir la capçalera
print()
print(f"{'Temperament':<12} {'Value':<6}    {'Quality':<8} {'Value':<6}")
print("-" * 40)

# Iterem pels dos diccionaris alhora
for (temp, t_value), (qual, q_value) in zip(temperaments.items(), qualities.items()):
    print(f"{temp:<12} {t_value:<6}    {qual:<8} {q_value:<6}")

# Print temperament scores



