def conv_name(name):
    pass

def con_obj(scenario, side):
    side = scenario.get_side_by_name(side)
    contact = side.contacts



    if side == '红方':
        return [1,0]
    else:
        return [0,1]

def con_lat(lat):
    return [lat/90]