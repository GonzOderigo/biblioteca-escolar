"""
Capa de acceso a datos (base de datos PostgreSQL / Supabase).
Todas las funciones que hablan con la base de datos viven acá,
para que el resto del programa no necesite saber nada de SQL.
"""
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv("config.env")  # lee el archivo config.env (debe estar en la misma carpeta)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "No se encontró DATABASE_URL. Revisá que exista el archivo "
            "config.env con tu cadena de conexión de Supabase."
        )
    return psycopg2.connect(DATABASE_URL)


def test_connection():
    """Devuelve (True, mensaje) o (False, mensaje_error)."""
    try:
        conn = get_connection()
        conn.close()
        return True, "Conexión exitosa"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------
# ROLES
# ---------------------------------------------------------
def listar_roles():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, nombre FROM roles ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# SOCIOS
# ---------------------------------------------------------
def crear_socio(nombre, apellido, email, dni_legajo, rol_id, curso_o_materia):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO socios (nombre, apellido, email, dni_legajo, rol_id, curso_o_materia)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
        (nombre, apellido, email, dni_legajo, rol_id, curso_o_materia),
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return new_id


def buscar_socios(texto):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    like = f"%{texto}%"
    cur.execute(
        """SELECT s.id, s.nombre, s.apellido, s.email, s.dni_legajo,
                  r.nombre AS rol, s.curso_o_materia
           FROM socios s JOIN roles r ON r.id = s.rol_id
           WHERE s.activo = TRUE AND (
             s.nombre ILIKE %s OR s.apellido ILIKE %s
             OR s.dni_legajo ILIKE %s OR s.email ILIKE %s
           )
           ORDER BY s.apellido, s.nombre LIMIT 50""",
        (like, like, like, like),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def listar_socios(limit=200):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT s.id, s.nombre, s.apellido, s.email, s.dni_legajo,
                  r.nombre AS rol, s.curso_o_materia
           FROM socios s JOIN roles r ON r.id = s.rol_id
           WHERE s.activo = TRUE
           ORDER BY s.apellido, s.nombre LIMIT %s""",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# AUTORES / MATERIAS
# ---------------------------------------------------------
def obtener_o_crear_autor(nombre):
    if not nombre:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM autores WHERE nombre = %s", (nombre,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]
    cur.execute("INSERT INTO autores (nombre) VALUES (%s) RETURNING id", (nombre,))
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return new_id


def obtener_o_crear_materia(nombre):
    if not nombre:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM materias WHERE nombre = %s", (nombre,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]
    cur.execute("INSERT INTO materias (nombre) VALUES (%s) RETURNING id", (nombre,))
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return new_id


# ---------------------------------------------------------
# LIBROS Y EJEMPLARES
# ---------------------------------------------------------
def crear_libro_con_ejemplar(titulo, autor_nombre, materia_nombre, numero_inventario, isbn=None):
    autor_id = obtener_o_crear_autor(autor_nombre)
    materia_id = obtener_o_crear_materia(materia_nombre)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO libros (titulo, autor_id, materia_id, isbn)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (titulo, autor_id, materia_id, isbn),
    )
    libro_id = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO ejemplares (libro_id, numero_inventario, estado)
           VALUES (%s, %s, 'disponible')""",
        (libro_id, numero_inventario),
    )
    conn.commit()
    conn.close()
    return libro_id


