# AutoPredict — Prompt for a Data Description Presentation Slide

Copy this entire file into GPT, or attach it and say: “Follow the instructions in this file.”

---

## Your task

Act as a technical presentation designer. Create **exactly one polished PowerPoint slide** titled **“Data Description”** for my project, **AutoPredict — Agentic Predictive Maintenance Platform**.

Use the verified project facts below. Make the slide suitable for an academic project presentation: clear, professional, visually balanced, and understandable to an audience with basic knowledge of machine learning.

The detailed reference material is context for selecting accurate content. **Do not squeeze every detail onto the slide.** Put supporting explanations in speaker notes.

## Required deliverables

1. Create an editable, single-slide `.pptx` if file generation is available. Use editable text, tables, and shapes rather than a flattened image.
2. Also provide the exact slide text in a neatly formatted Markdown block.
3. Provide a 60–90 second speaking script in the speaker notes and in your response.
4. If PowerPoint generation is unavailable, provide the slide text and precise layout instructions without claiming to have created a file.

Proceed using the supplied information; no clarification is needed.

## Slide design requirements

- Use a widescreen 16:9 layout.
- Use a light background, dark navy text, and restrained teal accents.
- Prefer a clean two-column layout with a compact metric strip at the top and a simple processing flow at the bottom.
- Use approximately 30–36 pt for the title and 18–22 pt for body text. Keep the limitation footer readable.
- Keep visible content to approximately 150–190 words, excluding the title.
- Use short phrases, clear grouping, and generous spacing.
- Use simple editable icons only if they improve comprehension.
- Do not add decorative charts, fabricated sample distributions, or performance statistics.
- Keep code paths, implementation details, and long feature tables in the notes.

## Content that must appear on the slide

### Title

Data Description

### Short introduction

Synthetic vehicle telemetry and supporting service data enable failure prediction, customer engagement, and appointment scheduling.

### Metric strip

- **10,000 synthetic samples***
- **10 ML input features**
- **80:20 train–test split**

### Left column: Data sources and coverage

- **Vehicle telemetry:** brake thickness, battery voltage, coolant temperature, oil pressure, tyre pressure, and mileage.
- **Supporting records:** vehicle profiles, maintenance history, customer preferences, conversations, and bookings.
- **Prototype coverage:** 10 seeded vehicles and normal, warning, and critical scenarios.

### Right column: Features and prediction targets

- **Inputs:** six vehicle measurements, maintenance-event count, and three critical-condition flags.
- **Targets:** synthetic failure label (0/1) and Remaining Useful Life (days).
- **Models:** RandomForest classifier and regressor.

### Bottom processing flow

Generate → Construct features → Split 80:20 → Standardize → Train and evaluate

### Required footer

*10,000 is the configurable default training size. Data and target labels are synthetic; real-world validation remains future work.*

You may refine wording and arrangement while retaining these facts and qualifications.

---

## Verified project reference material

### 1. Project purpose

AutoPredict is a prototype that combines vehicle-condition analysis, failure prediction, customer communication, and service scheduling. It includes a multi-agent backend, web dashboard, and mobile application.

The prototype uses internally generated synthetic vehicle data and simulated OBD telemetry. The documentation does not establish that a real-world fleet dataset was used for ML training.

### 2. Data categories

| Category | Available fields | Role in the system |
|---|---|---|
| Vehicle telemetry | Vehicle ID, timestamp, brake-pad thickness, battery voltage, coolant temperature, oil pressure, tyre pressures, odometer, engine RPM, speed | Vehicle-condition assessment and anomaly detection |
| Vehicle master data | Vehicle ID, VIN field, customer ID, make, model, year, engine type, transmission, last service date | Vehicle identification and service context |
| Maintenance history | Service ID, date, type, mileage, cost, replaced parts, technician notes | Service context and maintenance-event count |
| Customer profiles | Customer ID, contact details, preferred contact method and time, loyalty tier | Communication personalization |
| Conversations and memory | Messages, interpreted intent, sentiment, response time, acceptance or decline outcomes, channel preferences | Follow-ups and interaction history |
| Diagnostic references | DTC codes, descriptions, severity, occurrence information, recall campaign records | Simulated diagnostic enrichment |
| Scheduling data | Technician skills, service bays, working hours, service durations, holds, bookings | Appointment selection and resource allocation |
| Workflow and security data | Events, timestamps, confidence values, workflow state, simulated UEBA alerts | Execution tracking and prototype security checks |

