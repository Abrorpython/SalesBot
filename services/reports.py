def format_price(number):
    return "{0:,}".format(int(number)).replace(",", " ")


def is_number(text):
    try:
        int(text)
        return True
    except Exception:
        return False


def sale_preview(shop_name, product_name, qty, price):
    total = int(qty) * int(price)
    return (
        "{0}\n"
        "{1}: {2} x {3} = {4}"
    ).format(
        shop_name,
        product_name,
        qty,
        format_price(price),
        format_price(total)
    )