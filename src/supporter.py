def plusminus(label, operator, minimal=0, maximal=1000, dm=10):
    """ increases or decreases the value by a given amount in the boundaries"""
    try:
        value_ = int(label.text())
        value_ = value_ + (dm if operator == "+" else -dm)
        value_ = min(maximal, max(minimal, (value_ // dm) * dm))
    except ValueError:
        value_ = maximal if operator == "+" else minimal
    label.setText(str(value_))


###### This are temporary Helper Functions, they will be moved later in the UI parent class / there will be objects for them
def generate_CBB_names(w):
    return [getattr(w, f"CBB{x}") for x in range(1, 11)]


def generate_CBR_names(w):
    return [getattr(w, f"CBR{x}") for x in range(1, 9)]


def generate_LBelegung_names(w):
    return [getattr(w, f"LBelegung{x}") for x in range(1, 11)]


def generate_PBneu_names(w):
    return [getattr(w, f"PBneu{x}") for x in range(1, 11)]


def generate_ProBBelegung_names(w):
    return [getattr(w, f"ProBBelegung{x}") for x in range(1, 11)]


def generate_ingredient_fields(w):
    return [[w.LEZutatRezept, w.LEGehaltRezept, w.LEFlaschenvolumen], w.CHBHand, w.LWZutaten]


def generate_maker_ingredients_fields(w):
    return [getattr(w, f"LZutat{x}") for x in range(1, 11)]


def generate_maker_volume_fields(w):
    return [getattr(w, f"LMZutat{x}") for x in range(1, 11)]
