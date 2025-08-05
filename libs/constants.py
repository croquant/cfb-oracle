from core.models.enums import DivisionClassification

# Glicko2 constants
DEFAULT_RATING = 1500
DEFAULT_RD = 350
DEFAULT_VOLATILITY = 0.11
GLICKO2_SCALER = 173.7178
TAU = 0.9
CONVERGENCE_TOLERANCE = 0.000001

# Base ratings and rating deviations for each division
DIVISION_BASE_RATINGS = {
    DivisionClassification.FBS: 1500,
    DivisionClassification.FCS: 1300,
    DivisionClassification.II: 1100,
    DivisionClassification.III: 900,
}

DIVISION_BASE_RDS = {
    DivisionClassification.FBS: DEFAULT_RD,
    DivisionClassification.FCS: DEFAULT_RD,
    DivisionClassification.II: DEFAULT_RD,
    DivisionClassification.III: DEFAULT_RD,
}

# Maximum score margin considered when weighting Glicko updates
MARGIN_WEIGHT_CAP = 21

# Home-field advantage applied to Glicko ratings
HOME_FIELD_BONUS = 55