def agregar_ejemplar(libro_id, numero_inventario):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO ejemplares (libro_id, numero_inventario, estado)
           VALUES (%s, %s, 'disponible')""",
        (libro_id, numero_inventario),
    )
    conn.commit()
    conn.close()


def buscar_libros(texto):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    like = f"%{texto}%"
    cur.execute(
        """SELECT l.id AS libro_id, l.titulo,
                  COALESCE(a.nombre, '-') AS autor,
                  COALESCE(m.nombre, '-') AS materia,
                  COUNT(e.id) FILTER (WHERE e.estado = 'disponible') AS disponibles,
                  COUNT(e.id) AS total_ejemplares
           FROM libros l
           LEFT JOIN autores a ON a.id = l.autor_id
           LEFT JOIN materias m ON m.id = l.materia_id
           LEFT JOIN ejemplares e ON e.libro_id = l.id
           WHERE l.titulo ILIKE %s OR a.nombre ILIKE %s
           GROUP BY l.id, l.titulo, a.nombre, m.nombre
           ORDER BY l.titulo LIMIT 50""",
        (like, like),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def listar_ejemplares_disponibles(libro_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT id, numero_inventario FROM ejemplares
           WHERE libro_id = %s AND estado = 'disponible'
           ORDER BY numero_inventario""",
        (libro_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# PRESTAMOS
# ---------------------------------------------------------
def crear_prestamo(ejemplar_id, socio_id, fecha_devolucion_prevista, motivo, observaciones):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO prestamos (ejemplar_id, socio_id, fecha_devolucion_prevista, motivo, observaciones)
           VALUES (%s, %s, %s, %s, %s) RETURNING id""",
        (ejemplar_id, socio_id, fecha_devolucion_prevista, motivo, observaciones),
    )
    prestamo_id = cur.fetchone()[0]
    cur.execute("UPDATE ejemplares SET estado = 'prestado' WHERE id = %s", (ejemplar_id,))
    conn.commit()
    conn.close()
    return prestamo_id


def listar_prestamos_activos(socio_texto=None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    base = """SELECT p.id AS prestamo_id, s.nombre || ' ' || s.apellido AS socio,
                     l.titulo, e.numero_inventario,
                     p.fecha_prestamo, p.fecha_devolucion_prevista
              FROM prestamos p
              JOIN ejemplares e ON e.id = p.ejemplar_id
              JOIN libros l ON l.id = e.libro_id
              JOIN socios s ON s.id = p.socio_id
              WHERE p.estado = 'activo'"""
    params = ()
    if socio_texto:
        base += " AND (s.nombre ILIKE %s OR s.apellido ILIKE %s)"
        like = f"%{socio_texto}%"
        params = (like, like)
    base += " ORDER BY p.fecha_devolucion_prevista"
    cur.execute(base, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def listar_vencidos():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM vista_vencidos ORDER BY dias_de_atraso DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def devolver_prestamo(prestamo_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE prestamos SET estado = 'devuelto', fecha_devolucion_real = CURRENT_DATE
           WHERE id = %s RETURNING ejemplar_id""",
        (prestamo_id,),
    )
    ejemplar_id = cur.fetchone()[0]
    cur.execute("UPDATE ejemplares SET estado = 'disponible' WHERE id = %s", (ejemplar_id,))
    conn.commit()
    conn.close()


