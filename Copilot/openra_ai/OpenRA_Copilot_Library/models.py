from typing import List, Dict
from dataclasses import dataclass


class Location:
    def __init__(self, x, y):
        # x is the horion offset in the map.
        # y is the vertical offset in the map.
        self.x = x
        self.y = y

    def __eq__(self, other):
        if isinstance(other, Location):
            return self.x == other.x and self.y == other.y
        return False
    
    def __add__(self, other):
        if isinstance(other, Location):
            return Location(self.x + other.x, self.y + other.y)
        return NotImplemented
    
    def __floordiv__(self, other):
        if isinstance(other, int):
            return Location(self.x // other, self.y // other)
        return NotImplemented
    
    def to_dict(self):
        return {"x": self.x, "y": self.y}

    def manhattan_distance(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def euclidean_distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    


class TargetsQueryParam:
    # when construct the TargetQueryParam, The type should be a list or None. each element in the list is one of {ALL_UNITS}. otherwise, convert it to elements in the possible list.
    # The faction should be None or one of {ALL_ACTORS}, otherwise convert it to the possible value.
    # The group_id should be a list and each element in the list is one of  {ALL_GROUPS}, otherwise convert it to possible value.
    # The direction should be None or one of {ALL_DIRECTIONS}, otherwise convert it to possible value.
    def __init__(self, type: str = None, faction: str = None, group_id: list[int] = None, restrain=None, location: Location = None, direction: str = None, distance: int = None):
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

#地图信息查询返回结构体，IsVisible是当前视野可见的部分为true，IsExplored是探索过的格子就是true
@dataclass
class MapQueryResult:
    MapWidth: int
    MapHeight: int
    Height: List[List[int]]
    IsVisible: List[List[bool]]
    IsExplored: List[List[bool]]
    Terrain: List[List[str]]
    ResourcesType: List[List[str]]
    Resources: List[List[int]]

    def get_value_at_location(self, grid_name: str, location: 'Location'):
        grid = getattr(self, grid_name, None)
        if grid is None:
            raise AttributeError(
                f"Grid '{grid_name}' does not exist in MapQueryResult.")
        if 0 <= location.x < len(grid) and 0 <= location.y < len(grid[0]):
            return grid[location.x][location.y]
        else:
            raise ValueError("Location out of bounds")

#玩家基础信息查询返回结构体，Cash和Resources的和是玩家持有的金钱，Power是剩余电力
@dataclass
class PlayerBaseInfo:
    Cash: int
    Resources: int
    Power: int
    PowerDrained: int
    PowerProvided: int

#屏幕信息查询的返回结果，Min是屏幕左上角，Max是右下角，MousePosition是当前鼠标所在位置，Location都是整数坐标
@dataclass
class ScreenInfoResult:
    ScreenMin: Location
    ScreenMax: Location
    IsMouseOnScreen: bool
    MousePosition: Location

    def to_dict(self) -> Dict:
        return {
            "ScreenMin": self.ScreenMin.to_dict() if isinstance(self.ScreenMin, Location) else self.ScreenMin,
            "ScreenMax": self.ScreenMax.to_dict() if isinstance(self.ScreenMax, Location) else self.ScreenMax,
            "IsMouseOnScreen": self.IsMouseOnScreen,
            "MousePosition": self.MousePosition.to_dict() if isinstance(self.MousePosition, Location) else self.MousePosition,
        }
