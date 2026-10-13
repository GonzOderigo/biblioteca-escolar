-- =========================================================
-- AGREGADO: Solicitudes recibidas desde el Google Form
-- Correr este script en el SQL Editor de Supabase (además del
-- schema.sql original, no lo reemplaza).
-- =========================================================

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

-- Permite que el Google Form (a través del script) inserte filas
-- sin necesitar loguearse como bibliotecario.
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
