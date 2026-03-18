def is_number(text: str) -> bool:
    try:
        int(text)
        return True
    except:
        return False