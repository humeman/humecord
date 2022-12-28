def hex_to_int(inp):
    return int(inp.lower(), 16)

def int_to_hex(inp):
    return str(hex(inp))[2:]

def get_diff(ref, new):
    # Parse ref
    comp = []
    for i in range(0, 3):
        ref_v = hex_to_int(ref[i * 2:(i + 1) * 2])
        new_v = hex_to_int(new[i * 2:(i + 1) * 2])

        comp.append(new_v - ref_v)

    return comp

def get_order(val):
    val = val[1:].lower()

    info = {
        "r": hex_to_int(val[0:2]),
        "g": hex_to_int(val[2:4]),
        "b": hex_to_int(val[4:6])
    }

    base_diff_sort = {
        "r": 0,
        "g": 0,
        "b": 0
    }

    for i in range(0, 3):
        base_diff_sort[list(base_diff_sort)[i]] = info[list(base_diff_sort)[i]]

    base_diff_sort = {k: v for k, v in sorted(base_diff_sort.items(), key = lambda item: item[1])}

    order = []
    for i in range(0, 3):
        order.append(["r", "g", "b"].index(list(base_diff_sort)[i]))

    return order

def apply_diff(ref_order, old, diffs, order = None):
    if order is None:
        order = get_order(old)

    vals = []
    comp = [0, 0, 0]
    for i in range(0, 3):
        vals.append(hex_to_int(old[i * 2:(i + 1) * 2]))

    for i in range(0, 3):
        old_v = vals[i]

        # Apply based on order
        # Find index of this 'i' in current order
        order_current_i = order.index(i)

        # Match to the same ordered value in ref
        match_i = ref_order[order_current_i]

        new = old_v + diffs[match_i]

        overshoot = None
        if new > 255:
            overshoot = new - 255
            new = 255

        if new < 0:
            overshoot = 0 - new
            new = 0

        if overshoot is not None:
            for i_ in range(0, 3):
                if i_ == i:
                    continue
                
                if vals[i_] == 0 or old_v == 0:
                    continue # Div by 0

                offset = int(overshoot / old_v * vals[i_])
                temp = comp[i_] + offset
                if temp <= 0 or temp >= 255:
                    continue

                comp[i_] = temp

        comp[i] += new

    strcomp = []

    for i in comp:
        n = int_to_hex(new)

        if len(n) == 1:
            n = f"0{n}"

        strcomp.append(n)

    return "#" + "".join(strcomp)