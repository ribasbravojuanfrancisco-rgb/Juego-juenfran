# TANKFRAN'S WAR
# Juego de tanques por turnos con modo individual y multijugador local.
# Las secciones están separadas para facilitar la lectura y las modificaciones.

import math
import random
import pygame
import os

pygame.init()

ANCHO, ALTO = 1000, 600
PANTALLA = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("TANKFRAN'S WAR")
RELOJ = pygame.time.Clock()
FPS = 60
MAPA_ANCHO, MAPA_ALTO = 2400, 1400
MUNDO = pygame.Surface((MAPA_ANCHO, MAPA_ALTO))

CARPETA_IMAGENES = r"C:\Users\PC\Frantanks1.py\imagenes"

RUTA_FONDO = os.path.join(CARPETA_IMAGENES, "Fondofrantanks.png")
RUTA_TANQUE_FRAN = os.path.join(CARPETA_IMAGENES, "Tanque_Fran.png")
RUTA_TANQUE_ENEMIGO = os.path.join(CARPETA_IMAGENES, "Tanque_enemigo.png")

# Cargamos los sprites con transparencia.
TANQUE_FRAN_IMAGEN = pygame.image.load(RUTA_TANQUE_FRAN).convert_alpha()
TANQUE_ENEMIGO_IMAGEN = pygame.image.load(RUTA_TANQUE_ENEMIGO).convert_alpha()

# Tamaño máximo de los tanques en el mundo del juego.
# Se aumenta bastante el tamaño y se conserva la proporción original.
TANQUE_IMAGEN_ANCHO = 255
TANQUE_IMAGEN_ALTO = 180


def escalar_tanque(imagen):
    ancho_original, alto_original = imagen.get_size()
    escala = min(
        TANQUE_IMAGEN_ANCHO / ancho_original,
        TANQUE_IMAGEN_ALTO / alto_original
    )
    nuevo_tamano = (
        max(1, int(ancho_original * escala)),
        max(1, int(alto_original * escala))
    )
    # Escalado por vecino más cercano: conserva nítidos los píxeles del sprite.
    return pygame.transform.scale(imagen, nuevo_tamano)


TANQUE_FRAN_IMAGEN = escalar_tanque(TANQUE_FRAN_IMAGEN)
TANQUE_ENEMIGO_IMAGEN = escalar_tanque(TANQUE_ENEMIGO_IMAGEN)

# El enemigo está a la derecha: lo volteamos horizontalmente para que mire
# hacia la izquierda, en dirección al tanque de Fran.
TANQUE_ENEMIGO_IMAGEN = pygame.transform.flip(
    TANQUE_ENEMIGO_IMAGEN, True, False
)

FONDO_BATALLA = pygame.image.load(RUTA_FONDO).convert()
FONDO_BATALLA = pygame.transform.scale(
    FONDO_BATALLA,
    (MAPA_ANCHO, MAPA_ALTO)
)
ZOOM_COMBATE = 1.5
vista_general = False
vista_proyectil = False  # Cámara centrada en la bala principal y sus fragmentos
camara_x = camara_y = 0.0
zoom_actual = ZOOM_COMBATE
desfase_general_x = desfase_general_y = 0.0
BLANCO = (255, 255, 255)
NEGRO = (20, 20, 24)
VERDE = (50, 180, 50)
ROJO = (220, 50, 50)
GRIS = (100, 100, 100)
CIELO = (30, 30, 40)
TIERRA = (105, 75, 48)
TIERRA_CLARA = (135, 100, 62)
AMARILLO = (240, 205, 70)

#=========================
# TERRENO Y POSICIONES INICIALES
#=========================


# Las deformaciones y las zonas de fuego viven en coordenadas del mundo.
crateres = []
zonas_fuego = []
DURACION_ZONA_FUEGO = 6 * FPS
RADIO_ZONA_FUEGO = 105


def altura_terreno(x):
    """Altura del terreno, incluyendo los cráteres creados por ataques especiales."""
    base = (
        1000
        + 42 * math.sin(x / 180)
        + 20 * math.sin(x / 67)
        + 12 * math.sin(x / 39)
    )
    deformacion = 0.0
    for crater in crateres:
        distancia = abs(x - crater['x'])
        radio = crater['radio']
        if distancia < radio:
            # Cuenco suave: el suelo queda más bajo en el centro del impacto.
            proporcion = 1.0 - (distancia / radio) ** 2
            deformacion += crater['profundidad'] * proporcion
    return min(MAPA_ALTO - 8, base + deformacion)


def crear_crater(x, radio, profundidad):
    """Añade un cráter al terreno y vuelve a apoyar los tanques sobre la superficie."""
    global tanque_y, enemigo_y
    x = max(0.0, min(float(MAPA_ANCHO), float(x)))
    crateres.append({'x': x, 'radio': float(radio), 'profundidad': float(profundidad)})
    # Evita que la lista crezca indefinidamente en partidas largas.
    if len(crateres) > 80:
        crateres.pop(0)
    tanque_y = altura_terreno(tanque_x)
    enemigo_y = altura_terreno(enemigo_x)


def crear_zona_fuego(x, radio=RADIO_ZONA_FUEGO, duracion=DURACION_ZONA_FUEGO):
    """Crea una franja de fuego temporal sobre la superficie del terreno."""
    x = max(0.0, min(float(MAPA_ANCHO), float(x)))
    zonas_fuego.append({
        'x': x,
        'radio': float(radio),
        'frames': int(duracion),
        'tanque_dentro': False,
        'enemigo_dentro': False,
    })
    if len(zonas_fuego) > 30:
        zonas_fuego.pop(0)


def actualizar_zonas_fuego():
    """Mantiene las zonas activas y aplica quemadura al entrar en ellas."""
    global quemadura_tanque, quemadura_enemigo
    activas = []
    for zona in zonas_fuego:
        zona['frames'] -= 1
        if zona['frames'] <= 0:
            continue
        entra_tanque = abs(tanque_x - zona['x']) <= zona['radio'] + TANQUE_ANCHO / 2
        entra_enemigo = abs(enemigo_x - zona['x']) <= zona['radio'] + TANQUE_ANCHO / 2
        if entra_tanque and not zona['tanque_dentro'] and vida_tanque > 0:
            quemadura_tanque = max(quemadura_tanque, 2)
        if entra_enemigo and not zona['enemigo_dentro'] and vida_enemigo > 0:
            quemadura_enemigo = max(quemadura_enemigo, 2)
        zona['tanque_dentro'] = entra_tanque
        zona['enemigo_dentro'] = entra_enemigo
        activas.append(zona)
    zonas_fuego[:] = activas
TANQUE_ANCHO, TANQUE_ALTO = 60, 30
CAÑON_LARGO = 60
tanque_x = 300.0
tanque_y = altura_terreno(tanque_x)
enemigo_x = 2100.0
enemigo_y = altura_terreno(enemigo_x)
MOVIMIENTO_POR_TURNO = 300.0
VELOCIDAD_MOVIMIENTO = 3.0
movimiento_restante = MOVIMIENTO_POR_TURNO
turno_actual = 'JUGADOR'
estado_partida = 'MENU'
modo_juego = 'SINGLEPLAYER'
dificultad_ia = 'MEDIA'
AJUSTES_IA = {
    "FACIL": {
        "desviacion": 650,
        "precision": 0.05,
    },
    "MEDIA": {
        "desviacion": 420,
        "precision": 0.25,
    },
    "DIFICIL": {
        "desviacion": 190,
        "precision": 0.65,
    },
    "IMPOSIBLE": {
        "desviacion": 45,
        "precision": 0.90,
    },
}
angulo = math.radians(35)
angulo_ia = math.radians(145)
angulo_fijado = False
proyectil_activo = False
proyectil_de = None
proyectil_x = proyectil_y = 0.0
velocidad_x = velocidad_y = 0.0
RADIO_PROYECTIL = 7
GRAVEDAD = 0.14
potencia = 0.0
POTENCIA_MAXIMA = 20.0
tiempo_potencia = 0.0
cargando = False
VIDA_MAXIMA = 100
vida_tanque = vida_enemigo = VIDA_MAXIMA
MULTIPLICADOR_DAÑO = 2

