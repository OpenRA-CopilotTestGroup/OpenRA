from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Tuple, Callable
import socket
import json
import time
from threading import Lock

# Constants from more_context.txt
ALL_ACTORS = ['己方', '敌方', '敌人', '对方', '对手', '中立']
ALL_DIRECTIONS = ['上', '下', '左', '右', '东', '西', '南', '北', '左上', '右上', '左下', '右下', '东北', '西北', '东南', '西南', '附近', '左右', '旁边']
ALL_GROUPS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
ALL_REGIONS = ['地图中央', '地图左上', '地图上方', '地图右上', '地图右侧', '地图右下', '地图下方', '地图左下', '地图左侧', '视线范围', '全地图', '全屏幕', '屏幕中央', '屏幕左上', '屏幕上方', '屏幕右上', '屏幕右侧', '屏幕右下', '屏幕下方', '屏幕左下', '屏幕左侧']
ALL_RELATIVES = ['上方', '下方', '左侧', '右侧', '左上方', '左下方', '右上方', '右下方', '中央', '中间', '左边', '右边', '上边', '下边']

class UnitType(Enum):
    INFANTRY = "步兵"
    ROCKET_INFANTRY = "火箭兵"
    ENGINEER = "工程师"
    GRENADIER = "手雷兵"
    TANK = "重坦"
    HARVESTER = "矿车"
    ANTI_AIR = "防空车"
    APC = "装甲车"
    V2_LAUNCHER = "v2"
    MAMMOTH_TANK = "猛犸坦克"
    # ... other unit types

class BuildingType(Enum):
    POWER_PLANT = "电厂"
    BARRACKS = "兵营"
    ORE_REFINERY = "矿场"
    FACTORY = "车间"
    RADAR = "雷达"
    REPAIR_CENTER = "维修中心"
    NUCLEAR_PLANT = "核电"
    TECH_CENTER = "科技中心"
    AIRFIELD = "机场"
    STORAGE_TANK = "储油罐"
    WELL = "井"
    MONEY_STORAGE = "存钱罐"
    FLAME_TOWER = "喷火塔"
    TESLA_COIL = "特斯拉线圈"
    ANTI_AIR_TOWER = "防空塔"
    IRON_CURTAIN = "铁幕"
    MISSILE_SILO = "导弹发射井"
    # ... other building types

class PathFindingMethod(Enum):
    SHORTEST = "最短路"
    LEFT = "左路"
    RIGHT = "右路"

class Direction(Enum):
    NORTH = "上"
    EAST = "右"
    SOUTH = "下"
    WEST = "左"
    NORTHEAST = "右上"
    NORTHWEST = "左上"
    SOUTHEAST = "右下"
    SOUTHWEST = "左下"

# Building dependencies using enums
BUILDING_DEPENDENCIES = {
    BuildingType.POWER_PLANT: [],
    BuildingType.BARRACKS: [BuildingType.POWER_PLANT],
    BuildingType.ORE_REFINERY: [BuildingType.POWER_PLANT],
    BuildingType.FACTORY: [BuildingType.ORE_REFINERY],
    BuildingType.RADAR: [BuildingType.ORE_REFINERY],
    BuildingType.REPAIR_CENTER: [BuildingType.FACTORY],
    BuildingType.NUCLEAR_PLANT: [BuildingType.RADAR],
    BuildingType.TECH_CENTER: [BuildingType.FACTORY, BuildingType.RADAR],
    BuildingType.AIRFIELD: [BuildingType.RADAR]
}

# Unit dependencies using enums
UNIT_DEPENDENCIES = {
    UnitType.INFANTRY: [BuildingType.BARRACKS],
    UnitType.ROCKET_INFANTRY: [BuildingType.BARRACKS],
    UnitType.ENGINEER: [BuildingType.BARRACKS],
    UnitType.GRENADIER: [BuildingType.BARRACKS],
    UnitType.HARVESTER: [BuildingType.FACTORY],
    UnitType.ANTI_AIR: [BuildingType.FACTORY],
    UnitType.APC: [BuildingType.FACTORY],
    UnitType.TANK: [BuildingType.FACTORY, BuildingType.REPAIR_CENTER],
    UnitType.V2_LAUNCHER: [BuildingType.FACTORY, BuildingType.RADAR],
    UnitType.MAMMOTH_TANK: [BuildingType.FACTORY, BuildingType.REPAIR_CENTER, BuildingType.TECH_CENTER]
}

