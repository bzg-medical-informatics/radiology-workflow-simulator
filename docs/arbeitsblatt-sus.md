---
title: "Radiologie Workflow Simulator: Gruppenbegleitblatt"
numbersections: true
---

```{=latex}
\begin{learninggoal}
Lernziel: Ihr könnt nach der Übung erklären, welche Daten zwischen KIS, RIS, LIS, CT, PACS und Workstation fliessen. Dabei verfolgt ihr PatientID, AccessionNumber und StudyInstanceUID.
\end{learninggoal}
```

# So arbeitet ihr

Öffnet die App: https://orthanc.bohn-teaching.org. Verwendet pro Gruppe einen gemeinsamen Session-Key.

> **Dashboard zuerst:** Der **Geführte Lernpfad** sagt euch, was als Nächstes sinnvoll ist. Die **Statusspur** zeigt den Untersuchungsstatus. Im **Workflow-Panel** seht ihr Sender, Empfänger und Datenfluss.

| Rolle | Aufgabe |
|---|---|
| Verwaltung | Schritte 1-3 im Dashboard: KIS, LIS, RIS |
| Radiologiefachperson | Schritte 4-5: Worklist, CT und Bildversand |
| Radiologie | Schritte 6-7: Suche, Retrieve und Befund |
| Beobachtung | IDs, Statusspur und DICOM-Protokoll-Log dokumentieren |

> **Rollenwechsel:** Wechselt nach jedem Checkpoint die sprechende Person. Vor jedem Klick nennt sie: System, Nachricht und wichtigste Kennung.

![Dashboard: Geführter Lernpfad](dashboard-verwaltung.png){ width=82% }

> **Statusspur lesen:** Sie zeigt nacheinander `Auftrag freigegeben`, `Untersuchung begonnen`, `Untersuchung abgeschlossen` und `Befundet`. Der hervorgehobene Eintrag ist der aktuelle Stand eures Falls.

```{=latex}
\newpage
```

## ID-Spickzettel

| Kennung | Entsteht bei | Prüfen bei |
|---|---|---|
| `PatientID` | KIS / HL7 ADT | LIS, Worklist, DICOM-Tags |
| `AccessionNumber` | RIS / HL7 ORM | Worklist, DICOM-Tags |
| `StudyInstanceUID` | Bildstudie / C-STORE | PACS, C-MOVE, Befund |

# Checkpoint 1: Patient und Auftrag

**Dashboard-Schritte 1-3: KIS → RIS, RIS ↔ LIS, RIS → MWL**

1. Erfasst einen Patienten im KIS. Öffnet **„KIS erklärt“** und benennt Sender und Empfänger der ADT-Nachricht.
2. Fragt das Kreatinin beim LIS an. Öffnet **„LIS erklärt“** und findet die PatientID in der Nachricht.
3. Gebt den Auftrag im RIS frei. Öffnet **„RIS erklärt“** und notiert die AccessionNumber.

```{=latex}
\begin{tipbox}
Merke: QRY Q02 fragt einen Laborwert an. ORU R01 liefert ihn zurück. ORM O01 überträgt den radiologischen Auftrag.
\end{tipbox}
```

**Unsere PatientID:** ____________________  
**Unsere AccessionNumber:** ____________________  
**Warum braucht die Worklist beide Daten?** __________________________________________

# Checkpoint 2: Worklist und Bildversand

**Dashboard-Schritte 4-5: CT → MWL, CT → PACS**

1. Die Radiologiefachperson öffnet die CT-Konsole und aktualisiert die Worklist mit `C-FIND`.
2. Prüft: Findet ihr die AccessionNumber aus Checkpoint 1 wieder?
3. Beginnt die Untersuchung. Sendet anschliessend DICOM-Bilder mit `C-STORE` an das PACS.
4. Nutzt nach echtem Upload den **„Tag-Vergleich: Upload und Worklist“**.

```{=latex}
\begin{safetybox}
Sicherheitsprüfung: Eine abweichende PatientID oder Accession kann eine falsche Patienten- oder Auftragszuordnung bedeuten. Vergleicht Originalwerte und Worklist-Werte, bevor ihr die Bilder weiterverwendet.
\end{safetybox}
```

**Worklist gefunden?** [ ] Ja  [ ] Nein  
**C-STORE im Protokoll-Log:** [ ] OK  [ ] Fehler  
**Welche Kennung wurde im Tag-Vergleich geprüft?** ____________________

# Checkpoint 3: PACS und DICOM-Tags

**Nach Schritt 5: Bilder im Archiv prüfen**

Öffnet **PACS (SuS)**. Öffnet eure Studie, eine Serie und eine Instanz mit **„Viewer + Tags“**.

| DICOM-Tag | Wert in eurer Studie | Passt zur Gruppe? |
|---|---|---|
| `PatientID` | | [ ] Ja  [ ] Nein |
| `AccessionNumber` | | [ ] Ja  [ ] Nein |
| `StudyInstanceUID` | | [ ] Ja  [ ] Nein |
| `Modality` | | [ ] Ja  [ ] Nein |

> **Tipp:** `PatientID` und `AccessionNumber` verbinden Bilddaten mit Verwaltung. Die `StudyInstanceUID` verbindet alle Bilder einer Studie.

# Checkpoint 4: Suche, Retrieve und Befund

**Dashboard-Schritte 6-7: Workstation → PACS, Workstation ↔ PACS**

1. Die Radiologie sucht eure Studie mit `C-FIND`.
2. Fordert sie mit `C-MOVE` an und öffnet im Workflow-Panel die Rückkanal-Animation.
3. Erklärt beide Pfeile: Workstation → PACS und PACS → Workstation.
4. Erstellt einen kurzen Befund und prüft ihn danach im RIS-Dashboard.

![Dashboard: Prozesskarte und Rückkanal](dashboard-workflow.png){ width=55% }

**C-MOVE bedeutet:** _________________________________________________________________  
**C-STORE im Rückkanal bedeutet:** ___________________________________________________  
**Wo erscheint der Befund nach dem Senden?** _________________________________________

# Checkpoint 5: Fehlerfall und Reflexion

Wählt einen Fehlerfall im Dashboard:

- **C-ECHO fehlgeschlagen:** falscher Port simulieren.
- **Worklist leer:** prüfen, ob der RIS-Auftrag inklusive Accession freigegeben wurde.
- **C-MOVE ohne Empfang:** zuerst kurz warten, dann C-ECHO sowie Ziel-AE prüfen.

1. Öffnet das Workflow-Panel. Welche Verbindung ist rot markiert?
2. Nutzt den Hinweis **„Unterbrechung erkannt“** und nennt eure erste sinnvolle Prüfung.
3. Prüft zum Schluss den **Geführten Lernpfad** und die **Statusspur**.

## Gruppenfazit

**Der wichtigste Datenübergabepunkt war:**

________________________________________________________________________________

________________________________________________________________________________

________________________________________________________________________________

**Das hat uns vor einer Fehlzuordnung geschützt:**

________________________________________________________________________________

________________________________________________________________________________

________________________________________________________________________________

**Das möchten wir noch klären:**

________________________________________________________________________________

________________________________________________________________________________

________________________________________________________________________________

**Abschluss:** Nutzt das Quiz am Ende des Dashboards als Selbstcheck. Vergleicht anschliessend eure Antworten in der Gruppe.
