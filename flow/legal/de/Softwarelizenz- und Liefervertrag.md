# Softwarelizenz- und Liefervertrag

**Zwischen**

**Amadou Cisse**  
Marienhof 7  
22399 Hamburg  
Deutschland  
Steuernummer: 5003904247  
USt-IdNr.: DE369245022  
("Entwickler")  

und

**Patrycjusz Szmidt**  
Am Casinopark 15  
21465 Wentorf bei Hamburg  
Deutschland  
("Kunde")  

## 1. Vertragsgegenstand

Der Entwickler hat für den Kunden eine Software‑Anwendung ("Software") entwickelt und erstellt.
Gegenstand dieser Lieferung ist insbesondere das Feature "Text CAPTCHA Solver" gemäß der Leistungsbeschreibung in Anlage 1.
Der Entwickler verpflichtet sich, die Software an den Kunden zu liefern, und der Kunde verpflichtet sich, das vereinbarte Entgelt zu zahlen, jeweils nach Maßgabe dieses Vertrags.

## 2. Lieferung und Abnahme

2.1 Der Entwickler liefert die Software als verschleierten JavaScript‑Build (inklusive zugehöriger Laufzeit‑Assets), der zur Ausführung geeignet ist, ohne unverschleierten Quellcode oder Entwicklungs‑Toolchain. Eine Dokumentation ist nicht enthalten, sofern nicht ausdrücklich schriftlich vereinbart.

2.2 Der Kunde prüft die Software binnen 14 Tagen nach Lieferung. Entspricht die Software im Wesentlichen den vereinbarten Spezifikationen, erklärt der Kunde die Abnahme schriftlich. Erfolgt innerhalb dieser Frist kein schriftlicher Widerspruch, gilt die Software als abgenommen.

2.3 Sichere elektronische Lieferung (Downloadlink + Prüfsumme)  
(a) Verpackung und Benennung. Der Liefergegenstand wird als einzelnes .zip‑Archiv mit eindeutigem, versioniertem Dateinamen im Format productname_vX.Y.Z_YYYY-MM-DD.zip verpackt.  
(b) Prüfsumme. Vor der Lieferung berechnet der Entwickler eine SHA‑256‑Prüfsumme für das Archiv (die „Prüfsumme“).  
(c) Liefermitteilung und Lieferdatum. Der Entwickler versendet eine E‑Mail in Textform gemäß Abschnitt 7.3/7.7 an die Mitteilungsadressen mit (i) einem privaten, befristeten Downloadlink, der mindestens vierzehn (14) Kalendertage gültig ist (die „Link‑Gültigkeitsdauer“), und (ii) der Prüfsumme (die „Liefermitteilung“). Der Zeitpunkt des Versands der Liefermitteilung gilt als „Lieferdatum“.  
(d) Download und Verifikation durch den Kunden. Der Kunde lädt das Archiv innerhalb der Link-Gültigkeitsdauer herunter und verifiziert die Integrität, indem er eine SHA-256-Prüfsumme der heruntergeladenen Datei bildet und mit der Prüfsumme vergleicht. Der Kunde bestätigt Empfang und Integrität per Antwort-E-Mail. Der Entwickler stellt auf Anfrage des Kunden während der Prüf-/Abnahmefrist gemäß Abschnitt 2.2 erneut einen befristeten Downloadlink zur Verfügung.  
(e) Zugangs- oder Integritätsprobleme. Kann der Kunde auf den Link nicht zugreifen oder stellt er eine Abweichung der Prüfsumme fest, informiert er den Entwickler unverzüglich. Spätestens hat die Mitteilung innerhalb der Prüf-/Abnahmefrist gemäß Abschnitt 2.2 zu erfolgen. Der Entwickler stellt zeitnah einen neuen Downloadlink und eine neue Prüfsumme bereit. Bei vom Entwickler bestätigter Prüfsummenabweichung beginnt die Prüf-/Abnahmefrist gemäß Abschnitt 2.2 mit dem Datum der Neuzustellung erneut.  
(f) Nachweis. Die Liefermitteilung und die Prüfsumme stellen den maßgeblichen Nachweis für den Inhalt der gelieferten Datei dar. Der Entwickler darf die Liefermitteilung und zugehörige Protokolle als Liefernachweis aufbewahren.  
(g) Vertraulichkeit. Der Kunde behandelt den Downloadlink und das gelieferte Paket als vertrauliche Informationen und gibt den Link nur an Personen weiter, die nach diesem Vertrag zur Entgegennahme der Software berechtigt sind.  

