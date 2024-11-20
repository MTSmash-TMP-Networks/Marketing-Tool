# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('marketing_tool.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_email(email):
    conn = sqlite3.connect('marketing_tool.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO emails (email) VALUES (?)', (email,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # E-Mail bereits vorhanden
    conn.close()

def get_emails():
    conn = sqlite3.connect('marketing_tool.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM emails')
    emails = [row[0] for row in cursor.fetchall()]
    conn.close()
    return emails

def delete_email(email):
    conn = sqlite3.connect('marketing_tool.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM emails WHERE email = ?', (email,))
    conn.commit()
    conn.close()
