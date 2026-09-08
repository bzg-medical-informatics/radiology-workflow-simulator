---
title: "Lösungen: Radiologie Workflow Simulator"
numbersections: true
---

Hinweis: Dies sind Musterlösungen. Konkrete PatientIDs, AccessionNumbers, Kreatininwerte und DICOM-Tags unterscheiden sich zwischen den Gruppen.

# Checkpoint 1: Patient und Auftrag

- **KIS → RIS:** HL7 `ADT` überträgt Patientenstammdaten, insbesondere Patientenname und `PatientID`.
- **RIS ↔ LIS:** Das RIS sendet `QRY^Q02` mit der `PatientID`; das LIS antwortet mit `ORU^R01`. Der Kreatininwert steht im Segment `OBX`.
- **RIS → MWL:** `ORM^O01` überträgt den Auftrag. Die `AccessionNumber` verbindet Auftrag, Worklist und spätere Bildstudie.
- **Warum braucht die Worklist beide Daten?** Die `PatientID` ordnet den Auftrag dem Patienten zu; die `AccessionNumber` unterscheidet konkrete Untersuchungsaufträge.

# Checkpoint 2: Worklist und Bildversand

- **C-FIND:** Die CT-Modalität ruft die Worklist ab. Sie erzeugt den Auftrag nicht selbst.
- **C-STORE:** Die CT sendet DICOM-Bildinstanzen an das PACS.
- **Tag-Vergleich:** Mit aktiviertem Retagging werden PatientID, AccessionNumber, StudyInstanceUID und die Untersuchungsbeschreibung (`StudyDescription`) an den ausgewählten Worklist-Auftrag angepasst. Der überweisende Arzt wird in der Simulation ebenfalls gesetzt. Ohne Retagging bleiben die Originalwerte der Datei erhalten und müssen mit der Worklist übereinstimmen.
- **Sicherheitsrisiko:** Abweichende Kennungen können Bilder dem falschen Patienten oder Auftrag zuordnen.

# Checkpoint 3: PACS und DICOM-Tags

| DICOM-Tag | Bedeutung |
|---|---|
| `PatientID` | Identifiziert den Patienten und muss zur HL7-ADT-Datenübernahme passen. |
| `AccessionNumber` | Identifiziert den radiologischen Auftrag aus ORM und MWL. |
| `StudyInstanceUID` | Identifiziert die gesamte Bildstudie im PACS. |
| `Modality` | Kennzeichnet die bildgebende Modalität, hier typischerweise `CT`. |

# Checkpoint 4: Suche, Retrieve und Befund

- **C-FIND Study Root:** Die Workstation fragt das PACS nach verfügbaren Studien ab.
- **C-MOVE:** Die Workstation fordert eine bestimmte Studie anhand ihrer StudyInstanceUID an.
- **C-STORE Rückkanal:** Das PACS sendet die Bildinstanzen anschliessend aktiv an die Workstation. Darum ist C-MOVE ein Pull mit anschliessendem Push.
- **Befund:** Die Workstation übermittelt den Befund als `HL7 ORU^R01` an das RIS; er erscheint anschliessend im RIS-Befundbereich des Dashboards.

# Checkpoint 5: Fehlerfall und Reflexion

- **C-ECHO fehlgeschlagen:** Prüfe Host, Port, AE Title, Netzwerk und ob der DICOM-Dienst läuft.
- **Worklist leer:** Prüfe zuerst, ob der Patient aufgenommen, ein RIS-Auftrag mit AccessionNumber freigegeben und der richtige SuS-Code gesetzt wurde. Die Worklist ist nach SuS-Code gefiltert.
- **C-MOVE ohne Empfang:** Prüfe Timing, StudyInstanceUID, Ziel-AE und den C-STORE-Rückkanal. Ein C-ECHO ist ein sinnvoller erster Verbindungstest.
- **Rote Verbindung im Workflow-Panel:** Sie markiert die Prozessunterbrechung. Der Hinweis „Unterbrechung erkannt“ verweist auf die nächste technische Prüfung.

## Protokolle zuordnen

| Handlung | Protokoll |
|---|---|
| Patient aufnehmen | HL7 ADT |
| Laborwert anfordern / erhalten | HL7 QRY^Q02 / ORU^R01 |
| Auftrag freigeben | HL7 ORM^O01 |
| Worklist oder Studie suchen | DICOM C-FIND |
| Bilder senden | DICOM C-STORE |
| Bilder abrufen | DICOM C-MOVE, danach C-STORE |
