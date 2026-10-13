# Sistema de gestión de biblioteca escolar

Programa de escritorio para Windows que reemplaza el circuito de préstamos basado en un formulario de Google y una planilla de cálculo. Registra socios, libros, ejemplares, préstamos y devoluciones, y calcula automáticamente los préstamos vencidos.

Nació para resolver una necesidad real de la escuela donde trabajo y hoy está en etapa de **prueba piloto con bibliotecarios de dos instituciones**, cada una con su propia base de datos.

## Qué hace

- **Socios**: alta, edición, baja y búsqueda de alumnos, docentes y bibliotecarios. Importación masiva desde Excel y promoción de curso a fin de año.
- **Catálogo**: libros con autor y materia, y cada copia física como un ejemplar con su número de inventario. Importación masiva desde Excel o CSV sin duplicar títulos existentes.
- **Préstamos y devoluciones**: el ejemplar cambia de estado automáticamente. Permite prórrogas y registra su historial.
- **Préstamo masivo**: presta un mismo título a todos los alumnos de un curso en un solo paso e informa quiénes quedaron sin ejemplar.
- **Vencidos**: se calculan en tiempo real con una vista de base de datos, sin actualización manual.
- **Lista de interés**: si un libro no tiene stock, el socio queda anotado y el sistema avisa cuando se libera un ejemplar.
- **Solicitudes desde Google Forms**: los pedidos que alumnos y docentes completan desde el celular llegan directo al programa, y el bibliotecario confirma el préstamo real.
- **Reportes**: libros más prestados, stock por materia y socios más activos.

## Tecnologías

| Componente | Tecnología | Motivo |
|---|---|---|
| Interfaz | Python + CustomTkinter | Interfaz moderna, gratuita y empaquetable |
| Base de datos | PostgreSQL en Supabase | Motor profesional con capa gratuita, accesible desde cualquier PC |
| Conexión | psycopg2 | Conexión directa y estable a la base en la nube |
| Empaquetado | PyInstaller | Genera un `.exe` de Windows sin instalador |
| Integración | Google Apps Script | Envía las respuestas del formulario a la base de datos |

## Decisiones de diseño

- **Las credenciales no están en el código.** La conexión se lee de un archivo `config.env` local, que está excluido del repositorio.
- **Toda la lógica de base de datos vive en `db.py`**, separada de la interfaz (`app.py`).
- **Libro y ejemplar son entidades distintas**, para manejar varias copias del mismo título con stock individual.
- **El modelo ya contempla varias instituciones** con un campo `institucion_id`, para poder pasar a una base compartida sin migrar la estructura.

## Estructura

```
biblioteca-escolar/
├── app.py                        # Interfaz de usuario
├── db.py                         # Acceso a datos
├── schema.sql                    # Estructura de la base de datos
├── agregar_solicitudes_web.sql   # Tabla para las solicitudes del formulario
├── requirements.txt
├── config.env.ejemplo            # Modelo del archivo de configuración
├── plantillas/                   # Plantillas de Excel para importar libros y socios
└── docs/                         # Manual de usuario, guía de instalación y conexión con Google Forms
```

## Cómo ejecutarlo

1. Creá un proyecto gratuito en [Supabase](https://supabase.com) y ejecutá `schema.sql` en el SQL Editor.
2. Copiá `config.env.ejemplo` como `config.env` y completá tu cadena de conexión.
3. Instalá las dependencias y ejecutá el programa:

```bash
pip install -r requirements.txt
python app.py
```

La guía completa está en [`docs/guia-de-instalacion.pdf`](docs/guia-de-instalacion.pdf) y el uso diario, en el [manual de usuario](docs/manual-de-usuario.pdf). Para conectar un formulario de Google, seguí [`docs/conectar-google-form.md`](docs/conectar-google-form.md).

## Próximos pasos

Ajustes según la devolución de los bibliotecarios del piloto y, más adelante, una base de datos compartida para varias instituciones con un panel de administración central.

## Autor

**Gonzalo Matías Oderigo** · [LinkedIn](https://www.linkedin.com/in/gonzalo-matias-oderigo) · [GitHub](https://github.com/GonzOderigo)

Desarrollado con apoyo de IA generativa (Claude). El diseño funcional, las reglas del sistema y la implementación en la escuela son propios.