def prorrogar_prestamo(prestamo_id, nueva_fecha):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO prorrogas (prestamo_id, nueva_fecha_devolucion) VALUES (%s, %s)",
        (prestamo_id, nueva_fecha),
    )
    cur.execute(
        "UPDATE prestamos SET fecha_devolucion_prevista = %s WHERE id = %s",
        (nueva_fecha, prestamo_id),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# ESTADISTICAS PARA EL PANEL PRINCIPAL
# ---------------------------------------------------------
# ---------------------------------------------------------
# RESERVAS / INTERES
# ---------------------------------------------------------
def crear_reserva(libro_id, socio_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reservas_interes (libro_id, socio_id) VALUES (%s, %s)",
        (libro_id, socio_id),
    )
    conn.commit()
    conn.close()


def listar_reservas_pendientes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT r.id AS reserva_id, s.nombre || ' ' || s.apellido AS socio,
                  l.titulo, r.fecha_solicitud,
                  (SELECT COUNT(*) FROM ejemplares e
                     WHERE e.libro_id = l.id AND e.estado = 'disponible') AS disponibles
           FROM reservas_interes r
           JOIN libros l ON l.id = r.libro_id
           JOIN socios s ON s.id = r.socio_id
           WHERE r.estado = 'pendiente'
           ORDER BY r.fecha_solicitud""",
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def cancelar_reserva(reserva_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE reservas_interes SET estado = 'cancelada' WHERE id = %s", (reserva_id,))
    conn.commit()
    conn.close()


def cumplir_reserva(reserva_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE reservas_interes SET estado = 'cumplida' WHERE id = %s", (reserva_id,))
    conn.commit()
    conn.close()


def buscar_reservas_por_libro_disponible():
    """Devuelve reservas pendientes cuyo libro ya tiene ejemplares disponibles
    (útil para avisar al bibliotecario cuando algo que estaba reservado se liberó)."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT r.id AS reserva_id, s.nombre || ' ' || s.apellido AS socio,
                  l.titulo, l.id AS libro_id
           FROM reservas_interes r
           JOIN libros l ON l.id = r.libro_id
           JOIN socios s ON s.id = r.socio_id
           WHERE r.estado = 'pendiente'
             AND EXISTS (SELECT 1 FROM ejemplares e WHERE e.libro_id = l.id AND e.estado = 'disponible')
           ORDER BY r.fecha_solicitud""",
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# PRESTAMOS MASIVOS (a un curso completo)
# ---------------------------------------------------------
def crear_prestamo_masivo(curso, libro_id, socio_ids, fecha_devolucion_prevista, motivo):
    """Presta un ejemplar del libro indicado a cada socio de la lista.
    Si no hay ejemplares suficientes para todos, presta los que pueda y
    devuelve la lista de socios que quedaron sin ejemplar."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO prestamos_masivos (curso, detalle) VALUES (%s, %s) RETURNING id",
        (curso, f"Préstamo grupal de libro id={libro_id}"),
    )
    masivo_id = cur.fetchone()[0]

    sin_stock = []
    prestados = 0
    for socio_id in socio_ids:
        cur.execute(
            """SELECT id FROM ejemplares WHERE libro_id = %s AND estado = 'disponible'
               ORDER BY numero_inventario LIMIT 1 FOR UPDATE""",
            (libro_id,),
        )
        row = cur.fetchone()
        if not row:
            sin_stock.append(socio_id)
            continue
        ejemplar_id = row[0]
        cur.execute(
            """INSERT INTO prestamos (ejemplar_id, socio_id, prestamo_masivo_id,
                  fecha_devolucion_prevista, motivo)
               VALUES (%s, %s, %s, %s, %s)""",
            (ejemplar_id, socio_id, masivo_id, fecha_devolucion_prevista, motivo),
        )
        cur.execute("UPDATE ejemplares SET estado = 'prestado' WHERE id = %s", (ejemplar_id,))
        prestados += 1

    conn.commit()
    conn.close()
    return prestados, sin_stock