2.4 Auswirkung auf die Abnahmefrist  
Für Abschnitt 2.2 gilt die Lieferung mit dem Lieferdatum als erfolgt. Die vierzehntägige Prüf-/Abnahmefrist beginnt mit dem Zeitpunkt, zu dem der Kunde die Datei erstmals herunterladen kann (Zugangsmöglichkeit), spätestens jedoch zwei (2) Geschäftstage nach Lieferdatum, sofern der Downloadlink funktionsfähig war. Bei bestätigter Prüfsummenabweichung und Neuzustellung beginnt die vierzehntägige Frist mit dem Datum der Neuzustellung erneut.

## 3. Rechteeinräumung

3.1 Mit vollständiger Zahlung räumt der Entwickler dem Kunden ein einfaches, nicht übertragbares und nicht unterlizenzierbares Nutzungsrecht an der Software für die internen Geschäftszwecke des Kunden ein.

3.2 Die eingeräumten Rechte sind zeitlich und räumlich unbeschränkt, vorbehaltlich der Beschränkungen in diesem Abschnitt 3.

3.3 Der Kunde darf die Software zum Betrieb, für Backups und Archivierungszwecke ausführen und kopieren. Der Kunde darf die Software konfigurieren und Integrationen über dokumentierte Schnittstellen entwickeln. Ein Zugriff auf unverschleierten Quellcode wird nicht gewährt.

3.4 Der Kunde ist nicht berechtigt, die Software zurückzuentwickeln, zu dekompilieren, zu entschleiern oder sonst zu versuchen, den Quellcode herzuleiten, außer in dem gesetzlich zwingend zulässigen Umfang. Änderungen am verschleierten Build über Konfiguration und dokumentierte Erweiterungspunkte hinaus sind unzulässig.

3.5 Sämtliche Rechte an geistigem Eigentum verbleiben beim Entwickler. Der Entwickler ist berechtigt, Dritten Nutzungsrechte einzuräumen.

3.6 Open‑Source‑Komponenten. Sofern die Software Komponenten Dritter unter Open‑Source‑Lizenzen enthält, stehen diese unter deren jeweiligen Lizenzen. Der Entwickler stellt auf Anfrage einen Hinweis auf solche Komponenten bereit; der Kunde beachtet die einschlägigen Open‑Source‑Lizenzen.

3.7 Exklusivität der Lieferung.
Der Entwickler behält sämtliche Rechte an geistigem Eigentum an der Software, einschließlich des unverschleierten Quellcodes. Der Entwickler verpflichtet sich jedoch, den unter diesem Vertrag gelieferten identischen Software‑Build nicht an Dritte zu verkaufen, zu lizenzieren oder anderweitig bereitzustellen. Diese Beschränkung hindert den Entwickler nicht daran, (i) allgemeine Konzepte, Know‑how oder Komponenten, die im Zuge der Erstellung der Software entwickelt wurden, wiederzuverwenden, (ii) für andere Kunden abweichende Softwarelösungen zu entwickeln und zu lizenzieren oder (iii) Teile der Software zu verwenden, die allgemeiner Natur sind und nicht speziell auf die Spezifikationen des Kunden zugeschnitten wurden.

## 4. Gewährleistung und Haftung

4.1 Gewährleistung. Der Entwickler gewährleistet, dass die Software zum Zeitpunkt der Lieferung im Wesentlichen den vereinbarten Spezifikationen entspricht.

