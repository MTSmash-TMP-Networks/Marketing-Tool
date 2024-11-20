# openai_manager.py
import openai
import markdown
import re

def generate_marketing_text(product_description, product_link, api_key, model="text-davinci-003"):
    openai.api_key = api_key

    chat_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"]

    try:
        if model in chat_models:
            # Verwende den Chat-Completion Endpoint für Chat-Modelle
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du bist ein hochqualifizierter Marketingprofi mit umfassendem Wissen in den Bereichen digitales Marketing, "
                            "Content-Erstellung, SEO, Social Media Marketing und Branding. Deine Aufgabe ist es, ansprechende, überzeugende "
                            "und zielgerichtete Marketingtexte zu erstellen, die Kunden direkt ansprechen und detaillierte Informationen über "
                            "das Produkt oder die Dienstleistung liefern. Achte darauf, den Ton und den Stil an die Zielgruppe anzupassen und "
                            "professionelle Marketingstandards einzuhalten. Deine Texte sollen klar, präzise und wirkungsvoll sein, um die "
                            "Aufmerksamkeit der Kunden zu gewinnen und sie zum Handeln zu motivieren. Integriere den bereitgestellten Produktlink in den Text, indem du ihn als Hyperlink verwendest. Formatiere die Ausgabe in gut strukturiertem HTML ohne Codeblock-Deklarationen."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Erstelle einen ansprechenden Marketingtext für folgendes Produkt: {product_description} Verwende diesen Link, um weitere Informationen zu erhalten: {product_link}"
                    }
                ],
                max_tokens=500,  # Erhöht für detailliertere Texte
                temperature=0.7,  # Optional: Kreativität anpassen
            )
            generated_text = response.choices[0].message['content'].strip()
        else:
            # Verwende den Completion Endpoint für klassische Modelle
            prompt = (
                "Du bist ein hochqualifizierter Marketingprofi mit umfassendem Wissen in den Bereichen digitales Marketing, "
                "Content-Erstellung, SEO, Social Media Marketing und Branding. Deine Aufgabe ist es, ansprechende, überzeugende "
                "und zielgerichtete Marketingtexte zu erstellen, die Kunden direkt ansprechen und detaillierte Informationen über "
                "das Produkt oder die Dienstleistung liefern. Achte darauf, den Ton und den Stil an die Zielgruppe anzupassen und "
                "professionelle Marketingstandards einzuhalten. Deine Texte sollen klar, präzise und wirkungsvoll sein, um die "
                "Aufmerksamkeit der Kunden zu gewinnen und sie zum Handeln zu motivieren. Integriere den bereitgestellten Produktlink in den Text, indem du ihn als Hyperlink verwendest. Formatiere die Ausgabe in gut strukturiertem HTML ohne Codeblock-Deklarationen.\n\n"
                f"Erstelle einen ansprechenden Marketingtext für folgendes Produkt: {product_description} Verwende diesen Link, um weitere Informationen zu erhalten: {product_link}"
            )
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=500,  # Erhöht für detailliertere Texte
                temperature=0.7,  # Optional: Kreativität anpassen
            )
            generated_text = response.choices[0].text.strip()

        # Post-Processing: Entferne Codeblock-Deklarationen, falls vorhanden
        # Entferne ```html und ``` am Anfang und Ende des Textes
        generated_text = re.sub(r'^```html\s*', '', generated_text)
        generated_text = re.sub(r'```\s*$', '', generated_text)

        # Überprüfe, ob der Text bereits HTML enthält
        if not re.search(r'<[^>]+>', generated_text):
            # Kein HTML erkannt, konvertiere Markdown zu HTML
            generated_text = markdown.markdown(generated_text)

        return generated_text

    except openai.error.AuthenticationError:
        raise Exception("Authentifizierungsfehler: Überprüfe deinen API-Schlüssel.")
    except openai.error.OpenAIError as e:
        raise Exception(f"OpenAI-Fehler: {e}")
    except Exception as e:
        raise Exception(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

def generate_email_subject(product_description, product_link, api_key, model="text-davinci-003"):
    openai.api_key = api_key

    chat_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"]

    try:
        if model in chat_models:
            # Verwende den Chat-Completion Endpoint für Chat-Modelle
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du bist ein KI-Assistent, der prägnante und ansprechende E-Mail-Betreffzeilen für Marketingkampagnen erstellt. "
                            "Deine Betreffzeilen sollen die Aufmerksamkeit der Empfänger auf sich ziehen und zum Öffnen der E-Mail animieren."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Erstelle einen prägnanten und ansprechenden E-Mail-Betreff für eine Marketingkampagne basierend auf folgendem Produkt:\n\nBeschreibung: {product_description}\nLink: {product_link}\n\nBetreff: Ohne Anführungszeichen."
                    }
                ],
                max_tokens=15,
                temperature=0.7,
            )
            generated_subject = response.choices[0].message['content'].strip()
        else:
            # Verwende den Completion Endpoint für klassische Modelle
            prompt = (
                "Du bist ein KI-Assistent, der prägnante und ansprechende E-Mail-Betreffzeilen für Marketingkampagnen erstellt. "
                "Deine Betreffzeilen sollen die Aufmerksamkeit der Empfänger auf sich ziehen und zum Öffnen der E-Mail animieren.\n\n"
                f"Erstelle einen prägnanten und ansprechenden E-Mail-Betreff für eine Marketingkampagne basierend auf folgendem Produkt:\n\nBeschreibung: {product_description}\nLink: {product_link}\n\nBetreff: Ohne Anführungszeichen."
            )
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=50,
                temperature=0.7,
            )
            generated_subject = response.choices[0].text.strip()

        # Nachbearbeitung: Entferne Anführungszeichen, falls vorhanden
        generated_subject = re.sub(r'^["\']+', '', generated_subject)  # Entferne führende Anführungszeichen
        generated_subject = re.sub(r'["\']+$', '', generated_subject)  # Entferne abschließende Anführungszeichen

        # Weitere Nachbearbeitung: Entferne unerwünschte Leerzeichen oder Zeichen
        generated_subject = generated_subject.strip()

        return generated_subject

    except openai.error.AuthenticationError:
        raise Exception("Authentifizierungsfehler: Überprüfe deinen API-Schlüssel.")
    except openai.error.OpenAIError as e:
        raise Exception(f"OpenAI-Fehler: {e}")
    except Exception as e:
        raise Exception(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
