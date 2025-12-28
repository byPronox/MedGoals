"""
Service layer helpers for MedGoals.

Separating these utilities keeps controllers and models focused on
business rules while the services encapsulate cross-cutting concerns
like serialization or scoring strategies.
"""
from . import score_engine
from . import serializers
