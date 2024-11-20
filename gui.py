import re
import logging
import json
import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QListWidget, QListWidgetItem, QComboBox, QDialog, QTextBrowser,
    QProgressBar, QScrollArea
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from database import init_db, add_email, get_emails, delete_email
from openai_manager import generate_marketing_text, generate_email_subject
from email_manager import send_email

# Logging konfigurieren
logging.basicConfig(filename='marketing_tool.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class EmailSenderThread(QThread):
    # Define signals to communicate with the GUI
    finished = pyqtSignal(int, int)  # success_count, failure_count
    error = pyqtSignal(str)
    progress = pyqtSignal(int)       # Fortschritt in Prozent

    def __init__(self, smtp_server, sender_email, sender_password, emails, subject, body):
        super().__init__()
        self.smtp_server = smtp_server
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.emails = emails
        self.subject = subject
        self.body = body

    def run(self):
        success_count = 0
        failure_count = 0
        total_emails = len(self.emails)
        for index, email in enumerate(self.emails, start=1):
            sent = send_email(
                smtp_server=self.smtp_server,
                sender_email=self.sender_email,
                sender_password=self.sender_password,
                recipient_email=email,
                subject=self.subject,
                body=self.body
            )
            if sent:
                success_count += 1
            else:
                failure_count += 1
            progress_percentage = int((index / total_emails) * 100)
            self.progress.emit(progress_percentage)
        self.finished.emit(success_count, failure_count)

class MarketingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Marketing Tool")
        self.resize(800, 1100)  # Erhöht die Höhe für die neuen Felder
        init_db()
        self.smtp_config_file = "smtp_config.json"
        self.company_config_file = "company_config.json"  # Neue Datei für Firmendaten
        self.init_ui()
        self.load_smtp_config()
        self.load_company_config()  # Lade Firmendaten beim Start

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Erstelle eine ScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)  # Als Instanzvariable speichern

        # E-Mail-Adresse hinzufügen
        email_layout = QHBoxLayout()
        email_label = QLabel("E-Mail-Adresse hinzufügen:")
        email_label.setFont(QFont("Arial", 12))
        self.email_input = QLineEdit()
        self.email_input.setFont(QFont("Arial", 12))
        add_email_button = QPushButton("Hinzufügen")
        add_email_button.setFont(QFont("Arial", 12))
        add_email_button.clicked.connect(self.add_email)
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        email_layout.addWidget(add_email_button)
        self.scroll_layout.addLayout(email_layout)

        # Gespeicherte E-Mail-Adressen anzeigen
        self.email_list = QListWidget()
        self.refresh_email_list()
        email_list_label = QLabel("Gespeicherte E-Mail-Adressen:")
        email_list_label.setFont(QFont("Arial", 12))
        self.scroll_layout.addWidget(email_list_label)
        self.scroll_layout.addWidget(self.email_list)

        # Button zum Löschen von E-Mails
        delete_email_button = QPushButton("Ausgewählte E-Mail löschen")
        delete_email_button.setFont(QFont("Arial", 12))
        delete_email_button.clicked.connect(self.delete_selected_emails)
        self.scroll_layout.addWidget(delete_email_button)

        # OpenAI API-Schlüssel
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("OpenAI API-Schlüssel:")
        api_key_label.setFont(QFont("Arial", 12))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setFont(QFont("Arial", 12))
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        self.scroll_layout.addLayout(api_key_layout)

        # OpenAI Modell auswählen
        model_layout = QHBoxLayout()
        model_label = QLabel("OpenAI Modell auswählen:")
        model_label.setFont(QFont("Arial", 12))
        self.model_combo = QComboBox()
        self.model_combo.setFont(QFont("Arial", 12))
        self.model_combo.addItems([
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "gpt-4"
        ])
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        self.scroll_layout.addLayout(model_layout)

        # Produktbeschreibung
        product_layout = QHBoxLayout()
        product_label = QLabel("Produktbeschreibung:")
        product_label.setFont(QFont("Arial", 12))
        self.product_input = QLineEdit()
        self.product_input.setFont(QFont("Arial", 12))
        product_layout.addWidget(product_label)
        product_layout.addWidget(self.product_input)
        self.scroll_layout.addLayout(product_layout)

        # Produkt-Link
        link_layout = QHBoxLayout()
        link_label = QLabel("Produkt-Link:")
        link_label.setFont(QFont("Arial", 12))
        self.link_input = QLineEdit()
        self.link_input.setFont(QFont("Arial", 12))
        link_layout.addWidget(link_label)
        link_layout.addWidget(self.link_input)
        self.scroll_layout.addLayout(link_layout)

        # Button zum Generieren des Textes
        generate_button = QPushButton("Text generieren")
        generate_button.setFont(QFont("Arial", 12))
        generate_button.clicked.connect(self.generate_text)
        self.scroll_layout.addWidget(generate_button)

        # Button zur Vorschau des Textes
        preview_button = QPushButton("Vorschau anzeigen")
        preview_button.setFont(QFont("Arial", 12))
        preview_button.clicked.connect(self.preview_text)
        self.scroll_layout.addWidget(preview_button)

        # Rich-Text-Editor für den Marketingtext
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Arial", 12))
        marketing_text_label = QLabel("Marketingtext:")
        marketing_text_label.setFont(QFont("Arial", 12))
        self.scroll_layout.addWidget(marketing_text_label)
        self.scroll_layout.addWidget(self.text_editor)

        # Layout für Textformatierung
        format_layout = QHBoxLayout()

        bold_button = QPushButton("Fett")
        bold_button.setFont(QFont("Arial", 12))
        bold_button.clicked.connect(self.make_bold)
        format_layout.addWidget(bold_button)

        italic_button = QPushButton("Kursiv")
        italic_button.setFont(QFont("Arial", 12))
        italic_button.clicked.connect(self.make_italic)
        format_layout.addWidget(italic_button)

        underline_button = QPushButton("Unterstrichen")
        underline_button.setFont(QFont("Arial", 12))
        underline_button.clicked.connect(self.make_underline)
        format_layout.addWidget(underline_button)

        self.scroll_layout.addLayout(format_layout)

        # Firmenfooter hinzufügen
        footer_section_label = QLabel("Firmeninformationen für den Footer:")
        footer_section_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.scroll_layout.addWidget(footer_section_label)

        # Firmenname
        company_name_layout = QHBoxLayout()
        company_name_label = QLabel("Firmenname:")
        company_name_label.setFont(QFont("Arial", 12))
        self.company_name_input = QLineEdit()
        self.company_name_input.setFont(QFont("Arial", 12))
        company_name_layout.addWidget(company_name_label)
        company_name_layout.addWidget(self.company_name_input)
        self.scroll_layout.addLayout(company_name_layout)

        # Adresse
        address_layout = QHBoxLayout()
        address_label = QLabel("Adresse:")
        address_label.setFont(QFont("Arial", 12))
        self.address_input = QLineEdit()
        self.address_input.setFont(QFont("Arial", 12))
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_input)
        self.scroll_layout.addLayout(address_layout)

        # Telefonnummer
        phone_layout = QHBoxLayout()
        phone_label = QLabel("Telefonnummer:")
        phone_label.setFont(QFont("Arial", 12))
        self.phone_input = QLineEdit()
        self.phone_input.setFont(QFont("Arial", 12))
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(self.phone_input)
        self.scroll_layout.addLayout(phone_layout)

        # E-Mail-Adresse
        company_email_layout = QHBoxLayout()
        company_email_label = QLabel("E-Mail-Adresse:")
        company_email_label.setFont(QFont("Arial", 12))
        self.company_email_input = QLineEdit()
        self.company_email_input.setFont(QFont("Arial", 12))
        company_email_layout.addWidget(company_email_label)
        company_email_layout.addWidget(self.company_email_input)
        self.scroll_layout.addLayout(company_email_layout)

        # Website
        website_layout = QHBoxLayout()
        website_label = QLabel("Website:")
        website_label.setFont(QFont("Arial", 12))
        self.website_input = QLineEdit()
        self.website_input.setFont(QFont("Arial", 12))
        website_layout.addWidget(website_label)
        website_layout.addWidget(self.website_input)
        self.scroll_layout.addLayout(website_layout)

        # Button zum Speichern der Firmendaten
        save_company_button = QPushButton("Firmeninformationen speichern")
        save_company_button.setFont(QFont("Arial", 12))
        save_company_button.clicked.connect(self.save_company_config)
        self.scroll_layout.addWidget(save_company_button)

        # SMTP-Einstellungen
        smtp_layout = QVBoxLayout()
        smtp_label = QLabel("SMTP-Einstellungen:")
        smtp_label.setFont(QFont("Arial", 12))
        smtp_layout.addWidget(smtp_label)

        # SMTP Server
        smtp_server_layout = QHBoxLayout()
        smtp_server_label = QLabel("SMTP Server:")
        smtp_server_label.setFont(QFont("Arial", 12))
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setFont(QFont("Arial", 12))
        smtp_server_layout.addWidget(smtp_server_label)
        smtp_server_layout.addWidget(self.smtp_server_input)
        smtp_layout.addLayout(smtp_server_layout)

        # Absender E-Mail
        sender_email_layout = QHBoxLayout()
        sender_email_label = QLabel("Absender E-Mail:")
        sender_email_label.setFont(QFont("Arial", 12))
        self.sender_email_input = QLineEdit()
        self.sender_email_input.setFont(QFont("Arial", 12))
        sender_email_layout.addWidget(sender_email_label)
        sender_email_layout.addWidget(self.sender_email_input)
        smtp_layout.addLayout(sender_email_layout)

        # Passwort
        password_layout = QHBoxLayout()
        password_label = QLabel("Passwort:")
        password_label.setFont(QFont("Arial", 12))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Arial", 12))
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        smtp_layout.addLayout(password_layout)

        # Betreff wird entfernt, da er nun automatisch generiert wird

        # Button zum Speichern der SMTP-Konfiguration
        save_smtp_button = QPushButton("SMTP-Konfiguration speichern")
        save_smtp_button.setFont(QFont("Arial", 12))
        save_smtp_button.clicked.connect(self.save_smtp_config)
        smtp_layout.addWidget(save_smtp_button)

        self.scroll_layout.addLayout(smtp_layout)

        # Button zum Senden der E-Mails
        send_button = QPushButton("E-Mail senden")
        send_button.setFont(QFont("Arial", 12))
        send_button.clicked.connect(self.send_emails)
        self.send_button = send_button  # Referenz behalten, um den Button zu deaktivieren
        self.scroll_layout.addWidget(send_button)

        # Fortschrittsanzeige
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.scroll_layout.addWidget(self.progress_bar)

        # Setze das Layout für die ScrollArea
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Stylesheet für optische Verbesserungen
        self.setStyleSheet("""
            QWidget {
                font-family: Arial;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit, QTextEdit, QComboBox, QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel {
                font-weight: bold;
            }
        """)

        self.setLayout(main_layout)

    def add_email(self):
        """
        Fügt eine neue E-Mail-Adresse zur Liste und Datenbank hinzu.
        """
        email = self.email_input.text().strip()
        if email and self.validate_email(email):
            add_email(email)
            self.refresh_email_list()
            self.email_input.clear()
            QMessageBox.information(self, "Erfolg", "E-Mail-Adresse hinzugefügt.")
            logging.info(f"E-Mail-Adresse hinzugefügt: {email}")
        else:
            QMessageBox.warning(self, "Warnung", "Bitte eine gültige E-Mail-Adresse eingeben.")
            logging.warning("Versuch, eine ungültige E-Mail-Adresse hinzuzufügen.")

    def delete_selected_emails(self):
        """
        Löscht die ausgewählten E-Mail-Adressen aus der Liste und der Datenbank.
        """
        selected_items = self.email_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warnung", "Bitte wähle mindestens eine E-Mail-Adresse zum Löschen aus.")
            return

        confirm = QMessageBox.question(
            self,
            "Bestätigung",
            f"Möchtest du die ausgewählten {len(selected_items)} E-Mail(s) wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        for item in selected_items:
            email = item.text()
            delete_email(email)
            self.email_list.takeItem(self.email_list.row(item))
            logging.info(f"E-Mail-Adresse gelöscht: {email}")

        QMessageBox.information(self, "Erfolg", "Ausgewählte E-Mail-Adressen wurden gelöscht.")

    def refresh_email_list(self):
        """
        Aktualisiert die Liste der gespeicherten E-Mail-Adressen.
        """
        self.email_list.clear()
        emails = get_emails()
        for email in emails:
            self.email_list.addItem(QListWidgetItem(email))
        logging.info("E-Mail-Liste aktualisiert.")

    def validate_email(self, email):
        """
        Validiert die E-Mail-Adresse mit einer Regex.
        """
        email_pattern = re.compile(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        )
        return re.match(email_pattern, email) is not None

    def save_smtp_config(self):
        """
        Speichert die SMTP-Konfiguration in einer JSON-Datei.
        """
        smtp_server = self.smtp_server_input.text().strip()
        sender_email = self.sender_email_input.text().strip()
        password = self.password_input.text().strip()
        # Betreff wird nicht mehr benötigt

        if not all([smtp_server, sender_email, password]):
            QMessageBox.warning(self, "Warnung", "Bitte alle SMTP-Felder ausfüllen.")
            logging.warning("SMTP-Konfiguration speichern abgebrochen: Nicht alle Felder ausgefüllt.")
            return

        smtp_config = {
            "smtp_server": smtp_server,
            "sender_email": sender_email,
            "password": password
            # "subject": subject  # Entfernt, da Betreff automatisch generiert wird
        }

        try:
            with open(self.smtp_config_file, 'w') as file:
                json.dump(smtp_config, file)
            QMessageBox.information(self, "Erfolg", "SMTP-Konfiguration erfolgreich gespeichert.")
            logging.info("SMTP-Konfiguration erfolgreich gespeichert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der SMTP-Konfiguration: {e}")
            logging.error(f"Fehler beim Speichern der SMTP-Konfiguration: {e}")

    def load_smtp_config(self):
        """
        Lädt die SMTP-Konfiguration aus der JSON-Datei, falls vorhanden.
        """
        if not os.path.exists(self.smtp_config_file):
            return  # Keine gespeicherte Konfiguration vorhanden

        try:
            with open(self.smtp_config_file, 'r') as file:
                smtp_config = json.load(file)
            self.smtp_server_input.setText(smtp_config.get("smtp_server", ""))
            self.sender_email_input.setText(smtp_config.get("sender_email", ""))
            self.password_input.setText(smtp_config.get("password", ""))
            logging.info("SMTP-Konfiguration erfolgreich geladen.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der SMTP-Konfiguration: {e}")
            logging.error(f"Fehler beim Laden der SMTP-Konfiguration: {e}")

    def save_company_config(self):
        """
        Speichert die Firmeninformationen in einer JSON-Datei.
        """
        company_name = self.company_name_input.text().strip()
        address = self.address_input.text().strip()
        phone = self.phone_input.text().strip()
        company_email = self.company_email_input.text().strip()
        website = self.website_input.text().strip()

        if not all([company_name, address, phone, company_email, website]):
            QMessageBox.warning(self, "Warnung", "Bitte alle Firmenfelder ausfüllen.")
            logging.warning("Speichern der Firmeninformationen abgebrochen: Nicht alle Felder ausgefüllt.")
            return

        company_config = {
            "company_name": company_name,
            "address": address,
            "phone": phone,
            "company_email": company_email,
            "website": website
        }

        try:
            with open(self.company_config_file, 'w') as file:
                json.dump(company_config, file)
            QMessageBox.information(self, "Erfolg", "Firmeninformationen erfolgreich gespeichert.")
            logging.info("Firmeninformationen erfolgreich gespeichert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der Firmeninformationen: {e}")
            logging.error(f"Fehler beim Speichern der Firmeninformationen: {e}")

    def load_company_config(self):
        """
        Lädt die Firmeninformationen aus der JSON-Datei, falls vorhanden.
        """
        if not os.path.exists(self.company_config_file):
            return  # Keine gespeicherte Firmendaten vorhanden

        try:
            with open(self.company_config_file, 'r') as file:
                company_config = json.load(file)
            self.company_name_input.setText(company_config.get("company_name", ""))
            self.address_input.setText(company_config.get("address", ""))
            self.phone_input.setText(company_config.get("phone", ""))
            self.company_email_input.setText(company_config.get("company_email", ""))
            self.website_input.setText(company_config.get("website", ""))
            logging.info("Firmeninformationen erfolgreich geladen.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Firmeninformationen: {e}")
            logging.error(f"Fehler beim Laden der Firmeninformationen: {e}")

    def generate_text(self):
        """
        Generiert den Marketingtext und den E-Mail-Betreff unter Verwendung der OpenAI API.
        """
        product_description = self.product_input.text().strip()
        product_link = self.link_input.text().strip()
        api_key = self.api_key_input.text().strip()
        selected_model = self.model_combo.currentText()

        company_name = self.company_name_input.text().strip()
        address = self.address_input.text().strip()
        phone = self.phone_input.text().strip()
        company_email = self.company_email_input.text().strip()
        website = self.website_input.text().strip()

        logging.info("Generiere Marketingtext...")
        logging.info(f"Produktbeschreibung: {product_description}")
        logging.info(f"Produkt-Link: {product_link}")
        logging.info(f"Firmenname: {company_name}")
        logging.info(f"Adresse: {address}")
        logging.info(f"Telefonnummer: {phone}")
        logging.info(f"Firmen-E-Mail: {company_email}")
        logging.info(f"Website: {website}")
        logging.info(f"Ausgewähltes Modell: {selected_model}")

        # Validierungen
        if not product_description:
            QMessageBox.warning(self, "Warnung", "Bitte eine Produktbeschreibung eingeben.")
            logging.warning("Generierung abgebrochen: Keine Produktbeschreibung eingegeben.")
            return
        if not product_link:
            QMessageBox.warning(self, "Warnung", "Bitte einen Produkt-Link eingeben.")
            logging.warning("Generierung abgebrochen: Kein Produkt-Link eingegeben.")
            return
        # Einfache Regex zur Validierung von URLs
        url_pattern = re.compile(
            r'^(?:http|ftp)s?://' # http:// oder https://
            r'(?:\S+(?::\S*)?@)?' # optionaler Benutzername und Passwort
            r'(?:'
            r'(?:(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})' # Domainname
            r'|'
            r'\d{1,3}(?:\.\d{1,3}){3}' # oder IPv4
            r')'
            r'(?::\d+)?' # optionaler Port
            r'(?:/\S*)?$', re.IGNORECASE)

        if not re.match(url_pattern, product_link):
            QMessageBox.warning(self, "Warnung", "Bitte einen gültigen Produkt-Link eingeben.")
            logging.warning("Generierung abgebrochen: Ungültiger Produkt-Link eingegeben.")
            return

        # Validierung der Firmeninformationen
        if not company_name:
            QMessageBox.warning(self, "Warnung", "Bitte den Firmennamen eingeben.")
            logging.warning("Generierung abgebrochen: Kein Firmenname eingegeben.")
            return
        if not address:
            QMessageBox.warning(self, "Warnung", "Bitte die Firmenadresse eingeben.")
            logging.warning("Generierung abgebrochen: Keine Firmenadresse eingegeben.")
            return
        if not phone:
            QMessageBox.warning(self, "Warnung", "Bitte die Telefonnummer eingeben.")
            logging.warning("Generierung abgebrochen: Keine Telefonnummer eingegeben.")
            return
        if not company_email:
            QMessageBox.warning(self, "Warnung", "Bitte die Firmen-E-Mail-Adresse eingeben.")
            logging.warning("Generierung abgebrochen: Keine Firmen-E-Mail-Adresse eingegeben.")
            return
        if not website:
            QMessageBox.warning(self, "Warnung", "Bitte die Firmen-Website eingeben.")
            logging.warning("Generierung abgebrochen: Keine Firmen-Website eingegeben.")
            return
        if not api_key:
            QMessageBox.warning(self, "Warnung", "Bitte den OpenAI API-Schlüssel eingeben.")
            logging.warning("Generierung abgebrochen: Kein API-Schlüssel eingegeben.")
            return
        if not selected_model:
            QMessageBox.warning(self, "Warnung", "Bitte ein Modell auswählen.")
            logging.warning("Generierung abgebrochen: Kein Modell ausgewählt.")
            return

        # Überprüfe den API-Schlüssel
        if not re.match(r'^sk-[A-Za-z0-9-]{20,}$', api_key):
            QMessageBox.critical(self, "Fehler", "Der eingegebene API-Schlüssel scheint ungültig zu sein.")
            logging.error("Generierung abgebrochen: Ungültiger API-Schlüssel.")
            return

        try:
            # Generiere den Marketingtext
            marketing_text = generate_marketing_text(
                product_description, 
                product_link, 
                api_key, 
                model=selected_model
            )

            # Generiere den E-Mail-Betreff
            email_subject = generate_email_subject(
                product_description, 
                product_link, 
                api_key, 
                model=selected_model
            )

            # Speichere den generierten Betreff in einer Instanzvariable
            self.last_generated_subject = email_subject

            # Erstelle den Footer basierend auf den Firmeninformationen
            footer_html = self.create_footer(company_name, address, phone, company_email, website)

            # Füge den rechtlichen Hinweis hinzu
            disclaimer_html = self.create_disclaimer()

            # Füge den Footer und den Disclaimer an den generierten Marketingtext an
            full_body = marketing_text + footer_html + disclaimer_html

            # Setze den generierten Betreff und Body in die GUI
            self.text_editor.setHtml(full_body)  # Setze den vollständigen Text als HTML
            QMessageBox.information(self, "Erfolg", f"Marketingtext und Betreff erfolgreich generiert.\n\nBetreff: {email_subject}")
            logging.info("Marketingtext und Betreff erfolgreich generiert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Textgenerierung: {e}")
            logging.error(f"Fehler bei der Textgenerierung: {e}")

    def create_footer(self, company_name, address, phone, company_email, website):
        """
        Erstellt einen standardisierten HTML-Footer basierend auf den Firmeninformationen.
        """
        footer_template = f"""
        <br><br>
        <hr>
        <table>
            <tr>
                <td>
                    <strong>{company_name}</strong><br>
                    {address}<br>
                    Telefon: {phone}<br>
                    E-Mail: <a href="mailto:{company_email}">{company_email}</a><br>
                    Website: <a href="{website}">{website}</a>
                </td>
            </tr>
        </table>
        """
        return footer_template

    def create_disclaimer(self):
        """
        Erstellt den rechtlichen Hinweis als HTML.
        """
        disclaimer = """
        <br><br>
        <hr>
        <p style="font-size: 10px; color: gray;">
            Diese E-Mail könnte vertrauliche und/oder rechtlich geschützte Informationen enthalten. Wenn Sie nicht der richtige Adressat sind oder diese E-Mail irrtümlich erhalten haben, informieren Sie bitte sofort den Absender und vernichten Sie diese Mail. Das unerlaubte Kopieren sowie die unbefugte Weitergabe dieser Mail ist nicht gestattet.
        </p>
        """
        return disclaimer

    def preview_text(self):
        """
        Öffnet ein neues Fenster zur Vorschau des generierten Marketingtexts.
        """
        html_content = self.text_editor.toHtml()
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Vorschau des Marketingtexts")
        preview_dialog.resize(600, 400)
        layout = QVBoxLayout()
        text_browser = QTextBrowser()
        text_browser.setHtml(html_content)
        layout.addWidget(text_browser)
        preview_dialog.setLayout(layout)
        preview_dialog.exec_()

    def send_emails(self):
        """
        Sendet die generierten E-Mails an die gespeicherten Empfänger.
        """
        smtp_server = self.smtp_server_input.text().strip()
        sender_email = self.sender_email_input.text().strip()
        password = self.password_input.text().strip()

        # Überprüfe, ob ein Betreff generiert wurde
        if not hasattr(self, 'last_generated_subject') or not self.last_generated_subject:
            QMessageBox.warning(self, "Warnung", "Bitte zuerst einen Marketingtext generieren.")
            logging.warning("E-Mail-Versand abgebrochen: Kein Betreff generiert.")
            return

        subject = self.last_generated_subject
        body = self.text_editor.toHtml().strip()  # Verwende HTML-Inhalt

        if not all([smtp_server, sender_email, password, subject, body]):
            QMessageBox.warning(self, "Warnung", "Bitte alle SMTP-Felder ausfüllen und einen Marketingtext generieren.")
            logging.warning("E-Mail-Versand abgebrochen: Nicht alle Felder ausgefüllt.")
            return

        # Logge die SMTP-Informationen (ohne Passwort)
        logging.info(f"SMTP Server: {smtp_server}")
        logging.info(f"Absender E-Mail: {sender_email}")
        logging.info(f"Betreff: {subject}")

        emails = get_emails()
        if not emails:
            QMessageBox.warning(self, "Warnung", "Keine Empfänger-E-Mail-Adressen vorhanden.")
            logging.warning("E-Mail-Versand abgebrochen: Keine Empfänger-E-Mail-Adressen vorhanden.")
            return

        confirm = QMessageBox.question(
            self,
            "Bestätigung",
            "Möchtest du die E-Mails jetzt senden?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            logging.info("E-Mail-Versand abgebrochen durch Benutzer.")
            return

        # Deaktiviere den send Button und setze die Fortschrittsanzeige zurück
        self.send_button.setEnabled(False)
        self.progress_bar.setValue(0)

        # Starte den E-Mail-Versand in einem separaten Thread
        self.thread = EmailSenderThread(
            smtp_server=smtp_server,
            sender_email=sender_email,
            sender_password=password,
            emails=emails,
            subject=subject,
            body=body
        )
        self.thread.finished.connect(self.on_emails_sent)
        self.thread.error.connect(self.on_send_error)
        self.thread.progress.connect(self.update_progress)
        self.thread.start()
        logging.info("E-Mail-Versand gestartet.")

    def update_progress(self, value):
        """
        Aktualisiert die Fortschrittsanzeige während des E-Mail-Versands.
        """
        self.progress_bar.setValue(value)

    def on_emails_sent(self, success_count, failure_count):
        """
        Wird aufgerufen, wenn der E-Mail-Versand abgeschlossen ist.
        """
        # Aktiviere den send Button wieder und setze die Fortschrittsanzeige auf 100%
        self.send_button.setEnabled(True)
        self.progress_bar.setValue(100)

        summary = f"{success_count} von {len(get_emails())} E-Mails wurden erfolgreich gesendet."
        if failure_count > 0:
            summary += f"\n{failure_count} E-Mails konnten nicht gesendet werden."
        QMessageBox.information(self, "Ergebnis", summary)
        logging.info(f"E-Mail-Versand abgeschlossen: {summary}")

    def on_send_error(self, error_message):
        """
        Wird aufgerufen, wenn ein Fehler beim E-Mail-Versand auftritt.
        """
        # Aktiviere den send Button wieder und setze die Fortschrittsanzeige zurück
        self.send_button.setEnabled(True)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Fehler", f"Fehler beim E-Mail-Versand: {error_message}")
        logging.error(f"Fehler beim E-Mail-Versand: {error_message}")

    # Methoden zur Textformatierung
    def make_bold(self):
        """
        Formatiert den ausgewählten Text fett oder entfernt die Fettschrift.
        """
        fmt = self.text_editor.currentCharFormat()
        if fmt.fontWeight() == QFont.Bold:
            fmt.setFontWeight(QFont.Normal)
        else:
            fmt.setFontWeight(QFont.Bold)
        self.text_editor.setCurrentCharFormat(fmt)

    def make_italic(self):
        """
        Formatiert den ausgewählten Text kursiv oder entfernt die Kursivschrift.
        """
        fmt = self.text_editor.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.text_editor.setCurrentCharFormat(fmt)

    def make_underline(self):
        """
        Unterstreicht den ausgewählten Text oder entfernt die Unterstreichung.
        """
        fmt = self.text_editor.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.text_editor.setCurrentCharFormat(fmt)

    def create_disclaimer(self):
        """
        Erstellt den rechtlichen Hinweis als HTML.
        """
        disclaimer = """
        <br><br>
        <hr>
        <p style="font-size: 10px; color: gray;">
            Diese E-Mail könnte vertrauliche und/oder rechtlich geschützte Informationen enthalten. Wenn Sie nicht der richtige Adressat sind oder diese E-Mail irrtümlich erhalten haben, informieren Sie bitte sofort den Absender und vernichten Sie diese Mail. Das unerlaubte Kopieren sowie die unbefugte Weitergabe dieser Mail ist nicht gestattet.
        </p>
        """
        return disclaimer

    def generate_text(self):
        """
        Generiert den Marketingtext und den E-Mail-Betreff unter Verwendung der OpenAI API.
        """
        product_description = self.product_input.text().strip()
        product_link = self.link_input.text().strip()
        api_key = self.api_key_input.text().strip()
        selected_model = self.model_combo.currentText()

        company_name = self.company_name_input.text().strip()
        address = self.address_input.text().strip()
        phone = self.phone_input.text().strip()
        company_email = self.company_email_input.text().strip()
        website = self.website_input.text().strip()

        logging.info("Generiere Marketingtext...")
        logging.info(f"Produktbeschreibung: {product_description}")
        logging.info(f"Produkt-Link: {product_link}")
        logging.info(f"Firmenname: {company_name}")
        logging.info(f"Adresse: {address}")
        logging.info(f"Telefonnummer: {phone}")
        logging.info(f"Firmen-E-Mail: {company_email}")
        logging.info(f"Website: {website}")
        logging.info(f"Ausgewähltes Modell: {selected_model}")

        # Validierungen
        if not product_description:
            QMessageBox.warning(self, "Warnung", "Bitte eine Produktbeschreibung eingeben.")
            logging.warning("Generierung abgebrochen: Keine Produktbeschreibung eingegeben.")
            return
        if not product_link:
            QMessageBox.warning(self, "Warnung", "Bitte einen Produkt-Link eingeben.")
            logging.warning("Generierung abgebrochen: Kein Produkt-Link eingegeben.")
            return
        # Einfache Regex zur Validierung von URLs
        url_pattern = re.compile(
            r'^(?:http|ftp)s?://' # http:// oder https://
            r'(?:\S+(?::\S*)?@)?' # optionaler Benutzername und Passwort
            r'(?:'
            r'(?:(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})' # Domainname
            r'|'
            r'\d{1,3}(?:\.\d{1,3}){3}' # oder IPv4
            r')'
            r'(?::\d+)?' # optionaler Port
            r'(?:/\S*)?$', re.IGNORECASE)

        if not re.match(url_pattern, product_link):
            QMessageBox.warning(self, "Warnung", "Bitte einen gültigen Produkt-Link eingeben.")
            logging.warning("Generierung abgebrochen: Ungültiger Produkt-Link eingegeben.")
            return

        # Validierung der Firmeninformationen
        if not company_name:
            QMessageBox.warning(self, "Warnung", "Bitte den Firmennamen eingeben.")
            logging.warning("Generierung abgebrochen: Kein Firmenname eingegeben.")
            return
        if not address:
            QMessageBox.warning(self, "Warnung", "Bitte die Firmenadresse eingeben.")
            logging.warning("Generierung abgebrochen: Keine Firmenadresse eingegeben.")
            return
        if not phone:
            QMessageBox.warning(self, "Warnung", "Bitte die Telefonnummer eingeben.")
            logging.warning("Generierung abgebrochen: Keine Telefonnummer eingegeben.")
            return
        if not company_email:
            QMessageBox.warning(self, "Warnung", "Bitte die Firmen-E-Mail-Adresse eingeben.")
            logging.warning("Generierung abgebrochen: Keine Firmen-E-Mail-Adresse eingegeben.")
            return
        if not website:
            QMessageBox.warning(self, "Warnung", "Bitte die Firmen-Website eingeben.")
            logging.warning("Generierung abgebrochen: Keine Firmen-Website eingegeben.")
            return
        if not api_key:
            QMessageBox.warning(self, "Warnung", "Bitte den OpenAI API-Schlüssel eingeben.")
            logging.warning("Generierung abgebrochen: Kein API-Schlüssel eingegeben.")
            return
        if not selected_model:
            QMessageBox.warning(self, "Warnung", "Bitte ein Modell auswählen.")
            logging.warning("Generierung abgebrochen: Kein Modell ausgewählt.")
            return

        # Überprüfe den API-Schlüssel
        if not re.match(r'^sk-[A-Za-z0-9-]{20,}$', api_key):
            QMessageBox.critical(self, "Fehler", "Der eingegebene API-Schlüssel scheint ungültig zu sein.")
            logging.error("Generierung abgebrochen: Ungültiger API-Schlüssel.")
            return

        try:
            # Generiere den Marketingtext
            marketing_text = generate_marketing_text(
                product_description, 
                product_link, 
                api_key, 
                model=selected_model
            )

            # Generiere den E-Mail-Betreff
            email_subject = generate_email_subject(
                product_description, 
                product_link, 
                api_key, 
                model=selected_model
            )

            # Speichere den generierten Betreff in einer Instanzvariable
            self.last_generated_subject = email_subject

            # Erstelle den Footer basierend auf den Firmeninformationen
            footer_html = self.create_footer(company_name, address, phone, company_email, website)

            # Füge den rechtlichen Hinweis hinzu
            disclaimer_html = self.create_disclaimer()

            # Füge den Footer und den Disclaimer an den generierten Marketingtext an
            full_body = marketing_text + footer_html + disclaimer_html

            # Setze den generierten Betreff und Body in die GUI
            self.text_editor.setHtml(full_body)  # Setze den vollständigen Text als HTML
            QMessageBox.information(self, "Erfolg", f"Marketingtext und Betreff erfolgreich generiert.\n\nBetreff: {email_subject}")
            logging.info("Marketingtext und Betreff erfolgreich generiert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Textgenerierung: {e}")
            logging.error(f"Fehler bei der Textgenerierung: {e}")

    def create_footer(self, company_name, address, phone, company_email, website):
        """
        Erstellt einen standardisierten HTML-Footer basierend auf den Firmeninformationen.
        """
        footer_template = f"""
        <br><br>
        <hr>
        <table>
            <tr>
                <td>
                    <strong>{company_name}</strong><br>
                    {address}<br>
                    Telefon: {phone}<br>
                    E-Mail: <a href="mailto:{company_email}">{company_email}</a><br>
                    Website: <a href="{website}">{website}</a>
                </td>
            </tr>
        </table>
        """
        return footer_template

    def create_disclaimer(self):
        """
        Erstellt den rechtlichen Hinweis als HTML.
        """
        disclaimer = """
        <br><br>
        <hr>
        <p style="font-size: 10px; color: gray;">
            Diese E-Mail könnte vertrauliche und/oder rechtlich geschützte Informationen enthalten. Wenn Sie nicht der richtige Adressat sind oder diese E-Mail irrtümlich erhalten haben, informieren Sie bitte sofort den Absender und vernichten Sie diese Mail. Das unerlaubte Kopieren sowie die unbefugte Weitergabe dieser Mail ist nicht gestattet.
        </p>
        """
        return disclaimer

    def preview_text(self):
        """
        Öffnet ein neues Fenster zur Vorschau des generierten Marketingtexts.
        """
        html_content = self.text_editor.toHtml()
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Vorschau des Marketingtexts")
        preview_dialog.resize(600, 400)
        layout = QVBoxLayout()
        text_browser = QTextBrowser()
        text_browser.setHtml(html_content)
        layout.addWidget(text_browser)
        preview_dialog.setLayout(layout)
        preview_dialog.exec_()

    def send_emails(self):
        """
        Sendet die generierten E-Mails an die gespeicherten Empfänger.
        """
        smtp_server = self.smtp_server_input.text().strip()
        sender_email = self.sender_email_input.text().strip()
        password = self.password_input.text().strip()

        # Überprüfe, ob ein Betreff generiert wurde
        if not hasattr(self, 'last_generated_subject') or not self.last_generated_subject:
            QMessageBox.warning(self, "Warnung", "Bitte zuerst einen Marketingtext generieren.")
            logging.warning("E-Mail-Versand abgebrochen: Kein Betreff generiert.")
            return

        subject = self.last_generated_subject
        body = self.text_editor.toHtml().strip()  # Verwende HTML-Inhalt

        if not all([smtp_server, sender_email, password, subject, body]):
            QMessageBox.warning(self, "Warnung", "Bitte alle SMTP-Felder ausfüllen und einen Marketingtext generieren.")
            logging.warning("E-Mail-Versand abgebrochen: Nicht alle Felder ausgefüllt.")
            return

        # Logge die SMTP-Informationen (ohne Passwort)
        logging.info(f"SMTP Server: {smtp_server}")
        logging.info(f"Absender E-Mail: {sender_email}")
        logging.info(f"Betreff: {subject}")

        emails = get_emails()
        if not emails:
            QMessageBox.warning(self, "Warnung", "Keine Empfänger-E-Mail-Adressen vorhanden.")
            logging.warning("E-Mail-Versand abgebrochen: Keine Empfänger-E-Mail-Adressen vorhanden.")
            return

        confirm = QMessageBox.question(
            self,
            "Bestätigung",
            "Möchtest du die E-Mails jetzt senden?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            logging.info("E-Mail-Versand abgebrochen durch Benutzer.")
            return

        # Deaktiviere den send Button und setze die Fortschrittsanzeige zurück
        self.send_button.setEnabled(False)
        self.progress_bar.setValue(0)

        # Starte den E-Mail-Versand in einem separaten Thread
        self.thread = EmailSenderThread(
            smtp_server=smtp_server,
            sender_email=sender_email,
            sender_password=password,
            emails=emails,
            subject=subject,
            body=body
        )
        self.thread.finished.connect(self.on_emails_sent)
        self.thread.error.connect(self.on_send_error)
        self.thread.progress.connect(self.update_progress)
        self.thread.start()
        logging.info("E-Mail-Versand gestartet.")

    def update_progress(self, value):
        """
        Aktualisiert die Fortschrittsanzeige während des E-Mail-Versands.
        """
        self.progress_bar.setValue(value)

    def on_emails_sent(self, success_count, failure_count):
        """
        Wird aufgerufen, wenn der E-Mail-Versand abgeschlossen ist.
        """
        # Aktiviere den send Button wieder und setze die Fortschrittsanzeige auf 100%
        self.send_button.setEnabled(True)
        self.progress_bar.setValue(100)

        summary = f"{success_count} von {len(get_emails())} E-Mails wurden erfolgreich gesendet."
        if failure_count > 0:
            summary += f"\n{failure_count} E-Mails konnten nicht gesendet werden."
        QMessageBox.information(self, "Ergebnis", summary)
        logging.info(f"E-Mail-Versand abgeschlossen: {summary}")

    def on_send_error(self, error_message):
        """
        Wird aufgerufen, wenn ein Fehler beim E-Mail-Versand auftritt.
        """
        # Aktiviere den send Button wieder und setze die Fortschrittsanzeige zurück
        self.send_button.setEnabled(True)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Fehler", f"Fehler beim E-Mail-Versand: {error_message}")
        logging.error(f"Fehler beim E-Mail-Versand: {error_message}")

    # Methoden zur Textformatierung
    def make_bold(self):
        """
        Formatiert den ausgewählten Text fett oder entfernt die Fettschrift.
        """
        fmt = self.text_editor.currentCharFormat()
        if fmt.fontWeight() == QFont.Bold:
            fmt.setFontWeight(QFont.Normal)
        else:
            fmt.setFontWeight(QFont.Bold)
        self.text_editor.setCurrentCharFormat(fmt)

    def make_italic(self):
        """
        Formatiert den ausgewählten Text kursiv oder entfernt die Kursivschrift.
        """
        fmt = self.text_editor.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.text_editor.setCurrentCharFormat(fmt)

    def make_underline(self):
        """
        Unterstreicht den ausgewählten Text oder entfernt die Unterstreichung.
        """
        fmt = self.text_editor.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.text_editor.setCurrentCharFormat(fmt)

    def save_company_config(self):
        """
        Speichert die Firmeninformationen in einer JSON-Datei.
        """
        company_name = self.company_name_input.text().strip()
        address = self.address_input.text().strip()
        phone = self.phone_input.text().strip()
        company_email = self.company_email_input.text().strip()
        website = self.website_input.text().strip()

        if not all([company_name, address, phone, company_email, website]):
            QMessageBox.warning(self, "Warnung", "Bitte alle Firmenfelder ausfüllen.")
            logging.warning("Speichern der Firmeninformationen abgebrochen: Nicht alle Felder ausgefüllt.")
            return

        company_config = {
            "company_name": company_name,
            "address": address,
            "phone": phone,
            "company_email": company_email,
            "website": website
        }

        try:
            with open(self.company_config_file, 'w') as file:
                json.dump(company_config, file)
            QMessageBox.information(self, "Erfolg", "Firmeninformationen erfolgreich gespeichert.")
            logging.info("Firmeninformationen erfolgreich gespeichert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der Firmeninformationen: {e}")
            logging.error(f"Fehler beim Speichern der Firmeninformationen: {e}")

    def load_company_config(self):
        """
        Lädt die Firmeninformationen aus der JSON-Datei, falls vorhanden.
        """
        if not os.path.exists(self.company_config_file):
            return  # Keine gespeicherte Firmendaten vorhanden

        try:
            with open(self.company_config_file, 'r') as file:
                company_config = json.load(file)
            self.company_name_input.setText(company_config.get("company_name", ""))
            self.address_input.setText(company_config.get("address", ""))
            self.phone_input.setText(company_config.get("phone", ""))
            self.company_email_input.setText(company_config.get("company_email", ""))
            self.website_input.setText(company_config.get("website", ""))
            logging.info("Firmeninformationen erfolgreich geladen.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Firmeninformationen: {e}")
            logging.error(f"Fehler beim Laden der Firmeninformationen: {e}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MarketingApp()
    window.show()
    sys.exit(app.exec_())