@dataclass
class Unit:
    """Represents a game unit (building or military unit)"""
    actor_id: int
    type: Union[UnitType, BuildingType]
    position: Tuple[int, int]
    hp_percent: int
    state: str
    faction: str = "己方"
    
    @property
    def is_alive(self) -> bool:
        return self.hp_percent > 0
        
    @property
    def is_idle(self) -> bool:
        return self.state == "待命"

@dataclass
class Building(Unit):
    """Specialized unit type for buildings"""
    power_provided: int = 0
    power_required: int = 0
    is_powered: bool = True

@dataclass
class Resources:
    cash: int
    power: int
    available_power: int
    resource_nodes: int

@dataclass 
class StrategicInfo:
    explored_percent: float
    last_enemy_contact: Optional[Tuple[float, str]]  # (time, location)
    estimated_enemy_strength: Dict[UnitType, int]

@dataclass
class GameState:
    timestamp: float
    resources: Resources
    units: List[Unit]
    buildings: List[Building]
    strategic_info: StrategicInfo
    alerts: List[str]

@dataclass
class GameConnection:
    """Handles low-level socket communication with the game server"""
    host: str
    port: int
    _lock: Lock = Lock()  # Thread safety for concurrent requests

    def send_command(self, command: str, data: dict) -> Optional[dict]:
        """Send a command to the game server and receive the response
        
        Args:
            command: Command name
            data: Command parameters
            
        Returns:
            Optional[dict]: JSON response or None if failed
        """
        data['command'] = command
        json_data = json.dumps(data)
        
        with self._lock:  # Thread-safe communication
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((self.host, self.port))
                    sock.sendall(json_data.encode('utf-8'))
                    response = self._receive_data(sock)
                    
                response_json = json.loads(response)
                if response_json.get("status", 0) < 0:
                    print(f"Error: Command '{command}' failed with status {response_json['status']}")
                return response_json
            except Exception as e:
                print(f"Communication error: {str(e)}")
                return None
    
    def _receive_data(self, sock: socket.socket) -> str:
        """Receive all data from socket until connection closes"""
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks).decode('utf-8')

class GameStateCache:
    """Caches and manages game state information"""
    def __init__(self):
        self._state: Optional[GameState] = None
        self._last_update: float = 0
        self._cache_duration: float = 0.1  # State cache duration in seconds
        self._connection: Optional[GameConnection] = None
    
    def initialize(self, connection: GameConnection) -> None:
        """Initialize cache with game connection"""
        self._connection = connection
    
    def get_current_state(self) -> GameState:
        """Get current game state, refreshing if cache is stale"""
        current_time = time.time()
        if not self._state or (current_time - self._last_update) > self._cache_duration:
            self._refresh_state()
        return self._state
    
    def _refresh_state(self) -> None:
        """Refresh the cached game state"""
        if not self._connection:
            raise RuntimeError("GameStateCache not initialized with connection")
            
        # Get base info
        base_info = self._get_base_info()
        
        # Get units and buildings
        units = []
        buildings = []
        
        actors_response = self._connection.send_command('query_actor', {
            "targets": {"faction": "己方"}
        })
        
        if actors_response and "actors" in actors_response:
            for actor_data in actors_response["actors"]:
                unit = self._create_unit_from_data(actor_data)
                if isinstance(unit.type, BuildingType):
                    buildings.append(unit)
                else:
                    units.append(unit)
                    
        # Get strategic info
        strategic_info = self._get_strategic_info()
        
        # Update state
        self._state = GameState(
            timestamp=time.time(),
            resources=base_info,
            units=units,
            buildings=buildings,
            strategic_info=strategic_info,
            alerts=[]  # TODO: Implement alerts system
        )
        self._last_update = time.time()
    
    def _get_base_info(self) -> Resources:
        """Get player's base resource information"""
        response = self._connection.send_command('player_baseinfo_query', {})
        if not response:
            return Resources(0, 0, 0, 0)
            
        return Resources(
            cash=response.get('Cash', 0),
            power=response.get('Power', 0),
            available_power=response.get('PowerProvided', 0) - response.get('PowerDrained', 0),
            resource_nodes=response.get('Resources', 0)
        )
    
    def _get_strategic_info(self) -> StrategicInfo:
        """Get strategic game information"""
        # Get map info for exploration percentage
        map_response = self._connection.send_command('map_query', {})
        
        if not map_response:
            return StrategicInfo(0.0, None, {})
            
        # Calculate exploration percentage
        total_cells = len(map_response.get('IsExplored', [])) * len(map_response.get('IsExplored', [[]])[0])
        explored_cells = sum(sum(row) for row in map_response.get('IsExplored', [[]]))
        explored_percent = explored_cells / total_cells if total_cells > 0 else 0
        
        # TODO: Implement enemy contact tracking and strength estimation
        return StrategicInfo(
            explored_percent=explored_percent,
            last_enemy_contact=None,
            estimated_enemy_strength={}
        )
    
    def _create_unit_from_data(self, data: dict) -> Unit:
        """Create a Unit or Building instance from actor data"""
        unit_type = data.get('type')
        is_building = unit_type in [b.value for b in BuildingType]
        
        if is_building:
            return Building(
                actor_id=data['id'],
                type=BuildingType(unit_type),
                position=(data['position']['x'], data['position']['y']),
                hp_percent=data['hp'] * 100 // max(data['maxHp'], 1),
                state=data.get('state', '待命'),
                power_provided=data.get('powerProvided', 0),
                power_required=data.get('powerRequired', 0),
                is_powered=data.get('isPowered', True)
            )
        else:
            return Unit(
                actor_id=data['id'],
                type=UnitType(unit_type),
                position=(data['position']['x'], data['position']['y']),
                hp_percent=data['hp'] * 100 // max(data['maxHp'], 1),
                state=data.get('state', '待命')
            )
    
    def invalidate(self) -> None:
        """Force invalidate the cache"""
        self._state = None

