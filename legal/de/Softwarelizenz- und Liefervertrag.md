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

Der Entwickler hat eine Software‑Anwendung ("Software") nach den Spezifikationen des Kunden erstellt.
Der Entwickler verpflichtet sich, die Software an den Kunden zu liefern, und der Kunde verpflichtet sich, das vereinbarte Entgelt zu zahlen, jeweils nach Maßgabe dieses Vertrags.
Die vereinbarten technischen Spezifikationen sind in Funktionale Spezifikation „Flow“ (Nicht‑Technisch) v1.0 (Anlage: Flow‑Spezifikation) festgehalten und bilden einen integrierten Bestandteil dieses Vertrags.

## 2. Lieferung und Abnahme

2.1 Der Entwickler liefert die Software als verschleierten JavaScript‑Build (inklusive zugehöriger Laufzeit‑Assets), der zur Ausführung geeignet ist, ohne unverschleierten Quellcode oder Entwicklungs‑Toolchain. Eine Dokumentation ist nicht enthalten, sofern nicht ausdrücklich schriftlich vereinbart.
2.2 Der Kunde prüft die Software binnen 14 Tagen nach Lieferung. Entspricht die Software im Wesentlichen den vereinbarten Spezifikationen, erklärt der Kunde die Abnahme schriftlich. Erfolgt innerhalb dieser Frist kein schriftlicher Widerspruch, gilt die Software als abgenommen.

2.3 Sichere elektronische Lieferung (Downloadlink + Prüfsumme)
(a) Verpackung und Benennung. Der Liefergegenstand wird als einzelnes .zip‑Archiv mit eindeutigem, versioniertem Dateinamen im Format productname_vX.Y.Z_YYYY-MM-DD.zip verpackt.
(b) Prüfsumme. Vor der Lieferung berechnet der Entwickler eine SHA‑256‑Prüfsumme für das Archiv (die „Prüfsumme“).
(c) Liefermitteilung und Lieferdatum. Der Entwickler versendet eine E‑Mail in Textform gemäß Abschnitt 7.3/7.7 an die Mitteilungsadressen mit (i) einem privaten, befristeten Downloadlink, der mindestens sieben (7) Kalendertage gültig ist (die „Link‑Gültigkeitsdauer“), und (ii) der Prüfsumme (die „Liefermitteilung“). Der Zeitpunkt des Versands der Liefermitteilung gilt als „Lieferdatum“.
(d) Download und Verifikation durch den Kunden. Der Kunde lädt das Archiv innerhalb der Link‑Gültigkeitsdauer herunter und verifiziert die Integrität, indem er eine SHA‑256‑Prüfsumme der heruntergeladenen Datei bildet und mit der Prüfsumme vergleicht. Der Kunde bestätigt Empfang und Integrität per Antwort‑E‑Mail; das Ausbleiben einer Bestätigung berührt Lieferung und Abnahmefristen nicht.
(e) Zugangs‑ oder Integritätsprobleme. Kann der Kunde auf den Link nicht zugreifen oder stellt er eine Abweichung der Prüfsumme fest, informiert er den Entwickler unverzüglich, spätestens innerhalb von drei (3) Geschäftstagen ab Lieferdatum. Der Entwickler stellt zeitnah einen neuen Downloadlink und eine neue Prüfsumme bereit. Bei vom Entwickler bestätigter Prüfsummenabweichung beginnt die Prüf‑/Abnahmefrist gemäß Abschnitt 2.2 mit dem Datum der Neuzustellung erneut.
(f) Nachweis. Die Liefermitteilung und die Prüfsumme stellen den maßgeblichen Nachweis für den Inhalt der gelieferten Datei dar. Der Entwickler darf die Liefermitteilung und zugehörige Protokolle als Liefernachweis aufbewahren.
(g) Vertraulichkeit. Der Kunde behandelt den Downloadlink und das gelieferte Paket als vertrauliche Informationen und gibt den Link nur an Personen weiter, die nach diesem Vertrag zur Entgegennahme der Software berechtigt sind.

2.4 Auswirkung auf die Abnahmefrist
Für Abschnitt 2.2 gilt die Lieferung mit dem Lieferdatum als erfolgt. Die vierzehntägige Prüf‑/Abnahmefrist beginnt mit dem Lieferdatum; bei bestätigter Prüfsummenabweichung und Neuzustellung beginnt die vierzehntägige Frist mit dem Datum der Neuzustellung erneut.

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