# La ultimate se desbloquea al causar daño al rival en dos turnos distintos.
turnos_con_dano = {'JUGADOR': 0, 'JUGADOR2': 0}
dano_en_turno = {'JUGADOR': False, 'JUGADOR2': False}
ultimate_desbloqueada = {'JUGADOR': False, 'JUGADOR2': False}


def registrar_dano_jugador(propietario):
    """Marca que este jugador ha dañado al rival durante su turno actual."""
    if propietario in dano_en_turno:
        dano_en_turno[propietario] = True

# Selector y estados de los ataques especiales.
ataque_seleccionado = 1
TIPOS_ATAQUE = {
    1: "BASICO",
    2: "MULTIPROYECTIL",
    3: "ULTIMATE",
    4: "GRANADA",
    5: "INCENDIARIA",
}
tipo_proyectil = "BASICO"
fragmentos = []
multiproyectil_dividido = False
ultimate_contador = 0
ultimate_frames = 0
ultimate_activa = False
ultimate_pendientes = []  # Proyectiles ultimate aún no lanzados
ultimate_lanzamiento_timer = 0
ultimate_dano_restante = VIDA_MAXIMA // 3  # Daño máximo total de una salva ultimate
ULTIMATE_MAX_BALAS = 20
ULTIMATE_INTERVALO_SALIDA = 2  # Una bala nueva cada dos fotogramas
granada_rebotando = False
granada_frames = 0
granada_exploto = False
quemadura_tanque = 0
quemadura_enemigo = 0
DANO_QUEMADURA = 6

#=========================
# CÁMARA Y COORDENADAS
#=========================


def actualizar_camara():
    global camara_x, camara_y, zoom_actual
    global desfase_general_x, desfase_general_y
    if vista_general:
        zoom_actual = min(ANCHO / MAPA_ANCHO, ALTO / MAPA_ALTO)
        desfase_general_x = (ANCHO - MAPA_ANCHO * zoom_actual) / 2
        desfase_general_y = (ALTO - MAPA_ALTO * zoom_actual) / 2
        camara_x = camara_y = 0
        return

    desfase_general_x = desfase_general_y = 0
    if vista_proyectil and proyectil_activo:
        puntos = [(proyectil_x, proyectil_y)]
        puntos.extend((b["x"], b["y"]) for b in fragmentos)
        min_x = min(p[0] for p in puntos)
        max_x = max(p[0] for p in puntos)
        min_y = min(p[1] for p in puntos)
        max_y = max(p[1] for p in puntos)
        margen = 120
        ancho_necesario = max(ANCHO / 2.2, max_x - min_x + margen * 2)
        alto_necesario = max(ALTO / 2.0, max_y - min_y + margen * 2)
        zoom_actual = max(0.35, min(2.0, min(ANCHO / ancho_necesario, ALTO / alto_necesario)))
        ancho_vista, alto_vista = ANCHO / zoom_actual, ALTO / zoom_actual
        camara_x = (min_x + max_x) / 2 - ancho_vista / 2
        camara_y = (min_y + max_y) / 2 - alto_vista / 2
    else:
        zoom_actual = ZOOM_COMBATE
        ancho_vista, alto_vista = ANCHO / zoom_actual, ALTO / zoom_actual
        if turno_actual in ("JUGADOR2", "IA"):
            objetivo_camara_x, objetivo_camara_y = enemigo_x, enemigo_y
        else:
            objetivo_camara_x, objetivo_camara_y = tanque_x, tanque_y
        camara_x = objetivo_camara_x - ancho_vista * 0.32
        camara_y = objetivo_camara_y - alto_vista * 0.68
        # Al acercarse a 100 px del borde superior visible, seguimos el proyectil.
        if proyectil_activo:
            proyectil_pantalla_y = (proyectil_y - camara_y) * zoom_actual
            if proyectil_pantalla_y < 100:
                camara_y = proyectil_y - 100 / zoom_actual

    ancho_vista, alto_vista = ANCHO / zoom_actual, ALTO / zoom_actual
    camara_x = max(0, min(camara_x, max(0, MAPA_ANCHO - ancho_vista)))
    camara_y = max(0, min(camara_y, max(0, MAPA_ALTO - alto_vista)))


def pantalla_a_mundo(px, py):
    if vista_general:
        return (
            (px - desfase_general_x) / zoom_actual,
            (py - desfase_general_y) / zoom_actual,
        )
    return (
        camara_x + px / zoom_actual,
        camara_y + py / zoom_actual,
    )

#=========================
# APUNTADO Y MOVIMIENTO
#=========================


def actualizar_angulo():
    global angulo, angulo_ia
    if (
        turno_actual not in ('JUGADOR', 'JUGADOR2')
        or estado_partida != 'EN_CURSO'
    ):
        return
    if angulo_fijado or proyectil_activo or cargando:
        return
    px, py = pygame.mouse.get_pos()
    mx, my = pantalla_a_mundo(px, py)
    if turno_actual == 'JUGADOR':
        ox, oy = obtener_origen_canon(tanque_x, tanque_y, TANQUE_FRAN_IMAGEN)
        angulo = math.atan2(oy - my, mx - ox)
    else:
        ox, oy = obtener_origen_canon(enemigo_x, enemigo_y, TANQUE_ENEMIGO_IMAGEN)
        angulo_ia = math.atan2(oy - my, mx - ox)


def mover_jugador(teclas):
    global tanque_x, tanque_y, enemigo_x, enemigo_y, movimiento_restante
    if (
        turno_actual not in ('JUGADOR', 'JUGADOR2')
        or estado_partida != 'EN_CURSO'
        or proyectil_activo
        or cargando
        or movimiento_restante <= 0
    ):
        return
    dx = 0.0
    if turno_actual == 'JUGADOR':
        if teclas[pygame.K_a]:
            dx = -VELOCIDAD_MOVIMIENTO
        elif teclas[pygame.K_d]:
            dx = VELOCIDAD_MOVIMIENTO
        actual = tanque_x
    else:
        if teclas[pygame.K_LEFT]:
            dx = -VELOCIDAD_MOVIMIENTO
        elif teclas[pygame.K_RIGHT]:
            dx = VELOCIDAD_MOVIMIENTO
        actual = enemigo_x
    dx = max(-movimiento_restante, min(dx, movimiento_restante))
    nx = max(TANQUE_ANCHO / 2, min(actual + dx, MAPA_ANCHO - TANQUE_ANCHO / 2))
    movimiento_restante = max(0.0, movimiento_restante - abs(nx - actual))
    if turno_actual == 'JUGADOR':
        tanque_x, tanque_y = (nx, altura_terreno(nx))
    else:
        enemigo_x, enemigo_y = (nx, altura_terreno(nx))

#=========================
# DIBUJO DEL TERRENO
#=========================


