---
title: "Lösungen: Radiologie Workflow Simulator"
numbersections: true
---

> **Hinweis:** Dies sind Musterlösungen. Konkrete `PatientID`, `AccessionNumber`, Kreatininwerte und DICOM-Tags unterscheiden sich zwischen den Gruppen.

# Checkpoint 1: Patient und Auftrag

- **KIS → RIS:** Eine HL7-ADT-Nachricht überträgt Patientenstammdaten, insbesondere Patientenname und `PatientID`.
- **RIS ↔ LIS:** Das RIS sendet `QRY^Q02` mit der `PatientID`; das LIS antwortet mit `ORU^R01`. Der Kreatininwert steht im Segment `OBX`.
- **RIS → MWL:** `ORM^O01` überträgt den radiologischen Auftrag. Die `AccessionNumber` verbindet Auftrag, Worklist und spätere Bildstudie.

**Warum braucht die Worklist PatientID und AccessionNumber?**

Die `PatientID` ordnet den Auftrag dem richtigen Patienten zu. Die `AccessionNumber` identifiziert den konkreten radiologischen Untersuchungsauftrag.

# Checkpoint 2: Worklist und Bildversand

- **C-FIND:** Die CT-Modalität ruft die Worklist ab. Sie erzeugt den Auftrag nicht selbst.
- **C-STORE:** Die CT sendet DICOM-Bildinstanzen an das PACS.
- **Tag-Vergleich:** Geprüft werden insbesondere `PatientID`, `AccessionNumber` und `StudyInstanceUID`.
- Bei aktivierter Anpassung werden die Kennungen sowie die Untersuchungsbeschreibung an den ausgewählten Worklist-Auftrag angepasst.
- Ohne Anpassung bleiben die Originalwerte der Datei erhalten und müssen zur Worklist passen.

> **Sicherheitsaspekt:** Abweichende Kennungen können dazu führen, dass Bilder dem falschen Patienten oder dem falschen Auftrag zugeordnet werden.

# Checkpoint 3: PACS und DICOM-Tags

| DICOM-Tag | Bedeutung |
|---|---|
| `PatientID` | Identifiziert den Patienten und muss zur HL7-ADT-Datenübernahme passen. |
| `AccessionNumber` | Identifiziert den radiologischen Auftrag aus ORM und MWL. |
| `StudyInstanceUID` | Identifiziert die gesamte Bildstudie eindeutig im PACS. |
| `Modality` | Kennzeichnet die bildgebende Modalität, hier typischerweise CT. |

**Zusammenhang der Kennungen:**

- `PatientID` verbindet die Bilddaten mit dem Patienten.
- `AccessionNumber` verbindet die Bilddaten mit dem konkreten Untersuchungsauftrag.
- `StudyInstanceUID` verbindet alle Instanzen einer Studie.

# Checkpoint 4: Suche, Retrieve und Befund

- **C-FIND (Study Root):** Die Workstation fragt das PACS nach verfügbaren Studien ab.
- **C-MOVE:** Die Workstation fordert eine bestimmte Studie anhand ihrer `StudyInstanceUID` an.
- **C-STORE im Rückkanal:** Das PACS sendet die Bildinstanzen anschliessend aktiv an die Workstation.

**C-MOVE bedeutet:**  
Die Workstation fordert beim PACS an, dass eine bestimmte Studie an ein definiertes Ziel übertragen wird.

**C-STORE im Rückkanal bedeutet:**  
Das PACS sendet die angeforderten DICOM-Bildinstanzen an die Workstation.

**Wo erscheint der Befund nach dem Senden?**  
Im RIS-Befundbereich des Dashboards.

**Merke:** `C-MOVE` ist vereinfacht ein *Pull mit anschliessendem Push*: Die Workstation fordert die Studie an, das PACS überträgt die Bilder danach per `C-STORE`.

# Checkpoint 5: Fehlerfall und Reflexion

## C-ECHO fehlgeschlagen

Sinnvolle Prüfungen:

- Host
- Port
- AE Title
- Netzwerkverbindung
- läuft der DICOM-Dienst?

`C-ECHO` ist ein sinnvoller erster Verbindungstest.

## Worklist leer

Prüfen:

- Wurde der Patient im KIS aufgenommen?
- Wurde der RIS-Auftrag freigegeben?
- Besitzt der Auftrag eine `AccessionNumber`?
- Ist der richtige SuS-Code gesetzt?

## C-MOVE ohne Empfang

Prüfen:

- kurz warten / Timing
- richtige `StudyInstanceUID`
- korrektes Ziel-AE
- funktioniert der C-STORE-Rückkanal?
- `C-ECHO` als Verbindungstest

**Welche Verbindung ist rot markiert?**  
Das hängt vom gewählten Fehlerfall ab. Im Workflow-Panel wird die betroffene Verbindung rot dargestellt.

**Was bedeutet „Unterbrechung erkannt“?**  
Der Workflow ist an dieser Stelle technisch unterbrochen. Der Hinweis verweist auf die nächste sinnvolle Prüfung.

# Gruppenfazit – mögliche Musterantworten

**Der wichtigste Datenübergabepunkt war:**  
Zum Beispiel die Übernahme des RIS-Auftrags in die Worklist, weil hier Patient und Untersuchung korrekt miteinander verknüpft werden.

**Das hat uns vor einer Fehlzuordnung geschützt:**  
Der Vergleich von `PatientID` und `AccessionNumber` zwischen Worklist und DICOM-Daten.

**Einen Zusammenhang können wir jetzt erklären:**  
Das RIS stellt den Auftrag bereit → die CT findet ihn mit `C-FIND` → die CT sendet die Bilder mit `C-STORE` ans PACS → die Workstation findet die Studie und fordert sie mit `C-MOVE` an.

> **Abschluss:** Die Antworten sind als Muster gedacht. Entscheidend ist, dass die Lernenden den Datenfluss und die Rolle der Kennungen nachvollziehbar erklären können.