def listar_socios_por_curso(curso_texto):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT id, nombre, apellido FROM socios
           WHERE activo = TRUE AND curso_o_materia ILIKE %s
           ORDER BY apellido, nombre""",
        (f"%{curso_texto}%",),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------
# REPORTES
# ---------------------------------------------------------
def reporte_mas_prestados(limite=10):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT l.titulo, COUNT(p.id) AS veces_prestado
           FROM prestamos p
           JOIN ejemplares e ON e.id = p.ejemplar_id
           JOIN libros l ON l.id = e.libro_id
           GROUP BY l.titulo
           ORDER BY veces_prestado DESC LIMIT %s""",
        (limite,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def reporte_stock_por_materia():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT COALESCE(m.nombre, 'Sin materia') AS materia,
                  COUNT(e.id) AS total_ejemplares,
                  COUNT(e.id) FILTER (WHERE e.estado = 'disponible') AS disponibles
           FROM ejemplares e
           JOIN libros l ON l.id = e.libro_id
           LEFT JOIN materias m ON m.id = l.materia_id
           GROUP BY m.nombre
           ORDER BY total_ejemplares DESC""",
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def reporte_socios_mas_activos(limite=10):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT s.nombre || ' ' || s.apellido AS socio, COUNT(p.id) AS prestamos_totales
           FROM prestamos p
           JOIN socios s ON s.id = p.socio_id
           GROUP BY s.nombre, s.apellido
           ORDER BY prestamos_totales DESC LIMIT %s""",
        (limite,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows



# ---------------------------------------------------------
# ESTADISTICAS PARA EL PANEL PRINCIPAL
# ---------------------------------------------------------
def obtener_estadisticas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ejemplares")
    total_ejemplares = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM prestamos WHERE fecha_prestamo = CURRENT_DATE")
    prestados_hoy = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM prestamos WHERE estado = 'activo'")
    activos = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vista_vencidos")
    vencidos = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM solicitudes_web WHERE estado = 'pendiente'")
    solicitudes_pendientes = cur.fetchone()[0]
    conn.close()
    return {
        "ejemplares": total_ejemplares,
        "prestados_hoy": prestados_hoy,
        "activos": activos,
        "vencidos": vencidos,
        "solicitudes_pendientes": solicitudes_pendientes,
    }


# ---------------------------------------------------------
# SOLICITUDES WEB (Google Form)
# ---------------------------------------------------------
def listar_solicitudes_pendientes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT id, nombre_solicitante, email_solicitante, libro_texto,
                  tipo_solicitud, observaciones, creado_en
           FROM solicitudes_web
           WHERE estado = 'pendiente'
           ORDER BY creado_en"""
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def descartar_solicitud(solicitud_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE solicitudes_web SET estado = 'descartada' WHERE id = %s", (solicitud_id,))
    conn.commit()
    conn.close()


def marcar_solicitud_resuelta(solicitud_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE solicitudes_web SET estado = 'resuelta' WHERE id = %s", (solicitud_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# IMPORTACION MASIVA DE LIBROS (desde Excel/CSV)
# ---------------------------------------------------------
def importar_libros_masivo(filas):
    """Recibe una lista de diccionarios con las claves:
    titulo, autor, materia, numero_inventario.
    Cada fila representa UN ejemplar físico. Si ya existe un libro con
    el mismo título y autor, reutiliza ese libro y solo agrega el
    ejemplar nuevo (para poder cargar varias copias del mismo título).
    Devuelve un resumen: {"importados": N, "errores": [texto, ...]}."""
    resultados = {"importados": 0, "errores": []}

    for i, fila in enumerate(filas, start=2):  # fila 1 = encabezados
        titulo = (fila.get("titulo") or "").strip()
        numero_inventario = str(fila.get("numero_inventario") or "").strip()
        autor = (fila.get("autor") or "").strip()
        materia = (fila.get("materia") or "").strip()

        if not titulo or not numero_inventario:
            resultados["errores"].append(f"Fila {i}: falta título o número de inventario")
            continue

        conn = None
        try:
            autor_id = obtener_o_crear_autor(autor) if autor else None
            materia_id = obtener_o_crear_materia(materia) if materia else None

            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM libros WHERE titulo = %s AND autor_id IS NOT DISTINCT FROM %s",
                (titulo, autor_id),
            )
            row = cur.fetchone()
            if row:
                libro_id = row[0]
            else:
                cur.execute(
                    "INSERT INTO libros (titulo, autor_id, materia_id) VALUES (%s, %s, %s) RETURNING id",
                    (titulo, autor_id, materia_id),
                )
                libro_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO ejemplares (libro_id, numero_inventario, estado) VALUES (%s, %s, 'disponible')",
                (libro_id, numero_inventario),
            )
            conn.commit()
            resultados["importados"] += 1
        except Exception as e:
            if conn:
                conn.rollback()
            resultados["errores"].append(f"Fila {i} ('{titulo}', inv. {numero_inventario}): {e}")
        finally:
            if conn:
                conn.close()

    return resultados


# ---------------------------------------------------------
# SOCIOS: editar, dar de baja, filtrar, importar, gestión de fin de año
# ---------------------------------------------------------
def actualizar_socio(socio_id, nombre, apellido, email, dni_legajo, rol_id, curso_o_materia):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE socios SET nombre = %s, apellido = %s, email = %s,
               dni_legajo = %s, rol_id = %s, curso_o_materia = %s
           WHERE id = %s""",
        (nombre, apellido, email, dni_legajo, rol_id, curso_o_materia, socio_id),
    )
    conn.commit()
    conn.close()


def dar_baja_socio(socio_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE socios SET activo = FALSE WHERE id = %s", (socio_id,))
    conn.commit()
    conn.close()


def reactivar_socio(socio_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE socios SET activo = TRUE WHERE id = %s", (socio_id,))
    conn.commit()
    conn.close()


def obtener_socio(socio_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT s.id, s.nombre, s.apellido, s.email, s.dni_legajo,
                  s.rol_id, r.nombre AS rol, s.curso_o_materia
           FROM socios s JOIN roles r ON r.id = s.rol_id
           WHERE s.id = %s""",
        (socio_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def listar_cursos_existentes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT DISTINCT curso_o_materia FROM socios
           WHERE activo = TRUE AND curso_o_materia IS NOT NULL AND curso_o_materia <> ''
           ORDER BY curso_o_materia"""
    )
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def buscar_socios_filtrado(texto=None, curso=None, incluir_inactivos=False):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    condiciones = []
    params = []
    if not incluir_inactivos:
        condiciones.append("s.activo = TRUE")
    if texto:
        condiciones.append(
            "(s.nombre ILIKE %s OR s.apellido ILIKE %s OR s.dni_legajo ILIKE %s OR s.email ILIKE %s)"
        )
        like = f"%{texto}%"
        params += [like, like, like, like]
    if curso:
        condiciones.append("s.curso_o_materia = %s")
        params.append(curso)
    where = " AND ".join(condiciones) if condiciones else "TRUE"
    cur.execute(
        f"""SELECT s.id, s.nombre, s.apellido, s.email, s.dni_legajo,
                   r.nombre AS rol, s.curso_o_materia, s.activo
            FROM socios s JOIN roles r ON r.id = s.rol_id
            WHERE {where}
            ORDER BY s.apellido, s.nombre LIMIT 300""",
        params,
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def importar_socios_masivo(filas):
    """Recibe una lista de diccionarios con las claves:
    nombre, apellido, email, dni_legajo, rol, curso_o_materia.
    'rol' debe coincidir con un nombre de rol existente (alumno, docente, etc.)."""
    resultados = {"importados": 0, "errores": []}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM roles")
    roles_por_nombre = {nombre.strip().lower(): rid for rid, nombre in cur.fetchall()}
    conn.close()

    for i, fila in enumerate(filas, start=2):
        nombre = (fila.get("nombre") or "").strip()
        apellido = (fila.get("apellido") or "").strip()
        email = (fila.get("email") or "").strip()
        dni = (fila.get("dni_legajo") or "").strip()
        rol_texto = (fila.get("rol") or "").strip().lower()
        curso = (fila.get("curso_o_materia") or "").strip()

        if not nombre or not apellido:
            resultados["errores"].append(f"Fila {i}: falta nombre o apellido")
            continue
        rol_id = roles_por_nombre.get(rol_texto)
        if not rol_id:
            resultados["errores"].append(
                f"Fila {i} ('{nombre} {apellido}'): rol '{rol_texto}' no reconocido"
            )
            continue

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO socios (nombre, apellido, email, dni_legajo, rol_id, curso_o_materia)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (nombre, apellido, email or None, dni or None, rol_id, curso or None),
            )
            conn.commit()
            resultados["importados"] += 1
        except Exception as e:
            if conn:
                conn.rollback()
            resultados["errores"].append(f"Fila {i} ('{nombre} {apellido}'): {e}")
        finally:
            if conn:
                conn.close()

    return resultados


def promocionar_curso(curso_viejo, curso_nuevo):
    """Actualiza en bloque el campo curso_o_materia de todos los socios activos
    que tengan curso_viejo, cambiándolo a curso_nuevo. Devuelve cuántos se actualizaron."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE socios SET curso_o_materia = %s
           WHERE activo = TRUE AND curso_o_materia = %s""",
        (curso_nuevo, curso_viejo),
    )
    cantidad = cur.rowcount
    conn.commit()
    conn.close()
    return cantidad


def dar_baja_masiva_por_curso(curso):
    """Marca como inactivos a todos los socios activos de un curso dado
    (por ejemplo, egresados de fin de año). Devuelve cuántos se dieron de baja."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE socios SET activo = FALSE WHERE activo = TRUE AND curso_o_materia = %s",
        (curso,),
    )
    cantidad = cur.rowcount
    conn.commit()
    conn.close()
    return cantidad
