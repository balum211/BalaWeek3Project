from payments import Order, split_payment


def test_split_payment_even():
    assert split_payment(100, 4) == [25.0, 25.0, 25.0, 25.0]


def test_order_defaults():
    order = Order("o1", "c1", 50.0, 3)
    assert order.status == "paid"