4.2 Gewährleistungsfrist und Abhilfe. Die Gewährleistungsfrist beträgt 90 Tage ab Abnahme. Bei innerhalb der Gewährleistungsfrist berechtigt gerügten Mängeln wird der Entwickler nach eigener Wahl nachbessern oder Ersatz liefern. Scheitert die Nachbesserung/Ersatzlieferung endgültig innerhalb eines angemessenen Zeitraums, kann der Kunde die Vergütung mindern oder vom Vertrag zurücktreten. Während der Gewährleistungsfrist behebt der Entwickler reproduzierbare Mängel, die eine wesentliche Abweichung von den vereinbarten Spezifikationen in der vereinbarten Betriebsumgebung verursachen, ohne zusätzliche Vergütung; alle weiteren Support‑ und Wartungsleistungen (einschließlich Erweiterungen, Kompatibilitätsarbeiten und Nachbesserungen nach Ablauf der Gewährleistung) sind ausgeschlossen und Gegenstand einer gesonderten Vereinbarung.

4.3 Ausschlüsse. Die Gewährleistung erstreckt sich nicht auf Mängel, die durch Modifikationen, unsachgemäße Nutzung, Betrieb außerhalb der vereinbarten Umgebung oder externe Systeme verursacht werden.

4.4 Haftungsausschlüsse. Nichts in diesem Vertrag beschränkt oder schließt die Haftung für Vorsatz, grobe Fahrlässigkeit, Verletzung von Leben, Körper oder Gesundheit oder nach dem Produkthaftungsgesetz aus.

4.5 Kardinalpflichten. Bei leicht fahrlässigen Verletzungen wesentlicher Vertragspflichten (Kardinalpflichten) ist die Haftung auf den vorhersehbaren, typischerweise eintretenden Schaden begrenzt. Im Übrigen ist die Haftung für leichte Fahrlässigkeit ausgeschlossen.

4.6 Haftungshöchstbetrag. Vorstehendes vorausgesetzt, ist die Gesamthaftung des Entwicklers aus oder im Zusammenhang mit diesem Vertrag auf den vom Kunden für die Software gezahlten Betrag begrenzt.

## 5. Vergütung

5.1 Die Gesamtvergütung für die Software beträgt **3.000 EUR (dreitausend Euro) zzgl. gesetzlicher USt.**
5.2 Die Vergütung ist innerhalb von 14 Tagen nach Lieferung und Abnahme fällig.
5.3 Der Kunde erlangt die Nutzungsrechte erst nach vollständigem Zahlungseingang.

## 6. Vertraulichkeit

Beide Parteien behandeln im Rahmen dieses Vertrags erlangte geschäftliche oder technische Informationen vertraulich.

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

## 11. Kündigung bei rechtswidriger Nutzung

Der Entwickler ist berechtigt, diesen Vertrag mit sofortiger Wirkung zu kündigen, wenn er Kenntnis davon erlangt, dass die Software unter Verstoß gegen geltendes Recht oder in einer Weise genutzt wird, die den Entwickler rechtlichen Risiken aussetzt. In diesem Fall enden alle dem Kunden eingeräumten Rechte automatisch, unbeschadet sonstiger Rechte oder Rechtsbehelfe des Entwicklers.

## 12. Abschluss, Aussetzung und (optionale) vorzeitige Beendigung

1) Einmalige Beauftragung; keine allgemeine Kündigung
Diese Vereinbarung betrifft eine einmalige Lieferung. Sie endet automatisch mit Übergabe der vereinbarten Leistungen und Zahlung der Schlussrechnung. Abgesehen von der gesonderten Regelung zur rechtswidrigen/unerlaubten Nutzung besteht kein fortlaufendes Kündigungsrecht.

2) Aussetzung bei Zahlungsverzug oder Sicherheitsrisiken
Wir dürfen die Arbeit pausieren oder die Übergabe zurückhalten, wenn (a) Rechnungen überfällig sind, (b) die Leistung nach unserer vernünftigen Einschätzung rechtswidrig genutzt wird oder Rechte Dritter verletzt, oder (c) die Fortführung Sicherheits‑, Schutz‑ oder Compliance‑Risiken verursachen würde. Eine Aussetzung berührt unsere Ansprüche auf Vergütung und sonstige Rechte nicht.

3) Optional — Beendigung durch den Auftraggeber vor Abschluss
Vor der endgültigen Übergabe kann der Auftraggeber schriftlich beenden. In diesem Fall verpflichtet er sich zur Zahlung (i) der bis dahin erbrachten Leistungen, (ii) nicht stornierbarer Drittaufwände, und (iii) einer Abbruchpauschale von 30 % des Restauftragswerts (d. h. bis zu 900 EUR, abhängig vom noch offenen Auftragswert). Nach Zahlung stellen wir den Zwischenstand „wie besehen“ zur Verfügung. Nach endgültiger Abnahme bestehen keine Rückzahlungsansprüche.

4) Rechtsfolgen; Fortgeltung
Bereits für vollständig bezahlte Leistungen eingeräumte Rechte bleiben bestehen. Vertraulichkeit, Urheber‑/IP‑Regelungen, Zahlungspflichten, Haftungsbegrenzungen und Gewährleistungsausschlüsse gelten auch nach Beendigung, Aussetzung oder Abschluss fort.

**Unterschriften**

Amadou Cisse (Entwickler)


______________________________


Patrycjusz Szmidt (Kunde)


______________________________
