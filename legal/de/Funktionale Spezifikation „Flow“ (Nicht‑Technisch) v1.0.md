# Funktionale Spezifikation „Flow“ (Nicht‑Technisch) v1.0

Zweck dieses Dokuments
- Diese Spezifikation beschreibt in allgemeinverständlicher Sprache, was die gelieferte Browser‑Erweiterung („Flow“) tut und was nicht. Sie dient der Abnahme sowie als Bezugspunkt für die Gewährleistung. Alles, was hier nicht beschrieben ist, ist nicht Leistungsbestandteil und kann eine neue Vereinbarung erfordern.

1) Was die Erweiterung tut (High Level)
- Automatisiert einfache, wiederholbare Aktionen auf einer kleinen Menge von Webseiten im Zusammenhang mit Nachrichten und Produktangeboten.
- Überwacht neue Nachrichten und öffnet relevante Links innerhalb definierter Grenzen und Zeitfenster.
- Auf Produktseiten folgt sie Links und führt eine vordefinierte „Kaufangebot“-Sequenz aus, wenn die Bedingungen erfüllt sind.
- Ist eine bildbasierte Prüfung erforderlich (z. B. visuelle Erkennung), sendet sie das Bild an die TRC‑Backend‑API und nutzt den zurückgelieferten Text/das Ergebnis.
- Bietet ein Popup zur Anzeige aktiver Aufgaben („Flows“) und einen Schalter zum globalen Aktivieren/Deaktivieren der Erweiterung.
- Bietet eine Optionsseite zur Eingabe des API‑Tokens und zur Anpassung des Verhaltens (z. B. Aktualisierungsintervalle, tägliche Zeitfenster, aktive Überwachungen).