4.2 Gewährleistungsfrist und Abhilfe. Die Gewährleistungsfrist beträgt 90 Tage ab Abnahme. Bei innerhalb der Gewährleistungsfrist berechtigt gerügten Mängeln wird der Entwickler nach eigener Wahl nachbessern oder Ersatz liefern. Scheitert die Nachbesserung/Ersatzlieferung endgültig innerhalb eines angemessenen Zeitraums, kann der Kunde die Vergütung mindern oder vom Vertrag zurücktreten. Während der Gewährleistungsfrist behebt der Entwickler reproduzierbare Mängel, die eine wesentliche Abweichung von den vereinbarten Spezifikationen in der vereinbarten Betriebsumgebung verursachen, ohne zusätzliche Vergütung; alle weiteren Support‑ und Wartungsleistungen (einschließlich Erweiterungen, Kompatibilitätsarbeiten und Nachbesserungen nach Ablauf der Gewährleistung) sind ausgeschlossen, sofern nicht in Abschnitt 4.7 ausdrücklich abweichend geregelt.

4.3 Ausschlüsse. Die Gewährleistung erstreckt sich nicht auf Mängel, die durch Modifikationen, unsachgemäße Nutzung, Betrieb außerhalb der vereinbarten Umgebung oder externe Systeme verursacht werden.

4.4 Haftungsausschlüsse. Nichts in diesem Vertrag beschränkt oder schließt die Haftung für Vorsatz, grobe Fahrlässigkeit, Verletzung von Leben, Körper oder Gesundheit oder nach dem Produkthaftungsgesetz aus.

4.5 Kardinalpflichten; Haftungsbegrenzung bei leichter Fahrlässigkeit. Bei leicht fahrlässiger Verletzung wesentlicher Vertragspflichten (Kardinalpflichten) ist die Haftung des Entwicklers auf den vorhersehbaren, typischerweise eintretenden Schaden begrenzt, maximal jedoch auf das Zweifache der vom Kunden nach Abschnitt 5.1 gezahlten Gesamtvergütung. Im Übrigen ist die Haftung für leichte Fahrlässigkeit ausgeschlossen.

4.6 Haftungshöchstbetrag. Vorbehaltlich Abschnitt 4.4 ist die Gesamthaftung des Entwicklers aus oder im Zusammenhang mit diesem Vertrag, gleich aus welchem Rechtsgrund, auf das Zweifache der vom Kunden nach Abschnitt 5.1 gezahlten Gesamtvergütung begrenzt.

4.7 Wartung und Support (inklusive, begrenzt)  
(a) Wartungsbeginn. Die Wartung beginnt am späteren der folgenden Zeitpunkte: (i) 20. Januar 2026 oder (ii) Abnahme gemäß Abschnitt 2.2.  
(b) Laufzeit. Die Wartung wird für 3 Monate ab Wartungsbeginn erbracht.  
(c) Umfang. Die Wartung umfasst ausschließlich Bugfixes für Fehler, die unmittelbar den in Anlage 1 beschriebenen Funktionsumfang (Text CAPTCHA Solver) betreffen.  
(d) Ausschlüsse. Nicht umfasst sind neue Features, Scope‑Erweiterungen, Anpassungen außerhalb des in Anlage 1 beschriebenen Funktionsumfangs sowie Arbeiten, die nicht als Bugfix qualifizieren.  
(e) Reaktionszeit. Der Entwickler wird Wartungsanfragen in Textform innerhalb von **24 Stunden** beantworten (Bestätigung des Eingangs und erste Rückmeldung). Eine konkrete Lösungsfrist ist damit nicht zugesagt.  
(f) Vergütung. Für die in diesem Abschnitt 4.7 beschriebenen Wartungsleistungen fällt keine zusätzliche Vergütung an.  

## 5. Vergütung

5.1 Die Gesamtvergütung für die Software beträgt **2.000 EUR (zweitausend Euro) inkl. 19% USt.**  
5.2 Die Vergütung ist innerhalb von 14 Tagen nach Lieferung und Abnahme fällig.  
5.3 Der Kunde erlangt die Nutzungsrechte erst nach vollständigem Zahlungseingang.  

