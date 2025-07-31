from django.db import models


class DivisionClassification(models.TextChoices):
    """Enumeration for NCAA division classification."""

    FBS = "fbs", "FBS"
    FCS = "fcs", "FCS"
    II = "ii", "Division II"
    III = "iii", "Division III"
