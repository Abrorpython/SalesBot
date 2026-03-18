def format_price(number: int) -> str:
    return f"{number:,}".replace(",", " ")


def sale_preview(shop_name: str, product_name: str, qty: int, unit_price: int) -> str:
    total = qty * unit_price
    return (
        f"{shop_name}\n"
        f"{product_name}: {qty} x {format_price(unit_price)} = {format_price(total)}"
    )