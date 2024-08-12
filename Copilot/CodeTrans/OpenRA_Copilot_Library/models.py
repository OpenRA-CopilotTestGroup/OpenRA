class Location:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_dict(self):
        return {"x": self.x, "y": self.y}

class TargetsQueryParam:
    def __init__(self, type=None, faction=None, group_id=None, restrain=None, location=None, direction=None, distance=None):
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
        self.type = type
        self.faction = faction
        self.position = position
