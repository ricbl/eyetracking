from pathlib import Path

# Paths
HOME_DIR = Path.home()
PARSING_MODEL_DIR = HOME_DIR / ".local/share/bllipparser/GENIA+PubMed"

# Observation constants
SUPPORT_DEVICES = "support devices"
NO_FINDING = "no finding"
OBSERVATION = "observation"
CATEGORIES = ["Acute fracture & Fracture",
              "Airway wall thickening",
              "Atelectasis",
              "Consolidation",
              "enlarged cardiac silhouette",
              "Enlarged hilum",
              "Groundglass opacity",
              "Hiatal Hernia",
              "High lung volume - emphysema & Emphysema",
              "Interstitial lung disease & Fibrosis",
              "Lung nodule or mass",
              "Mass",
              "Nodule",
              "Pleural abnormality",
              "Pleural Effusion",
              "Pleural thickening",
              "Pneumothorax",
              "Pulmonary Edema",
              "Quality issue",
              "Support devices",
              "Wide mediastinum & Abnormal mediastinum contour"]
CATEGORIES = [element.lower() for element in CATEGORIES]
# Numeric constants
POSITIVE = 1
NEGATIVE = 0
UNCERTAIN = -1

# Misc. constants
UNCERTAINTY = "uncertainty"
NEGATION = "negation"
REPORTS = "Reports"
