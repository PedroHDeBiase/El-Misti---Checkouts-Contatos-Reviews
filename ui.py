import sys
from datetime import date, timedelta
import pandas as pd
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QFont, QKeySequence, QShortcut, QIcon, QPixmap
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QProgressBar, QLabel, QTabWidget, QComboBox, QTableView, QHeaderView, QMainWindow,
    QMessageBox, QListView, QCalendarWidget, QDialog, QDialogButtonBox
)
import ctypes
import main as main_script
import json
import os

# THREAD: Worker -------------------------------------------------------

class WorkerSignals(QObject):
    progress = Signal(str)
    finished = Signal()

class FunctionWorker(QThread):
    def __init__(self, func):
        super().__init__()
        self.func = func
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.func()
        except Exception as e:
            self.signals.progress.emit(f"Erro: {e}")
        finally:
            self.signals.finished.emit()

# SAVING HELPER --------------------------------------------------------

def save_reviews_to_file(filename, sections_dict, reviews_dict):
    try:
        # Read existing file to preserve structure
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Create new structure if file doesn't exist
            data = {
                "Booking": {"Reviews": [], "Soma": 0.0, "Quantidade": 0, "Media": "0.00"},
                "Hostel World": {"Reviews": [], "Soma": 0.0, "Quantidade": 0, "Media": "0.00"},
                "Google": {"Reviews": [], "Soma": 0.0, "Quantidade": 0, "Media": "0.00"}
            }
        
        # Update reviews for each platform
        platform_mapping = {
            'BOOKING': 'Booking',
            'HOSTEL WORLD': 'Hostel World',
            'GOOGLE': 'Google'
        }
        
        for internal_key, json_key in platform_mapping.items():
            if internal_key in reviews_dict:
                # Update the reviews list
                data[json_key]['Reviews'] = reviews_dict[internal_key]
                
                # Recalculate statistics for platforms with numeric ratings
                if internal_key in ['BOOKING', 'HOSTEL WORLD', 'GOOGLE']:
                    reviews = reviews_dict[internal_key]
                    valid_ratings = []
                    
                    for review in reviews:
                        nota = review.get('Nota', '')
                        if nota and nota != '':
                            try:
                                # Handle both "10" and "9,0" formats
                                rating = float(str(nota).replace(',', '.'))
                                valid_ratings.append(rating)
                            except (ValueError, TypeError):
                                continue
                    
                    if valid_ratings:
                        soma = sum(valid_ratings)
                        quantidade = len(valid_ratings)
                        media = soma / quantidade
                        
                        data[json_key]['Soma'] = round(soma, 2)
                        data[json_key]['Quantidade'] = quantidade
                        data[json_key]['Media'] = f"{media:.2f}"
                    else:
                        data[json_key]['Soma'] = 0.0
                        data[json_key]['Quantidade'] = 0
                        data[json_key]['Media'] = "0.00"
        
        # Write back to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        return True
    
    except Exception as e:
        print(f"Error saving reviews: {e}")
        return False

# TABLE HELPERS --------------------------------------------------------

def pandas_model(df):
    model = QStandardItemModel()
    model.setColumnCount(len(df.columns))
    model.setHorizontalHeaderLabels(df.columns.astype(str).tolist())

    for r in range(len(df)):
        for c in range(len(df.columns)):
            raw = df.iat[r, c]
            val = "" if raw is None or pd.isna(raw) or raw == 'None' else str(raw)

            item = QStandardItem(val)
            item.setEditable(False)
            model.setItem(r, c, item)
    return model

def copy_table_selection(table_view):
    selection = table_view.selectionModel()
    if not selection.hasSelection():
        return
    
    indexes = sorted(selection.selectedIndexes(), key=lambda i: (i.row(), i.column()))
    rows_data = {}

    for idx in indexes:
        rows_data.setdefault(idx.row(), {})[idx.column()] = idx.data() or ""

    lines = []
    for row in sorted(rows_data.keys()):
        cols = rows_data[row]
        minc, maxc = min(cols), max(cols)
        line = "\t".join(cols.get(c, "") for c in range(minc, maxc+1))
        lines.append(line)

    QApplication.clipboard().setText("\n".join(lines))
    table_view.clearSelection()
    return len(indexes)

