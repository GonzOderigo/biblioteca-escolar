-- =========================================================
-- ESQUEMA: Sistema de Biblioteca Escolar
-- Motor: PostgreSQL (Supabase)
-- Diseñado para arrancar con UNA institución y poder escalar
-- a multi-institución sin rehacer tablas (columna institucion_id
-- ya presente, con valor por defecto 1 mientras haya una sola escuela).
-- =========================================================

-- ---------------------------------------------------------
-- 0. INSTITUCIONES (cada colegio/biblioteca que use el sistema)
-- ---------------------------------------------------------
CREATE TABLE instituciones (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- IMPORTANTE: reemplazar 'NOMBRE DE TU BIBLIOTECA' por el nombre real
-- de la institución antes de correr este script. Cada institución que
-- participe del piloto corre este mismo script en su PROPIO proyecto
-- de Supabase (su propia base de datos), así los datos no se mezclan.
INSERT INTO instituciones (nombre) VALUES ('NOMBRE DE TU BIBLIOTECA');

-- ---------------------------------------------------------
-- 1. ROLES DE USUARIO (catálogo fijo, fácil de ampliar)
-- ---------------------------------------------------------
CREATE TABLE roles (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(30) NOT NULL UNIQUE  -- alumno, docente, bibliotecario, preceptor, otro
);

INSERT INTO roles (nombre) VALUES
    ('alumno'), ('docente'), ('bibliotecario'), ('preceptor'), ('otro');

-- ---------------------------------------------------------
-- 2. SOCIOS (usuarios que piden prestado)
-- ---------------------------------------------------------
CREATE TABLE socios (
    id              SERIAL PRIMARY KEY,
    institucion_id  INTEGER NOT NULL REFERENCES instituciones(id) DEFAULT 1,
    nombre          VARCHAR(100) NOT NULL,
    apellido        VARCHAR(100) NOT NULL,
    email           VARCHAR(150),
    dni_legajo      VARCHAR(30),
    rol_id          INTEGER NOT NULL REFERENCES roles(id),
    curso_o_materia VARCHAR(100),   -- ej: "5to A" si es alumno, "Historia" si es docente
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_socios_institucion ON socios(institucion_id);
CREATE INDEX idx_socios_email ON socios(email);

-- ---------------------------------------------------------
-- 3. AUTORES
-- ---------------------------------------------------------
CREATE TABLE autores (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(150) NOT NULL UNIQUE
);

-- ---------------------------------------------------------
-- 4. MATERIAS / TEMAS
-- ---------------------------------------------------------
CREATE TABLE materias (
    id      SERIAL PRIMARY KEY,
    nombre  VARCHAR(100) NOT NULL UNIQUE
);

-- ---------------------------------------------------------
-- 5. LIBROS (la obra, no el ejemplar físico)
-- ---------------------------------------------------------
CREATE TABLE libros (
    id              SERIAL PRIMARY KEY,
    institucion_id  INTEGER NOT NULL REFERENCES instituciones(id) DEFAULT 1,
    titulo          VARCHAR(250) NOT NULL,
    autor_id        INTEGER REFERENCES autores(id),
    materia_id      INTEGER REFERENCES materias(id),
    isbn            VARCHAR(20),
    creado_en       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_libros_titulo ON libros(titulo);
CREATE INDEX idx_libros_institucion ON libros(institucion_id);

-- ---------------------------------------------------------
-- 6. EJEMPLARES (stock físico real, cada copia con su N° inventario)
-- ---------------------------------------------------------
CREATE TABLE ejemplares (
    id                SERIAL PRIMARY KEY,
    libro_id          INTEGER NOT NULL REFERENCES libros(id),
    numero_inventario VARCHAR(30) NOT NULL UNIQUE,
    estado            VARCHAR(20) NOT NULL DEFAULT 'disponible'
                        CHECK (estado IN ('disponible', 'prestado', 'baja', 'perdido')),
    ubicacion         VARCHAR(100),  -- ej: estante, sección
    creado_en         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ejemplares_libro ON ejemplares(libro_id);
CREATE INDEX idx_ejemplares_estado ON ejemplares(estado);

-- ---------------------------------------------------------
-- 7. PRESTAMOS MASIVOS (préstamo grupal a un curso, opcional)
-- ---------------------------------------------------------
CREATE TABLE prestamos_masivos (
    id          SERIAL PRIMARY KEY,
    curso       VARCHAR(100) NOT NULL,
    fecha       DATE NOT NULL DEFAULT CURRENT_DATE,
    detalle     TEXT
);

-- ---------------------------------------------------------
-- 8. PRESTAMOS (individuales; pueden pertenecer a un masivo)
-- ---------------------------------------------------------
CREATE TABLE prestamos (
    id                      SERIAL PRIMARY KEY,
    ejemplar_id             INTEGER NOT NULL REFERENCES ejemplares(id),
    socio_id                INTEGER NOT NULL REFERENCES socios(id),
    prestamo_masivo_id      INTEGER REFERENCES prestamos_masivos(id),
    fecha_prestamo          DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_devolucion_prevista DATE NOT NULL,
    fecha_devolucion_real   DATE,
    estado                  VARCHAR(20) NOT NULL DEFAULT 'activo'
                              CHECK (estado IN ('activo', 'devuelto', 'vencido')),
    motivo                  VARCHAR(100),  -- ej: trabajo práctico, interés personal
    observaciones           TEXT
);

CREATE INDEX idx_prestamos_socio ON prestamos(socio_id);
CREATE INDEX idx_prestamos_ejemplar ON prestamos(ejemplar_id);
CREATE INDEX idx_prestamos_estado ON prestamos(estado);

-- ---------------------------------------------------------
-- 9. PRORROGAS (historial de extensiones de un préstamo)
-- ---------------------------------------------------------
CREATE TABLE prorrogas (
    id                        SERIAL PRIMARY KEY,
    prestamo_id               INTEGER NOT NULL REFERENCES prestamos(id),
    fecha                     DATE NOT NULL DEFAULT CURRENT_DATE,
    nueva_fecha_devolucion    DATE NOT NULL
);

-- ---------------------------------------------------------
-- 10. RESERVAS / INTERES (alguien quiere un libro que está prestado)
-- ---------------------------------------------------------
CREATE TABLE reservas_interes (
    id                SERIAL PRIMARY KEY,
    libro_id          INTEGER NOT NULL REFERENCES libros(id),
    socio_id          INTEGER NOT NULL REFERENCES socios(id),
    fecha_solicitud   DATE NOT NULL DEFAULT CURRENT_DATE,
    estado            VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                        CHECK (estado IN ('pendiente', 'cumplida', 'cancelada'))
);

-- =========================================================
-- VISTA ÚTIL: libros vencidos (para la pestaña "Vencidos")
-- =========================================================
CREATE VIEW vista_vencidos AS
SELECT
    p.id AS prestamo_id,
    s.nombre || ' ' || s.apellido AS socio,
    l.titulo,
    e.numero_inventario,
    p.fecha_devolucion_prevista,
    CURRENT_DATE - p.fecha_devolucion_prevista AS dias_de_atraso
FROM prestamos p
JOIN ejemplares e ON e.id = p.ejemplar_id
JOIN libros l ON l.id = e.libro_id
JOIN socios s ON s.id = p.socio_id
WHERE p.estado = 'activo'
  AND p.fecha_devolucion_prevista < CURRENT_DATE;

-- ---------------------------------------------------------
-- 11. SOLICITUDES WEB (pedidos que llegan desde el Google Form)
-- ---------------------------------------------------------
CREATE TABLE solicitudes_web (
    id                  SERIAL PRIMARY KEY,
    nombre_solicitante  VARCHAR(200) NOT NULL,
    email_solicitante   VARCHAR(150),
    libro_texto         VARCHAR(250) NOT NULL,
    tipo_solicitud      VARCHAR(20) NOT NULL CHECK (tipo_solicitud IN ('prestamo', 'devolucion')),
    observaciones       TEXT,
    estado              VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                          CHECK (estado IN ('pendiente', 'resuelta', 'descartada')),
    creado_en           TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE solicitudes_web ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Cualquiera puede crear una solicitud"
  ON solicitudes_web FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Cualquiera puede leer solicitudes (uso interno del programa)"
  ON solicitudes_web FOR SELECT
  USING (true);

CREATE POLICY "Cualquiera puede actualizar el estado (uso interno del programa)"
  ON solicitudes_web FOR UPDATE
  USING (true);