## 6. Vertraulichkeit

6.1 Vertrauliche Informationen. “Vertrauliche Informationen” sind alle nicht allgemein bekannten geschäftlichen, technischen oder sonstigen Informationen, die eine Partei der anderen Partei im Zusammenhang mit diesem Vertrag offenlegt oder zugänglich macht, einschließlich insbesondere der Software, des gelieferten Pakets, Downloadlinks, Prüfsummen, Spezifikationen, Erkenntnisse über Funktionsweise, Testdaten sowie Preis- und Vertragsinhalte.

6.2 Verpflichtung. Die empfangende Partei wird Vertrauliche Informationen (i) ausschließlich zur Durchführung dieses Vertrags verwenden, (ii) geheim halten und mit mindestens der gleichen Sorgfalt schützen wie eigene vertrauliche Informationen, mindestens jedoch mit angemessener Sorgfalt, und (iii) nur solchen Mitarbeitern oder beauftragten Dritten zugänglich machen, die diese Informationen zur Vertragserfüllung benötigen und zur Vertraulichkeit verpflichtet sind.

6.3 Ausnahmen. Die Vertraulichkeitspflicht gilt nicht für Informationen, die die empfangende Partei nachweislich (i) bereits rechtmäßig kannte, (ii) ohne Verstoß gegen diesen Vertrag öffentlich bekannt werden, (iii) von einem Dritten rechtmäßig ohne Vertraulichkeitsverpflichtung erhalten hat oder (iv) unabhängig ohne Nutzung der Vertraulichen Informationen entwickelt hat.

6.4 Gesetzliche Offenlegung. Soweit eine Partei aufgrund Gesetzes, gerichtlicher oder behördlicher Anordnung zur Offenlegung verpflichtet ist, wird sie die andere Partei, soweit rechtlich zulässig, vorab informieren und den Umfang der Offenlegung auf das erforderliche Minimum beschränken.

6.5 Dauer. Diese Vertraulichkeitsverpflichtungen gelten für die Laufzeit dieses Vertrags und für drei (3) Jahre nach dessen Beendigung; für Geschäftsgeheimnisse im Sinne des GeschGehG gilt die Verpflichtung solange, wie diese Informationen Geschäftsgeheimnisse darstellen.

## 7. Sonstiges

7.1 Es gilt deutsches Recht.

7.2 Gerichtsstand ist Hamburg, Deutschland.

7.3 Änderungen bedürfen der Schriftform (Textform ausreichend, z. B. E‑Mail), sofern gesetzlich keine strengere Form erforderlich ist.

7.4 Salvatorische Klausel. Bleibt eine Bestimmung unwirksam, bleibt der Vertrag im Übrigen wirksam.

7.5 Höhere Gewalt. Keine Partei haftet für Verzögerungen oder Nichterfüllung aufgrund von Ereignissen außerhalb ihres zumutbaren Einflussbereichs, einschließlich Naturereignissen, Naturkatastrophen, Krieg, Terrorismus, Arbeitskämpfen, behördlichen Maßnahmen oder Ausfällen von Netzen/Cloud‑Anbietern Dritter.

7.6 Abtretung und Unterauftragsvergabe. Der Kunde darf Rechte oder Pflichten aus diesem Vertrag nur mit vorheriger schriftlicher Zustimmung des Entwicklers abtreten. Der Entwickler darf Subunternehmer einsetzen, bleibt jedoch für die Vertragserfüllung verantwortlich.

7.7 Mitteilungen. Mitteilungen sind an die oben genannten Adressen oder an schriftlich mitgeteilte aktualisierte Kontakte zu richten.

7.8 Rangfolge und Gesamtabrede. Dieser Vertrag stellt die Gesamtabrede der Parteien in Bezug auf die Software dar und geht entgegenstehenden Bedingungen vor, sofern die Parteien nicht ausdrücklich schriftlich etwas anderes vereinbaren.

