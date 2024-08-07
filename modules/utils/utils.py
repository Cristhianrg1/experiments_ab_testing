import numpy as np

def convert_to_serializable(obj):
    """
    Recursively converts non-serializable objects (e.g., numpy types) to serializable types.

    Args:
        obj: The object to be converted.

    Returns:
        The converted object.
    """
    if isinstance(obj, np.float64):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    else:
        return obj
