class Location:
    def __init__(self, x, y):
        # x is the horion offset in the map.
        # y is the vertical offset in the map.
        self.x = x
        self.y = y

    def to_dict(self):
        return {"x": self.x, "y": self.y}

class TargetsQueryParam:
    # when construct the TargetQueryParam, The type should be a list or None. each element in the list is one of {ALL_UNITS}. otherwise, convert it to elements in the possible list.
    # The faction should be None or one of {ALL_ACTORS}, otherwise convert it to the possible value.
    # The group_id should be a list and each element in the list is one of  {ALL_GROUPS}, otherwise convert it to possible value.
    # The direction should be None or one of {ALL_DIRECTIONS}, otherwise convert it to possible value.
    def __init__(self, type: str = None, faction: str = None, group_id: list[int] = None, restrain = None, location: Location = None, direction: str = None, distance: int = None):
        # type is the list of {ALL_UNITS}, or None.
        # faction is one of the {ALL_ACTORS}, or None
        # group_id is  the list of {ALL_GROUPS}, or None
        # direction is one of the {ALL_DIRECTIONS}, or None
        self.type = type
        self.faction = faction
        self.group_id = group_id
        self.restrain = restrain
        self.location = location
        self.direction = direction
        self.distance = distance

    def to_dict(self):
        query = {}
        if self.type:
            query["type"] = self.type
        if self.faction:
            query["faction"] = self.faction
        if self.group_id:
            query["groupId"] = self.group_id
        if self.restrain:
            query["restrain"] = self.restrain
        if self.location:
            query["location"] = self.location.to_dict()
        if self.direction:
            query["direction"] = self.direction
        if self.distance:
            query["distance"] = self.distance
        return query

class Actor:
    def __init__(self, actor_id: int):
        self.actor_id: int = actor_id
        self.type: str = None
        self.faction: str = None
        self.position: Location = None

    def update_details(self, type: str, faction: str, position: Location):
        # type is one of all {ALL_UNITS}
        # factor is one of the {ALL_ACTORS}
        self.type = type
        self.faction = faction
        self.position = position
