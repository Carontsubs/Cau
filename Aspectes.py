from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import flatlib.aspects as aspects
import flatlib.const as const
import datetime
import pytz


# Definir data i posició (Barcelona, Espanya)
# date = Datetime('2025/02/01', '12:00', '+02:00')
pos = GeoPos('41n23', '2e11')

# Obtenir l'objecte pytz per Barcelona
barcelona_tz = pytz.timezone('Europe/Madrid')

# Obtenir la data i hora actual a Barcelona (amb el fus horari correcte)
local_time = datetime.datetime.now(barcelona_tz)

# Ajustar l'offset de fus horari a format '+01:00'
offset = local_time.strftime('%z')
formatted_offset = f"{offset[:3]}:{offset[3:]}"  # Convertir de +0100 a +01:00

# Convertir la data i hora a format que espera flatlib
flatlib_datetime = Datetime(local_time.strftime('%Y/%m/%d'), local_time.strftime('%H:%M'), formatted_offset)
print(flatlib_datetime)

# # Crear la carta astral
# chart = Chart(date, pos)
# Crear la carta astral
chart = Chart(flatlib_datetime, pos, IDs=const.LIST_OBJECTS)

# Obtenir objectes disponibles
objectes = list(chart.objects.content.values())

# Mapeig dels aspectes numèrics a noms
aspecte_noms = {
    const.CONJUNCTION: 'Conjunció',
    const.SEXTILE: 'Sextil',
    const.SQUARE: 'Quadrat',
    const.TRINE: 'Trígon',
    const.OPPOSITION: 'Oposició',
    const.SEMISQUARE: 'Semiquadratura',
    const.SEMISEXTILE: 'Semisextil',
    const.SESQUISQUARE: 'Sesquiquadratura',
    const.QUINCUNX: 'Quincunx',
    const.QUINTILE: 'Quintil',
    const.SEMIQUINTILE: 'Semiquintil',
    const.SESQUIQUINTILE: 'Sesquiquintil',
    const.BIQUINTILE: 'Biquintil',
}

# Buscar aspectes entre planetes
for obj1 in objectes:
    for obj2 in objectes:
        if obj1.id != obj2.id:  # Evitem comparar un planeta amb si mateix
            aspecte = aspects.getAspect(obj1, obj2, const.ALL_ASPECTS)
            
            # Mostrar aspectes principals
            if aspecte:
                # Obtenim el nom de l'aspecte basat en la seva id
                aspecte_nom = aspecte_noms.get(aspecte.type, "Desconegut")
                if aspecte.type != - 1:
                    print(f"{obj1.id} té un {aspecte_nom} {aspecte.type} amb {obj2.id}")
               