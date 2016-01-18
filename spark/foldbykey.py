def append(a, b):
    return a.append(b)

def name_fold(a, b):
    folded_ids = a[0] + b[0]
    folded_positions = a[1] + b[1]
    return (folded_ids, folded_positions)