import sys
sys.path.insert(0, 'c:/Users/win/the_first')

from .shared.database.base import UUIDMixin, BaseModel, TimestampMixin

print("Import successful!")
print("UUIDMixin:", UUIDMixin)
print("BaseModel:", BaseModel)
print("TimestampMixin:", TimestampMixin)
