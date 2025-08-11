"""Shared constants for the rating systems (Glicko-2, Elo)."""

from core.models.enums import DivisionClassification

# Glicko2 constants
DEFAULT_RATING = 1500
DEFAULT_RD = 350
DEFAULT_VOLATILITY = 0.11
GLICKO2_SCALER = 173.7178
TAU = 0.9
CONVERGENCE_TOLERANCE = 0.000001

# Elo constants
ELO_DEFAULT_RATING = 1500
ELO_K_FACTOR = 32
ELO_HOME_ADVANTAGE = 55
ELO_DECAY_DEFAULT = 0.75  # Fraction of a rating retained between seasons
# Base for logarithmic score differential scaling in the Elo formula.
# Rating change = K * log(diff + 1, ELO_SCORE_DIFFERENTIAL_BASE)
#                 * (actual - expected)
ELO_SCORE_DIFFERENTIAL_BASE = 10

# Base ratings and rating deviations for each division
DIVISION_BASE_RATINGS = {
    DivisionClassification.FBS: 1500,
    DivisionClassification.FCS: 1300,
    DivisionClassification.II: 1100,
    DivisionClassification.III: 900,
}

DIVISION_BASE_RDS = {
    DivisionClassification.FBS: DEFAULT_RD
    * (DIVISION_BASE_RATINGS[DivisionClassification.FBS] / DEFAULT_RATING),
    DivisionClassification.FCS: DEFAULT_RD
    * (DIVISION_BASE_RATINGS[DivisionClassification.FCS] / DEFAULT_RATING),
    DivisionClassification.II: DEFAULT_RD
    * (DIVISION_BASE_RATINGS[DivisionClassification.II] / DEFAULT_RATING),
    DivisionClassification.III: DEFAULT_RD
    * (DIVISION_BASE_RATINGS[DivisionClassification.III] / DEFAULT_RATING),
}
