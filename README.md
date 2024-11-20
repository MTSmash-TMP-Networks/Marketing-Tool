```
# Marketing Tool

Dieses Projekt ist ein leistungsstarkes Marketing-Tool, das eine grafische Benutzeroberfläche (GUI) bietet, um Marketingtexte zu erstellen und E-Mails direkt zu versenden. Es integriert die **OpenAI API**, um KI-generierte Inhalte zu erstellen, und bietet umfassende Konfigurationsmöglichkeiten.

## **Funktionen**

- **KI-generierte Marketingtexte:**
  - Geben Sie eine Produktbeschreibung und einen Link ein, und das Tool erstellt automatisch ansprechende Marketingtexte.
  - Betreffzeilen für E-Mails werden ebenfalls automatisch generiert.

- **SMTP-Integration:**
  - Senden Sie E-Mails direkt aus der Anwendung.
  - Speichern und bearbeiten Sie SMTP-Konfigurationen.

- **Footer-Konfiguration:**
  - Fügen Sie automatisch Firmeninformationen und rechtliche Hinweise zum Footer Ihrer E-Mails hinzu.

- **GUI mit benutzerfreundlicher Oberfläche:**
  - Übersichtliche Felder für alle Einstellungen.
  - Vorschau der generierten E-Mail vor dem Versand.

## **Voraussetzungen**

- Python 3.11 oder höher
- Abhängigkeiten aus der Datei `requirements.txt`

## **Installation**

### **1. Klone das Repository**
```bash
git clone https://github.com/MTSmash-TMP-Networks/TMP-Networks-Marketing-Tool/marketing-tool.git
cd marketing-tool
```

### **2. Virtuelle Umgebung erstellen**
Erstelle eine virtuelle Umgebung, um Abhängigkeiten zu isolieren:
```bash
python3.11 -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate
```

### **3. Abhängigkeiten installieren**
Installiere alle benötigten Bibliotheken:
```bash
pip install -r requirements.txt
```

## **Verwendung**

### **1. Anwendung starten**
Führe die GUI-Anwendung mit folgendem Befehl aus:
```bash
python gui.py
```

### **2. Funktionen der GUI**
1. **Produktbeschreibung und Link eingeben**:
   - Geben Sie die Beschreibung des Produkts und einen Link ein, um Inhalte zu generieren.
2. **Marketingtext und Betreff generieren**:
   - Klicken Sie auf "Text generieren", um den Vorschlag anzuzeigen.
3. **E-Mail-Versand**:
   - Geben Sie die SMTP-Daten ein, oder laden Sie sie aus einer gespeicherten Konfiguration.
   - Testen Sie den Versand, bevor Sie die E-Mail final verschicken.

## **Build und Distribution**

### **1. Erstellung einer ausführbaren Datei**
Verwende **PyInstaller**, um eine ausführbare Datei zu erstellen:

#### **Für Windows**
```bash
pyinstaller --onefile --windowed --icon=assets/logo.ico \
    --add-data "smtp_config.json;." \
    --add-data "company_config.json;." \
    --add-data "assets;assets" \
    gui.py
```

#### **Für macOS**
```bash
pyinstaller --onefile --windowed --icon=assets/logo.icns \
    --add-data "smtp_config.json:." \
    --add-data "company_config.json:." \
    --add-data "assets:assets" \
    gui.py
```

### **2. GitHub Actions verwenden**
Der Build-Prozess wird automatisch ausgeführt, wenn Änderungen in den `main`-Branch gepusht werden. Die erstellte EXE-Datei kann unter **Actions > Artifacts** heruntergeladen werden.

## **Konfigurationsdateien**

### **1. SMTP-Konfiguration**
Die Datei `smtp_config.json` enthält die SMTP-Daten, die direkt in der GUI geladen werden können.

### **2. Firmeninformationen**
Die Datei `company_config.json` speichert die Footer-Daten und andere firmenbezogene Details.

## **Beispiel für die JSON-Dateien**

### **smtp_config.json**
```json
{
  "smtp_server": "smtp.example.com",
  "sender_email": "your-email@example.com",
  "password": "your-password"
}
```

### **company_config.json**
```json
{
  "company_name": "Ihr Unternehmen",
  "address": "123 Musterstraße, 10115 Berlin",
  "phone": "+49 30 123456",
  "company_email": "info@ihr-unternehmen.de",
  "website": "https://www.ihr-unternehmen.de"
}
```

## **Rechtlicher Hinweis**

Die generierten E-Mails enthalten folgenden Hinweis, der automatisch angehängt wird:

> Diese E-Mail könnte vertrauliche und/oder rechtlich geschützte Informationen enthalten. Wenn Sie nicht der richtige Adressat sind oder diese E-Mail irrtümlich erhalten haben, informieren Sie bitte sofort den Absender und vernichten Sie diese Mail. Das unerlaubte Kopieren sowie die unbefugte Weitergabe dieser Mail ist nicht gestattet.

---

## **Powered by TMP-Networks**

Dieses Tool wurde mit Liebe und technischer Präzision von **TMP-Networks** entwickelt. Gemeinsam schaffen wir Lösungen, die Ihr Unternehmen voranbringen.

## **Lizenz**

Dieses Projekt ist unter der **MIT-Lizenz** lizenziert. Weitere Informationen finden Sie in der Datei `LICENSE`.

---

Viel Spaß mit dem Marketing-Tool! 🎉