def dibujar_terreno():
    MUNDO.blit(FONDO_BATALLA, (0, 0))
    puntos = []
    paso = 8
    for x in range(0, MAPA_ANCHO + paso, paso):
        xx = min(x, MAPA_ANCHO)
        puntos.append((xx, int(altura_terreno(xx))))
    pygame.draw.polygon(MUNDO, TIERRA, [(0, MAPA_ALTO)] + puntos + [(MAPA_ANCHO, MAPA_ALTO)])
    pygame.draw.lines(MUNDO, TIERRA_CLARA, False, puntos, 4)
    # Las llamas se dibujan pegadas a la superficie; el suelo sigue siendo sólido.
    for zona in zonas_fuego:
        inicio = max(0, int(zona['x'] - zona['radio']))
        fin = min(MAPA_ANCHO, int(zona['x'] + zona['radio']))
        for fx in range(inicio, fin + 1, 14):
            fy = int(altura_terreno(fx))
            altura_llama = 8 + ((fx // 14) % 3) * 4
            color_llama = (255, 105, 20) if (fx // 14) % 2 else (255, 190, 35)
            pygame.draw.polygon(MUNDO, color_llama, [
                (fx - 5, fy + 2), (fx, fy - altura_llama), (fx + 5, fy + 2)
            ])

#=========================
# TANQUES Y BARRAS DE VIDA
#=========================


def obtener_rect_tanque(x, y, imagen):
    """Coloca la parte visible inferior del tanque justo sobre el terreno.

    Algunos PNG tienen píxeles transparentes alrededor del dibujo. Alinear
    el rectángulo completo puede dejar el tanque flotando o enterrado; por
    eso usamos los límites de los píxeles realmente visibles.
    """
    limites_visibles = imagen.get_bounding_rect(min_alpha=1)
    if limites_visibles.width == 0 or limites_visibles.height == 0:
        return imagen.get_rect(midbottom=(int(x), int(y)))

    izquierda = int(x - imagen.get_width() / 2)
    arriba = int(y - limites_visibles.bottom)
    return pygame.Rect(izquierda, arriba, imagen.get_width(), imagen.get_height())


def obtener_hitbox_tanque(x, y, imagen, es_enemigo=False):
    """Hitbox basada en el cuerpo visible del sprite, no en el tamaño antiguo 60x30."""
    rect_sprite = obtener_rect_tanque(x, y, imagen)
    visible = imagen.get_bounding_rect(min_alpha=1)
    hitbox = pygame.Rect(
        rect_sprite.left + visible.left,
        rect_sprite.top + visible.top,
        visible.width,
        visible.height
    )

    # Se reduce un poco el contorno para no contar el cañón ni píxeles sueltos
    # como parte del cuerpo del tanque.
    margen_x = max(2, int(hitbox.width * 0.07))
    margen_superior = int(hitbox.height * 0.22)
    margen_inferior = max(1, int(hitbox.height * 0.04))
    hitbox.left += margen_x
    hitbox.width = max(1, hitbox.width - 2 * margen_x)
    hitbox.top += margen_superior
    hitbox.height = max(1, hitbox.height - margen_superior - margen_inferior)

    # El sprite enemigo se dibuja 2 px más abajo para que las orugas toquen suelo.
    if es_enemigo:
        hitbox.y += 2
    return hitbox


def proyectil_intersecta_hitbox(px, py, x, y, imagen, es_enemigo=False):
    hitbox = obtener_hitbox_tanque(x, y, imagen, es_enemigo)
    punto_cercano_x = max(hitbox.left, min(px, hitbox.right))
    punto_cercano_y = max(hitbox.top, min(py, hitbox.bottom))
    return math.hypot(px - punto_cercano_x, py - punto_cercano_y) <= RADIO_PROYECTIL


def obtener_origen_canon(x, y, imagen):
    """Coloca el origen del cañón en la zona visible de la torreta."""
    rect = obtener_rect_tanque(x, y, imagen)
    limites_visibles = imagen.get_bounding_rect(min_alpha=1)
    centro_torreta_y = (
        rect.top + limites_visibles.top + limites_visibles.height * 0.43
    )
    return (float(x), float(centro_torreta_y))


def dibujar_barra_vida(x, y, vida, ancho=110):
    alto = 11
    vida = max(0, min(vida, VIDA_MAXIMA))
    fondo = pygame.Rect(int(x - ancho / 2), int(y), ancho, alto)
    pygame.draw.rect(MUNDO, NEGRO, fondo.inflate(4, 4), border_radius=3)
    pygame.draw.rect(MUNDO, GRIS, fondo, border_radius=2)
    relleno = fondo.copy()
    relleno.width = int(ancho * vida / VIDA_MAXIMA)
    if relleno.width > 0:
        pygame.draw.rect(MUNDO, ROJO, relleno, border_radius=2)


def dibujar_tanque():
    rect_tanque = obtener_rect_tanque(tanque_x, tanque_y, TANQUE_FRAN_IMAGEN)
    MUNDO.blit(TANQUE_FRAN_IMAGEN, rect_tanque)
    limites_visibles = TANQUE_FRAN_IMAGEN.get_bounding_rect(min_alpha=1)
    parte_superior_visible = rect_tanque.top + limites_visibles.top
    dibujar_barra_vida(tanque_x, parte_superior_visible - 25, vida_tanque)


def dibujar_enemigo():
    if vida_enemigo <= 0:
        return
    rect_enemigo = obtener_rect_tanque(enemigo_x, enemigo_y, TANQUE_ENEMIGO_IMAGEN)
    # Pequeño ajuste visual para apoyar las orugas sobre el terreno.
    rect_enemigo.y += 2
    MUNDO.blit(TANQUE_ENEMIGO_IMAGEN, rect_enemigo)
    limites_visibles = TANQUE_ENEMIGO_IMAGEN.get_bounding_rect(min_alpha=1)
    parte_superior_visible = rect_enemigo.top + limites_visibles.top
    dibujar_barra_vida(enemigo_x, parte_superior_visible - 25, vida_enemigo)

#=========================
# CAÑONES Y APUNTADO VISUAL
#=========================


def obtener_punta_canon(x, y, ang):
    imagen = TANQUE_FRAN_IMAGEN if abs(x - tanque_x) <= abs(x - enemigo_x) else TANQUE_ENEMIGO_IMAGEN
    ox, oy = obtener_origen_canon(x, y, imagen)
    return (ox, oy, ox + math.cos(ang) * CAÑON_LARGO, oy - math.sin(ang) * CAÑON_LARGO)


def dibujar_canon(x, y, ang):
    ox, oy, px, py = obtener_punta_canon(x, y, ang)
    pygame.draw.line(MUNDO, NEGRO, (int(ox), int(oy)), (int(px), int(py)), 9)
    pygame.draw.circle(MUNDO, NEGRO, (int(ox), int(oy)), 6)


def dibujar_angulo():
    ox, oy = obtener_origen_canon(tanque_x, tanque_y, TANQUE_FRAN_IMAGEN)
    for i in range(1, 9):
        px = ox + math.cos(angulo) * 22 * i
        py = oy - math.sin(angulo) * 22 * i
        pygame.draw.circle(MUNDO, BLANCO, (int(px), int(py)), 3)

#=========================
# POTENCIA Y HUD
#=========================


def actualizar_potencia():
    global potencia, tiempo_potencia
    if cargando:
        tiempo_potencia += 0.05
        potencia = (math.sin(tiempo_potencia) + 1) / 2 * POTENCIA_MAXIMA


def dibujar_hud():
    fuente = pygame.font.SysFont(None, 24)
    pequena = pygame.font.SysFont(None, 20)
    if estado_partida == 'VICTORIA':
        estado = '¡VICTORIA! Has destruido al enemigo.'
    elif estado_partida == 'DERROTA':
        estado = 'DERROTA: tu tanque ha sido destruido.'
    elif turno_actual == 'JUGADOR':
        estado = f'JUGADOR 1 | Movimiento: {movimiento_restante:.0f} px'
    elif turno_actual == 'JUGADOR2':
        estado = f'JUGADOR 2 | Movimiento: {movimiento_restante:.0f} px'
    else:
        estado = f'Turno de la IA ({dificultad_ia.lower()})...'
    PANTALLA.blit(fuente.render(estado, True, BLANCO), (20, 12))
    x, y, ancho, alto = (ANCHO // 2 - 150, 43, 300, 18)
    pygame.draw.rect(PANTALLA, GRIS, (x, y, ancho, alto))
    pygame.draw.rect(PANTALLA, ROJO, (x, y, int(ancho * potencia / POTENCIA_MAXIMA), alto))
    nombres = {
        1: "1 Básico",
        2: "2 Multiproyectil",
        3: "3 Ultimate",
        4: "4 Granada",
        5: "5 Incendiaria",
    }
    selector = f"Ataque: {nombres[ataque_seleccionado]} | Teclas 1-5 para cambiar"
    PANTALLA.blit(pequena.render(selector, True, AMARILLO), (20, 68))
    if quemadura_tanque > 0 or quemadura_enemigo > 0:
        estado_fuego = f"Quemadura: jugador {quemadura_tanque} turnos | rival {quemadura_enemigo} turnos"
        PANTALLA.blit(pequena.render(estado_fuego, True, (255, 110, 35)), (20, 92))
    ayuda = 'P1: A/D | P2: flechas | Clic mantenido/suelto: disparar | TAB: vista general | C: cámara bala | ESPACIO: ataques especiales'
    PANTALLA.blit(pequena.render(ayuda, True, BLANCO), (20, ALTO - 25))
    if tipo_proyectil == "ULTIMATE" and ultimate_activa:
        if ultimate_frames <= 0:
            aviso = "¡ULTIMATE EN EL AIRE! Pulsa ESPACIO para iniciar los 3 segundos"
        else:
            aviso = f"¡METRALLA! ESPACIO añade balas ({ultimate_contador}/{ULTIMATE_MAX_BALAS}) | Sale en {ultimate_frames / FPS:.1f}s"
        PANTALLA.blit(fuente.render(aviso, True, AMARILLO), (ANCHO // 2 - 220, 90))
    elif tipo_proyectil == "GRANADA" and granada_rebotando:
        aviso = f"Granada: explosión en {granada_frames / FPS:.1f}s"
        PANTALLA.blit(fuente.render(aviso, True, AMARILLO), (ANCHO // 2 - 100, 90))

#=========================
# MENÚ INICIAL
#=========================


def dibujar_menu():
    PANTALLA.fill((18, 22, 30))
    titulo = pygame.font.SysFont(None, 58, bold=True)
    fuente = pygame.font.SysFont(None, 30)
    pequena = pygame.font.SysFont(None, 22)
    PANTALLA.blit(titulo.render("TANKFRAN'S WAR", True, AMARILLO), (ANCHO // 2 - 220, 65))
    PANTALLA.blit(fuente.render('Elige modo de juego', True, BLANCO), (ANCHO // 2 - 130, 145))
    for rect, texto, color in [
        (pygame.Rect(300, 195, 400, 55), 'SINGLEPLAYER', VERDE),
        (pygame.Rect(300, 260, 400, 55), 'MULTIPLAYER LOCAL', ROJO),
    ]:
        pygame.draw.rect(PANTALLA, color, rect, border_radius=8)
        t = fuente.render(texto, True, BLANCO)
        PANTALLA.blit(t, (rect.centerx - t.get_width() // 2, rect.y + 15))
    PANTALLA.blit(fuente.render('Dificultad de la IA', True, BLANCO), (ANCHO // 2 - 105, 340))
    for texto, x in [('FACIL', 190), ('MEDIA', 350), ('DIFICIL', 510), ('IMPOSIBLE', 670)]:
        rect = pygame.Rect(x, 390, 140, 48)
        seleccionado = dificultad_ia == texto
        pygame.draw.rect(PANTALLA, AMARILLO if seleccionado else GRIS, rect, border_radius=6)
        t = pequena.render(texto, True, NEGRO if seleccionado else BLANCO)
        PANTALLA.blit(t, (rect.centerx - t.get_width() // 2, rect.y + 14))
    PANTALLA.blit(pequena.render('Multiplayer: J1 A/D, J2 flechas. Ambos apuntan con el ratón.', True, BLANCO), (175, 485))
    PANTALLA.blit(pequena.render('Pulsa un modo para empezar.', True, BLANCO), (ANCHO // 2 - 115, 530))

#=========================
# DAÑO Y COLISIONES
#=========================


def calcular_dano():
    rapidez = math.sqrt(velocidad_x ** 2 + velocidad_y ** 2)
    return max(1, int(rapidez * MULTIPLICADOR_DAÑO))


def proyectil_toca_tanque(x, y, es_enemigo=False):
    imagen = TANQUE_ENEMIGO_IMAGEN if es_enemigo else TANQUE_FRAN_IMAGEN
    return proyectil_intersecta_hitbox(
        proyectil_x, proyectil_y, x, y, imagen, es_enemigo
    )


def comprobar_impacto_tanque():
    global vida_enemigo, vida_tanque, quemadura_tanque, quemadura_enemigo
    if proyectil_de == 'JUGADOR' and vida_enemigo > 0 and proyectil_toca_tanque(enemigo_x, enemigo_y, True):
        vida_enemigo = max(0, vida_enemigo - calcular_dano())
        registrar_dano_jugador('JUGADOR')
        if tipo_proyectil == 'INCENDIARIA':
            quemadura_enemigo = max(quemadura_enemigo, 2)
            crear_zona_fuego(enemigo_x)
        return True
    if modo_juego == 'MULTIPLAYER' and proyectil_de == 'JUGADOR2' and (vida_tanque > 0) and proyectil_toca_tanque(tanque_x, tanque_y, False):
        vida_tanque = max(0, vida_tanque - calcular_dano())
        registrar_dano_jugador('JUGADOR2')
        if tipo_proyectil == 'INCENDIARIA':
            quemadura_tanque = max(quemadura_tanque, 2)
            crear_zona_fuego(tanque_x)
        return True
    if modo_juego == 'SINGLEPLAYER' and proyectil_de == 'IA' and (vida_tanque > 0) and proyectil_toca_tanque(tanque_x, tanque_y, False):
        vida_tanque = max(0, vida_tanque - calcular_dano())
        if tipo_proyectil == 'INCENDIARIA':
            quemadura_tanque = max(quemadura_tanque, 2)
            crear_zona_fuego(tanque_x)
        return True
    return False

#=========================
# PROYECTILES Y TURNOS
#=========================


def terminar_proyectil():
    global proyectil_activo, proyectil_de, angulo_fijado, cargando, turno_actual, movimiento_restante, estado_partida
    global fragmentos, tipo_proyectil, multiproyectil_dividido, ultimate_activa
    global quemadura_tanque, quemadura_enemigo
    global ultimate_frames, ultimate_contador, ultimate_pendientes, ultimate_lanzamiento_timer, ultimate_dano_restante
    global granada_rebotando, granada_frames, granada_exploto
    global vida_enemigo, vida_tanque
    propietario = proyectil_de
    if propietario in dano_en_turno and dano_en_turno[propietario]:
        turnos_con_dano[propietario] += 1
        if turnos_con_dano[propietario] >= 2:
            ultimate_desbloqueada[propietario] = True
        dano_en_turno[propietario] = False
    proyectil_activo = False
    proyectil_de = None
    angulo_fijado = cargando = False
    fragmentos = []
    multiproyectil_dividido = False
    ultimate_activa = False
    ultimate_frames = 0
    ultimate_contador = 0
    ultimate_pendientes = []
    ultimate_lanzamiento_timer = 0
    ultimate_dano_restante = VIDA_MAXIMA // 3
    granada_rebotando = False
    granada_frames = 0
    granada_exploto = False
    if vida_enemigo <= 0:
        estado_partida = 'VICTORIA'
    elif vida_tanque <= 0:
        estado_partida = 'DERROTA'
    elif modo_juego == 'MULTIPLAYER':
        turno_actual = 'JUGADOR2' if propietario == 'JUGADOR' else 'JUGADOR'
        movimiento_restante = MOVIMIENTO_POR_TURNO
    elif propietario in ('JUGADOR', 'JUGADOR2'):
        turno_actual = 'IA'
    else:
        turno_actual = 'JUGADOR'
        movimiento_restante = MOVIMIENTO_POR_TURNO

    # El fuego causa daño al comienzo de cada turno del tanque afectado.
    if turno_actual in ('JUGADOR2', 'IA') and quemadura_enemigo > 0:
        vida_enemigo = max(0, vida_enemigo - DANO_QUEMADURA)
        quemadura_enemigo -= 1
    elif turno_actual == 'JUGADOR' and quemadura_tanque > 0:
        vida_tanque = max(0, vida_tanque - DANO_QUEMADURA)
        quemadura_tanque -= 1
    if vida_enemigo <= 0:
        estado_partida = 'VICTORIA'
    elif vida_tanque <= 0:
        estado_partida = 'DERROTA'


def _impacto_rect_tanque(x, y, tanque_centro_x, tanque_base_y):
    """Comprueba el impacto contra la hitbox real del sprite correspondiente."""
    es_enemigo = abs(tanque_centro_x - enemigo_x) <= abs(tanque_centro_x - tanque_x)
    imagen = TANQUE_ENEMIGO_IMAGEN if es_enemigo else TANQUE_FRAN_IMAGEN
    return proyectil_intersecta_hitbox(
        x, y, tanque_centro_x, tanque_base_y, imagen, es_enemigo
    )


def _aplicar_dano_a_objetivo(propietario, x, y, dano, es_ultimate=False):
    """Aplica daño; todas las balas ultimate comparten un límite total de daño."""
    global vida_tanque, vida_enemigo, ultimate_dano_restante
    impacto = False
    if propietario == 'JUGADOR':
        if vida_enemigo > 0 and _impacto_rect_tanque(x, y, enemigo_x, enemigo_y):
            impacto = True
            if es_ultimate:
                dano = min(max(0, int(dano)), ultimate_dano_restante)
            if dano > 0:
                vida_enemigo = max(0, vida_enemigo - dano)
                registrar_dano_jugador('JUGADOR')
    elif propietario in ('JUGADOR2', 'IA'):
        if vida_tanque > 0 and _impacto_rect_tanque(x, y, tanque_x, tanque_y):
            impacto = True
            if es_ultimate:
                dano = min(max(0, int(dano)), ultimate_dano_restante)
            if dano > 0:
                vida_tanque = max(0, vida_tanque - dano)
                registrar_dano_jugador('JUGADOR2')

    if impacto and es_ultimate:
        ultimate_dano_restante = max(0, ultimate_dano_restante - dano)
    return impacto


def crear_fragmentos():
    """Divide el proyectil multiproyectil en tres balas con trayectorias distintas."""
    global fragmentos, multiproyectil_dividido
    if tipo_proyectil != 'MULTIPROYECTIL' or multiproyectil_dividido:
        return
    rapidez = max(4.0, math.hypot(velocidad_x, velocidad_y) * 0.82)
    angulo_base = math.atan2(velocidad_y, velocidad_x)
    propietario = proyectil_de
    fragmentos = []
    for desviacion in (-0.24, 0.0, 0.24):
        ang = angulo_base + desviacion
        fragmentos.append({
            'x': float(proyectil_x),
            'y': float(proyectil_y),
            'vx': math.cos(ang) * rapidez,
            'vy': math.sin(ang) * rapidez,
            'propietario': propietario,
            'ultimate': False,
        })
    multiproyectil_dividido = True


def explotar_ultimate():
    """Prepara una salva guiada; cada bala sale desde la explosión con un ángulo distinto."""
    global fragmentos, ultimate_activa, ultimate_frames
    global ultimate_pendientes, ultimate_lanzamiento_timer, ultimate_dano_restante
    cantidad = max(1, min(ULTIMATE_MAX_BALAS, ultimate_contador))
    propietario = proyectil_de
    ultimate_dano_restante = VIDA_MAXIMA // 3
    objetivo_x = tanque_x if propietario in ('IA', 'JUGADOR2') else enemigo_x
    objetivo_y = (tanque_y if propietario in ('IA', 'JUGADOR2') else enemigo_y) - TANQUE_ALTO / 2
    angulo_objetivo = math.atan2(objetivo_y - proyectil_y, objetivo_x - proyectil_x)
    ultimate_pendientes = []
    fragmentos = []
    for i in range(cantidad):
        # Un abanico moderado de ángulos crea arcos distintos sin lanzar balas al azar.
        proporcion = 0.0 if cantidad == 1 else (i / (cantidad - 1)) * 2.0 - 1.0
        desviacion_angular = proporcion * 0.48
        ang = angulo_objetivo + desviacion_angular
        # La dispersión puede abrirse mucho, pero las balas no deben arrancar
        # apuntando hacia el lado vertical contrario al objetivo.
        dy_objetivo = objetivo_y - proyectil_y
        if dy_objetivo * math.sin(ang) < 0:
            ang = math.atan2(-math.sin(ang), math.cos(ang))
        rapidez_inicial = random.uniform(7.5, 10.5)
        ultimate_pendientes.append({
            'x': float(proyectil_x), 'y': float(proyectil_y),
            'vx': math.cos(ang) * rapidez_inicial,
            'vy': math.sin(ang) * rapidez_inicial,
            'propietario': propietario, 'ultimate': True,
            'curva': proporcion,
            'edad': 0,
        })
    ultimate_lanzamiento_timer = 0
    ultimate_activa = False
    ultimate_frames = 0


def explotar_granada():
    """Detona la granada y aplica daño por proximidad al tanque en su radio."""
    global vida_tanque, vida_enemigo, granada_exploto
    if granada_exploto:
        return
    granada_exploto = True
    radio_explosion = 145.0
    dano_maximo = 42
    objetivos = []
    if proyectil_de == 'JUGADOR':
        objetivos.append(('enemigo', enemigo_x, enemigo_y))
    elif proyectil_de in ('JUGADOR2', 'IA'):
        objetivos.append(('jugador', tanque_x, tanque_y))
    for nombre, tx, ty in objetivos:
        distancia = math.hypot(proyectil_x - tx, proyectil_y - (ty - TANQUE_ALTO / 2))
        if distancia <= radio_explosion:
            proporcion = 1.0 - distancia / radio_explosion
            dano = max(5, int(dano_maximo * proporcion))
            if nombre == 'enemigo':
                vida_enemigo = max(0, vida_enemigo - dano)
                registrar_dano_jugador('JUGADOR')
            else:
                vida_tanque = max(0, vida_tanque - dano)
                registrar_dano_jugador('JUGADOR2')
    # La granada deja un cráter bastante más grande que el de la ultimate.
    crear_crater(proyectil_x, radio=125, profundidad=48)
    terminar_proyectil()


def actualizar_proyectil():
    global proyectil_x, proyectil_y, velocidad_x, velocidad_y
    global proyectil_activo, proyectil_de, tipo_proyectil
    global fragmentos, ultimate_contador, ultimate_frames, ultimate_activa
    global ultimate_pendientes, ultimate_lanzamiento_timer
    global granada_rebotando, granada_frames, granada_exploto
    if not proyectil_activo:
        return

    # La ultimate queda suspendida en su punto más alto mientras se activa
    # el temporizador. No se elimina por salir de los límites de la pantalla.
    if tipo_proyectil == 'ULTIMATE' and ultimate_activa:
        # Mantiene la bomba quieta dentro del mapa durante la espera.
        proyectil_x = max(RADIO_PROYECTIL, min(MAPA_ANCHO - RADIO_PROYECTIL, proyectil_x))
        proyectil_y = max(RADIO_PROYECTIL, min(MAPA_ALTO - RADIO_PROYECTIL, proyectil_y))
        if ultimate_frames > 0:
            ultimate_frames -= 1
            if ultimate_frames <= 0:
                explotar_ultimate()
        return

    # La ultimate lanza una bala pendiente cada pocos fotogramas, no toda la salva a la vez.
    if tipo_proyectil == 'ULTIMATE' and ultimate_pendientes:
        if ultimate_lanzamiento_timer > 0:
            ultimate_lanzamiento_timer -= 1
        if ultimate_lanzamiento_timer <= 0:
            fragmentos.append(ultimate_pendientes.pop(0))
            ultimate_lanzamiento_timer = ULTIMATE_INTERVALO_SALIDA

    # Los fragmentos activos se procesan por separado. La ultimate usa guiado
    # progresivo y colisión barrida para no atravesar tanques ni el terreno a alta velocidad.
    if fragmentos or ultimate_pendientes:
        supervivientes = []
        for bala in fragmentos:
            es_ultimate = bala.get('ultimate', False)
            anterior_x, anterior_y = bala['x'], bala['y']
            if es_ultimate:
                objetivo_x = tanque_x if bala['propietario'] in ('IA', 'JUGADOR2') else enemigo_x
                objetivo_y = (tanque_y if bala['propietario'] in ('IA', 'JUGADOR2') else enemigo_y) - TANQUE_ALTO / 2
                dx_obj = objetivo_x - bala['x']
                dy_obj = objetivo_y - bala['y']
                distancia = max(1.0, math.hypot(dx_obj, dy_obj))
                ux, uy = dx_obj / distancia, dy_obj / distancia

                # La aceleración gravitatoria hacia el tanque crece al acercarse.
                aceleracion = min(1.25, 0.12 + 0.75 * (1.0 - min(1.0, distancia / 1500.0)))
                bala['vx'] += ux * aceleracion
                bala['vy'] += uy * aceleracion

                # Curva lateral fuerte al principio, que se atenúa para que el guiado cierre.
                factor_curva = max(0.0, 1.0 - bala['edad'] / 100.0)
                fuerza_lateral = bala['curva'] * 0.16 * factor_curva
                bala['vx'] += -uy * fuerza_lateral
                bala['vy'] += ux * fuerza_lateral
                # Un toque de gravedad mantiene los arcos visuales, sin hacerlas caer sin control.
                bala['vy'] += GRAVEDAD * 0.22

                rapidez = max(0.01, math.hypot(bala['vx'], bala['vy']))
                rapidez_maxima = 10.0 + (1.0 - min(1.0, distancia / 1500.0)) * 20.0
                if rapidez > rapidez_maxima:
                    bala['vx'] = bala['vx'] / rapidez * rapidez_maxima
                    bala['vy'] = bala['vy'] / rapidez * rapidez_maxima
                bala['edad'] += 1
            else:
                bala['vy'] += GRAVEDAD

            bala['x'] += bala['vx']
            bala['y'] += bala['vy']
            dx_trayecto = bala['x'] - anterior_x
            dy_trayecto = bala['y'] - anterior_y
            distancia_trayecto = math.hypot(dx_trayecto, dy_trayecto)
            pasos = max(1, int(distancia_trayecto / 4.0))
            impacto = False
            toca_suelo = False
            dano_fragmento = max(1, int(math.hypot(bala['vx'], bala['vy']) * (0.38 if tipo_proyectil == 'MULTIPROYECTIL' else 0.8)))

            for paso in range(1, pasos + 1):
                t = paso / pasos
                px = anterior_x + dx_trayecto * t
                py = anterior_y + dy_trayecto * t
                impacto = _aplicar_dano_a_objetivo(
                    bala['propietario'], px, py, dano_fragmento,
                    es_ultimate=es_ultimate
                )
                if impacto:
                    break
                xx = max(0, min(MAPA_ANCHO, px))
                if py + RADIO_PROYECTIL >= altura_terreno(xx):
                    toca_suelo = True
                    if es_ultimate:
                        # Cada impacto de ultimate deja un agujero pequeño.
                        crear_crater(px, radio=24, profundidad=10)
                    break

            if not impacto and not toca_suelo:
                # Si una bala abandona los límites del mundo, se elimina con seguridad.
                if (bala['x'] < 0 or bala['x'] > MAPA_ANCHO
                        or bala['y'] < -50 or bala['y'] > MAPA_ALTO + 50):
                    continue
                supervivientes.append(bala)
        fragmentos = supervivientes
        if not fragmentos and not ultimate_pendientes:
            terminar_proyectil()
        return

    proyectil_x += velocidad_x
    proyectil_y += velocidad_y

    # Granada: al tocar el tanque o el terreno rebota y empieza su cuenta atrás.
    if tipo_proyectil == 'GRANADA':
        if granada_rebotando:
            granada_frames -= 1
            velocidad_y += GRAVEDAD
            if granada_frames <= 0:
                explotar_granada()
                return
            xx = max(0, min(MAPA_ANCHO, proyectil_x))
            if proyectil_y + RADIO_PROYECTIL >= altura_terreno(xx):
                proyectil_y = altura_terreno(xx) - RADIO_PROYECTIL
                velocidad_y = -abs(velocidad_y) * 0.45
                velocidad_x *= 0.75
            return
        toca_tanque = (
            (proyectil_de == 'JUGADOR' and vida_enemigo > 0 and _impacto_rect_tanque(proyectil_x, proyectil_y, enemigo_x, enemigo_y))
            or (proyectil_de in ('JUGADOR2', 'IA') and vida_tanque > 0 and _impacto_rect_tanque(proyectil_x, proyectil_y, tanque_x, tanque_y))
        )
        if toca_tanque:
            granada_rebotando = True
            granada_frames = 2 * FPS
            velocidad_y = -max(3.0, abs(velocidad_y) * 0.6)
            velocidad_x *= -0.45
            return

    # La ultimate nunca puede salir por el borde superior del mapa.
    # Si toca el límite superior, se queda justo debajo y entra en modo de espera.
    # También entra en espera de forma normal al alcanzar el punto más alto.
    if tipo_proyectil == 'ULTIMATE' and not ultimate_activa:
        ha_llegado_al_punto_mas_alto = velocidad_y >= 0
        if ha_llegado_al_punto_mas_alto:
            proyectil_y = max(RADIO_PROYECTIL, proyectil_y)
            velocidad_y = 0.0
            ultimate_activa = True
            ultimate_frames = 0
            ultimate_contador = 0
            return

    if comprobar_impacto_tanque():
        terminar_proyectil()
        return

    xx = max(0, min(MAPA_ANCHO, proyectil_x))
    if proyectil_y + RADIO_PROYECTIL >= altura_terreno(xx):
        if tipo_proyectil == 'GRANADA':
            granada_rebotando = True
            granada_frames = 2 * FPS
            proyectil_y = altura_terreno(xx) - RADIO_PROYECTIL
            velocidad_y = -max(3.0, abs(velocidad_y) * 0.6)
            velocidad_x *= 0.65
            return
        if tipo_proyectil == 'ULTIMATE':
            crear_crater(proyectil_x, radio=24, profundidad=10)
        elif tipo_proyectil == 'INCENDIARIA':
            crear_zona_fuego(proyectil_x)
        # El disparo básico y el multiproyectil no deforman ni incendian el terreno.
        terminar_proyectil()
        return

    velocidad_y += GRAVEDAD
    # No se termina un proyectil solo por salir del rectángulo del mapa.
    # El terreno se consulta usando la altura del borde más cercano.

#=========================
# DISPAROS
#=========================


def disparar_jugador():
    global proyectil_activo, proyectil_de, proyectil_x, proyectil_y
    global velocidad_x, velocidad_y, tipo_proyectil, fragmentos
    global multiproyectil_dividido, ultimate_contador, ultimate_activa
    global ultimate_pendientes, ultimate_lanzamiento_timer, ultimate_dano_restante
    global granada_rebotando, granada_frames, granada_exploto, ataque_seleccionado
    if ataque_seleccionado == 3 and not ultimate_desbloqueada.get(turno_actual, False):
        ataque_seleccionado = 1
    if turno_actual == 'JUGADOR':
        x, y, ang = (tanque_x, tanque_y, angulo)
        proyectil_de = 'JUGADOR'
    else:
        x, y, ang = (enemigo_x, enemigo_y, angulo_ia)
        proyectil_de = 'JUGADOR2'
    _, _, proyectil_x, proyectil_y = obtener_punta_canon(x, y, ang)
    velocidad_x = math.cos(ang) * potencia
    velocidad_y = -math.sin(ang) * potencia
    tipo_proyectil = TIPOS_ATAQUE[ataque_seleccionado]
    fragmentos = []
    multiproyectil_dividido = False
    ultimate_contador = 0
    ultimate_activa = False
    ultimate_pendientes = []
    ultimate_lanzamiento_timer = 0
    ultimate_dano_restante = VIDA_MAXIMA // 3
    granada_rebotando = False
    granada_frames = 0
    granada_exploto = False
    # La ultimate recibe un impulso vertical inicial para llegar alto.
    if tipo_proyectil == "ULTIMATE":
        velocidad_y = -max(8.0, potencia * 0.9)
        velocidad_x *= 0.45
    elif tipo_proyectil == "GRANADA":
        velocidad_x *= 0.8
        velocidad_y *= 0.8
    elif tipo_proyectil == "INCENDIARIA":
        velocidad_x *= 0.9
        velocidad_y *= 0.9
    proyectil_activo = True


def disparar_ia(ang, pot):
    global proyectil_activo, proyectil_de, proyectil_x, proyectil_y
    global velocidad_x, velocidad_y, angulo_ia, tipo_proyectil
    angulo_ia = ang
    tipo_proyectil = "BASICO"
    _, _, proyectil_x, proyectil_y = obtener_punta_canon(enemigo_x, enemigo_y, angulo_ia)
    velocidad_x = math.cos(angulo_ia) * pot
    velocidad_y = -math.sin(angulo_ia) * pot
    proyectil_de = 'IA'
    proyectil_activo = True
    print(f'La IA dispara: ángulo {math.degrees(ang):.1f}°, potencia {pot:.1f}.')

#=========================
# INTELIGENCIA ARTIFICIAL
#=========================


def simular_disparo_ia(ang, pot, objetivo_x=None, objetivo_y=None):
    """Simula el disparo sin cambiar la posición real de ningún tanque."""
    if objetivo_x is None:
        objetivo_x = tanque_x
    if objetivo_y is None:
        objetivo_y = tanque_y
    _, _, x, y = obtener_punta_canon(enemigo_x, enemigo_y, ang)
    vx = math.cos(ang) * pot
    vy = -math.sin(ang) * pot
    for _ in range(500):
        x += vx
        y += vy
        toca_objetivo = (
            x + RADIO_PROYECTIL >= objetivo_x - TANQUE_ANCHO / 2
            and x - RADIO_PROYECTIL <= objetivo_x + TANQUE_ANCHO / 2
            and y + RADIO_PROYECTIL >= objetivo_y - TANQUE_ALTO
            and y - RADIO_PROYECTIL <= objetivo_y
        )
        if toca_objetivo:
            return True
        xx = max(0, min(MAPA_ANCHO, x))
        if y + RADIO_PROYECTIL >= altura_terreno(xx):
            return False
        vy += GRAVEDAD
        if x < 0 or x > MAPA_ANCHO or y < 0 or (y > MAPA_ALTO):
            return False
    return False


def buscar_disparo_ia():
    """Busca un tiro hacia un punto real o desviado según la dificultad."""
    opciones = []
    ajuste = AJUSTES_IA[dificultad_ia]
    objetivo_x = tanque_x
    objetivo_y = tanque_y
    if random.random() >= ajuste['precision']:
        desplazamiento = random.uniform(
            -ajuste["desviacion"],
            ajuste["desviacion"],
        )
        objetivo_x = max(
            TANQUE_ANCHO / 2,
            min(
                MAPA_ANCHO - TANQUE_ANCHO / 2,
                tanque_x + desplazamiento,
            ),
        )
        objetivo_y = altura_terreno(objetivo_x)
    for grados in range(95, 180, 2):
        ang = math.radians(grados)
        pot = 8.0
        while pot <= POTENCIA_MAXIMA + 0.001:
            if simular_disparo_ia(ang, pot, objetivo_x, objetivo_y):
                puntuacion = abs(pot - 12.0) + abs(grados - 140) * 0.025
                opciones.append((puntuacion, ang, pot))
                break
            pot += 0.5
    if not opciones:
        return None
    opciones.sort(key=lambda item: item[0])
    return (opciones[0][1], opciones[0][2])

#=========================
# MOVIMIENTO DE LA IA
#=========================


def mover_ia_hacia_jugador():
    global enemigo_x, enemigo_y
    nueva_x = max(tanque_x + TANQUE_ANCHO + 20, enemigo_x - MOVIMIENTO_POR_TURNO)
    nueva_x = min(MAPA_ANCHO - TANQUE_ANCHO / 2, nueva_x)
    enemigo_x = nueva_x
    enemigo_y = altura_terreno(enemigo_x)


def ejecutar_turno_ia():
    disparo = buscar_disparo_ia()
    if disparo is None:
        mover_ia_hacia_jugador()
        disparo = buscar_disparo_ia()
    if disparo is None:
        disparo = (math.radians(140), POTENCIA_MAXIMA)
    disparar_ia(*disparo)

#=========================
# CONTROLES Y EVENTOS
#=========================


def controlar_evento(evento):
    global angulo_fijado, cargando, tiempo_potencia, potencia, vista_general, vista_proyectil
    global estado_partida, modo_juego, dificultad_ia, turno_actual
    global tanque_x, tanque_y, enemigo_x, enemigo_y
    global vida_tanque, vida_enemigo, movimiento_restante, quemadura_tanque, quemadura_enemigo
    global ataque_seleccionado, ultimate_contador, ultimate_frames
    global tipo_proyectil, multiproyectil_dividido
    global proyectil_y
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_TAB:
        vista_general = not vista_general
        if vista_general:
            vista_proyectil = False
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_c:
        vista_proyectil = not vista_proyectil
        if vista_proyectil:
            vista_general = False
    if estado_partida == 'MENU':
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            mx, my = evento.pos
            if pygame.Rect(300, 195, 400, 55).collidepoint(mx, my):
                modo_juego, estado_partida, turno_actual = ('SINGLEPLAYER', 'EN_CURSO', 'JUGADOR')
                tanque_x, tanque_y, enemigo_x, enemigo_y = (300.0, altura_terreno(300.0), 2100.0, altura_terreno(2100.0))
                vida_tanque = vida_enemigo = VIDA_MAXIMA
                turnos_con_dano.update({'JUGADOR': 0, 'JUGADOR2': 0})
                dano_en_turno.update({'JUGADOR': False, 'JUGADOR2': False})
                ultimate_desbloqueada.update({'JUGADOR': False, 'JUGADOR2': False})
                ataque_seleccionado = 1
                quemadura_tanque = quemadura_enemigo = 0
                crateres.clear()
                zonas_fuego.clear()
                movimiento_restante = MOVIMIENTO_POR_TURNO
            elif pygame.Rect(300, 260, 400, 55).collidepoint(mx, my):
                modo_juego, estado_partida, turno_actual = ('MULTIPLAYER', 'EN_CURSO', 'JUGADOR')
                tanque_x, tanque_y, enemigo_x, enemigo_y = (300.0, altura_terreno(300.0), 2100.0, altura_terreno(2100.0))
                vida_tanque = vida_enemigo = VIDA_MAXIMA
                turnos_con_dano.update({'JUGADOR': 0, 'JUGADOR2': 0})
                dano_en_turno.update({'JUGADOR': False, 'JUGADOR2': False})
                ultimate_desbloqueada.update({'JUGADOR': False, 'JUGADOR2': False})
                ataque_seleccionado = 1
                quemadura_tanque = quemadura_enemigo = 0
                crateres.clear()
                zonas_fuego.clear()
                movimiento_restante = MOVIMIENTO_POR_TURNO
            for texto, x in [('FACIL', 190), ('MEDIA', 350), ('DIFICIL', 510), ('IMPOSIBLE', 670)]:
                if pygame.Rect(x, 390, 140, 48).collidepoint(mx, my):
                    dificultad_ia = texto
        return
    if estado_partida in ('VICTORIA', 'DERROTA'):
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN:
            estado_partida = 'MENU'
        return
    if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
        estado_partida = 'MENU'
        return
    if turno_actual not in ('JUGADOR', 'JUGADOR2'):
        return
    if evento.type == pygame.KEYDOWN:
        if evento.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5) and not proyectil_activo and not cargando:
            nuevo_ataque = {
                pygame.K_1: 1,
                pygame.K_2: 2,
                pygame.K_3: 3,
                pygame.K_4: 4,
                pygame.K_5: 5,
            }[evento.key]
            if nuevo_ataque != 3 or ultimate_desbloqueada[turno_actual]:
                ataque_seleccionado = nuevo_ataque
        elif evento.key == pygame.K_SPACE and proyectil_activo:
            if tipo_proyectil == 'MULTIPROYECTIL' and not multiproyectil_dividido:
                crear_fragmentos()
            elif tipo_proyectil == 'ULTIMATE' and ultimate_activa:
                if ultimate_frames <= 0:
                    # Coloca la bomba aproximadamente a 100 px del borde superior visible.
                    altura_objetivo = camara_y + 100 / max(0.35, zoom_actual)
                    if proyectil_y < altura_objetivo:
                        proyectil_y = min(MAPA_ALTO - RADIO_PROYECTIL, altura_objetivo)
                    ultimate_contador = 1
                    ultimate_frames = 3 * FPS
                else:
                    ultimate_contador = min(ULTIMATE_MAX_BALAS, ultimate_contador + 1)
    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and (not proyectil_activo) and (not cargando):
        angulo_fijado = True
        cargando = True
        tiempo_potencia = 0
        potencia = 0
    if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and cargando:
        cargando = False
        disparar_jugador()

#=========================
# BUCLE PRINCIPAL DEL JUEGO
#=========================

ejecutando = True
while ejecutando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False
        else:
            controlar_evento(evento)
    if estado_partida == 'EN_CURSO':
        if turno_actual in ('JUGADOR', 'JUGADOR2'):
            mover_jugador(pygame.key.get_pressed())
        actualizar_camara()
        actualizar_angulo()
        actualizar_potencia()
        actualizar_zonas_fuego()
        actualizar_proyectil()
        if modo_juego == 'SINGLEPLAYER' and estado_partida == 'EN_CURSO' and (turno_actual == 'IA') and (not proyectil_activo):
            ejecutar_turno_ia()
    actualizar_camara()
    if estado_partida == 'MENU':
        dibujar_menu()
    else:
        dibujar_terreno()
        dibujar_tanque()
        dibujar_enemigo()
        dibujar_canon(tanque_x, tanque_y, angulo)
        dibujar_canon(enemigo_x, enemigo_y, angulo_ia)
        if turno_actual in ('JUGADOR', 'JUGADOR2') and (not proyectil_activo):
            if turno_actual == 'JUGADOR':
                dibujar_angulo()
            else:
                ox, oy = obtener_origen_canon(enemigo_x, enemigo_y, TANQUE_ENEMIGO_IMAGEN)
                for i in range(1, 9):
                    pygame.draw.circle(MUNDO, BLANCO, (int(ox + math.cos(angulo_ia) * 22 * i), int(oy - math.sin(angulo_ia) * 22 * i)), 3)
        if proyectil_activo:
            color = BLANCO if proyectil_de in ('JUGADOR', 'JUGADOR2') else AMARILLO
            if tipo_proyectil == "GRANADA":
                color = (150, 150, 150)
            elif tipo_proyectil == "ULTIMATE":
                color = AMARILLO
            elif tipo_proyectil == "INCENDIARIA":
                color = (255, 95, 25)
            pygame.draw.circle(MUNDO, color, (int(proyectil_x), int(proyectil_y)), RADIO_PROYECTIL + (2 if tipo_proyectil == "GRANADA" else 0))
            for bala in fragmentos:
                color_bala = AMARILLO if bala.get("ultimate", False) else BLANCO
                pygame.draw.circle(MUNDO, color_bala, (int(bala["x"]), int(bala["y"])), max(3, RADIO_PROYECTIL - 2))
        PANTALLA.fill(NEGRO)
        if vista_general:
            wr, hr = (int(MAPA_ANCHO * zoom_actual), int(MAPA_ALTO * zoom_actual))
            PANTALLA.blit(pygame.transform.scale(MUNDO, (wr, hr)), (int(desfase_general_x), int(desfase_general_y)))
        else:
            av = max(1, int(ANCHO / zoom_actual))
            hv = max(1, int(ALTO / zoom_actual))
            av = min(av, MAPA_ANCHO)
            hv = min(hv, MAPA_ALTO)
            camara_x = max(0, min(camara_x, MAPA_ANCHO - av))
            camara_y = max(0, min(camara_y, MAPA_ALTO - hv))
            zona = pygame.Rect(int(camara_x), int(camara_y), av, hv)
            PANTALLA.blit(pygame.transform.scale(MUNDO.subsurface(zona), (ANCHO, ALTO)), (0, 0))
        dibujar_hud()
        if estado_partida in ('VICTORIA', 'DERROTA'):
            t = pygame.font.SysFont(None, 38).render('ENTER: volver al menú', True, BLANCO)
            PANTALLA.blit(t, (ANCHO // 2 - 150, ALTO // 2))
    pygame.display.flip()
    RELOJ.tick(FPS)
pygame.quit()
