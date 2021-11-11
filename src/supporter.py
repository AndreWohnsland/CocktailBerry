def plusminus(label, operator, minimal=0, maximal=1000, delta=10):
    """ increases or decreases the value by a given amount in the boundaries"""
    try:
        value_ = int(label.text())
        value_ = value_ + (delta if operator == "+" else -delta)
        value_ = min(maximal, max(minimal, (value_ // delta) * delta))
    except ValueError:
        value_ = maximal if operator == "+" else minimal
    label.setText(str(value_))
