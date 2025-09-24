# Flow‑Lieferumfang Spezifikation v1.0 (Anlage zu SALE-v1.0)

1. Überblick und Zweck
- Liefergegenstand: Eine mit Chrome kompatible Browser‑Erweiterung („Flow“) als verschleierter JavaScript‑Build (kein unverschleierter Quellcode).
- Zweck: Automatisierung von Nutzer‑Flows auf bestimmten Webseiten, Überwachung von Posteingängen, Öffnen relevanter Produktlinks sowie bildbasierte Verarbeitung über die TRC‑Backend‑API.
- Primäre Domains und Kontexte:
  - Microsoft Outlook Web: https://outlook.office.com/mail/* (sowie mcas‑Spiegel)
  - HanseMerkur‑Auktionsseiten:
    - Artikelseite: https://auktion.hansemerkur.de/item.php (und localhost‑Variante)
    - Kauf‑Jetzt‑Seite: https://auktion.hansemerkur.de/buy_now/id/* (und localhost‑Variante)
    - Nachrichtenansicht: https://auktion.hansemerkur.de/my_message_center_show_message.php (und localhost‑Variante)
    - Posteingang: https://auktion.hansemerkur.de/my_message_center_inbox.html (und localhost‑Variante)

2. Architektur und Komponenten
- Hintergrund‑Service Worker: background.js
  - Empfängt Nachrichten von Content‑Skripten und orchestriert Aktionen.
  - Verwaltet Tab‑Lebenszyklus (Öffnen/Schließen/Neu laden), Flow‑Status und Buying‑State‑Koordination.
  - Stellt einen Bildverarbeitungsbefehl bereit, der das TRC‑Backend aufruft.
- Content‑Skripte (als IIFE‑Bundles kompiliert):
  - email.iife.js, inbox.iife.js, item.iife.js, buyOffer.iife.js, myOffer.iife.js
  - Einsatz gemäß Manifest‑Matches (siehe Abschnitt 1).
  - Erkennen Seitenzustände, extrahieren IDs/Metadaten, senden Befehle an den Hintergrund.
- Popup‑UI: popup/index.html (Benutzersicht und Schnellsteuerung).
- Optionsseite: options/index.html (Konfigurationsoberfläche, Token‑Eingabe, Feature‑Schalter).
- Geteilte Pakete: Konfiguration, Logging, Utilities, i18n, Storage und Typen, die moduleübergreifend genutzt werden.

3. Konfiguration
- Backend‑Basis‑URL (Build‑Zeit): per Umgebungsvariable CEB_TRC_BACKEND_URL; erforderlich für Produktions‑Builds.
- API‑Token (Laufzeit): Speicherung in der Extension Local Storage über die Optionsseite.
- Zentrale Schalter und Timings (Laufzeit, in Optionen verwaltet):
  - emailMode (an/aus), inboxMode (an/aus)
  - inboxReloadSeconds, inboxPostReloadDelayMs, inboxMaxLinksPerScan, inboxInterOpenDelayMs
  - operationalHours pro Tag (enabled/min/max)
  - Produkt‑Strategie‑Flags und Timer (animals, cancer, people)
- Storage: Chrome Extension Local Storage (zustandsbezogene Schlüssel mit Live‑Updates). Kein Server‑Side‑Storage.

4. Backend‑API‑Integration
- Endpoint: POST {CEB_TRC_BACKEND_URL}/api/core/solve
- Authentifizierung: Authorization: Bearer <token>
  - Tokens werden über /api/customers/tokens erstellt und verwaltet (Server‑Side; nicht Teil der Extension).
  - Nutzer muss Bedingungen akzeptiert und E‑Mail verifiziert haben, damit Tokens gültig sind.
- Request (multipart/form‑data):
  - file: Bild‑Binary (PNG/JPEG), aus Base64 von der Extension konvertiert
  - flow_id: String‑Bezeichner des aktuellen Flows (für Ergebnis‑Caching/Attribution)
- Erfolgsantwort (HTTP 200, JSON):
  - {
    "request_id": string,
    "result": string,    // Solver‑Ausgabe
    "duration_ms": number
  }
- Fehlerantworten:
  - 400: fehlende/ungültige Eingaben
  - 401: fehlendes/ungültiges Token
  - 500: Solver/Interner Fehler (Body enthält { detail, code })
- Hinweise:
  - Backend kann gecachte Ergebnisse zurückliefern, wenn flow_id mit früherem Solve übereinstimmt.
  - Extension behandelt Non‑2xx als Fehler und zeigt Meldungen im Log an.

5. Funktionales Verhalten (High Level)
- E‑Mail‑Route (Outlook):
  - Scannt ungelesene E‑Mails gemäß Konfiguration, öffnet Ziellinks, die zu Artikel‑ oder Kauf‑Jetzt‑Seiten führen.