# CALENDAR DIALOG --------------------------------------------------
def ultima_sexta():
    hoje = date.today()
    dia_da_semana = hoje.weekday()

    dias_atras = (dia_da_semana - 4 + 7) % 7
    
    if dias_atras == 0:
        dias_atras = 7

    sexta = hoje - timedelta(days=dias_atras)
    return sexta

class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Período de Reviews")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Data inicial
        layout.addWidget(QLabel("Data Inicial:"))
        self.cal_inicio = QCalendarWidget()
        self.cal_inicio.setGridVisible(True)
        self.cal_inicio.setMaximumDate(date.today())
        self.apply_calendar_style(self.cal_inicio)
        layout.addWidget(self.cal_inicio)
        
        # Data final
        layout.addWidget(QLabel("Data Final:"))
        self.cal_fim = QCalendarWidget()
        self.cal_fim.setGridVisible(True)
        self.cal_fim.setMaximumDate(date.today())
        self.cal_fim.setSelectedDate(date.today())
        self.apply_calendar_style(self.cal_fim)
        layout.addWidget(self.cal_fim)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Define data inicial como 7 dias atrás
        #semana_atras = date.today() - timedelta(days=7)
        semana_atras = ultima_sexta()
        hoje = date.today()
        if hoje.day < 8:
            semana_atras = hoje - timedelta(hoje.day-1)
        self.cal_inicio.setSelectedDate(semana_atras)
    
    def apply_calendar_style(self, calendar):
        """Aplica estilo personalizado ao calendário."""
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)

        weekend_format = calendar.weekdayTextFormat(Qt.Saturday)
        weekend_format.setForeground(Qt.white)
        calendar.setWeekdayTextFormat(Qt.Saturday, weekend_format)
        calendar.setWeekdayTextFormat(Qt.Sunday, weekend_format)
    
    def get_dates(self):
        inicio = self.cal_inicio.selectedDate().toPython()
        fim = self.cal_fim.selectedDate().toPython()
        return inicio, fim

