import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import random
import copy
import sys
import reportlab.lib.pagesizes as pagesizes
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta absoluta al recurso, considerando si la app está
    empaquetada con PyInstaller (sys._MEIPASS) o ejecutándose desde el código fuente.
    """
    # cuando PyInstaller empaqueta, crea sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


BASE_DIR = resource_path("")


QUESTIONS_FILE = resource_path("questions.json")
SAVED_ORDER_FILE = resource_path("questions_saved_order.json")
LOGO_FILE = resource_path("univalle_logo.png")

pdf_title = "Cuestionario - Estado actual"

SAMPLE_QUESTIONS = [
    {"pregunta": "¿Cuál es la capital de Francia?",
     "opciones": ["París", "Londres", "Roma", "Berlín"], "respuesta": "París"},
    {"pregunta": "¿Cuál es el océano más grande del mundo?",
     "opciones": ["Atlántico", "Índico", "Pacífico", "Ártico"], "respuesta": "Pacífico"},
    {"pregunta": "¿Cuánto es 5 * 3?",
     "opciones": ["8", "15", "10", "20"], "respuesta": "15"}
]


def safe_show_error(title, msg):
    try:
        if tk._default_root is None:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title, msg)
            root.destroy()
        else:
            messagebox.showerror(title, msg)
    except Exception:
        print(f"ERROR: {title}: {msg}", file=sys.stderr)


def safe_show_info(title, msg):
    try:
        if tk._default_root is None:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(title, msg)
            root.destroy()
        else:
            messagebox.showinfo(title, msg)
    except Exception:
        print(f"INFO: {title}: {msg}")


def safe_show_warning(title, msg):
    try:
        if tk._default_root is None:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(title, msg)
            root.destroy()
        else:
            messagebox.showwarning(title, msg)
    except Exception:
        print(f"WARNING: {title}: {msg}")


def ensure_questions(path=QUESTIONS_FILE):
    if not os.path.exists(path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(SAMPLE_QUESTIONS, f, ensure_ascii=False, indent=2)
        except Exception as e:
            safe_show_error("Error", f"No se pudo crear {path}:\n{e}")


def load_questions(path=QUESTIONS_FILE):

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if not isinstance(raw, list):
            raise ValueError("El JSON debe contener una lista de preguntas")

        normalized = []
        for item in raw:
            if isinstance(item, dict):
                pregunta = item.get("pregunta") or item.get("question") or ""
                opciones = item.get("opciones") or item.get("options") or []
                respuesta = item.get("respuesta") or item.get("answer") or ""
                if not isinstance(opciones, list):
                    opciones = list(opciones) if opciones is not None else []
                if not pregunta or not isinstance(opciones, list) or len(opciones) < 2:
                    raise ValueError("Cada pregunta debe tener 'pregunta' (o 'question') y al menos 2 'opciones' (o 'options')")
                if not respuesta:
                    respuesta = opciones[0]
                normalized.append({
                    "pregunta": pregunta,
                    "opciones": opciones,
                    "respuesta": respuesta
                })
            else:
                raise ValueError("Formato inválido: cada elemento debe ser un objeto (dict)")
        return normalized

    except FileNotFoundError:
        safe_show_warning("Aviso", f"No se encontró {path}. Se creará un archivo de ejemplo.")
        ensure_questions(path)
        return load_questions(path)
    except Exception as e:
        safe_show_error("Error al cargar preguntas", str(e))
        return []


def save_questions_to_file(questions, path=QUESTIONS_FILE):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        safe_show_error("Error al guardar", str(e))
        return False


def export_single_pdf(questions, filepath, title="Cuestionario"):
    try:

        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, PageBreak
        from reportlab.lib.units import inch

        styles = getSampleStyleSheet()
        question_style = ParagraphStyle(
            'QuestionStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkblue
        )
        option_style = ParagraphStyle(
            'OptionStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leftIndent=20
        )
        answer_style = ParagraphStyle(
            'AnswerStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            textColor=colors.darkred
        )
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            alignment=1
        )

        def header_footer(cnv, doc):
            cnv.saveState()
            width, height = pagesizes.letter
            logo_path = os.path.join(BASE_DIR, "univalle_logo.png")
            try:
                cnv.drawImage(logo_path, 40, height - 90, width=70, height=70, preserveAspectRatio=True, mask='auto')
            except Exception:
                cnv.setFont('Helvetica-Oblique', 8)
                cnv.drawString(40, height - 40, "[Logo no encontrado]")

            header_text = (
                "UNIVERSIDAD DEL VALLE SEDE YUMBO\n"
                "TECNOLOGÍA EN DESARROLLO DE SOFTWARE\n"
                "Matemáticas Discretas II\n"
                "Código: 750005C - gustavo.neira@correounivalle.edu.co Docente: Gustavo Neira"
            )
            cnv.setFont("Helvetica-Bold", 9)
            text_y = height - 45
            for line in header_text.split("\n"):
                cnv.drawCentredString(width / 2 + 40, text_y, line.strip())
                text_y -= 12

            cnv.setStrokeColor(colors.black)
            cnv.setLineWidth(0.8)
            cnv.line(40, height - 100, width - 40, height - 100)
            cnv.setFont("Helvetica", 8)
            cnv.drawRightString(width - 40, 25, f"Página {doc.page}")
            cnv.restoreState()

        doc = SimpleDocTemplate(
            filepath,
            pagesize=pagesizes.letter,
            rightMargin=40, leftMargin=40,
            topMargin=110, bottomMargin=40
        )

        flow = []
        flow.append(Paragraph(title, title_style))
        flow.append(Spacer(1, 12))

        for idx, q in enumerate(questions, start=1):
            flow.append(Paragraph(f"{idx}. {q['pregunta']}", question_style))
            for opt_idx, opt in enumerate(q['opciones'], start=1):
                flow.append(Paragraph(f"{chr(64+opt_idx)}. {opt}", option_style))
            flow.append(Spacer(1, 6))

        flow.append(PageBreak())

        flow.append(Paragraph("Claves de Respuestas", styles['Heading1']))
        flow.append(Spacer(1, 12))
        for idx, q in enumerate(questions, start=1):
            try:
                pos = q['opciones'].index(q['respuesta'])
                letter = chr(65 + pos)
            except Exception:
                letter = "N/A"
            flow.append(Paragraph(f"{idx}. {letter} — {q['respuesta']}", answer_style))
            flow.append(Spacer(1, 4))

        doc.build(flow, onFirstPage=header_footer, onLaterPages=header_footer)
        return True
    except Exception as e:
        safe_show_error("Error al exportar PDF", str(e))
        return False


def build_versions_pdf(versions_list, filepath, title="Examen - Múltiples versiones"):
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, PageBreak
        from reportlab.lib.units import inch

        styles = getSampleStyleSheet()
        question_style = ParagraphStyle(
            'QuestionStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkblue
        )
        option_style = ParagraphStyle(
            'OptionStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leftIndent=20
        )
        answer_style = ParagraphStyle(
            'AnswerStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            textColor=colors.darkred
        )
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            alignment=1  # centered
        )

        def header_footer(cnv, doc):
            cnv.saveState()
            width, height = pagesizes.letter
            logo_path = os.path.join(BASE_DIR, "univalle_logo.png")
            try:
                cnv.drawImage(logo_path, 40, height - 90, width=70, height=70, preserveAspectRatio=True, mask='auto')
            except Exception:
                cnv.setFont('Helvetica-Oblique', 8)
                cnv.drawString(40, height - 40, "[Logo no encontrado]")

            header_text = (
                "UNIVERSIDAD DEL VALLE SEDE YUMBO\n"
                "TECNOLOGÍA EN DESARROLLO DE SOFTWARE\n"
                "Matemáticas Discretas II\n"
                "Código: 750005C - gustavo.neira@correounivalle.edu.co Docente: Gustavo Neira"
            )
            cnv.setFont("Helvetica-Bold", 9)
            text_y = height - 45
            for line in header_text.split("\n"):
                cnv.drawCentredString(width / 2 + 40, text_y, line.strip())
                text_y -= 12

            cnv.setStrokeColor(colors.black)
            cnv.setLineWidth(0.8)
            cnv.line(40, height - 100, width - 40, height - 100)
            cnv.setFont("Helvetica", 8)
            cnv.drawRightString(width - 40, 25, f"Página {doc.page}")
            cnv.restoreState()

        doc = SimpleDocTemplate(
            filepath,
            pagesize=pagesizes.letter,
            rightMargin=40, leftMargin=40,
            topMargin=110, bottomMargin=40
        )

        flow = []

        flow.append(Paragraph(title, title_style))
        flow.append(Spacer(1, 12))

        for ver_num, questions in versions_list:
            flow.append(Paragraph(f"Versión {ver_num}", styles['Heading2']))
            flow.append(Spacer(1, 8))
            for idx, q in enumerate(questions, start=1):
                flow.append(Paragraph(f"{idx}. {q['pregunta']}", question_style))
                for opt_idx, opt in enumerate(q['opciones'], start=1):
                    flow.append(Paragraph(f"{chr(64+opt_idx)}. {opt}", option_style))
                flow.append(Spacer(1, 6))

            flow.append(PageBreak())

        flow.append(Paragraph("Claves de respuestas", styles['Heading1']))
        flow.append(Spacer(1, 12))

        for ver_num, questions in versions_list:
            flow.append(Paragraph(f"Clave - Versión {ver_num}", styles['Heading2']))
            flow.append(Spacer(1, 8))
            for idx, q in enumerate(questions, start=1):
                try:
                    pos = q['opciones'].index(q['respuesta'])
                    letter = chr(65 + pos)
                except Exception:
                    letter = "N/A"
                flow.append(Paragraph(f"{idx}. {letter} — {q.get('respuesta','')}", answer_style))
            flow.append(PageBreak())

        doc.build(flow, onFirstPage=header_footer, onLaterPages=header_footer)
        return True
    except Exception as e:
        safe_show_error("Error al generar PDF de versiones", str(e))
        return False


def cambiar_titulo_pdf():
    global pdf_title
    nuevo_titulo = simpledialog.askstring(
        "Cambiar título del PDF",
        "Ingrese el nuevo título que desea colocar en el PDF:",
        initialvalue=pdf_title
    )
    if nuevo_titulo and nuevo_titulo.strip():
        pdf_title = nuevo_titulo.strip()
        safe_show_info("Título actualizado", f"El nuevo título será:\n\n{pdf_title}")
    else:
        safe_show_warning("Sin cambios", "No se modificó el título.")


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiz Interactivo - Versión Final")
        self.geometry("980x640")
        ensure_questions()
        self.questions = load_questions()
        self.current_index = 0

        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(top, text="Mezclar preguntas", command=self.shuffle_questions).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Mezclar opciones", command=self.shuffle_options).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Exportar PDF (actual)", command=self.export_current_pdf).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Generar versiones (PDF)", command=self.generate_versions_ui).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Guardar orden actual", command=self.save_current_order).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Recargar desde JSON", command=self.reload_from_file).pack(side=tk.LEFT, padx=4)

        ttk.Button(top, text="Cambiar título del PDF", command=cambiar_titulo_pdf).pack(side=tk.LEFT, padx=8)

        ttk.Button(top, text="Añadir pregunta", command=self.add_question_ui).pack(side=tk.RIGHT, padx=6)
        ttk.Button(top, text="Editar pregunta", command=self.edit_question_ui).pack(side=tk.RIGHT, padx=6)
        ttk.Button(top, text="Eliminar pregunta", command=self.delete_question_ui).pack(side=tk.RIGHT, padx=6)

        left = ttk.Frame(self, width=320)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        ttk.Label(left, text="Preguntas:", font=(None, 11, 'bold')).pack(anchor='w')
        self.lb = tk.Listbox(left, width=46, height=34)
        self.lb.pack(fill=tk.Y, expand=True)
        self.lb.bind('<<ListboxSelect>>', self.on_list_select)
        self.refresh_listbox()

        right = ttk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.question_label = ttk.Label(right, text="", wraplength=580, font=(None, 13))
        self.question_label.pack(anchor='w', pady=(0,10))
        self.options_container = ttk.Frame(right)
        self.options_container.pack(anchor='w')

        nav = ttk.Frame(right)
        nav.pack(fill=tk.X, pady=12)
        ttk.Button(nav, text="Anterior", command=self.prev_question).pack(side=tk.LEFT, padx=4)
        ttk.Button(nav, text="Siguiente", command=self.next_question).pack(side=tk.LEFT, padx=4)

        if self.questions:
            self.show_question(0)

    def refresh_listbox(self):
        self.lb.delete(0, tk.END)
        for i, q in enumerate(self.questions, start=1):
            short = q['pregunta'][:72].replace('\\n',' ')
            self.lb.insert(tk.END, f"{i}. {short}")

    def on_list_select(self, event):
        sel = self.lb.curselection()
        if sel:
            self.show_question(sel[0])

    def show_question(self, idx):
        if idx < 0 or idx >= len(self.questions):
            return
        self.current_index = idx
        q = self.questions[idx]
        self.question_label.config(text=f"{idx+1}. {q['pregunta']}")
        for child in self.options_container.winfo_children():
            child.destroy()
        self.selected_var = tk.StringVar(value="")
        for opt in q['opciones']:
            rb = ttk.Radiobutton(self.options_container, text=opt, variable=self.selected_var, value=opt)
            rb.pack(anchor='w', pady=2)
        self.lb.selection_clear(0, tk.END)
        self.lb.selection_set(idx)
        self.lb.see(idx)

    def prev_question(self):
        if self.current_index > 0:
            self.show_question(self.current_index - 1)

    def next_question(self):
        if self.current_index < len(self.questions) - 1:
            self.show_question(self.current_index + 1)

    def shuffle_questions(self):
        if not self.questions:
            return
        random.shuffle(self.questions)
        self.refresh_listbox()
        self.show_question(0)
        safe_show_info("Hecho", "Orden de preguntas aleatorizado y GUI actualizada.")

    def shuffle_options(self):
        if not self.questions:
            return
        for q in self.questions:
            random.shuffle(q['opciones'])
        idx = min(self.current_index, len(self.questions)-1)
        self.refresh_listbox()
        self.show_question(idx)
        safe_show_info("Hecho", "Opciones barajadas para todas las preguntas y GUI actualizada.")

    def reload_from_file(self):
        self.questions = load_questions()
        self.refresh_listbox()
        if self.questions:
            self.show_question(0)
        safe_show_info("Recargado", "Preguntas recargadas desde questions.json")

    def save_current_order(self):
        try:
            with open(SAVED_ORDER_FILE, "w", encoding="utf-8") as f:
                json.dump(self.questions, f, ensure_ascii=False, indent=2)
            safe_show_info("Guardado", f"Orden actual guardado en: {SAVED_ORDER_FILE}")
        except Exception as e:
            safe_show_error("Error al guardar", str(e))

    def add_question_ui(self):
        dlg = QuestionEditor(self, title="Añadir pregunta")
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            self.questions.append(dlg.result)
            self.refresh_listbox()
            self.show_question(len(self.questions)-1)
            safe_show_info("Añadido", "Pregunta añadida correctamente.")

    def edit_question_ui(self):
        if not self.questions:
            return
        idx = self.current_index
        dlg = QuestionEditor(self, title="Editar pregunta", data=self.questions[idx])
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            self.questions[idx] = dlg.result
            self.refresh_listbox()
            self.show_question(idx)
            safe_show_info("Editado", "Pregunta editada correctamente.")

    def delete_question_ui(self):
        if not self.questions:
            return
        idx = self.current_index
        q = self.questions[idx]
        if messagebox.askyesno("Confirmar eliminación", f"¿Eliminar la pregunta {idx+1}?\n{q['pregunta']}"):
            del self.questions[idx]
            self.refresh_listbox()
            if self.questions:
                new_idx = min(idx, len(self.questions)-1)
                self.show_question(new_idx)
            else:
                self.question_label.config(text="")
                for child in self.options_container.winfo_children():
                    child.destroy()
            safe_show_info("Eliminado", "Pregunta eliminada.")

    def export_current_pdf(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files","*.pdf")], initialfile="quiz_export.pdf")
        if not path:
            return
        ok = export_single_pdf(self.questions, path, title=pdf_title)
        if ok:
            safe_show_info("Exportado", f"PDF exportado en:\n{path}")

    def generate_versions_ui(self):
        n = simpledialog.askinteger("Generar versiones", "¿Cuántas versiones quieres generar?", minvalue=1, maxvalue=200)
        if not n:
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files","*.pdf")], initialfile="versions_quiz.pdf")
        if not path:
            return
        versions = []
        for i in range(1, n+1):
            qcopy = copy.deepcopy(self.questions)
            random.shuffle(qcopy)
            for q in qcopy:
                random.shuffle(q['opciones'])
            versions.append((i, qcopy))
        ok = build_versions_pdf(versions, path, title=pdf_title)
        if ok:
            safe_show_info("Generado", f"PDF con {n} versiones generado en:\n{path}")


class QuestionEditor(tk.Toplevel):
    def __init__(self, parent, title="Pregunta", data=None):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.result = None

        ttk.Label(self, text="Pregunta:").grid(row=0, column=0, sticky='w', padx=6, pady=6)
        self.entry_q = tk.Text(self, width=70, height=4)
        self.entry_q.grid(row=0, column=1, columnspan=3, padx=6, pady=6)

        self.option_vars = []
        for i in range(6):
            ttk.Label(self, text=f"Opción {i+1}:").grid(row=1+i, column=0, sticky='w', padx=6)
            var = tk.StringVar()
            ttk.Entry(self, textvariable=var, width=60).grid(row=1+i, column=1, columnspan=3, padx=6, pady=2, sticky='w')
            self.option_vars.append(var)

        ttk.Label(self, text="Respuesta correcta (copiar exactamente una de las opciones):").grid(row=7, column=0, columnspan=4, sticky='w', padx=6, pady=(8,0))
        self.correct_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.correct_var, width=70).grid(row=8, column=0, columnspan=4, padx=6, pady=6)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=9, column=0, columnspan=4, pady=8)
        ttk.Button(btn_frame, text="Cancelar", command=self.cancel).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btn_frame, text="Guardar", command=self.on_save).pack(side=tk.RIGHT, padx=6)

        if data:
            self.entry_q.insert('1.0', data.get('pregunta',''))
            for i, opt in enumerate(data.get('opciones', [])):
                if i < len(self.option_vars):
                    self.option_vars[i].set(opt)
            self.correct_var.set(data.get('respuesta',''))

        self.bind('<Return>', lambda e: self.on_save())
        self.bind('<Escape>', lambda e: self.cancel())

        self.update_idletasks()
        w = self.winfo_width(); h = self.winfo_height()
        ws = self.winfo_screenwidth(); hs = self.winfo_screenheight()
        x = (ws//2) - (w//2); y = (hs//2) - (h//2)
        self.geometry(f'+{x}+{y}')

    def on_save(self):
        pregunta = self.entry_q.get('1.0', 'end').strip()
        opciones = [v.get().strip() for v in self.option_vars if v.get().strip()]
        respuesta = self.correct_var.get().strip()
        if not pregunta:
            safe_show_error("Error", "La pregunta no puede estar vacía.")
            return
        if len(opciones) < 2:
            safe_show_error("Error", "Debes proporcionar al menos 2 opciones.")
            return
        if respuesta not in opciones:
            safe_show_error("Error", "La respuesta correcta debe ser exactamente igual a una de las opciones.")
            return
        self.result = {'pregunta': pregunta, 'opciones': opciones, 'respuesta': respuesta}
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


if __name__ == '__main__':
    app = QuizApp()
    app.mainloop()
