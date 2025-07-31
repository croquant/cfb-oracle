from django.db import models


class DivisionClassification(models.TextChoices):
    """Enumeration for NCAA division classification."""

    FBS = "fbs", "FBS"
    FCS = "fcs", "FCS"
    II = "ii", "Division II"
    III = "iii", "Division III"


class SeasonType(models.TextChoices):
    """Enumeration for NCAA season types."""

    REGULAR = "regular", "Regular"
    POSTSEASON = "postseason", "Postseason"
    BOTH = "both", "Both"
    ALLSTAR = "allstar", "Allstar"
    SPRING_REGULAR = "spring_regular", "Spring Regular"
    SPRING_POSTSEASON = "spring_postseason", "Spring Postseason"
