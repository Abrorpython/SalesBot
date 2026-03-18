from models import StockMovement


async def add_stock(session, product, qty: int, user_id: int, comment: str = "Omborga qo‘shildi"):
    before_qty = product.quantity
    product.quantity += qty
    after_qty = product.quantity

    movement = StockMovement(
        product_id=product.id,
        type="in",
        quantity=qty,
        before_qty=before_qty,
        after_qty=after_qty,
        comment=comment,
        created_by=user_id
    )
    session.add(movement)
    await session.commit()
    return after_qty


async def subtract_stock(session, product, qty: int, user_id: int, comment: str = "Sotuv"):
    if product.quantity < qty:
        return False, product.quantity

    before_qty = product.quantity
    product.quantity -= qty
    after_qty = product.quantity

    movement = StockMovement(
        product_id=product.id,
        type="out",
        quantity=qty,
        before_qty=before_qty,
        after_qty=after_qty,
        comment=comment,
        created_by=user_id
    )
    session.add(movement)
    await session.commit()
    return True, after_qty