All these categories support the application. **Only the 10 numerical features below are inputs to the failure-prediction model.** Customer names, conversations, and booking records are not inputs to that model.

### 3. ML dataset structure

| Property | Verified configuration |
|---|---|
| Source | Internally generated using Python and NumPy |
| Default dataset size | 10,000 synthetic samples; configurable through the training script |
| Observation unit | One synthetic vehicle-condition sample |
| Feature matrix | 10,000 × 10 under the default configuration |
| Training subset | 8,000 samples under the default configuration |
| Testing subset | 2,000 samples under the default configuration |
| Random seed | 42 for training-data generation and splitting |
| Classification target | Synthetic binary failure label: 0 or 1 |
| Regression target | Synthetic Remaining Useful Life in days |

**Do not equate 10,000 samples with 10,000 real vehicles.** The independently generated training samples are separate from the dashboard's 10 seeded demonstration vehicles. The default script configuration does not establish the exact training size used to produce existing model artifacts.

### 4. Exact model features

| # | Feature | Unit/type | Synthetic training range or definition |
|---|---|---|---|
| 1 | Brake-pad thickness | mm | 1.0–8.0 |
| 2 | Battery voltage | V | 10.5–13.0 |
| 3 | Coolant temperature | °C | 85–120 |
| 4 | Oil pressure | bar | 2.0–4.5 |
| 5 | Tyre pressure | PSI | 28–36 |
| 6 | Odometer | Thousands of kilometres | 10–200, equivalent to 10,000–200,000 km |
| 7 | Maintenance-event count | Integer | 0–19 |
| 8 | Critical brake flag | Binary | 1 if brake thickness < 3.0 mm; otherwise 0 |
| 9 | Critical battery flag | Binary | 1 if battery voltage < 11.5 V; otherwise 0 |
| 10 | Critical coolant flag | Binary | 1 if coolant temperature > 110°C; otherwise 0 |

These are synthetic sampling ranges and implemented feature thresholds, not manufacturer specifications. Speed and engine RPM are available to the application but are not included in this 10-feature model.

### 5. Target generation

- **Failure label:** A predefined score uses brake, battery, and coolant conditions, with added random variation. A score greater than 0.5 produces label 1; otherwise the label is 0.
- **RUL label:** A formula uses brake thickness, the assigned failure class, and random variation to generate remaining days.
- These targets are **simulation-derived labels**, not observed breakdowns or measured component lifetimes.
- No empirically validated failure-prediction horizon is established by these labels. Do not invent one such as “failure within 30 days.”

### 6. Data preparation and models

1. Generate synthetic numerical measurements and maintenance counts.
2. Construct the seven base features and three binary flags.
3. Split into 80% training and 20% testing data using `random_state=42`.
4. Fit `StandardScaler` on training data only and apply it to both subsets.
5. Train a `RandomForestClassifier` for failure classification/probability and a `RandomForestRegressor` for RUL.
6. Calculate classification accuracy, precision, recall, and regression mean absolute error.
7. Save the classifier, regressor, and scaler as `.joblib` artifacts.

Both forests are configured with 100 estimators and maximum depth 10. The script does not demonstrate separate imputation, duplicate removal, class balancing, or cross-validation steps. Do not claim these were performed.

No measured evaluation results are supplied here. Mention metric names only; do not invent scores.

### 7. Runtime simulation scenarios