## 8. Einhaltung von Recht und Nutzungsbedingungen

Der Kunde sichert zu und gewährleistet, dass die Nutzung der Software sämtlichen anwendbaren Gesetzen, Verordnungen und vertraglichen Verpflichtungen (einschließlich Nutzungsbedingungen Dritter oder Zugriffs­beschränkungen) entspricht. Der Kunde darf die Software nicht in einer Weise nutzen oder nutzen lassen, die einen unrechtmäßigen Zugriff auf oder eine missbräuchliche Verwendung von Computersystemen, Netzen oder Diensten darstellt oder erleichtert.

## 9. Verantwortlichkeit für die Nutzung

Der Kunde erkennt an, dass der Entwickler keinen Einfluss darauf hat, wie die Software genutzt wird. Der Kunde trägt die alleinige Verantwortung für Installation, Konfiguration und Betrieb der Software und dafür, dass eine solche Nutzung rechtmäßig ist. Der Entwickler billigt oder autorisiert keinen bestimmten Anwendungsfall.

## 10. Freistellung

10.1 Der Kunde stellt den Entwickler sowie dessen Organe, Mitarbeiter, Vertreter und Unterauftragnehmer von sämtlichen Ansprüchen, Forderungen, Klagen, Schäden, Bußgeldern, Strafen, Verbindlichkeiten, Kosten und Aufwendungen (einschließlich angemessener Rechtsanwalts- und Gerichtskosten) frei, verteidigt sie und hält sie schadlos, die sich aus oder im Zusammenhang mit Folgendem ergeben:

(a) der Nutzung der Software durch den Kunden, einschließlich jeglicher Nutzung, die gegen geltende Gesetze, Vorschriften oder vertragliche Bedingungen Dritter (einschließlich, aber nicht beschränkt auf Website‑Nutzungsbedingungen, Plattformregeln oder technische Schutzmaßnahmen) verstößt,
(b) der Behauptung, dass die Nutzung der Software durch den Kunden einem Dritten Schaden zugefügt hat oder in Systeme oder Dienste eines Dritten eingegriffen hat, oder
(c) jedem Verstoß gegen Zusicherungen, Verpflichtungen oder Pflichten aus diesem Vertrag.

10.2 Die Freistellungsverpflichtung gilt unabhängig davon, ob der Anspruch eines Dritten auf Vertrag, Delikt, gesetzliche Vorschriften oder andere Anspruchsgrundlagen gestützt wird.

10.3 Der Kunde erstattet dem Entwickler auf erste Anforderung sämtliche im Zusammenhang mit der Abwehr solcher Ansprüche entstehenden Kosten, einschließlich angemessener Rechtsanwalts- und Gerichtskosten, wobei der Entwickler den Kunden bei der Verteidigung in zumutbarer Weise unterstützt.

11.1 Der Entwickler ist berechtigt, diesen Vertrag mit sofortiger Wirkung zu kündigen, wenn er Kenntnis davon erlangt, dass die Software unter Verstoß gegen geltendes Recht oder entgegen vertraglichen Verpflichtungen Dritter (einschließlich Nutzungsbedingungen, Plattformregeln oder Zugriffs- bzw. Schutzmaßnahmen) genutzt wird oder wenn eine solche Nutzung den Entwickler rechtlichen Risiken aussetzt.

11.2 Im Falle einer Kündigung nach diesem Abschnitt 11 enden sämtliche dem Kunden eingeräumten Nutzungsrechte mit Zugang der Kündigungserklärung automatisch, auch wenn die Vergütung bereits vollständig gezahlt wurde. Der Kunde hat die Nutzung unverzüglich einzustellen und alle Kopien der Software zu löschen oder dauerhaft unbrauchbar zu machen, soweit nicht zwingendes Recht die Aufbewahrung verlangt.

11.3 Weitergehende Ansprüche und Rechte des Entwicklers (insbesondere auf Unterlassung, Schadensersatz und Freistellung) bleiben unberührt.

