from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const, object, props
import flatlib.aspects as aspects
import pytz
import datetime
from flatlib.dignities import essential
import locale 

# Configuració de la localització a català
locale.setlocale(locale.LC_TIME, 'ca_ES.UTF-8')


# --- Funcions auxiliars (Retornen només la seva línia/bloc de text) ---

def fase_lluna(carta: Chart) -> str:
    # Obtenir la fase de la Lluna
    fase_lluna = carta.getMoonPhase()
    return f'Fase de la Lluna: {fase_lluna}'

def variacio_latitud(astre: object.Object, astre_a: object.Object) -> str:
    if abs(astre_a.lat - astre.lat) < 0.001:
        return f"No hi ha canvi a {astre.id}."
    elif astre_a.lat < astre.lat:
        return f"La {astre.id} creix de {round(astre_a.lat, 2)}° a {round(astre.lat, 2)}° ({round((astre.lat-astre_a.lat), 7)}°)"
    elif astre_a.lat > astre.lat:
        return f"{astre.id} decreix de {round(astre_a.lat, 2)}° a {round(astre.lat, 2)}° ({round((astre.lat-astre_a.lat), 7)}°)"
    else:
        return f"No hi ha canvi en la latitud: {astre.lat}°."

def info_astres(carta: Chart) -> str:
    """Recull tota la informació dels astres en una llista i la retorna unida."""
    output = []
    for obj in carta.objects:
        line = f'{obj.id} en el signe de {obj.sign} ({round(obj.signlon)}°) {object.Object.movement(obj)} '
        line += ', '.join(essential.EssentialInfo(obj).getDignities())
        output.append(line)
    return '\n'.join(output)

def aspectes_astre(carta: Chart) -> str:
    """Recull tots els aspectes tancats en una llista i la retorna unida."""
    output = ['Aspectes:']
    for obj1 in carta.objects:
        for obj2 in carta.objects:
            if obj1.id != obj2.id:
                
                lon_obj1 = obj1.signlon
                lon_obj2 = obj2.signlon
                
                separacio = abs(lon_obj1 - lon_obj2)
                if separacio > 180:
                    separacio = 360 - separacio
                    
                aspecte = aspects.getAspect(obj1, obj2, const.MAJOR_ASPECTS)
                
                if aspecte and aspecte.type != -1:
                    if separacio <= 4:
                        output.append(f"{obj1.id} i {obj2.id} tenen un {props.aspect.name[aspecte.type]} de {separacio:.1f}°")

    return '\n'.join(output)


# --- Funció Principal (Retorna la informació agregada com a STRING) ---

def obtenir_info_astral_actual(
    latitud: str = '41n28', 
    longitud: str = '2e18',
    tz_name: str = 'Europe/Madrid',
    planetes: list = const.LIST_SEVEN_PLANETS,
    periode: str = 'actual' # Pot ser 'actual', 'ahir' (a), o 'setmana' (a7)
) -> str: # <--- El tipus de retorn ara és 'str'
    
    # 1. CÀLCUL DE DATES I POSICIÓ
    barcelona_tz = pytz.timezone(tz_name)
    local_time = datetime.datetime.now(barcelona_tz)
    local_time_a = local_time + datetime.timedelta(days=1)
    local_time_a7 = local_time + datetime.timedelta(days=7)

    offset = local_time.strftime('%z')
    formatted_offset = f"{offset[:3]}:{offset[3:]}"

    data_i_hora = Datetime(local_time.strftime('%Y/%m/%d'), local_time.strftime('%H:%M'), formatted_offset)
    data_i_hora_a = Datetime(local_time_a.strftime('%Y/%m/%d'), local_time_a.strftime('%H:%M'), formatted_offset)
    data_i_hora_a7 = Datetime(local_time_a7.strftime('%Y/%m/%d'), local_time_a7.strftime('%H:%M'), formatted_offset)

    lloc = GeoPos(latitud, longitud) 

    # 2. CREACIÓ DE CARTES ASTRALS
    carta_astral = Chart(data_i_hora, lloc, IDs=planetes)
    carta_astral_a = Chart(data_i_hora_a, lloc, IDs=planetes)
    carta_astral_a7 = Chart(data_i_hora_a7, lloc, IDs=planetes)

    lluna = carta_astral.getObject(const.MOON)
    lluna_a = carta_astral_a.getObject(const.MOON)
    lluna_a7 = carta_astral_a7.getObject(const.MOON)
    sol = carta_astral.getObject(const.SUN)
    sol_a = carta_astral_a.getObject(const.SUN)
    sol_a7 = carta_astral_a7.getObject(const.SUN)

    # 🌟 NOU BLOC DE SELECCIÓ DE CARTA BASE
    if periode == 'diari':
        carta_base = carta_astral_a
        data_base = data_i_hora_a
        lluna_base = lluna_a
        sol_base = sol_a
    elif periode == 'setmanal':
        carta_base = carta_astral_a7
        data_base = data_i_hora_a7
        lluna_base = lluna_a7
        sol_base = sol_a7
    else: # Per defecte o 'actual'
        carta_base = carta_astral
        data_base = data_i_hora
        lluna_base = lluna
        sol_base = sol


    # 3. CONSTRUCCIÓ DE LA CADENA DE TEXT FINAL
    
    # Utilitzem una llista per construir el prompt amb salts de línia
    prompt_lines = []
    
    # Capçalera (la línia del vostre original)
    prompt_lines.append(f'{data_base} {lloc}\n')

    # Afegeix els resultats de les funcions auxiliars
    prompt_lines.append(fase_lluna(carta_base))
    prompt_lines.append('') # Salt de línia
    
    prompt_lines.append(variacio_latitud(lluna,lluna_a))
    prompt_lines.append('')
    prompt_lines.append(variacio_latitud(sol,sol_a7))
    prompt_lines.append('')

    prompt_lines.append(info_astres(carta_base))
    prompt_lines.append('')

    prompt_lines.append(aspectes_astre(carta_base))
    
    # RETORNA TOTA LA INFORMACIÓ COM UNA ÚNICA CADENA
    return '\n'.join(prompt_lines)

# --- Execució per PROVAR el retorn ---

# L'execució ja no imprimeix res fins que no ho demanem explícitament:
info_per_prompt = obtenir_info_astral_actual()

# Ara la variable 'info_per_prompt' conté tot el text preparat:
# print(info_per_prompt) # Imprimiria tot el bloc de text

# Finalment, si crides la funció, obtindràs la cadena:
# print(obtenir_info_astral_actual())
# print(obtenir_info_astral_actual(periode='diari'))