2) Wo sie funktioniert (unterstützte Seiten)
- Outlook Web (Posteingang): outlook.office.com (sowie Microsofts sicherheitsgespiegelte Domain) — „E‑Mail‑Modus“.
- HanseMerkur‑Seiten (und localhost‑Äquivalente für Tests):
  - Posteingang: my_message_center_inbox.html — „Inbox‑Modus“
  - Nachrichtendetails: my_message_center_show_message.php
  - Artikelseite: item.php
  - Kauf‑Jetzt‑Seite: buy_now/id/*

3) Verhalten auf den einzelnen Seiten
A. Outlook Web: E‑Mail‑Modus
- Ist der E‑Mail‑Modus EIN, prüft die Erweiterung den Posteingang in konfigurierten Intervallen (siehe Optionen) und sucht nach Nachrichten mit relevanten Links.
- Findet sie einen relevanten Link, wird dieser in einem neuen Tab geöffnet, um die Verarbeitung auf der Zielseite fortzusetzen.
- Sie sendet keine E‑Mails, löscht keine E‑Mails, markiert keine E‑Mails als gelesen/ungelesen und ändert keine Postfacheinstellungen.
- Ist der E‑Mail‑Modus AUS, findet keine Prüfung oder Öffnung von Links statt.

B. HanseMerkur Posteingang: my_message_center_inbox.html
- Ist der Inbox‑Modus EIN, lädt die Erweiterung diese Seite in der konfigurierten Frequenz neu und scannt sie nach Nachrichtenlinks, die den Kriterien entsprechen.
- Es werden pro Scan bis zu einer konfigurierten Maximalzahl von Links geöffnet (Grenze in den Optionen einstellbar).
- Zwischen dem Öffnen von Links wird kurz pausiert, um Browser/Seite zu schonen (einstellbar in den Optionen).
- Ist der Inbox‑Modus AUS, werden diese Seite nicht neu geladen und keine Links geöffnet.

C. HanseMerkur Nachrichtendetails: my_message_center_show_message.php
- Wird die Seite aus dem E‑Mail‑ oder Inbox‑Modus heraus geöffnet, sucht die Erweiterung den primären Produktlink und öffnet ihn.
- Ist kein Link vorhanden oder hat sich das Seitenformat geändert, erfolgt keine Aktion.

D. HanseMerkur Artikelseite: item.php
- Die Erweiterung liest sichtbare Informationen aus, die für die Entscheidung über das weitere Vorgehen erforderlich sind (z. B. Produkttyp oder Alter auf der Seite).
- Bietet die Seite einen „Jetzt kaufen“-Link, folgt die Erweiterung diesem zur Kauf‑Jetzt‑Seite.
- Die Erweiterung bearbeitet auf dieser Seite keine Inhalte und sendet keine Formulare ab.

E. HanseMerkur Kauf‑Jetzt‑Seite: buy_now/id/*
- Die Erweiterung führt eine vordefinierte „Kaufangebot“-Sequenz aus, die für diese Seite ausgelegt ist.
- Fehlen erwartete Elemente oder hat sich die Seite wesentlich geändert, protokolliert die Erweiterung das Problem und stoppt (keine unsicheren Aktionen).
- Sicherheitsprüfungen werden nicht umgangen. Erscheint eine bildbasierte Abfrage (z. B. Captcha), kann die Erweiterung das Bild erfassen und an das TRC‑Backend senden. Liefert das Backend ein Ergebnis, wird dieses genutzt; andernfalls stoppt die Erweiterung kontrolliert.

Wichtig: Die Erweiterung agiert ausschließlich auf den oben genannten Seiten. Ändern sich Layout, Bezeichnungen oder Verhalten dieser Seiten oder kommen neue Seiten hinzu, kann zusätzlicher, vergütungspflichtiger Aufwand erforderlich werden.

4) Popup‑Seite (für den Nutzer sichtbar)
- Ein/Aus‑Schalter: Ein globaler Umschalter, der die Automation EIN/AUS schaltet.
- Aktive Flows: Eine einfache Liste jüngster/aktiver Aufgaben mit ihrem Status (laufend, erledigt, fehlgeschlagen), Startzeit und Dauer. Diese Liste dient nur der Sichtbarkeit und ermöglicht keine manuelle Steuerung der Einzelschritte.

5) Optionsseite (Konfiguration)
A. Authentifizierung
- API‑Token: Feld zum Einfügen des vom TRC‑Webportal erhaltenen Tokens. Ohne gültiges Token funktionieren bildbasierte Lösungen nicht; entsprechende Aufgaben schlagen kontrolliert fehl.

B. Nachrichtenüberwachung — E‑Mail‑Modus
- E‑Mail‑Modus (EIN/AUS): Ist EIN, wird der Outlook‑Web‑Posteingang auf neue relevante Nachrichten geprüft.
- Aktualisierungszeitraum E‑Mail: Zwei Zahlen (Minimum und Maximum, in Minuten) bestimmen die Prüfintervalle. Die Erweiterung nutzt diese, um Abstände zu variieren und ständiges Polling zu vermeiden.

C. Nachrichtenüberwachung — Inbox‑Modus
- Inbox‑Modus (EIN/AUS): Ist EIN, wird die HanseMerkur‑Inbox regelmäßig aktualisiert.
- Inbox‑Aktualisierungsfrequenz: Ein einfaches Schema, wie oft die Seite aktualisiert wird (Standard: häufige, kurze Checks). Praktisch bedeutet dies „lade die Inbox alle paar Sekunden neu“, solange die Seite geöffnet ist.
- Max. Links pro Scan: Begrenzt, wie viele Nachrichtenlinks pro Scan geöffnet werden (Standard 10), um zu viele Tabs zu vermeiden.
- Verzögerung zwischen Linköffnungen: Kurze Pause zwischen dem Öffnen jedes Links (Standard ~0,4 Sekunden) für Stabilität.

D. Gültige Tageszeiten (je Wochentag)
- Für jeden Tag (Sonntag–Samstag) können Automation und Start‑/Endzeiten konfiguriert werden. Außerhalb dieser Zeiten laufen keine automatisierten Aktionen, selbst wenn Modi EIN sind.

E. Produktfilter (falls vorhanden)
- Kategorie‑Schalter (z. B. Tiere, Krebs, Personen) aktivieren/deaktivieren die Verarbeitung entsprechender Produktkategorien. Ist eine Kategorie AUS, überspringt die Erweiterung diese Elemente.
- Zusätzliche Zeitwerte pro Kategorie steuern die ungefähre Taktung.

6) Was die Erweiterung NICHT tut
- Sie sendet oder löscht keine E‑Mails.
- Sie ändert keine Postfacheinstellungen und verwaltet keine Ordner.
- Sie agiert nicht auf anderen Websites als den ausdrücklich genannten.
- Sie garantiert keinen Kauf/Erfolg auf Drittseiten (Verfügbarkeit, UI‑Änderungen, Netzwerkeffekte oder Sicherheitsmechanismen können Aktionen verhindern).
- Sie speichert keine personenbezogenen Daten auf externen Diensten, außer den Bildern/Ergebnissen, die ausschließlich zur Bildinterpretation bei Bedarf an das TRC‑Backend gesendet werden.

7) Schutzmechanismen und Grenzen
- Globaler EIN/AUS‑Schalter im Popup.
- Tägliche Zeitfenster zur Vermeidung von Aktionen außerhalb der Geschäftszeiten.
- Ratenbegrenzungen: maximale Links pro Scan; kurze Pausen zwischen Öffnungen.
- Fehlt das API‑Token oder ist es ungültig, werden betroffene Aktionen gestoppt und ein Fehler geloggt.
- Ändert sich eine Seite oder fehlt ein erforderliches Element, stoppt die Erweiterung die Aktion und protokolliert dies.

8) Annahmen und Abhängigkeiten
- Die unterstützten Websites bleiben im Wesentlichen so, wie während der Entwicklung verwendet (gleiche Seitennamen und wesentliche Elemente).
- Der Nutzer stellt ein gültiges API‑Token bereit und akzeptiert die TRC‑Bedingungen.
- Das TRC‑Backend ist erreichbar und liefert Ergebnisse für bildbasierte Prüfungen.
- Die Erweiterung ist aktiviert, die relevanten Modi sind EIN und der Browser bleibt auf den relevanten Seiten geöffnet.

9) Abnahmekriterien (nutzer‑sichtbar)
- Installation: Die Erweiterung lässt sich in Chrome laden und zeigt Popup und Optionsseite an.
- Konfiguration: Der Nutzer kann ein API‑Token einfügen; Einstellungen werden gespeichert.
- E‑Mail‑Modus: Ist EIN und innerhalb gültiger Zeitfenster, prüft die Erweiterung periodisch den Outlook‑Web‑Posteingang und öffnet relevante Links. Ist AUS, passiert dort nichts.
- Inbox‑Modus: Ist EIN und innerhalb gültiger Zeitfenster, aktualisiert die Erweiterung die HanseMerkur‑Inbox, öffnet bis zur konfigurierten Maximalzahl an Links pro Scan und pausiert kurz zwischen Öffnungen. Ist AUS, passiert dort nichts.
- Produkt‑Flow: Auf Artikel‑ und Kauf‑Jetzt‑Seiten folgt die Erweiterung der vordefinierten Sequenz; fehlt etwas oder hat sich etwas geändert, stoppt sie sicher und protokolliert dies.
- Bildlösung: Erforderlichenfalls sendet die Erweiterung ein Bild an das TRC‑Backend und nutzt das Ergebnis bei Erfolg; andernfalls protokolliert sie und stoppt.

10) Bezug zur Gewährleistung
- Die 90‑Tage‑Gewährleistung deckt reproduzierbare Fehler ab, bei denen die Erweiterung die hier beschriebenen Verhaltensweisen innerhalb der konfigurierten Optionen und gültigen Zeitfenster auf den unterstützten Seiten in der vereinbarten Umgebung nicht erbringt.
- Änderungen an Drittseiten, zusätzliche Seiten, neue Flows oder hier nicht beschriebene Verhaltensweisen sind nicht umfasst und können eine gesonderte, vergütungspflichtige Beauftragung erfordern.

11) Bildlöser – Gewährleistung und Nutzungshinweis
- Der Bildlöser ist eine optionale Komfortfunktion, die versucht, eine Matheaufgabe aus einem Bild zu erkennen und nur das endgültige Zahlen‑Ergebnis zurückzugeben.
- Er nutzt einen KI‑Dienst eines externen Anbieters. Genauigkeit, Verfügbarkeit und Antwortzeiten sind nicht garantiert und können sich ohne Ankündigung ändern.
- Ergebnisse können unvollständig oder falsch sein, oder es wird keine Aufgabe erkannt – insbesondere bei unscharfen oder qualitativ schlechten Bildern. Bitte prüfen Sie Ergebnisse stets eigenständig.
- Die Funktion ist nicht für sicherheitskritische oder andere risikoreiche Anwendungen gedacht. Die Nutzung erfolgt auf eigenes Risiko; wir haften nicht für Schäden, die aus der Nutzung der Ergebnisse entstehen.
- Übermittelte Bilder werden ausschließlich zur Bearbeitung der Anfrage an den externen Anbieter übertragen; wir bewahren sie nicht länger auf als für die Leistungserbringung notwendig. Die Nutzung dieser Funktion setzt Ihre Zustimmung zu dieser Übertragung voraus.
- Wir können die Funktion jederzeit einschränken, aussetzen oder einstellen (z. B. aufgrund von Anbieterlimits, Kosten, Richtlinien oder Missbrauchsprävention).
- Wenn keine gültige Matheaufgabe erkannt wird, kann eine entsprechende Hinweis‑Meldung zurückgegeben werden.
- Die Funktion ändert Ihre Daten oder Dokumente nicht automatisch; sie liefert lediglich einen Vorschlag, den Sie selbst prüfen.
- Diese Funktion wird „wie besehen“ und ohne Gewähr bereitgestellt (einschließlich ohne Gewähr für Genauigkeit oder Eignung für einen bestimmten Zweck).
- Erkennungs- und Ausgaberegeln für Matheaufgaben:
  - Enthält das Bild eine Matheaufgabe, gib ausschließlich die numerische Lösung zurück.
  - Bei Ausdrücken wie "2+2": gib "4" zurück.
  - Bei Gleichungen wie "x=5+3": gib "8" zurück.
  - Gibt es mehrere Aufgaben, löse alle und gib die Lösungen kommagetrennt aus.
  - Kann keine Matheaufgabe erkannt werden, gib "ERROR: No math problem found" zurück.
  - Keine Einheiten, Erklärungen oder sonstiger Text — nur die Zahl(en).
- Beispiele (nicht abschließend):
  - Bild zeigt "3 + 5" → Rückgabe: "8"
  - Bild zeigt "12 × 4" → Rückgabe: "48"
  - Bild zeigt "100 ÷ 5" → Rückgabe: "20"
  - Bild zeigt "7 - 3" → Rückgabe: "4"
  - Bild zeigt "2³" → Rückgabe: "8"
  - Bild zeigt "√16" → Rückgabe: "4"
  - Bild zeigt "Wie viel sind 15 % von 200?" → Rückgabe: "30"
  - Bild zeigt mehrere: "2+2" und "3×3" → Rückgabe: "4, 9"
