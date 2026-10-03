import sys
import psycopg2
import logging
logging.basicConfig(
    filename='app.log',              # Имя файла для логов
    level=logging.INFO,              # Уровень: записываем INFO и выше (ERROR тоже)
    format='%(asctime)s - %(levelname)s - %(message)s', # Формат: дата - уровень - сообщение
    encoding='utf-8'                 # Кодировка (чтобы русский текст был читаемым)
)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, 
                               QDialog, QFormLayout, QLineEdit, QComboBox, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt

# Настройки БД
DB_NAME = "lab1_db"
DB_USER = "postgres"
DB_PASSWORD = "your_password_here"  
DB_HOST = "localhost"
DB_PORT = "5432"


SQL_CREATE_SCRIPT = """
CREATE TYPE attack_type_enum AS ENUM ('DDoS', 'BruteForce', 'SQLInjection', 'XSS');
CREATE TABLE models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (model_name, version)
);
CREATE TABLE experiments (
    experiment_id SERIAL PRIMARY KEY,
    model_id INT NOT NULL,
    attack_type attack_type_enum NOT NULL,
    accuracy NUMERIC(5, 2) CHECK (accuracy > 0 AND accuracy <= 100),
    is_successful BOOLEAN DEFAULT FALSE,
    start_time TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_model FOREIGN KEY (model_id) REFERENCES models (model_id) ON DELETE CASCADE ON UPDATE CASCADE
);
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа №1: ИИ и DDoS")
        self.resize(800, 600)

        # Центральный виджет и компоновка
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Кнопка "Создать схему"
        self.btn_create = QPushButton("Создать схему и таблицы")
        self.btn_create.clicked.connect(self.create_schema)
        layout.addWidget(self.btn_create)

        # Кнопка "Внести данные"
        self.btn_insert = QPushButton("Внести данные")
        self.btn_insert.clicked.connect(self.open_insert_dialog)
        layout.addWidget(self.btn_insert)

        # Кнопка "Показать данные"
        self.btn_show = QPushButton("Показать данные")
        self.btn_show.clicked.connect(self.show_data)
        layout.addWidget(self.btn_show)

        layout.addStretch() # Прижать кнопки к верху

    def get_connection(self):
        return psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )

    # Кнопка "Создать схему" 
    def create_schema(self):
        logging.info("Попытка создания схемы БД (CREATE)")
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(SQL_CREATE_SCRIPT)
            conn.commit()
            cur.close()
            conn.close()
            logging.info("Схема БД успешно создана")
            QMessageBox.information(self, "Успех", "Таблицы успешно созданы!")
        except Exception as e:
            logging.error(f"Ошибка создания схемы: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать таблицы:\n{e}")

    # Кнопка "Внести данные"
    def open_insert_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить эксперимент")
        dialog.setModal(True)  # Делает окно модальным
        dialog.resize(400, 300)

        layout = QFormLayout(dialog)

        model_name_edit = QLineEdit()
        version_edit = QLineEdit()
        attack_combo = QComboBox()
        attack_combo.addItems(['DDoS', 'BruteForce', 'SQLInjection', 'XSS'])
        accuracy_edit = QLineEdit()
        accuracy_edit.setPlaceholderText("Например: 95.5")
        
        layout.addRow("Название модели:", model_name_edit)
        layout.addRow("Версия:", version_edit)
        layout.addRow("Тип атаки:", attack_combo)
        layout.addRow("Точность (%):", accuracy_edit)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addRow(btn_box)

        btn_cancel.clicked.connect(dialog.reject)

        def save_data():
            name = model_name_edit.text().strip()
            version = version_edit.text().strip()
            attack = attack_combo.currentText()
            accuracy_text = accuracy_edit.text().strip()

            if not name or not version or not accuracy_text:
                logging.warning("Попытка вставки с пустыми полями")
                QMessageBox.warning(dialog, "Ошибка", "Все поля обязательны!")
                return
            
            try:
                accuracy = float(accuracy_text)
            except ValueError:
                logging.warning(f"Некорректная точность: {accuracy_text}")
                QMessageBox.warning(dialog, "Ошибка", "Точность должна быть числом!")
                return

            logging.info(f"Попытка INSERT: модель={name}, версия={version}, атака={attack}, точность={accuracy}")
            try:
                conn = self.get_connection()
                cur = conn.cursor()
                
                cur.execute("SELECT model_id FROM models WHERE model_name = %s AND version = %s;", (name, version))
                result = cur.fetchone()
                
                if result:
                    model_id = result[0]
                else:
                    cur.execute(
                        "INSERT INTO models (model_name, version) VALUES (%s, %s) RETURNING model_id;",
                        (name, version)
                    )
                    model_id = cur.fetchone()[0]
                    logging.info(f"Добавлена новая модель: {name} {version} (ID={model_id})")
                
                cur.execute(
                    """INSERT INTO experiments (model_id, attack_type, accuracy, is_successful) 
                       VALUES (%s, %s, %s, %s);""",
                    (model_id, attack, accuracy, accuracy > 90)
                )
                
                conn.commit()
                cur.close()
                conn.close()
                
                logging.info("INSERT успешно выполнен")
                QMessageBox.information(dialog, "Успех", "Эксперимент добавлен!")
                dialog.accept()
                
            except Exception as e:
                logging.error(f"Ошибка INSERT: {e}")
                QMessageBox.critical(dialog, "Ошибка БД", f"Не удалось добавить данные:\n{e}")

        btn_save.clicked.connect(save_data)
        dialog.exec()

    # Кнопка "Показать данные"
    def show_data(self):
        self.data_window = QWidget()
        self.data_window.setWindowTitle("Просмотр экспериментов")
        self.data_window.resize(900, 500)
        
        layout = QVBoxLayout(self.data_window)

        # Блок фильтров 
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Тип атаки:"))
        self.filter_attack = QComboBox()
        self.filter_attack.addItems(["Все", "DDoS", "BruteForce", "SQLInjection", "XSS"])
        filter_layout.addWidget(self.filter_attack)

        filter_layout.addWidget(QLabel("Успешность:"))
        self.filter_success = QComboBox()
        self.filter_success.addItems(["Все", "Успешные", "Неуспешные"])
        filter_layout.addWidget(self.filter_success)

        self.btn_apply_filter = QPushButton("Применить фильтр")
        self.btn_apply_filter.clicked.connect(self.load_filtered_data)
        filter_layout.addWidget(self.btn_apply_filter)
        
        filter_layout.addStretch() # Прижать фильтры влево
        layout.addLayout(filter_layout)

        # Таблица
        self.data_table = QTableWidget()
        layout.addWidget(self.data_table)

        # Загружаем данные первый раз 
        self.load_filtered_data()
        
        self.data_window.show()

    def load_filtered_data(self):
        attack_filter = self.filter_attack.currentText()
        success_filter = self.filter_success.currentText()
        
        logging.info(f"Запрос данных с фильтрами: attack={attack_filter}, success={success_filter}")

        query = """
            SELECT 
                e.experiment_id,
                m.model_name,
                m.version,
                e.attack_type,
                e.accuracy,
                e.is_successful,
                e.start_time
            FROM experiments e
            JOIN models m ON e.model_id = m.model_id
        """
        
        conditions = []
        params = []

        if attack_filter != "Все":
            conditions.append("e.attack_type = %s")
            params.append(attack_filter)
        
        if success_filter == "Успешные":
            conditions.append("e.is_successful = TRUE")
        elif success_filter == "Неуспешные":
            conditions.append("e.is_successful = FALSE")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY e.experiment_id;"

        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
            headers = ["ID", "Модель", "Версия", "Тип атаки", "Точность", "Успех", "Время"]
            self.data_table.setColumnCount(len(headers))
            self.data_table.setHorizontalHeaderLabels(headers)
            self.data_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.data_table.setItem(i, j, item)
            
            self.data_table.resizeColumnsToContents()
            
            logging.info(f"Загружено {len(rows)} записей")
            cur.close()
            conn.close()
        except Exception as e:
            logging.error(f"Ошибка SELECT: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
