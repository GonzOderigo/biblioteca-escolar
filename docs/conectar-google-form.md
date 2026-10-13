# Conectar un Google Form al sistema

Permite que alumnos y docentes pidan préstamos desde el celular. Cada respuesta del formulario llega a la tabla `solicitudes_web` y el bibliotecario la revisa dentro del programa antes de confirmar el préstamo.

El script está armado para un formulario con estas preguntas, en este orden: email, título del libro, autor, número de inventario, nombre y apellido, rol, año y curso o asignatura, motivo y observaciones. Si tu formulario tiene otro orden, ajustá los índices de `r[...]`.

## 1. Obtener los datos de Supabase

En tu proyecto de Supabase, andá a **Settings → API** y copiá:

- **Project URL**, por ejemplo `https://TU-PROYECTO.supabase.co`
- **anon public key**

## 2. Crear la tabla de solicitudes

En el SQL Editor de Supabase, ejecutá `agregar_solicitudes_web.sql`.

## 3. Agregar el script al formulario

1. Abrí el formulario en modo edición.
2. Menú de tres puntos → **Editor de secuencia de comandos** (Apps Script).
3. Pegá el código de abajo y reemplazá `SUPABASE_URL` y `SUPABASE_ANON_KEY` con tus valores.
4. Guardá.
5. En **Activadores**, agregá uno con la función `alEnviarFormulario` y el evento **Al enviarse el formulario**.
6. Aceptá los permisos que pide Google la primera vez.

```javascript
function alEnviarFormulario(e) {
  var SUPABASE_URL = "https://TU-PROYECTO.supabase.co";
  var SUPABASE_ANON_KEY = "TU-ANON-KEY-ACA";

  var r = e.values;
  // r[0] marca de tiempo, r[1] email, r[2] título, r[3] autor,
  // r[4] N° inventario, r[5] nombre y apellido, r[6] rol,
  // r[7] año y curso o asignatura, r[8] motivo, r[9] observaciones

  var email = r[1] || "";
  var titulo = r[2] || "";
  var autor = r[3] || "";
  var inventario = r[4] || "";
  var nombre = r[5] || "";
  var rol = r[6] || "";
  var curso = r[7] || "";
  var motivo = r[8] || "";
  var obsTexto = r[9] || "";

  var libroCompleto = titulo + (autor ? " (" + autor + ")" : "");

  var observacionesCompletas =
    "Rol: " + rol +
    (curso ? " | Curso/materia: " + curso : "") +
    (motivo ? " | Motivo: " + motivo : "") +
    (inventario ? " | N° inventario sugerido: " + inventario : "") +
    (obsTexto ? " | Obs: " + obsTexto : "");

  var payload = {
    nombre_solicitante: nombre,
    email_solicitante: email || null,
    libro_texto: libroCompleto,
    tipo_solicitud: "prestamo",
    observaciones: observacionesCompletas
  };

  var opciones = {
    method: "post",
    contentType: "application/json",
    headers: {
      "apikey": SUPABASE_ANON_KEY,
      "Authorization": "Bearer " + SUPABASE_ANON_KEY
    },
    payload: JSON.stringify(payload)
  };

  UrlFetchApp.fetch(SUPABASE_URL + "/rest/v1/solicitudes_web", opciones);
}
```

## 4. Probarlo

Completá el formulario como si fueras un alumno y revisá la sección **Solicitudes web** del programa, o la tabla `solicitudes_web` en Supabase.

Si no aparece nada, verificá que la tabla exista, que la URL y la clave estén bien copiadas, y revisá el registro de **Ejecuciones** en Apps Script.