@dataclass
class PrerequisiteStatus:
    """Status of prerequisites check"""
    can_produce: bool
    missing_prereqs: List[Union[UnitType, BuildingType]]
    error_message: Optional[str] = None

class ActionStatus(Enum):
    PENDING = 0
    SUCCESS = 1
    FAILED = -1
    PREREQ_NOT_MET = -2

@dataclass
class ActionResult:
    status: ActionStatus
    wait_id: Optional[int] = None
    required_prereqs: List[str] = None
    estimated_time: float = 0.0

class DependencyManager:
    """Manages building and unit dependencies"""
    def __init__(self):
        self.building_chains = BUILDING_DEPENDENCIES
        self.unit_chains = UNIT_DEPENDENCIES
        self._state_cache: Optional[GameStateCache] = None
        
    def initialize(self, state_cache: GameStateCache) -> None:
        """Initialize with game state cache"""
        self._state_cache = state_cache
        
    def check_prerequisites(self, target: Union[UnitType, BuildingType]) -> PrerequisiteStatus:
        """Check if all prerequisites are met for a target unit/building
        
        Args:
            target: Unit or building type to check
            
        Returns:
            PrerequisiteStatus with results
        """
        if not self._state_cache:
            raise RuntimeError("DependencyManager not initialized with state cache")
            
        # Get current game state
        state = self._state_cache.get_current_state()
        
        # Determine which dependency chain to use
        deps = self.building_chains.get(target, []) if isinstance(target, BuildingType) else self.unit_chains.get(target, [])
            
        # Check each dependency
        missing = []
        for dep in deps:
            has_dep = any(b.type == dep and b.is_powered for b in state.buildings)
            if not has_dep:
                missing.append(dep)
                
        return PrerequisiteStatus(
            can_produce=len(missing) == 0,
            missing_prereqs=missing,
            error_message=f"Missing required buildings: {', '.join(d.value for d in missing)}" if missing else None
        )
        
    def get_build_order(self, target: Union[UnitType, BuildingType]) -> List[BuildingType]:
        """Get optimal build order to enable production of target
        
        Args:
            target: Desired unit or building type
            
        Returns:
            List of buildings needed in optimal order
        """
        deps = self.building_chains.get(target, []) if isinstance(target, BuildingType) else self.unit_chains.get(target, [])
            
        # Simple topological sort
        build_order = []
        seen = set()
        
        def add_deps(building: BuildingType) -> None:
            if building not in seen:
                seen.add(building)
                for dep in self.building_chains.get(building, []):
                    add_deps(dep)
                build_order.append(building)
                
        for dep in deps:
            add_deps(dep)
            
        return build_order

