from uuid import uuid4


def generate_uuid() -> str:
    """
    generate_uuid: Generate uuid.

    Returns:
        str: Generated uuid.
    """

    return uuid4().hex