## 12. Abschluss, Aussetzung und (optionale) vorzeitige Beendigung

1) Einmalige Beauftragung; keine allgemeine Kündigung
Diese Vereinbarung betrifft eine einmalige Lieferung. Sie endet automatisch mit Übergabe der vereinbarten Leistungen und Zahlung der Schlussrechnung. Abgesehen von der gesonderten Regelung zur rechtswidrigen/unerlaubten Nutzung besteht kein fortlaufendes Kündigungsrecht.

2) Aussetzung bei Zahlungsverzug oder Sicherheitsrisiken
Der Entwickler darf die Arbeit pausieren oder die Übergabe zurückhalten, wenn (a) Rechnungen überfällig sind, (b) die Leistung nach unserer vernünftigen Einschätzung rechtswidrig genutzt wird oder Rechte Dritter verletzt, oder (c) die Fortführung Sicherheits‑, Schutz‑ oder Compliance‑Risiken verursachen würde. Eine Aussetzung berührt unsere Ansprüche auf Vergütung und sonstige Rechte nicht.

3) Optional, Beendigung durch den Auftraggeber vor Abschluss
Vor der endgültigen Übergabe kann der Auftraggeber schriftlich beenden. In diesem Fall verpflichtet er sich zur Zahlung (i) der bis dahin erbrachten Leistungen, (ii) nicht stornierbarer Drittaufwände, und (iii) einer Abbruchpauschale von 30 % des Restauftragswerts (d. h. bis zu 600 EUR, abhängig vom noch offenen Auftragswert). Nach Zahlung stellen wir den Zwischenstand „wie besehen“ zur Verfügung. Nach endgültiger Abnahme bestehen keine Rückzahlungsansprüche.

4) Rechtsfolgen; Fortgeltung
Bereits für vollständig bezahlte Leistungen eingeräumte Rechte bleiben bestehen. Vertraulichkeit, Urheber‑/IP‑Regelungen, Zahlungspflichten, Haftungsbegrenzungen und Gewährleistungsausschlüsse gelten auch nach Beendigung, Aussetzung oder Abschluss fort. Dies gilt nicht im Falle einer Kündigung nach Abschnitt 11; in diesem Fall enden die Nutzungsrechte gemäß Abschnitt 11.

## Anlage 1: Leistungsbeschreibung Text CAPTCHA Solver

1) Zweck
Der Text CAPTCHA Solver dient dazu, Text‑CAPTCHAs (Buchstaben und Zahlen) aus einem Bild zu extrahieren und als Lösung zurückzugeben. Die Groß‑ und Kleinschreibung ist dabei relevant.

2) Funktionsumfang  
(a) Konfigurierbarer Solver‑Modus. In den Erweiterungsoptionen kann der CAPTCHA‑Lösermodus ausgewählt werden (z. B. Mathe‑Modus oder Text‑Modus).  
(b) Text‑Modus. Im Text‑Modus wird der im CAPTCHA‑Bild enthaltene Text extrahiert und als Ergebnis zurückgegeben.  
(c) Case‑Sensitivity. Der zurückgegebene Text ist case sensitive (Groß‑ und Kleinschreibung wird beibehalten).  
(d) Beispiele. Erwartete Ausgaben (case sensitive) sind beispielsweise: `rbkd`, `qSKq`, `871u`.  
(e) Lokale Bildlösung. Die CAPTCHA‑Lösung erfolgt über den lokalen Bildlösungsweg innerhalb der Erweiterung. Eine Backend‑Lösung für CAPTCHAs ist nicht Bestandteil dieses Funktionsumfangs.  

3) Nicht im Funktionsumfang enthalten  
(a) Erweiterungen oder neue Features über den beschriebenen Funktionsumfang hinaus.  
(b) Unterstützung für eine serverseitige CAPTCHA‑Lösung über ein externes Backend.  

**Unterschriften**

Amadou Cisse (Entwickler)


______________________________


Patrycjusz Szmidt (Kunde)


______________________________
