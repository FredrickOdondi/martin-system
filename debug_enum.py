import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from backend.app.models.models import TWGPillar
from sqlalchemy import Enum

print("--- Inspecting TWGPillar ---")
print(f"Enum members: {list(TWGPillar.__members__.keys())}")
print(f"Enum values: {[e.value for e in TWGPillar]}")

try:
    val = TWGPillar("energy_infrastructure")
    print(f"Successfully instantiated: {val}")
except Exception as e:
    print(f"Failed to instantiate: {e}")

print("\n--- Inspecting SQLAlchemy Enum Type ---")
sa_enum = Enum(TWGPillar)
# Simulate what SQLAlchemy does internally
try:
    # This is internal API usage simulation
    lookup = {e.value: e for e in TWGPillar}
    print(f"Manual lookup check: 'energy_infrastructure' in lookup? {'energy_infrastructure' in lookup}")
except Exception as e:
    print(f"Lookup creation failed: {e}")
