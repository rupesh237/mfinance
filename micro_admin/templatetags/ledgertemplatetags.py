from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def demand_collections_difference(demand, collection):
    """
    Returns the difference between demand and collection as a Decimal.
    """
    if demand is None:
        demand = 0
    if collection is None:
        collection = 0
    diff = Decimal(demand) - Decimal(collection)
    return diff