- Inbox‑Route (HanseMerkur):
  - Lädt die Inbox‑Seite periodisch neu und scannt sie nach relevanten Nachrichten/Links bis zu konfigurierten Limits.
- Artikel‑Route:
  - Extrahiert Produktinformationen (z. B. versicherte Art/Alter) und stellt sie dem Flow für Entscheidungen bereit.
- Kauf‑Jetzt‑Route:
  - Führt den „Kaufangebot“-Workflow (Injector/Executor‑Modell) mit konfiguriertem Timeout und Telemetrie aus.
- Nachrichtenansicht:
  - Navigiert zu und öffnet erforderliche Produktlink(s).
- Bildverarbeitung:
  - Bei Bedarf Base64‑Bild an den Hintergrund senden; dieser konvertiert zu Blob und POSTet an /api/core/solve mit flow_id; bei Erfolg { result } zurück an Content‑Ursprung.

6. Sicherheit und Datenschutz
- API‑Tokens werden lokal in der Extension mittels Chrome Storage gespeichert und vom Hintergrund für API‑Aufrufe gelesen.
- API‑Aufrufe erfolgen aus dem Hintergrundskript zur Vermeidung von CORS‑Problemen.
- Host‑Permissions sind breit („<all_urls>“), um den Betrieb über benötigte Seiten hinweg zu gewährleisten; Matches sind in Content‑Skripten eingeschränkt.
- Es werden keine personenbezogenen Daten an das Backend übertragen, außer diejenigen, die in Bildern oder bewusst durch Flows in Logs enthalten sind.

7. Packaging und Lieferung
- Build‑Prozess: pnpm build (erfordert Node >= 22.x; Vite + Turbo‑Repo Tooling).
- Erforderliche Env: CEB_TRC_BACKEND_URL muss zur Build‑Zeit gesetzt sein.
- Output: gezippter Extension‑Bundle via pnpm zip, geeignet für manuelle Installation oder Store‑Upload.
- Obfuskation: Ausgelieferter JS ist minifiziert/verschleiert; kein unverschleierter Quellcode oder Toolchain enthalten.

8. Abnahmekriterien
- Installation: Extension kann in Chrome geladen werden und zeigt Options‑ und Popup‑Seiten.
- Konfiguration: Nutzer kann API‑Token in Optionen setzen; Status wird persistiert.
- Domain‑Matching: Content‑Skripte laden nur auf den in Abschnitt 1 genannten URLs.
- Flow‑Start/Tracking: Start eines Flows (E‑Mail oder Inbox) erzeugt einen Flow‑Record; Flows können als erledigt/fehlgeschlagen markiert werden; Tab‑Management ist konsistent (öffnen, schließen, aufräumen).
- API‑Call: Bei gültigem Token und Backend‑URL sendet Hintergrund POST an /api/core/solve mit (file, flow_id), erhält JSON mit result und gibt es an den Content‑Originator zurück.
- Fehlerbehandlung: Non‑2xx oder Netzwerkfehler werden erfasst und im Log angezeigt, ohne die Extension zum Absturz zu bringen.
- Performance: Standard‑Polling/Reload‑Intervalle und Link‑Limits werden eingehalten; kein übermäßiger Tab‑Churn; Hintergrund‑Logs bleiben responsiv.

9. Nicht‑funktionale Anforderungen
- Browser: Chrome (MV3 Service Worker). Firefox‑Build durch Skripte vorbereitet, aber außerhalb des Umfangs, sofern nicht ausdrücklich angefragt.
- Resilienz: Blockiert UI nicht; Retry/Backoff für transiente Fehler, wo implementiert; respektiert konfigurierte Betriebszeiten.
- Observability: Hintergrund‑Logger vorhanden; Telemetrie‑Events in Konsole (kann künftig an externe Senken angepasst werden).

10. Außerhalb des Umfangs
- Store‑Einreichung, Signierung oder Bereitstellung in Marktplätzen.
- Server‑seitige Token‑Ausgabe oder Web‑Portal‑Workflows.
- Nutzerdefinierte Captchas oder Änderungen auf Drittseiten, die sich nicht in Manifests/Selektoren widerspiegeln.

11. Referenzen
- Flow‑Diagramme: flow/diagrams/*.puml (email_flow, inbox_flow, overview)
- Manifest und Content‑Registrierungen: flow/chrome-extension/manifest.ts
- Hintergrund‑Entry: flow/chrome-extension/src/background/index.ts (processImageAPI, Tab‑ und Flow‑Handler)
- Konfigurations‑Storage Defaults: flow/packages/storage/lib/impl/extension-config-storage.ts
- Typen und Kommandos: flow/packages/types/lib/app/types.ts
- Backend‑Endpunkte: backend/core/urls.py (/api/core/solve), backend/customers/urls.py (Tokens, Nutzung), backend/README.md (API‑Nutzung)
