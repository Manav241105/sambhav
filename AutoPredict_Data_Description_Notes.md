# Slide text

AUTOPREDICT  /  AGENTIC PREDICTIVE MAINTENANCE

Data Description

Synthetic vehicle telemetry and supporting service data enable failure prediction,
customer engagement, and appointment scheduling.

10,000*

Synthetic training samples

10

ML input features

80:20

Train–test split

DATA SOURCES & COVERAGE

FEATURES & PREDICTION TARGETS

Vehicle telemetry

Brake thickness, battery voltage, coolant temperature,
oil pressure, tyre pressure, and mileage.

Supporting records

Vehicle profiles, maintenance history, customer
preferences, conversations, and bookings.

Inputs

Six vehicle measurements, maintenance-event count,
and three critical-condition flags.

Targets

Synthetic failure label (0/1) and Remaining Useful Life
(days); RandomForest classifier and regressor.

PROTOTYPE COVERAGE   10 seeded vehicles  •  Normal, warning, and critical scenarios

Generate   →   Construct features   →   Split 80:20   →   Standardize   →   Train and evaluate

*10,000 is the configurable default training size. Data and target labels are synthetic; real-world validation remains future work.

# Speaker notes

AutoPredict combines synthetic vehicle telemetry with maintenance, customer, and scheduling information. Our default training pipeline generates 10,000 vehicle-condition samples with 10 input features. These include six vehicle measurements, a maintenance-event count, and three flags indicating critical brake, battery, or coolant conditions. We split the dataset into 80% training and 20% testing data and standardize the features using parameters fitted on the training set. A RandomForest classifier estimates failure probability, while a regressor estimates Remaining Useful Life in days. The application also uses supporting records to personalize communication and schedule service appointments. Its demonstration fleet contains 10 seeded vehicles covering normal, warning, and critical scenarios. The training labels and telemetry are synthetic, so this prototype demonstrates the workflow; validation against actual failures and service outcomes is a future requirement.
