class Unit(object):
    """The class for all of the units here"""

    def __init__(self, base_unit, base_to_unit, unit_to_base):
        """
        Unit constructor, used as a mechanism to convert between various measurements
        :param base_unit: The instance of Unit to base conversions from. If None, then assume it is the ultimate base unit
        :param base_to_unit: A callable to convert measurements between this unit and the base unit
        :param unit_to_base: A callable to convert measurements between the base unit and this unit
        """
        self.base_unit = base_unit
        self.base_to_unit = base_to_unit
        self.unit_to_base = unit_to_base


def convert(source_unit, target_unit, value):
    """
    Convert between units, returns value in target_unit
    :param source_unit: The unit of value
    :param target_unit: The desired output unit
    :param value: The value, in source_unit, to convert
    """
    # Convert value from source_unit to the ultimate base unit
    current_unit = source_unit
    current_value = value
    while current_unit.base_unit is not None:
        current_value = current_unit.unit_to_base(current_value)
        next_unit = current_unit.base_unit
        current_unit = next_unit

    # Get the chain of conversions between target_unit and the ultimate base unit
    current_unit = target_unit
    unit_chain = []
    while current_unit.base_unit is not None:
        unit_chain.append(current_unit)
        next_unit = current_unit.base_unit
        current_unit = next_unit

    # Follow the chain of conversions back to target_unit
    for unit in reversed(unit_chain):
        current_value = unit.base_to_unit(current_value)

    # Return it!
    return current_value


# Some typical units to be used
meter = Unit(base_unit=None, base_to_unit=lambda x: None, unit_to_base=lambda x: None)
centimeter = Unit(
    base_unit=meter, base_to_unit=lambda x: x * 100, unit_to_base=lambda x: x / 100
)

foot = Unit(
    base_unit=meter,
    base_to_unit=lambda x: x / 0.3048,
    unit_to_base=lambda x: x * 0.3048,
)
inch = Unit(
    base_unit=foot, base_to_unit=lambda x: x * 12, unit_to_base=lambda x: x / 12
)
