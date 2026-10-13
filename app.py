"""
Sistema de gestión de biblioteca escolar - Programa de escritorio
Punto de entrada de la aplicación.
"""
import datetime
import csv
import customtkinter as ctk
from tkinter import messagebox, filedialog
import db

try:
    import openpyxl
except ImportError:
    openpyxl = None


def leer_archivo_generico(path):
    """Lee un .xlsx o .csv y devuelve una lista de diccionarios con las
    claves titulo, autor, materia, numero_inventario, tomadas de la
    primera fila (encabezados)."""
    filas = []
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as f:
            lector = csv.DictReader(f)
            for r in lector:
                filas.append({(k or "").strip().lower(): (v or "").strip() for k, v in r.items()})
    elif path.lower().endswith(".xlsx"):
        if openpyxl is None:
            raise RuntimeError("Falta instalar la librería openpyxl (py -m pip install openpyxl)")
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb["Libros"] if "Libros" in wb.sheetnames else wb.active
        filas_crudas = list(ws.iter_rows(values_only=True))
        if not filas_crudas:
            return []
        encabezados = [str(h or "").strip().lower() for h in filas_crudas[0]]
        for fila in filas_crudas[1:]:
            if all(v is None or str(v).strip() == "" for v in fila):
                continue
            dicc = {}
            for i, valor in enumerate(fila):
                if i < len(encabezados):
                    dicc[encabezados[i]] = "" if valor is None else str(valor).strip()
            filas.append(dicc)
    else:
        raise RuntimeError("Formato no soportado. Usá un archivo .xlsx o .csv")
    return filas

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Biblioteca Escolar")
        self.geometry("1000x620")

        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.contenido = ctk.CTkFrame(self)
        self.contenido.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(
            self.sidebar, text="📚 Biblioteca", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 30), padx=20)

        botones = [
            ("Inicio", self.mostrar_inicio),
            ("Socios", self.mostrar_socios),
            ("Libros", self.mostrar_libros),
            ("Préstamos", self.mostrar_prestamos),
            ("Solicitudes web", self.mostrar_solicitudes),
            ("Reservas", self.mostrar_reservas),
            ("Vencidos", self.mostrar_vencidos),
            ("Reportes", self.mostrar_reportes),
        ]
        for texto, comando in botones:
            ctk.CTkButton(self.sidebar, text=texto, command=comando, anchor="w").pack(
                fill="x", padx=15, pady=5
            )

        self.mostrar_inicio()

    def limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    # -----------------------------------------------------
    # INICIO
    # -----------------------------------------------------
    def mostrar_inicio(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Panel general", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(25, 15)
        )
        try:
            stats = db.obtener_estadisticas()
        except Exception as e:
            ctk.CTkLabel(self.contenido, text=f"Error de conexión: {e}", text_color="red").pack(padx=30)
            return

        cards = ctk.CTkFrame(self.contenido, fg_color="transparent")
        cards.pack(fill="x", padx=30)
        datos = [
            ("Ejemplares", stats["ejemplares"]),
            ("Prestados hoy", stats["prestados_hoy"]),
            ("Activos", stats["activos"]),
            ("Vencidos", stats["vencidos"]),
            ("Solicitudes web", stats["solicitudes_pendientes"]),
        ]
        for titulo, valor in datos:
            card = ctk.CTkFrame(cards, corner_radius=10)
            card.pack(side="left", expand=True, fill="both", padx=8, pady=5)
            ctk.CTkLabel(card, text=titulo, text_color="gray").pack(pady=(15, 0))
            ctk.CTkLabel(card, text=str(valor), font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(0, 15))

    # -----------------------------------------------------
    # SOCIOS
    # -----------------------------------------------------
    def mostrar_socios(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Socios", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(25, 15)
        )

        tabs = ctk.CTkTabview(self.contenido)
        tabs.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        tab_listado = tabs.add("Listado")
        tab_fin_anio = tabs.add("Fin de año")

        roles = db.listar_roles()
        nombres_roles = [r["nombre"] for r in roles]

        # --- Alta manual ---
        form = ctk.CTkFrame(tab_listado)
        form.pack(fill="x", padx=5, pady=(10, 10))

        nombre_e = ctk.CTkEntry(form, placeholder_text="Nombre")
        apellido_e = ctk.CTkEntry(form, placeholder_text="Apellido")
        email_e = ctk.CTkEntry(form, placeholder_text="Email")
        dni_e = ctk.CTkEntry(form, placeholder_text="DNI / Legajo")
        curso_e = ctk.CTkEntry(form, placeholder_text="Curso o materia")

        rol_var = ctk.StringVar(value=nombres_roles[0] if nombres_roles else "")
        rol_menu = ctk.CTkOptionMenu(form, variable=rol_var, values=nombres_roles)

        for i, widget in enumerate([nombre_e, apellido_e, email_e, dni_e, rol_menu, curso_e]):
            widget.grid(row=0, column=i, padx=6, pady=12, sticky="ew")
            form.grid_columnconfigure(i, weight=1)

        def guardar():
            if not nombre_e.get() or not apellido_e.get():
                messagebox.showwarning("Falta información", "Nombre y apellido son obligatorios.")
                return
            rol_id = next((r["id"] for r in roles if r["nombre"] == rol_var.get()), None)
            db.crear_socio(
                nombre_e.get(), apellido_e.get(), email_e.get(),
                dni_e.get(), rol_id, curso_e.get(),
            )
            for w in [nombre_e, apellido_e, email_e, dni_e, curso_e]:
                w.delete(0, "end")
            actualizar_lista()

        botones_alta = ctk.CTkFrame(tab_listado, fg_color="transparent")
        botones_alta.pack(fill="x", padx=5, pady=(0, 10))
        ctk.CTkButton(botones_alta, text="+ Agregar socio", command=guardar).pack(side="left")

        def importar_socios_archivo():
            path = filedialog.askopenfilename(
                title="Elegí el archivo de socios a importar",
                filetypes=[("Excel o CSV", "*.xlsx *.csv")],
            )
            if not path:
                return
            try:
                filas = leer_archivo_generico(path)  # mismo lector genérico (encabezados variables)
            except Exception as e:
                messagebox.showerror("Error al leer el archivo", str(e))
                return
            if not filas:
                messagebox.showwarning("Archivo vacío", "No encontré filas con datos en ese archivo.")
                return
            resultado = db.importar_socios_masivo(filas)
            mensaje = f"Se importaron {resultado['importados']} de {len(filas)} filas."
            if resultado["errores"]:
                primeros = "\n".join(resultado["errores"][:10])
                mensaje += f"\n\n{len(resultado['errores'])} fila(s) con problemas:\n{primeros}"
                if len(resultado["errores"]) > 10:
                    mensaje += "\n(y más...)"
            messagebox.showinfo("Importación finalizada", mensaje)
            actualizar_lista()

        ctk.CTkButton(
            botones_alta, text="📥 Importar desde Excel/CSV", fg_color="#0f6e56",
            command=importar_socios_archivo,
        ).pack(side="left", padx=8)

        # --- Filtros ---
        filtros = ctk.CTkFrame(tab_listado, fg_color="transparent")
        filtros.pack(fill="x", padx=5, pady=(0, 10))

        buscador = ctk.CTkEntry(filtros, placeholder_text="Buscar por nombre, apellido, DNI o email...")
        buscador.pack(side="left", fill="x", expand=True, padx=(0, 8))

        cursos_disponibles = ["Todos los cursos"] + db.listar_cursos_existentes()
        curso_filtro_var = ctk.StringVar(value="Todos los cursos")
        curso_filtro_menu = ctk.CTkOptionMenu(filtros, variable=curso_filtro_var, values=cursos_disponibles)
        curso_filtro_menu.pack(side="left", padx=(0, 8))

        incluir_inactivos_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            filtros, text="Incluir dados de baja", variable=incluir_inactivos_var,
            command=lambda: actualizar_lista(),
        ).pack(side="left")

        lista_frame = ctk.CTkScrollableFrame(tab_listado)
        lista_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        def abrir_editor_socio(socio_id):
            s = db.obtener_socio(socio_id)
            if not s:
                return
            ventana = ctk.CTkToplevel(self)
            ventana.title(f"Editar socio: {s['nombre']} {s['apellido']}")
            ventana.geometry("420x420")
            ventana.grab_set()  # modal: bloquea la ventana principal hasta cerrarla

            campos = {}
            for etiqueta, clave, valor in [
                ("Nombre", "nombre", s["nombre"]),
                ("Apellido", "apellido", s["apellido"]),
                ("Email", "email", s["email"] or ""),
                ("DNI / Legajo", "dni_legajo", s["dni_legajo"] or ""),
                ("Curso o materia", "curso_o_materia", s["curso_o_materia"] or ""),
            ]:
                ctk.CTkLabel(ventana, text=etiqueta, anchor="w").pack(fill="x", padx=20, pady=(12, 0))
                e = ctk.CTkEntry(ventana)
                e.insert(0, valor)
                e.pack(fill="x", padx=20)
                campos[clave] = e

            ctk.CTkLabel(ventana, text="Rol", anchor="w").pack(fill="x", padx=20, pady=(12, 0))
            rol_edit_var = ctk.StringVar(value=s["rol"])
            ctk.CTkOptionMenu(ventana, variable=rol_edit_var, values=nombres_roles).pack(fill="x", padx=20)

            def guardar_cambios():
                rol_id = next((r["id"] for r in roles if r["nombre"] == rol_edit_var.get()), s["rol_id"])
                db.actualizar_socio(
                    socio_id, campos["nombre"].get(), campos["apellido"].get(),
                    campos["email"].get(), campos["dni_legajo"].get(), rol_id,
                    campos["curso_o_materia"].get(),
                )
                ventana.destroy()
                actualizar_lista()

            ctk.CTkButton(ventana, text="Guardar cambios", command=guardar_cambios).pack(pady=20)

        def actualizar_lista(*_):
            for w in lista_frame.winfo_children():
                w.destroy()
            texto = buscador.get().strip()
            curso_sel = curso_filtro_var.get()
            curso_param = None if curso_sel == "Todos los cursos" else curso_sel
            socios = db.buscar_socios_filtrado(
                texto=texto or None, curso=curso_param, incluir_inactivos=incluir_inactivos_var.get()
            )
            for s in socios:
                fila = ctk.CTkFrame(lista_frame)
                fila.pack(fill="x", pady=3)
                estado_txt = "" if s["activo"] else "  [DE BAJA]"
                texto_fila = (
                    f"{s['apellido']}, {s['nombre']}  |  {s['rol']}  |  "
                    f"{s['curso_o_materia'] or '-'}  |  {s['dni_legajo'] or '-'}{estado_txt}"
                )
                color = "#b3261e" if not s["activo"] else None
                ctk.CTkLabel(fila, text=texto_fila, anchor="w", text_color=color).pack(
                    side="left", padx=8, pady=6, expand=True, fill="x"
                )
                if s["activo"]:
                    ctk.CTkButton(
                        fila, text="Dar de baja", width=100, fg_color="#b3261e",
                        command=lambda sid=s["id"]: (db.dar_baja_socio(sid), actualizar_lista()),
                    ).pack(side="right", padx=5)
                else:
                    ctk.CTkButton(
                        fila, text="Reactivar", width=100,
                        command=lambda sid=s["id"]: (db.reactivar_socio(sid), actualizar_lista()),
                    ).pack(side="right", padx=5)
                ctk.CTkButton(
                    fila, text="Editar", width=80, fg_color="gray",
                    command=lambda sid=s["id"]: abrir_editor_socio(sid),
                ).pack(side="right", padx=5)

        buscador.bind("<KeyRelease>", actualizar_lista)
        curso_filtro_menu.configure(command=lambda _=None: actualizar_lista())
        actualizar_lista()

        # --- Fin de año: promoción y baja masiva por curso ---
        ctk.CTkLabel(
            tab_fin_anio, text="Promoción de curso", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(15, 5))
        ctk.CTkLabel(
            tab_fin_anio,
            text="Cambia de una sola vez el curso de TODOS los socios activos de un curso a otro (ej: '5to A' → '6to A').",
            text_color="gray", wraplength=800, justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        cursos_para_promocion = db.listar_cursos_existentes()
        curso_viejo_var = ctk.StringVar(value=cursos_para_promocion[0] if cursos_para_promocion else "")
        fila_promo = ctk.CTkFrame(tab_fin_anio, fg_color="transparent")
        fila_promo.pack(fill="x", padx=10, pady=5)
        ctk.CTkOptionMenu(fila_promo, variable=curso_viejo_var, values=cursos_para_promocion or ["(sin cursos)"]).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkLabel(fila_promo, text="→").pack(side="left", padx=8)
        curso_nuevo_e = ctk.CTkEntry(fila_promo, placeholder_text="Nuevo curso (ej: 6to A)")
        curso_nuevo_e.pack(side="left", fill="x", expand=True, padx=8)

        def promocionar():
            viejo = curso_viejo_var.get()
            nuevo = curso_nuevo_e.get().strip()
            if not viejo or not nuevo:
                messagebox.showwarning("Falta información", "Elegí el curso actual y escribí el curso nuevo.")
                return
            if not messagebox.askyesno(
                "Confirmar promoción",
                f"¿Cambiar el curso de TODOS los socios activos de '{viejo}' a '{nuevo}'?",
            ):
                return
            cantidad = db.promocionar_curso(viejo, nuevo)
            messagebox.showinfo("Listo", f"Se actualizaron {cantidad} socio(s) de '{viejo}' a '{nuevo}'.")
            self.mostrar_socios()

        ctk.CTkButton(tab_fin_anio, text="Promocionar curso", command=promocionar).pack(
            anchor="w", padx=10, pady=(0, 25)
        )

        ctk.CTkLabel(
            tab_fin_anio, text="Baja masiva por curso", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 5))
        ctk.CTkLabel(
            tab_fin_anio,
            text="Da de baja de una sola vez a TODOS los socios activos de un curso (ej: egresados de fin de año).",
            text_color="gray", wraplength=800, justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        curso_baja_var = ctk.StringVar(value=cursos_para_promocion[0] if cursos_para_promocion else "")
        fila_baja = ctk.CTkFrame(tab_fin_anio, fg_color="transparent")
        fila_baja.pack(fill="x", padx=10, pady=5)
        ctk.CTkOptionMenu(fila_baja, variable=curso_baja_var, values=cursos_para_promocion or ["(sin cursos)"]).pack(
            side="left", padx=(0, 8)
        )

        def dar_baja_curso():
            curso = curso_baja_var.get()
            if not curso:
                return
            if not messagebox.askyesno(
                "Confirmar baja masiva",
                f"¿Dar de baja a TODOS los socios activos del curso '{curso}'? Esta acción se puede revertir "
                "socio por socio desde el listado, pero no tiene un botón de 'deshacer' masivo.",
            ):
                return
            cantidad = db.dar_baja_masiva_por_curso(curso)
            messagebox.showinfo("Listo", f"Se dieron de baja {cantidad} socio(s) del curso '{curso}'.")
            self.mostrar_socios()

        ctk.CTkButton(
            tab_fin_anio, text="Dar de baja a todo el curso", fg_color="#b3261e", command=dar_baja_curso
        ).pack(anchor="w", padx=10, pady=(0, 15))

    # -----------------------------------------------------
    # LIBROS
    # -----------------------------------------------------
    def mostrar_libros(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Libros", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(25, 15)
        )

        form = ctk.CTkFrame(self.contenido)
        form.pack(fill="x", padx=30, pady=(0, 15))

        titulo_e = ctk.CTkEntry(form, placeholder_text="Título")
        autor_e = ctk.CTkEntry(form, placeholder_text="Autor")
        materia_e = ctk.CTkEntry(form, placeholder_text="Materia / tema")
        inventario_e = ctk.CTkEntry(form, placeholder_text="N° de inventario")

        for i, widget in enumerate([titulo_e, autor_e, materia_e, inventario_e]):
            widget.grid(row=0, column=i, padx=6, pady=12, sticky="ew")
            form.grid_columnconfigure(i, weight=1)

        def guardar():
            if not titulo_e.get() or not inventario_e.get():
                messagebox.showwarning("Falta información", "Título y N° de inventario son obligatorios.")
                return
            try:
                db.crear_libro_con_ejemplar(
                    titulo_e.get(), autor_e.get(), materia_e.get(), inventario_e.get()
                )
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")
                return
            for w in [titulo_e, autor_e, materia_e, inventario_e]:
                w.delete(0, "end")
            actualizar_lista()

        ctk.CTkButton(self.contenido, text="+ Agregar libro", command=guardar).pack(padx=30, pady=(0, 15), anchor="w")

        def importar_archivo():
            path = filedialog.askopenfilename(
                title="Elegí el archivo de libros a importar",
                filetypes=[("Excel o CSV", "*.xlsx *.csv")],
            )
            if not path:
                return
            try:
                filas = leer_archivo_generico(path)
            except Exception as e:
                messagebox.showerror("Error al leer el archivo", str(e))
                return
            if not filas:
                messagebox.showwarning("Archivo vacío", "No encontré filas con datos en ese archivo.")
                return
            resultado = db.importar_libros_masivo(filas)
            mensaje = f"Se importaron {resultado['importados']} de {len(filas)} filas."
            if resultado["errores"]:
                primeros = "\n".join(resultado["errores"][:10])
                mensaje += f"\n\n{len(resultado['errores'])} fila(s) con problemas:\n{primeros}"
                if len(resultado["errores"]) > 10:
                    mensaje += "\n(y más...)"
            messagebox.showinfo("Importación finalizada", mensaje)
            actualizar_lista()

        ctk.CTkButton(
            self.contenido, text="📥 Importar desde Excel/CSV", fg_color="#0f6e56", command=importar_archivo
        ).pack(padx=30, pady=(0, 15), anchor="w")

        buscador = ctk.CTkEntry(self.contenido, placeholder_text="Buscar por título o autor...")
        buscador.pack(fill="x", padx=30, pady=(0, 10))

        lista_frame = ctk.CTkScrollableFrame(self.contenido)
        lista_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        def actualizar_lista(*_):
            for w in lista_frame.winfo_children():
                w.destroy()
            texto = buscador.get().strip() or "%"
            libros = db.buscar_libros(texto if texto != "%" else "")
            for l in libros:
                fila = f"{l['titulo']}  |  {l['autor']}  |  {l['materia']}  |  Disponibles: {l['disponibles']}/{l['total_ejemplares']}"
                ctk.CTkLabel(lista_frame, text=fila, anchor="w").pack(fill="x", padx=5, pady=3)

        buscador.bind("<KeyRelease>", actualizar_lista)
        actualizar_lista()

    # -----------------------------------------------------
    # PRESTAMOS
    # -----------------------------------------------------
    def mostrar_prestamos(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Préstamos", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(25, 15)
        )

        tabs = ctk.CTkTabview(self.contenido)
        tabs.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        tab_nuevo = tabs.add("Nuevo préstamo")
        tab_activos = tabs.add("Activos / devolver")
        tab_masivo = tabs.add("Préstamo masivo")

        # --- Nuevo préstamo ---
        socio_e = ctk.CTkEntry(tab_nuevo, placeholder_text="Buscar socio (nombre o apellido)")
        socio_e.pack(fill="x", padx=10, pady=(15, 5))
        socio_resultado = ctk.CTkOptionMenu(tab_nuevo, values=["Buscá un socio..."])
        socio_resultado.pack(fill="x", padx=10, pady=5)
        socios_encontrados = {}

        def buscar_socio(*_):
            texto = socio_e.get().strip()
            if len(texto) < 2:
                return
            resultados = db.buscar_socios(texto)
            socios_encontrados.clear()
            opciones = []
            for s in resultados:
                etiqueta = f"{s['apellido']}, {s['nombre']} ({s['dni_legajo'] or 's/dni'})"
                socios_encontrados[etiqueta] = s["id"]
                opciones.append(etiqueta)
            if opciones:
                socio_resultado.configure(values=opciones)
                socio_resultado.set(opciones[0])

        socio_e.bind("<KeyRelease>", buscar_socio)

        libro_e = ctk.CTkEntry(tab_nuevo, placeholder_text="Buscar libro (título)")
        libro_e.pack(fill="x", padx=10, pady=(15, 5))
        libro_resultado = ctk.CTkOptionMenu(tab_nuevo, values=["Buscá un libro..."])
        libro_resultado.pack(fill="x", padx=10, pady=5)
        libros_encontrados = {}

        def buscar_libro(*_):
            texto = libro_e.get().strip()
            if len(texto) < 2:
                return
            resultados = db.buscar_libros(texto)
            libros_encontrados.clear()
            opciones = []
            for l in resultados:
                etiqueta = f"{l['titulo']} — disp: {l['disponibles']}"
                libros_encontrados[etiqueta] = l["libro_id"]
                opciones.append(etiqueta)
            if opciones:
                libro_resultado.configure(values=opciones)
                libro_resultado.set(opciones[0])

        libro_e.bind("<KeyRelease>", buscar_libro)

        dias_e = ctk.CTkEntry(tab_nuevo, placeholder_text="Días de préstamo (ej: 15)")
        dias_e.pack(fill="x", padx=10, pady=(15, 5))
        motivo_e = ctk.CTkEntry(tab_nuevo, placeholder_text="Motivo (trabajo práctico, interés personal, etc.)")
        motivo_e.pack(fill="x", padx=10, pady=5)

        def registrar_prestamo():
            etiqueta_socio = socio_resultado.get()
            etiqueta_libro = libro_resultado.get()
            socio_id = socios_encontrados.get(etiqueta_socio)
            libro_id = libros_encontrados.get(etiqueta_libro)
            if not socio_id or not libro_id:
                messagebox.showwarning("Falta información", "Elegí un socio y un libro de la lista.")
                return
            ejemplares = db.listar_ejemplares_disponibles(libro_id)
            if not ejemplares:
                messagebox.showwarning("Sin stock", "No hay ejemplares disponibles de ese libro.")
                return
            try:
                dias = int(dias_e.get() or 15)
            except ValueError:
                dias = 15
            fecha_devolucion = datetime.date.today() + datetime.timedelta(days=dias)
            db.crear_prestamo(
                ejemplares[0]["id"], socio_id, fecha_devolucion, motivo_e.get(), ""
            )
            messagebox.showinfo("Listo", f"Préstamo registrado. Devolución prevista: {fecha_devolucion}")
            actualizar_activos()

        ctk.CTkButton(tab_nuevo, text="Registrar préstamo", command=registrar_prestamo).pack(pady=15)

        # --- Activos / devolver ---
        lista_activos = ctk.CTkScrollableFrame(tab_activos)
        lista_activos.pack(fill="both", expand=True, padx=10, pady=10)

        def actualizar_activos():
            for w in lista_activos.winfo_children():
                w.destroy()
            for p in db.listar_prestamos_activos():
                fila = ctk.CTkFrame(lista_activos)
                fila.pack(fill="x", pady=3)
                texto = (
                    f"{p['socio']}  |  {p['titulo']} (N° {p['numero_inventario']})  |  "
                    f"vence {p['fecha_devolucion_prevista']}"
                )
                ctk.CTkLabel(fila, text=texto, anchor="w").pack(side="left", padx=8, expand=True, fill="x")

                def prorrogar(pid=p["prestamo_id"]):
                    dialogo = ctk.CTkInputDialog(
                        text="¿Cuántos días más de plazo? (ej: 7)", title="Prorrogar préstamo"
                    )
                    dias_texto = dialogo.get_input()
                    if not dias_texto:
                        return
                    try:
                        dias = int(dias_texto)
                    except ValueError:
                        messagebox.showwarning("Valor inválido", "Ingresá un número de días.")
                        return
                    nueva_fecha = datetime.date.today() + datetime.timedelta(days=dias)
                    db.prorrogar_prestamo(pid, nueva_fecha)
                    messagebox.showinfo("Listo", f"Nueva fecha de devolución: {nueva_fecha}")
                    actualizar_activos()

                ctk.CTkButton(fila, text="Prorrogar", width=90, fg_color="#c98a1f", command=prorrogar).pack(
                    side="right", padx=5
                )
                def devolver(pid=p["prestamo_id"], titulo=p["titulo"]):
                    db.devolver_prestamo(pid)
                    interesados = [
                        r for r in db.buscar_reservas_por_libro_disponible() if r["titulo"] == titulo
                    ]
                    if interesados:
                        nombres = ", ".join(r["socio"] for r in interesados)
                        messagebox.showinfo(
                            "Hay interesados en este libro",
                            f"'{titulo}' fue devuelto y tiene reservas pendientes de: {nombres}\n"
                            "Podés avisarles y gestionar la reserva desde la sección Reservas.",
                        )
                    actualizar_activos()

                ctk.CTkButton(fila, text="Devolver", width=90, command=devolver).pack(side="right", padx=5)

        actualizar_activos()

        # --- Préstamo masivo ---
        ctk.CTkLabel(
            tab_masivo, text="Prestar un mismo libro a todo un curso", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(15, 5))

        curso_e = ctk.CTkEntry(tab_masivo, placeholder_text="Curso (ej: 5to A) — debe coincidir con 'Curso o materia' de los socios")
        curso_e.pack(fill="x", padx=10, pady=5)

        libro_masivo_e = ctk.CTkEntry(tab_masivo, placeholder_text="Buscar libro (título)")
        libro_masivo_e.pack(fill="x", padx=10, pady=(15, 5))
        libro_masivo_resultado = ctk.CTkOptionMenu(tab_masivo, values=["Buscá un libro..."])
        libro_masivo_resultado.pack(fill="x", padx=10, pady=5)
        libros_masivo_encontrados = {}

        def buscar_libro_masivo(*_):
            texto = libro_masivo_e.get().strip()
            if len(texto) < 2:
                return
            resultados = db.buscar_libros(texto)
            libros_masivo_encontrados.clear()
            opciones = []
            for l in resultados:
                etiqueta = f"{l['titulo']} — disp: {l['disponibles']}"
                libros_masivo_encontrados[etiqueta] = l["libro_id"]
                opciones.append(etiqueta)
            if opciones:
                libro_masivo_resultado.configure(values=opciones)
                libro_masivo_resultado.set(opciones[0])

        libro_masivo_e.bind("<KeyRelease>", buscar_libro_masivo)

        dias_masivo_e = ctk.CTkEntry(tab_masivo, placeholder_text="Días de préstamo (ej: 15)")
        dias_masivo_e.pack(fill="x", padx=10, pady=(15, 5))

        resultado_label = ctk.CTkLabel(tab_masivo, text="", justify="left")
        resultado_label.pack(fill="x", padx=10, pady=(10, 0))

        def registrar_masivo():
            curso = curso_e.get().strip()
            etiqueta_libro = libro_masivo_resultado.get()
            libro_id = libros_masivo_encontrados.get(etiqueta_libro)
            if not curso or not libro_id:
                messagebox.showwarning("Falta información", "Completá el curso y elegí un libro.")
                return
            socios = db.listar_socios_por_curso(curso)
            if not socios:
                messagebox.showwarning(
                    "Sin socios", f"No encontré socios con curso/materia '{curso}'."
                )
                return
            try:
                dias = int(dias_masivo_e.get() or 15)
            except ValueError:
                dias = 15
            fecha_devolucion = datetime.date.today() + datetime.timedelta(days=dias)
            socio_ids = [s["id"] for s in socios]
            prestados, sin_stock = db.crear_prestamo_masivo(
                curso, libro_id, socio_ids, fecha_devolucion, "Préstamo masivo"
            )
            texto = f"Prestados: {prestados} de {len(socio_ids)} alumnos del curso '{curso}'."
            if sin_stock:
                texto += f"\n{len(sin_stock)} alumno(s) quedaron sin ejemplar por falta de stock."
            resultado_label.configure(text=texto)
            actualizar_activos()

        ctk.CTkButton(tab_masivo, text="Registrar préstamo masivo", command=registrar_masivo).pack(pady=15)

    # -----------------------------------------------------
    # VENCIDOS
    # -----------------------------------------------------
    def mostrar_vencidos(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Préstamos vencidos", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(25, 15)
        )
        lista_frame = ctk.CTkScrollableFrame(self.contenido)
        lista_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        for v in db.listar_vencidos():
            texto = (
                f"{v['socio']}  |  {v['titulo']} (N° {v['numero_inventario']})  |  "
                f"vencía {v['fecha_devolucion_prevista']}  |  {v['dias_de_atraso']} días de atraso"
            )
            ctk.CTkLabel(lista_frame, text=texto, anchor="w", text_color="#b3261e").pack(fill="x", padx=5, pady=3)

    # -----------------------------------------------------
    # SOLICITUDES WEB (desde el Google Form)
    # -----------------------------------------------------
    def mostrar_solicitudes(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Solicitudes desde el Google Form", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(25, 5)
        )
        ctk.CTkLabel(
            self.contenido,
            text="Estos son pedidos que llegaron por el formulario web. Revisalos y completá el préstamo o la devolución real en la sección Préstamos; después marcalos como resueltos acá.",
            text_color="gray", wraplength=800, justify="left",
        ).pack(anchor="w", padx=30, pady=(0, 15))

        lista_frame = ctk.CTkScrollableFrame(self.contenido)
        lista_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        def actualizar_lista():
            for w in lista_frame.winfo_children():
                w.destroy()
            solicitudes = db.listar_solicitudes_pendientes()
            if not solicitudes:
                ctk.CTkLabel(lista_frame, text="No hay solicitudes pendientes por ahora.", text_color="gray").pack(
                    padx=5, pady=10
                )
                return
            for s in solicitudes:
                fila = ctk.CTkFrame(lista_frame)
                fila.pack(fill="x", pady=4)
                tipo_legible = "Préstamo" if s["tipo_solicitud"] == "prestamo" else "Devolución"
                texto = (
                    f"[{tipo_legible}] {s['nombre_solicitante']}  |  '{s['libro_texto']}'  |  "
                    f"{s['creado_en'].strftime('%d/%m %H:%M')}"
                )
                if s["observaciones"]:
                    texto += f"\nObs: {s['observaciones']}"
                ctk.CTkLabel(fila, text=texto, anchor="w", justify="left").pack(
                    side="left", padx=8, pady=6, expand=True, fill="x"
                )
                ctk.CTkButton(
                    fila, text="Descartar", width=90, fg_color="gray",
                    command=lambda sid=s["id"]: (db.descartar_solicitud(sid), actualizar_lista()),
                ).pack(side="right", padx=5)
                ctk.CTkButton(
                    fila, text="Marcar resuelta", width=120,
                    command=lambda sid=s["id"]: (db.marcar_solicitud_resuelta(sid), actualizar_lista()),
                ).pack(side="right", padx=5)

        ctk.CTkButton(self.contenido, text="Actualizar lista", command=actualizar_lista).pack(
            anchor="w", padx=30, pady=(0, 10)
        )
        actualizar_lista()

    # -----------------------------------------------------
    # RESERVAS / INTERES
    # -----------------------------------------------------
    def mostrar_reservas(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Reservas / Lista de interés", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(25, 15)
        )

        form = ctk.CTkFrame(self.contenido)
        form.pack(fill="x", padx=30, pady=(0, 15))

        socio_e = ctk.CTkEntry(form, placeholder_text="Buscar socio")
        socio_e.grid(row=0, column=0, padx=6, pady=12, sticky="ew")
        socio_menu = ctk.CTkOptionMenu(form, values=["Buscá un socio..."])
        socio_menu.grid(row=0, column=1, padx=6, pady=12, sticky="ew")
        socios_map = {}

        def buscar_socio(*_):
            texto = socio_e.get().strip()
            if len(texto) < 2:
                return
            socios_map.clear()
            opciones = []
            for s in db.buscar_socios(texto):
                etiqueta = f"{s['apellido']}, {s['nombre']}"
                socios_map[etiqueta] = s["id"]
                opciones.append(etiqueta)
            if opciones:
                socio_menu.configure(values=opciones)
                socio_menu.set(opciones[0])

        socio_e.bind("<KeyRelease>", buscar_socio)

        libro_e = ctk.CTkEntry(form, placeholder_text="Buscar libro")
        libro_e.grid(row=0, column=2, padx=6, pady=12, sticky="ew")
        libro_menu = ctk.CTkOptionMenu(form, values=["Buscá un libro..."])
        libro_menu.grid(row=0, column=3, padx=6, pady=12, sticky="ew")
        libros_map = {}

        def buscar_libro(*_):
            texto = libro_e.get().strip()
            if len(texto) < 2:
                return
            libros_map.clear()
            opciones = []
            for l in db.buscar_libros(texto):
                etiqueta = l["titulo"]
                libros_map[etiqueta] = l["libro_id"]
                opciones.append(etiqueta)
            if opciones:
                libro_menu.configure(values=opciones)
                libro_menu.set(opciones[0])

        libro_e.bind("<KeyRelease>", buscar_libro)
        for i in range(4):
            form.grid_columnconfigure(i, weight=1)

        lista_frame = ctk.CTkScrollableFrame(self.contenido)

        def actualizar_lista():
            for w in lista_frame.winfo_children():
                w.destroy()
            for r in db.listar_reservas_pendientes():
                fila = ctk.CTkFrame(lista_frame)
                fila.pack(fill="x", pady=3)
                disponible = r["disponibles"] > 0
                color = "#0f6e56" if disponible else None
                texto = f"{r['socio']}  |  {r['titulo']}  |  desde {r['fecha_solicitud']}"
                if disponible:
                    texto += "  ⚡ ¡ya hay disponible!"
                ctk.CTkLabel(fila, text=texto, anchor="w", text_color=color).pack(
                    side="left", padx=8, expand=True, fill="x"
                )
                ctk.CTkButton(
                    fila, text="Cancelar", width=90, fg_color="gray",
                    command=lambda rid=r["reserva_id"]: (db.cancelar_reserva(rid), actualizar_lista()),
                ).pack(side="right", padx=5)
                ctk.CTkButton(
                    fila, text="Cumplida", width=90,
                    command=lambda rid=r["reserva_id"]: (db.cumplir_reserva(rid), actualizar_lista()),
                ).pack(side="right", padx=5)

        def registrar_reserva():
            socio_id = socios_map.get(socio_menu.get())
            libro_id = libros_map.get(libro_menu.get())
            if not socio_id or not libro_id:
                messagebox.showwarning("Falta información", "Elegí un socio y un libro de la lista.")
                return
            db.crear_reserva(libro_id, socio_id)
            actualizar_lista()

        ctk.CTkButton(self.contenido, text="+ Anotar interés", command=registrar_reserva).pack(
            padx=30, pady=(0, 15), anchor="w"
        )
        lista_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        actualizar_lista()

    # -----------------------------------------------------
    # REPORTES
    # -----------------------------------------------------
    def mostrar_reportes(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Reportes", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(25, 15)
        )

        tabs = ctk.CTkTabview(self.contenido)
        tabs.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        tab_mas = tabs.add("Más prestados")
        tab_stock = tabs.add("Stock por materia")
        tab_socios = tabs.add("Socios activos")

        f1 = ctk.CTkScrollableFrame(tab_mas)
        f1.pack(fill="both", expand=True, padx=5, pady=5)
        for r in db.reporte_mas_prestados():
            ctk.CTkLabel(f1, text=f"{r['titulo']}  —  {r['veces_prestado']} préstamos", anchor="w").pack(
                fill="x", padx=5, pady=3
            )

        f2 = ctk.CTkScrollableFrame(tab_stock)
        f2.pack(fill="both", expand=True, padx=5, pady=5)
        for r in db.reporte_stock_por_materia():
            ctk.CTkLabel(
                f2, text=f"{r['materia']}  —  disponibles {r['disponibles']} / total {r['total_ejemplares']}",
                anchor="w",
            ).pack(fill="x", padx=5, pady=3)

        f3 = ctk.CTkScrollableFrame(tab_socios)
        f3.pack(fill="both", expand=True, padx=5, pady=5)
        for r in db.reporte_socios_mas_activos():
            ctk.CTkLabel(f3, text=f"{r['socio']}  —  {r['prestamos_totales']} préstamos totales", anchor="w").pack(
                fill="x", padx=5, pady=3
            )

if __name__ == "__main__":
    ok, msg = db.test_connection()
    if not ok:
        print("No se pudo conectar a la base de datos:", msg)
        print("Revisá el archivo config.env")
    app = App()
    app.mainloop()