# MAIN WINDOW ----------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("El Misti - Reviews & Checkout")
        self.setGeometry(100, 100, 1200, 800)

        # Windows icon fix
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "mycompany.myproduct.subproduct.version"
        )
        ico_path = "./_internal/logo-ipanema.ico"
        self.setWindowIcon(QIcon(ico_path))

        cw = QWidget()
        self.setCentralWidget(cw)
        layout = QVBoxLayout(cw)

        # Logo ----------------------------------------------------------
        self.image_label = QLabel()
        self.image_label.setPixmap(QPixmap(ico_path))

        # Header ----------------------------------------------------------
        self.hotels = [
            "El Misti Hostel Ipanema",
            "El Misti Suites Copacabana",
            "El Misti Coliving Obelisco",
            "El Misti Centro Buenos Aires",
            "El Misti Maipu Buenos Aires"
        ]

        self.cmb_hotels = QComboBox()
        self.cmb_hotels.addItems(self.hotels)
        self.cmb_hotels.setCurrentIndex(0)

        self.cmb_hotels.setView(QListView())

        self.cmb_hotels.view().setFont(QFont("Arial", 13))

        self.cmb_hotels.view().setSpacing(4)

        self.cmb_hotels.setStyleSheet("""
            QComboBox {
                background-color: transparent;
                color: #f0f0f0;
                border: none;
                padding: 0px;
                font-size: 35px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                width: 0px;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #0078d7;
                padding: 4px;
            }
            QComboBox:hover {
                background-color: #2d2d2d;
                color: #ffffff;
                text-decoration: underline;
            }
        """)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.image_label)
        header_layout.addWidget(self.cmb_hotels)
        header_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(header_layout)

        self.cmb_hotels.currentTextChanged.connect(self.on_hotel_changed)
        main_script.hotel_name_change(self.cmb_hotels.currentText())

        # Dates ---------------------------------------------------------
        self.data_inicio = date.today() - timedelta(days=7)
        self.data_fim = date.today()

        date_container = QHBoxLayout()
        
        self.lbl_date = QLabel()
        self.lbl_date.setFont(QFont("Arial", 10))
        self.lbl_date.setCursor(Qt.PointingHandCursor)  # Cursor de mão ao passar
        self.lbl_date.setStyleSheet("""
            QLabel {
                color: #f0f0f0;
                padding: 8px;
                border-radius: 6px;
            }
            QLabel:hover {
                background-color: #2d2d2d;
                text-decoration: underline;
            }
        """)
        self.update_date_label()
        self.lbl_date.mousePressEvent = self.open_date_picker

        date_container.addStretch()
        date_container.addWidget(self.lbl_date)
        date_container.addStretch()
        layout.addLayout(date_container)

        # Buttons -------------------------------------------------------
        btn_row = QHBoxLayout()
        self.btn_checkins = QPushButton("📅 Obter Check-ins")
        self.btn_contatos = QPushButton("📞 Pegar Contatos")
        self.btn_checkouts = QPushButton("📅 Obter Checkouts")
        self.btn_scraping = QPushButton("🌐 Pegar Reviews")
        self.btn_copy = QPushButton("📋 Copiar Seleção")
        self.btn_delete = QPushButton("🗑️ Deletar Review")

        for b in (self.btn_checkouts, self.btn_scraping, self.btn_copy, self.btn_delete):
            b.setMinimumWidth(150)
            b.setMaximumWidth(150)

        btn_row.addStretch()
        #btn_row.addWidget(self.btn_checkins)
        #btn_row.addWidget(self.btn_contatos)
        btn_row.addWidget(self.btn_checkouts)
        btn_row.addWidget(self.btn_scraping)
        btn_row.addWidget(self.btn_copy)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Progress + Log -----------------------------------------------
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(50)
        layout.addWidget(self.log)

        # Tabs ----------------------------------------------------------
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ----------- CHECK-INS TAB ----------
        t_checkins = QWidget()
        lc = QVBoxLayout(t_checkins)
        
        self.table_checkins = QTableView()
        self.table_checkins.setSelectionMode(QTableView.ExtendedSelection)
        self.table_checkins.setEditTriggers(QTableView.NoEditTriggers)
        lc.addWidget(self.table_checkins)

        shortcut_checkins = QShortcut(QKeySequence.Copy, self.table_checkins)
        shortcut_checkins.activated.connect(self.copy_checkins_selection)

        # ----------- REVIEWS TAB ----------
        t_reviews = QWidget()
        lr = QVBoxLayout(t_reviews)
        hl = QHBoxLayout()

        hl.addWidget(QLabel("Plataforma:"))
        self.cmb = QComboBox()
        self.platform_display_names = {
            "BOOKING": "Booking",
            "HOSTEL WORLD": "Hostel World",
            "GOOGLE": "Google",
            "TRIP ADVISOR": "Trip Advisor"
        }
        self.cmb.addItems(["Booking", "Hostel World", "Google", "Trip Advisor"])
        hl.addWidget(self.cmb)

        hl.addStretch()

        self.lbl_qtd = QLabel("Qtd: —")
        self.lbl_soma = QLabel("Soma: —")
        self.lbl_media = QLabel("Média: —")
        for lbl in (self.lbl_qtd, self.lbl_soma, self.lbl_media):
            lbl.setStyleSheet("color: #bbbbbb; font-size: 14px; padding-left: 6px;")

        hl.addWidget(self.lbl_qtd)
        hl.addWidget(self.lbl_soma)
        hl.addWidget(self.lbl_media)

        self.table_reviews = QTableView()
        self.table_reviews.setSelectionMode(QTableView.ExtendedSelection)
        self.table_reviews.setSelectionBehavior(QTableView.SelectItems)
        self.table_reviews.setEditTriggers(QTableView.NoEditTriggers)
        lr.addLayout(hl)
        lr.addWidget(self.table_reviews)

        shortcut_reviews = QShortcut(QKeySequence.Copy, self.table_reviews)
        shortcut_reviews.activated.connect(self.copy_reviews_selection)
        
        # Atalho para deletar com tecla Delete
        shortcut_delete = QShortcut(QKeySequence.Delete, self.table_reviews)
        shortcut_delete.activated.connect(self.delete_selected_reviews)

        # ----------- SUMMARY TAB ----------
        t_summary = QWidget()
        ls = QVBoxLayout(t_summary)
        self.resumo_layout = QHBoxLayout()
        ls.addLayout(self.resumo_layout)

        self.colors = {
            "BOOKING": "#0078d7",
            "HOSTEL WORLD": "#e67e22",
            "GOOGLE": "#f1c40f",
            "TRIP ADVISOR": "#2ecc71"
        }

        self.tables = {}
        for plat in ["BOOKING", "HOSTEL WORLD", "GOOGLE", "TRIP ADVISOR"]:
            col = QVBoxLayout()
            display_name = self.platform_display_names[plat]
            bar = QLabel(f"  {display_name}")
            bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            bar.setStyleSheet(f"""
                background-color: {self.colors[plat]};
                color: black;
                font-weight: bold;
                padding: 6px 10px;
                border-radius: 6px;
            """)
            table = QTableView()
            table.setSelectionMode(QTableView.ExtendedSelection)
            table.setEditTriggers(QTableView.NoEditTriggers)
            table.verticalHeader().hide()
            table.horizontalHeader().hide()
            table.setMinimumWidth(260)
            col.addWidget(bar)
            col.addWidget(table)
            self.resumo_layout.addLayout(col)
            self.tables[plat] = table

        self.shortcut_summary = QShortcut(QKeySequence.Copy, t_summary)
        self.shortcut_summary.activated.connect(self.copy_from_summary_tables)

        self.lbl_reservas = QLabel()
        self.lbl_reservas.setAlignment(Qt.AlignLeft)
        ls.addWidget(self.lbl_reservas)

        #self.tabs.addTab(t_checkins, "Check-ins Futuros")
        self.tabs.addTab(t_summary, "Resumo Plataformas")
        self.tabs.addTab(t_reviews, "Reviews")

        # BUTTON SIGNALS
        self.btn_checkins.clicked.connect(self.run_checkins)
        self.btn_contatos.clicked.connect(self.run_contatos)
        self.btn_checkouts.clicked.connect(self.run_checkouts)
        self.btn_scraping.clicked.connect(self.run_scraping)
        self.btn_copy.clicked.connect(self.copy_active_table)
        self.btn_delete.clicked.connect(self.delete_selected_reviews)
        self.cmb.currentTextChanged.connect(self.reload_reviews)

        # INITIAL LOAD
        self.reload()

        # THEME
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1e1e1e; color: #f0f0f0; }
            QPushButton {
                background-color: #2d2d2d; color: #f0f0f0;
                border: 1px solid #3c3c3c; border-radius: 8px; padding: 8px 14px;
            }
            QPushButton:hover { background-color: #3a3a3a; }
            QProgressBar {
                border: 1px solid #3c3c3c; border-radius: 7px;
                background: #2b2b2b; color: #ffffff;
            }
            QProgressBar::chunk { background-color: #0078d7; border-radius: 7px; }
            QTextEdit {
                background-color: #2a2a2a; color: #dddddd;
                border: 1px solid #3c3c3c; border-radius: 6px;
            }
            QTableView {
                gridline-color: #444;
                selection-background-color: #0078d7;
                selection-color: #ffffff;
                alternate-background-color: #252525;
            }
        """)

    # ------------------------------
    # Filenames (hotel-aware)
    # ------------------------------
    def contatos_filename(self):
        hotel = self.cmb_hotels.currentText().replace(":", "").replace("/", "")
        #today = date.today().strftime("%Y-%m-%d")
        today = self.data_fim

        return f"./_internal/0_jsons/Contatos - {hotel} - {today}.json"

    def read_contatos_file(self):
        contatos = {}
        if os.path.exists(self.contatos_filename()):
            with open(self.contatos_filename(), 'r', encoding="utf-8") as f:
                contatos = json.load(f)
        return contatos

    def response_filename(self):
        hotel = self.cmb_hotels.currentText().replace(":", "").replace("/", "")
        #today = date.today().strftime("%Y-%m-%d")
        today = self.data_fim

        return f"./_internal/0_jsons/Reviews - {hotel} - {today}.json"

    def checkouts_filename(self):
        hotel = self.cmb_hotels.currentText().replace(":", "").replace("/", "")
        #today = date.today().strftime("%Y-%m-%d")
        today = self.data_fim

        return f"./_internal/0_jsons/Checkouts - {hotel} - {today}.json"

    def read_response_file(self):
        reviews = {}
        if os.path.exists(self.response_filename()):
            with open(self.response_filename(), 'r', encoding="utf-8") as f:
                reviews = json.load(f)
        return reviews

    # ------------------------------
    # Logging & copy helpers
    # ------------------------------
    def log_msg(self, msg):
        self.log.append(msg)

    def copy_active_table(self):
        current_tab = self.tabs.currentIndex()

        # check-ins tab
        if current_tab == 0:
            count = copy_table_selection(self.table_checkins)
            if count:
                self.log_msg(f"✓ {count} célula(s) copiada(s) da tabela de check-ins")
            else:
                self.log_msg("⚠ Nenhuma célula selecionada na tabela de check-ins")
        
        # summary tab
        if current_tab == 0:
            total_copied = 0
            for plat in ["BOOKING", "HOSTEL WORLD", "GOOGLE", "TRIP ADVISOR"]:
                table = self.tables[plat]
                selection = table.selectionModel()
                if selection and selection.hasSelection():
                    count = copy_table_selection(table)
                    if count:
                        total_copied += count
                        display_name = self.platform_display_names[plat]
                        self.log_msg(f"✓ {count} célula(s) copiada(s) de {display_name}")
                        return
            if total_copied == 0:
                self.log_msg("⚠ Nenhuma célula selecionada nas tabelas do resumo")
        
        # reviews tab
        elif current_tab == 1:
            count = copy_table_selection(self.table_reviews)
            if count:
                self.log_msg(f"✓ {count} célula(s) copiada(s) da tabela de reviews")
            else:
                self.log_msg("⚠ Nenhuma célula selecionada na tabela de reviews")

    def copy_checkins_selection(self):
        count = copy_table_selection(self.table_checkins)
        if count:
            self.log_msg(f"✓ {count} célula(s) copiada(s) para a área de transferência")
        else:
            self.log_msg("⚠ Nenhuma célula selecionada")

    def copy_reviews_selection(self):
        count = copy_table_selection(self.table_reviews)
        if count:
            self.log_msg(f"✓ {count} célula(s) copiada(s) para a área de transferência")
        else:
            self.log_msg("⚠ Nenhuma célula selecionada")

    def copy_from_summary_tables(self):
        for plat in ["BOOKING", "HOSTEL WORLD", "GOOGLE", "TRIP ADVISOR"]:
            table = self.tables[plat]
            selection = table.selectionModel()
            if selection and selection.hasSelection():
                count = copy_table_selection(table)
                if count:
                    display_name = self.platform_display_names[plat]
                    self.log_msg(f"✓ {count} célula(s) copiada(s) de {display_name}")
                return
        self.log_msg("⚠ Nenhuma célula selecionada no resumo")

    # ------------------------------
    # Delete reviews
    # ------------------------------
    def pandas_model_with_checkbox(self, df):
        model = QStandardItemModel()

        # Apenas 1 coluna de checkbox + colunas originais do dataframe
        model.setColumnCount(len(df.columns) + 1)

        headers = [""] + df.columns.astype(str).tolist()   # ← sem nome no checkbox
        model.setHorizontalHeaderLabels(headers)

        for r in range(len(df)):
            # Checkbox
            check_item = QStandardItem()
            check_item.setCheckable(True)
            check_item.setCheckState(Qt.Unchecked)
            check_item.setEditable(False)
            model.setItem(r, 0, check_item)

            # Dados normais
            for c in range(len(df.columns)):
                raw = df.iat[r, c]
                val = "" if raw is None or pd.isna(raw) else str(raw)
                item = QStandardItem(val)
                item.setEditable(False)
                model.setItem(r, c + 1, item)

        return model

    def delete_selected_reviews(self):
        """Deleta apenas as linhas marcadas no checkbox (coluna 0)."""
        model = self.table_reviews.model()
        if not model:
            return

        rows_to_delete = []

        # Verificar checkboxes
        for row in range(model.rowCount()):
            item = model.item(row, 0)  # coluna do checkbox
            if item and item.checkState() == Qt.Checked:
                rows_to_delete.append(row)

        if not rows_to_delete:
            self.log_msg("⚠ Nenhuma linha marcada para deletar (use o checkbox)")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Deleção",
            f"Tem certeza que deseja deletar {len(rows_to_delete)} review(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Plataforma atual
        display_name = self.cmb.currentText()
        plat = self.get_platform_key(display_name)

        # Deleta do dicionário (de trás pra frente)
        for row in sorted(rows_to_delete, reverse=True):
            if row < len(self.reviews[plat]):
                del self.reviews[plat][row]

        # Salva alterações
        save_reviews_to_file(self.response_filename(), self.sections, self.reviews)

        # Recarrega
        self.reload()

        self.log_msg(f"✓ {len(rows_to_delete)} review(s) deletada(s) com sucesso")

    # ------------------------------
    # Run tasks (threaded)
    # ------------------------------
    def run_checkins(self):
        self._run(main_script.get_hospedes, "Check-ins")

    def run_contatos(self):
        self._run(main_script.ler_futuros_hospedes, "Contatos")

    def run_checkouts(self):
        # this assumes your main_script.get_check_outs writes the hotel-named file on its own
        self._run(main_script.get_check_outs, "Check-outs")

    def run_scraping(self):
        # likewise for playwright
        self._run(main_script.playwright, "Reviews")

    def _run(self, func, task_name):
        self.btn_checkins.setEnabled(False)
        self.btn_contatos.setEnabled(False)
        self.btn_checkouts.setEnabled(False)
        self.btn_scraping.setEnabled(False)
        self.progress.show()
        self.log.clear()
        self.log_msg(f"Pegando {task_name}...")

        self.worker = FunctionWorker(func)
        self.worker.signals.progress.connect(self.log_msg)
        self.worker.signals.finished.connect(self.on_done)
        self.worker.start()

    def on_done(self):
        self.log_msg("\n✓ Concluido com sucesso!")
        self.btn_checkins.setEnabled(True)
        self.btn_contatos.setEnabled(True)
        self.btn_checkouts.setEnabled(True)
        self.btn_scraping.setEnabled(True)
        self.progress.hide()
        self.reload()

    # ------------------------------
    # Reload data for current hotel
    # ------------------------------
    def on_hotel_changed(self):
        main_script.hotel_name_change(self.cmb_hotels.currentText())   
        self.reload()

    def reload(self):
        contatos = self.read_contatos_file()
        if contatos != {}:
            self.checkins_data = contatos['data']
        else:
            self.checkins_data = []

        self.sections = self.read_response_file()
        if self.sections != {}:
            self.reviews = {
                'BOOKING': self.sections['Booking']['Reviews'],
                'HOSTEL WORLD': self.sections['Hostel World']['Reviews'],
                'GOOGLE': self.sections['Google']['Reviews'],
                'TRIP ADVISOR': []
            }
            self.summaries = {
                'BOOKING': (self.sections['Booking']['Soma'], self.sections['Booking']['Quantidade'], self.sections['Booking']['Media']),
                'HOSTEL WORLD': (self.sections['Hostel World']['Soma'], self.sections['Hostel World']['Quantidade'], self.sections['Hostel World']['Media']),
                'GOOGLE': (self.sections['Google']['Soma'], self.sections['Google']['Quantidade'], self.sections['Google']['Media']),
                'TRIP ADVISOR': (0.0, 0, 0.0)
            }
        else:
            self.reviews = {}
            self.summaries = {}

        path = self.checkouts_filename()

        if os.path.exists(path):
            with open(path, 'r', encoding="utf-8") as f:
                cks = json.load(f)
            
            if 'total' in cks.keys():
                total = cks['total']
            else:
                total = 0

            if 'Booking' in cks.keys():
                booking = cks['Booking']
            else:
                booking = 0

            if 'Hostel World' in cks.keys():
                hostel_world = cks['Hostel World']
            else:
                hostel_world = 0

            if 'Outros' in cks.keys():
                outros = cks['Outros']
            else:
                outros = total - hostel_world - booking

            self.checkouts = {"Total": total, "Booking.com": booking, "Hostelworld": hostel_world, "Outros": outros}
        else:
            self.checkouts = {"Total": 0, "Booking.com": 0, "Hostelworld": 0, "Outros": 0}

        # Update UI
        #self.reload_checkins()
        self.reload_reviews()
        self.reload_summary()

    # ------------------------------
    # Check-ins UI update
    # ------------------------------
    def reload_checkins(self):
        df = pd.DataFrame(self.checkins_data) if self.checkins_data else pd.DataFrame()
        self.table_checkins.setModel(pandas_model(df))
        self.table_checkins.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        self.table_checkins.setStyleSheet("""
            QTableView {
                border: 1px solid #01aaaa;
                border-radius: 7px; 
                gridline-color: #444;
                selection-background-color: #01aaaa;
                selection-color: #ffffff;
                alternate-background-color: #252525;
            }
            QHeaderView::section {
                font-weight: bold;
            }
            QTableView::item {border:0px; padding-left: 6px;}
        """)

    # ------------------------------
    # Reviews UI update
    # ------------------------------
    def get_platform_key(self, display_name):
        name_to_key = {
            "Booking": "BOOKING",
            "Hostel World": "HOSTEL WORLD",
            "Google": "GOOGLE",
            "Trip Advisor": "TRIP ADVISOR"
        }
        return name_to_key.get(display_name, display_name)

    def reload_reviews(self):
        """
        Reload and display reviews for the currently selected platform.
        This method should be part of the MainWindow class.
        """
        display_name = self.cmb.currentText()
        plat = self.get_platform_key(display_name)
        
        # Get reviews and statistics for selected platform
        reviews = self.reviews.get(plat, [])
        soma, qtd, media = self.summaries.get(plat, (None, None, None))
        
        # Update summary labels
        soma_txt = f"{float(soma):.2f}" if soma is not None else "—"
        qtd_txt = str(int(qtd)) if qtd is not None else "—"
        
        # Handle media which can be string or float
        if media is not None:
            try:
                media_txt = f"{float(str(media).replace(',', '.')):.2f}"
            except (ValueError, TypeError):
                media_txt = str(media) if media else "—"
        else:
            media_txt = "—"
        
        self.lbl_qtd.setText(f"Qtd: {qtd_txt}")
        self.lbl_soma.setText(f"Soma: {soma_txt}")
        self.lbl_media.setText(f"Média: {media_txt}")
        
        # Convert reviews to DataFrame
        if reviews:
            df = pd.json_normalize(reviews)
        else:
            df = pd.DataFrame()
        
        # Create model with checkbox column
        model = QStandardItemModel()
        
        if not df.empty:
            # Set up columns: checkbox + all data columns
            model.setColumnCount(len(df.columns) + 1)
            headers = [""] + df.columns.astype(str).tolist()
            model.setHorizontalHeaderLabels(headers)
            
            # Populate rows
            for r in range(len(df)):
                # Checkbox column
                check_item = QStandardItem()
                check_item.setCheckable(True)
                check_item.setCheckState(Qt.Unchecked)
                check_item.setEditable(False)
                model.setItem(r, 0, check_item)
                
                # Data columns
                for c in range(len(df.columns)):
                    raw = df.iat[r, c]
                    val = "" if raw is None or pd.isna(raw) or raw == 'None' else str(raw)
                    item = QStandardItem(val)
                    item.setEditable(False)
                    model.setItem(r, c + 1, item)
        else:
            # Empty table with just checkbox column
            model.setColumnCount(1)
            model.setHorizontalHeaderLabels([""])
        
        # Apply model to table
        self.table_reviews.setModel(model)
        self.table_reviews.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_reviews.verticalHeader().setMinimumWidth(30)
        self.table_reviews.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        
        # Set checkbox column width
        if not df.empty:
            self.table_reviews.setColumnWidth(0, 30)
        
        # Apply platform-specific styling
        color = self.colors.get(plat, "#0078d7")
        self.table_reviews.setStyleSheet(f"""
            QTableView {{
                border: 1px solid {color};
                border-radius: 7px; 
                gridline-color: #444;
                selection-background-color: {color};
                selection-color: #000000;
                alternate-background-color: #252525;
            }}
            QHeaderView::section {{
                font-weight: bold;
            }}
            QTableView::item {{border:0px; padding-left: 6px;}}
        """)
        
        # Update combo box styling
        self.cmb.setStyleSheet(f"""
            QComboBox {{
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid {color};
                border-radius: 7px;
                padding: 4px 8px;
                min-width: 40px;
            }}
            QComboBox:hover {{
                background-color: #3a3a3a;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2d2d2d;
                color: #f0f0f0;
                selection-background-color: {color};
                selection-color: #000000;
                border: 1px solid {color};
            }}
        """)

    # ------------------------------
    # Summary UI
    # ------------------------------
    def reload_summary(self):
        """
        Reload and display the summary tables for all platforms.
        This method should be part of the MainWindow class.
        """
        # Get checkout data (default to zeros if not available)
        ck = self.checkouts or {"Total": 0, "Booking.com": 0, "Hostelworld": 0, "Outros": 0}
        
        # Update each platform's summary table
        for plat in ["BOOKING", "HOSTEL WORLD", "GOOGLE", "TRIP ADVISOR"]:
            # Get statistics for this platform
            soma, qtd, media = self.summaries.get(plat, (None, None, None))
            
            # Format values for display
            soma_val = f"{float(soma):.2f}" if soma is not None else ""
            qtd_val = int(qtd) if qtd is not None else ""
            
            # Handle media which can be string or float
            if media is not None:
                try:
                    media_val = f"{float(str(media).replace(',', '.')):.2f}"
                except (ValueError, TypeError):
                    media_val = str(media) if media else ""
            else:
                media_val = ""
            
            # Build rows for this platform
            rows = [
                ["Soma", soma_val],
                ["Média", media_val]
            ]
            
            # Add reservation count for Booking and Hostel World
            if plat in ["BOOKING", "HOSTEL WORLD"]:
                reservas_key = "Booking.com" if plat == "BOOKING" else "Hostelworld"
                reservas = int(ck.get(reservas_key, 0))
                rows.append(["Qtd de Reservas", reservas])
            
            # Add review count for all platforms
            rows.append(["Qtd de Avaliações", qtd_val])
            
            # Create DataFrame and model
            df = pd.DataFrame(rows, columns=["", "Valor"])
            model = pandas_model(df)
            
            # Get the table for this platform
            table = self.tables[plat]
            table.setModel(model)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            # Apply platform-specific styling
            table.setStyleSheet(f"""
                QTableView {{
                    background-color: rgba(255,255,255,0.04);
                    border: 1px solid {self.colors[plat]};
                    border-radius: 6px;
                    selection-background-color: {self.colors[plat]};
                    selection-color: #000000;
                }}
                QTableView::item {{ border:0px; padding-left: 6px;}}
            """)
        
        # Update the reservations summary label
        txt = (
            f"Total de reservas: {ck['Total']} | "
            f"Booking.com: {ck['Booking.com']} | "
            f"Hostelworld: {ck['Hostelworld']} | "
            f"Outros: {ck['Outros']}"
        )
        self.lbl_reservas.setText(txt)

    # ------------------------------
    # Dates
    # ------------------------------

    def update_date_label(self):
        """Atualiza o texto do label de data."""
        texto = (
            f"Reviews de: {self.data_inicio.strftime('%d/%m/%Y')} "
            f"até {self.data_fim.strftime('%d/%m/%Y')} "
            f"📅"
        )
        self.lbl_date.setText(texto)
    
    def open_date_picker(self, event):
        """Abre o diálogo de seleção de datas."""
        dialog = DateRangeDialog(self)

        dialog.cal_inicio.setSelectedDate(self.data_inicio)
        dialog.cal_fim.setSelectedDate(self.data_fim)
        
        if dialog.exec() == QDialog.Accepted:
            inicio, fim = dialog.get_dates()

            if inicio > fim:
                QMessageBox.warning(
                    self,
                    "Datas Inválidas",
                    "A data inicial não pode ser posterior à data final!"
                )
                return

            self.data_inicio = inicio
            self.data_fim = fim
            self.update_date_label()
            
            # Aqui você pode adicionar lógica para recarregar os dados
            # com o novo período, se necessário
            self.log_msg(f"✓ Período alterado para {inicio.strftime('%d/%m/%Y')} - {fim.strftime('%d/%m/%Y')}")
            
            # Se você quiser recarregar automaticamente:
            self.reload()

# ENTRY POINT ----------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()