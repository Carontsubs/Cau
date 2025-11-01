from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const, object, props
import flatlib.aspects as aspects
from flatlib.dignities import essential
import pytz
import datetime

# Obtenir l'objecte pytz per Barcelona
barcelona_tz = pytz.timezone('Europe/Madrid')

# Obtenir la data i hora actual a Barcelona (amb el fus horari correcte)
local_time = datetime.datetime.now(barcelona_tz)

# Ajustar l'offset de fus horari a format '+01:00'
offset = local_time.strftime('%z')
formatted_offset = f"{offset[:3]}:{offset[3:]}"  # Convertir de +0100 a +01:00

# Convertir la data i hora a format que espera flatlib
# data_i_hora = Datetime(local_time.strftime('%Y/%m/%d'), local_time.strftime('%H:%M'), formatted_offset)
# data_i_hora = Datetime('1979/10/08', '15:00', '+02:00')
# data_i_hora = Datetime('1978/09/29', '13:30', '+02:00')
# data_i_hora = Datetime('2008/11/16', '13:30', '+01:00')
data_i_hora = Datetime('2011/12/06', '15:30', '+01:00')

# Creació de la carta astral
lloc = GeoPos('41n23', '2e10')
carta_astral = Chart(data_i_hora, lloc, IDs=const.LIST_SEVEN_PLANETS, hsys=const.HOUSES_PLACIDUS)
print(data_i_hora, lloc)
print()

# # Llistar tots els angles (AC,DC)
# for angle in carta_astral.angles:
#     print(f'{angle.id} en el signe {angle.sign}')

# Obtenir la fase de la Lluna
print()
fase_lluna = carta_astral.getMoonPhase()
print(f'Fase de la Lluna: {fase_lluna}')
print()
print(f"Ascendent és {carta_astral.get(const.ASC).sign}")

astres = []
# Llistar tots els objectes
for obj in carta_astral.objects:
    # Obtenir la casa on està cada planeta
    casa = carta_astral.houses.getObjectHouse(obj)
    astres.append((obj.id, obj.sign, round(obj.signlon), casa.id, object.Object.movement(obj), "; ".join(essential.EssentialInfo(obj).getDignities())))
#     print(f'{obj.id} en el signe de {obj.sign} ({round(obj.signlon, 2)}º). Casa {casa.id}')


# objectes = list(carta_astral.objects.content.values())

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
                if aspecte.type != -1 and separacio <= 4:
                    # Imprimir aspecte amb el nom i els graus exactes de separació
                    # print(f"{obj1.id} i {obj2.id} tenen un {aspecte_nom} a {separacio:.2f}º")     
                    aspectes.append((obj1.id, obj2.id, props.aspect.name[aspecte.type], round(separacio, 1)))
                    




print(f"{'Planet':<10}{'Sign':<10}{'°':<5}{'House':<10}{'Movement':<15}{'Dignities'}")
print("-" * 60)

# Formatació de cada línia
for planeta, signe, grau, casa, moviment, dignitat in astres:
    print(f"{planeta:<10}{signe:<10}{grau:<5}{casa:<10}{moviment:<15}{dignitat}")
print()
# print(aspectes)
print(f"{'Planet':<10}{'Planet':<10}{'Aspecte':<15}{'°':<5}")
print("-" * 50)
for planeta1, planeta2, aspecte, grau in aspectes:
    print(f"{planeta1:<10}{planeta2:<10}{aspecte:<15}{grau:<5}")
