from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='divide')
def divide(value, arg):
    """
    Divides the value by the argument
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiplies the value by the argument
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return None

@register.filter(name='subtract')
def subtract(value, arg):
    """
    Subtracts the argument from the value
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return None

@register.filter
def monthly_payment(value):
    """Calculate monthly payment for a 3-month installment"""
    try:
        total = Decimal(str(value))
        return (total / 3).quantize(Decimal('0.01'))
    except:
        return 0