class EnhancedGameAPI:
    def __init__(self, host: str, port: int = 7445):
        """Initialize the enhanced game API
        
        Args:
            host: Game server host
            port: Game server port
        """
        # Initialize components
        self.connection = GameConnection(host, port)
        self.state_cache = GameStateCache()
        self.dependency_mgr = DependencyManager()
        
        # Connect components
        self.state_cache.initialize(self.connection)
        self.dependency_mgr.initialize(self.state_cache)
        
    def wait_for_action(self, wait_id: int, timeout: float = 20.0) -> ActionResult:
        """Wait for an action to complete
        
        Args:
            wait_id: Action wait ID
            timeout: Maximum wait time in seconds
            
        Returns:
            ActionResult with final status
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.connection.send_command('query_wait_info', {"waitId": wait_id})
            if not response:
                return ActionResult(status=ActionStatus.FAILED)
                
            if response.get("waitStatus") == "success":
                return ActionResult(status=ActionStatus.SUCCESS)
                
            time.sleep(0.1)
            
        return ActionResult(
            status=ActionStatus.FAILED,
            error_message="Action timed out"
        )
        
    def auto_build(self, target: Union[UnitType, BuildingType]) -> ActionResult:
        """Automatically build all prerequisites and then the target
        
        Args:
            target: Desired unit or building type
            
        Returns:
            ActionResult for the final build action
        """
        # Get build order
        build_order = self.dependency_mgr.get_build_order(target)
        
        # Build each prerequisite
        for building in build_order:
            result = self.build_structure(building)
            if result.status != ActionStatus.SUCCESS:
                if result.wait_id:
                    result = self.wait_for_action(result.wait_id)
                if result.status != ActionStatus.SUCCESS:
                    return result
                    
        # Build the target if it's a building
        if isinstance(target, BuildingType):
            result = self.build_structure(target)
            if result.wait_id:
                return self.wait_for_action(result.wait_id)
            return result
            
        return ActionResult(status=ActionStatus.SUCCESS)
        
    def get_unit_by_id(self, actor_id: int) -> Optional[Unit]:
        """Get unit by its actor ID
        
        Args:
            actor_id: Actor ID to find
            
        Returns:
            Unit if found, None otherwise
        """
        response = self.connection.send_command('query_actor', {
            "targets": {"actorId": [actor_id]}
        })
        
        if response and "actors" in response and response["actors"]:
            return self.state_cache._create_unit_from_data(response["actors"][0])
        return None

    def find_path(self, units: List[Unit], destination: Tuple[int, int], method: str) -> List[Tuple[int, int]]:
        response = self.connection.send_command('find_path', {
            "actors": [u.actor_id for u in units],
            "destination": {"x": destination[0], "y": destination[1]},
            "method": method
        })
        return response.get("path", [destination]) if response else [destination]

    def move_units_by_path(self, units: List[Unit], path: List[Tuple[int, int]]) -> ActionResult:
        for point in path:
            result = self.move_units({"actorId": [u.actor_id for u in units]}, point)
            if result.status != ActionStatus.SUCCESS:
                return result
        return ActionResult(status=ActionStatus.SUCCESS)
    # Core Action Methods
    def build_structure(self, 
                       building: BuildingType, 
                       quantity: int = 1, 
                       check_existing: bool = True) -> ActionResult:
        """Build a structure
        
        Parameters:
        - building: 建筑类型 (BuildingType enum)
        - quantity: 建造数量
        - check_existing: 是否自动检查已有建筑
        """
        # Check prerequisites first
        prereq_status = self.check_prerequisites(building)
        if not prereq_status.can_produce:
            return ActionResult(
                status=ActionStatus.PREREQ_NOT_MET,
                required_prereqs=prereq_status.missing_prereqs,
                error_message=prereq_status.error_message
            )
            
        # Check if we already have enough of this building type
        if check_existing:
            existing = self.find_units(unit_type=building, state="完成")
            if len(existing) >= quantity:
                return ActionResult(status=ActionStatus.SUCCESS)
        
        # Send build command
        response = self.connection.send_command('start_production', {
            "units": [{
                "unit_type": building.value,
                "quantity": quantity
            }]
        })
        
        if not response:
            return ActionResult(status=ActionStatus.FAILED)
            
        return ActionResult(
            status=ActionStatus.PENDING if response.get("waitId") else ActionStatus.FAILED,
            wait_id=response.get("waitId"),
            estimated_time=response.get("estimatedTime", 0.0)
        )

    def produce_units(self,
                     unit: UnitType,
                     quantity: int = 1,
                     rally_point: Optional[Tuple[int, int]] = None) -> ActionResult:
        """Produce military units
        
        Parameters:
        - unit: 单位类型 (UnitType enum)
        - quantity: 生产数量
        - rally_point: 集合点坐标 (x,y)
        """
        # Check prerequisites
        prereq_status = self.check_prerequisites(unit)
        if not prereq_status.can_produce:
            return ActionResult(
                status=ActionStatus.PREREQ_NOT_MET,
                required_prereqs=prereq_status.missing_prereqs,
                error_message=prereq_status.error_message
            )
        
        # Prepare production command
        command_data = {
            "units": [{
                "unit_type": unit.value,
                "quantity": quantity
            }]
        }
        
        if rally_point:
            command_data["rally_point"] = {"x": rally_point[0], "y": rally_point[1]}
            
        response = self.connection.send_command('start_production', command_data)
        
        if not response:
            return ActionResult(status=ActionStatus.FAILED)
            
        return ActionResult(
            status=ActionStatus.PENDING if response.get("waitId") else ActionStatus.FAILED,
            wait_id=response.get("waitId"),
            estimated_time=response.get("estimatedTime", 0.0)
        )

    def move_units(self,
                  unit_filter: Dict,
                  destination: Union[Tuple[int, int], str],
                  formation: str = "默认",
                  attack_move: bool = False) -> ActionResult:
        """Move units to a destination
        
        Parameters:
        - unit_filter: 单位筛选条件 
          (e.g. {"type": UnitType.INFANTRY, "state": "待命"})
        - destination: 目标位置 (坐标或战略点名称)
        - formation: 阵型配置
        - attack_move: 是否攻击移动
        """
        # Find units matching the filter
        units = self.find_units(**unit_filter)
        if not units:
            return ActionResult(
                status=ActionStatus.FAILED,
                error_message="No units found matching the filter criteria"
            )
            
        # Handle strategic point names
        if isinstance(destination, str):
            strategic_points = self.get_strategic_points()
            if destination not in strategic_points:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    error_message=f"Unknown strategic point: {destination}"
                )
            destination = strategic_points[destination]
            
        # Prepare move command
        command_data = {
            "targets": {"actorId": [unit.actor_id for unit in units]},
            "location": {"x": destination[0], "y": destination[1]},
            "formation": formation,
            "isAttackMove": 1 if attack_move else 0
        }
        
        response = self.connection.send_command('move_actor', command_data)
        
        if not response:
            return ActionResult(status=ActionStatus.FAILED)
            
        return ActionResult(
            status=ActionStatus.SUCCESS if response.get("status", 0) > 0 else ActionStatus.FAILED
        )

    # State Management
    def get_game_state(self) -> GameState:
        """返回结构化游戏状态"""
        return self.state_cache.get_current_state()

    # Dependency Management
    def check_prerequisites(self, target: Union[UnitType, BuildingType]) -> PrerequisiteStatus:
        """检查建造/生产前提条件"""
        return self.dependency_mgr.check_prerequisites(target)

    # Enhanced Query Methods
    def find_units(self, 
                  unit_type: UnitType = None,
                  state: str = "待命",
                  area: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None) -> List[Unit]:
        """Query units with advanced filtering
        
        Parameters:
        - unit_type: 单位类型过滤
        - state: 单位状态 (待命/移动中/战斗中)
        - area: 搜索区域 ((min_x, min_y), (max_x, max_y))
        """
        query_params = {
            "type": [unit_type.value] if unit_type else None,
            "state": state,
            "faction": "己方"
        }
        
        if area:
            query_params["area"] = {
                "min": {"x": area[0][0], "y": area[0][1]},
                "max": {"x": area[1][0], "y": area[1][1]}
            }
            
        response = self.connection.send_command('query_actor', {"targets": query_params})
        
        if not response or "actors" not in response:
            return []
            
        units = []
        for actor_data in response["actors"]:
            unit = Unit(
                actor_id=actor_data["id"],
                type=UnitType(actor_data["type"]),
                position=(actor_data["position"]["x"], actor_data["position"]["y"]),
                hp_percent=actor_data["hp"] * 100 // max(actor_data["maxHp"], 1),
                state=actor_data.get("state", state)
            )
            units.append(unit)
            
        return units

    # Utility Methods
    def get_strategic_points(self) -> Dict[str, Tuple[int, int]]:
        """获取关键战略点坐标"""
        return {
            "MAIN_BASE": (47, 98),
            "ENEMY_BASE_ESTIMATED": (85, 72),
            "RESOURCE_FIELD": (62, 108)
        }

    # Event Callbacks
    def register_action_callback(self, 
                               wait_id: int,
                               callback: Callable[[ActionResult], None]):
        """注册动作完成回调"""
        pass