| Parameter | Normal | Warning | Critical |
|---|---|---|---|
| Brake-pad thickness | 4.0–6.0 mm | 3.0–4.5 mm | 1.5–3.0 mm |
| Battery voltage | 12.0–12.8 V | 11.8–12.0 V | 11.2–11.7 V |
| Coolant temperature | 85–95°C | 95–105°C | 105–115°C |
| Oil pressure | 3.0–4.0 bar | 2.5–3.0 bar | 2.0–2.5 bar |

These are runtime generation ranges, separate from ML training ranges. Scenario names are generation settings; diagnosis and priority assignment apply their own rules.

### 8. Supporting prototype coverage

| Item | Coverage |
|---|---|
| Initial dashboard fleet | 10 mock vehicles, VEH001–VEH010 |
| Initial bookings | 6 |
| Initial conversations | 4 |
| Generated telemetry history | Default seven daily snapshots per vehicle |
| Generated maintenance history | 3–8 service events per vehicle |
| DTC catalogue | 10 hardcoded diagnostic trouble codes |
| Recall catalogue | 4 mock recall campaigns |
| Scheduling resources | 5 technicians and 5 service bays |

The runtime maintenance-history count of 3–8 differs from the training generator's sampled maintenance-count range of 0–19. Do not merge these into one dataset statistic.

The RandomForest models process individual feature vectors. The seven-day history supports application views; the current models do not directly learn from full time-series sequences.

### 9. Current scope and future data requirements

| Current prototype | Future data requirement |
|---|---|
| Synthetic telemetry and OBD simulation | Actual telemetry with reliable timestamps and consistent units |
| Generated maintenance history | Verified repairs, replacements, and service records |
| Rule-generated failure and RUL targets | Confirmed failures and measured component lifetimes |
| Hardcoded DTC and mock recall catalogues | Verified diagnostic references and applicable recall records |
| Generated customer profiles and stored interaction memory | Consented customer preferences and actual service outcomes |
| Proposed RAG architecture | Curated manuals, technical bulletins, policies, and historical cases |

### 10. Accuracy rules for your output

- Describe the project as a **prototype using synthetic and simulated data**.
- Label 10,000 samples as the **default training configuration**.
- Do not claim the project uses a Kaggle, NASA, OEM, or other external training dataset.
- Do not present the dashboard's `0.94` accuracy placeholder as a measured 94% result.
- Do not claim real-world predictive performance from synthetic test data.
- Do not describe simulated OBD readings as measurements collected from connected vehicles.
- Do not present mock recalls as verified real campaigns.
- RAG, embeddings, a vector store, and ingested manuals are proposed extensions in the documentation, not established implemented data sources.
- Do not report example RAG ingestion counts as actual dataset sizes.
- Keep model outputs, training labels, and measured real-world outcomes distinct.

### 11. Source basis

This prompt was prepared from the full `PROJECT_DOCUMENTATION.md`, with dataset and generation details checked against `backend/ml_training.py` and `backend/data_generator.py`.

Use only the supplied project facts. External research is unnecessary for this slide.

## Suggested speaker-note narrative

“AutoPredict combines synthetic vehicle telemetry with maintenance, customer, and scheduling information. Our default training pipeline generates 10,000 vehicle-condition samples with 10 input features. These include six vehicle measurements, a maintenance-event count, and three flags indicating critical brake, battery, or coolant conditions. We split the dataset into 80% training and 20% testing data and standardize the features using parameters fitted on the training set. A RandomForest classifier estimates failure probability, while a regressor estimates Remaining Useful Life in days. The application also uses supporting records to personalize communication and schedule service appointments. Its demonstration fleet contains 10 seeded vehicles covering normal, warning, and critical scenarios. The training labels and telemetry are synthetic, so this prototype demonstrates the workflow; validation against actual failures and service outcomes is a future requirement.”

Now create the single slide and deliverables requested above.
