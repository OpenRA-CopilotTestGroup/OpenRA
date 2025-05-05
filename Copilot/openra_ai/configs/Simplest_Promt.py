
@dataclass
class Location:
    x: int
    y: int

# 查询目标的查询参数，用于查询符合条件的目标。
@dataclass
class TargetsQueryParam:
    type: Optional[List[str]] = None
    faction: Optional[str] = None
    group_id: Optional[List[int]] = None
    restrain: Optional[List[dict]] = None

    location: Optional[Location] = None
    direction: Optional[str] = None
    range: Optional[str] = None

    def to_dict(self):
        pass


@dataclass
class Actor:
    actor_id: int
    type: Optional[str] = None
    faction: Optional[str] = None
    position: Optional[Location] = None
    hppercent: Optional[int] = None

# 地图信息查询返回结构体，IsVisible 是当前视野可见的部分为 True，IsExplored 是探索过的格子为 True。
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
        # 根据位置获取指定网格中的值。
        pass

@dataclass
class PlayerBaseInfo:
    Cash: int
    Resources: int
    Power: int
    PowerDrained: int
    PowerProvided: int

# 屏幕信息查询返回结果，Min 是屏幕左上角，Max 是右下角，MousePosition 是当前鼠标所在位置，Location 都是整数坐标。
@dataclass
class ScreenInfoResult:
    ScreenMin: Location
    ScreenMax: Location
    IsMouseOnScreen: bool
    MousePosition: Location

class GameAPI:
    def move_camera_by_location(self, location: Location) -> None:
        pass

    def move_camera_by_direction(self, direction: str, distance: int) -> None:
        pass

    def able_to_produce(self, unit_type: str) -> bool:
        pass

    def produce(self, unit_type: str, quantity: int) -> Optional[int]:
        pass

    def produce_wait(self, unit_type: str, quantity: int):
        pass

    def is_ready(self, waitId: int) -> bool:
        pass

    def wait(self, waitId: int, maxWaitTime: float = 20.0) -> bool:
        pass

    def move_units_by_location(self, actors: List[Actor], location: Location, attackmove: bool = False) -> None:
        pass

    def move_units_by_direction(self, actors: List[Actor], direction: str, distance: int) -> None:
        pass

    def move_units_by_path(self, actors: List[Actor], path: List[Location]) -> None:
        pass

    def select_units(self, query_params: TargetsQueryParam) -> None:
        pass

    def form_group(self, actors: List[Actor], group_id: int) -> None:
        pass

    def query_actor(self, query_params: TargetsQueryParam) -> List[Actor]:
        pass

    def find_path(self, actors: List[Actor], destination: Location, method: str) -> List[Location]:
        pass

    def get_actor_by_id(self, actor_id: int) -> Optional[Actor]:
        pass

    def update_actor(self, actor: Actor) -> bool:
        pass

    def deploy_units(self, actors: List[Actor]) -> dict:
        pass

    def move_camera_to(self, actor: Actor) -> None:
        pass

    def occupy_units(self, occupiers: List[Actor], targets: List[Actor]) -> None:
        pass

    def attack_target(self, attacker: Actor, target: Actor) -> bool:
        pass

    def can_attack_target(self, attacker: Actor, target: Actor) -> bool:
        pass

    def repair_units(self, actors: List[Actor]) -> Optional[int]:
        pass

    def stop(self, actors: List[Actor]) -> None:
        pass

    def visible_query(self, location: Location) -> bool:
        pass

    def explorer_query(self, location: Location) -> bool:
        pass

    def unit_range_query(self, actors: List[Actor]) -> List[int]:
        pass

    def map_query(self) -> MapQueryResult:
        pass

    def player_base_info_query(self) -> PlayerBaseInfo:
        pass

    def screen_info_query(self) -> ScreenInfoResult:
        pass

    def deploy_mcv_and_wait(self, wait_time: float = 1.0) -> None:
        pass

    def ensure_can_build_wait(self, building_name: str) -> bool:
        pass

    def ensure_can_produce_unit(self, unit_name: str) -> bool:
        pass

    def get_unexplored_nearby_positions(self, map_query_result: MapQueryResult, current_pos: Location,
                                        max_distance: int) -> List[Location]:
        pass

    def move_units_by_location_and_wait(self, actors: List[Actor], location: Location,
                                        max_wait_time: float = 10.0, tolerance_dis: int = 1) -> bool:
        pass





