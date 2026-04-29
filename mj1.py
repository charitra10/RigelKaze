from __future__ import annotations

import time
from heapq import heappush, heappop

from cambc import Controller, Direction, EntityType, Environment, Position, ResourceType


CARDINAL_DIRECTIONS = (
    Direction.NORTH,
    Direction.EAST,
    Direction.SOUTH,
    Direction.WEST,
)
ALL_DIRECTIONS = (
    Direction.NORTH,
    Direction.NORTHEAST,
    Direction.EAST,
    Direction.SOUTHEAST,
    Direction.SOUTH,
    Direction.SOUTHWEST,
    Direction.WEST,
    Direction.NORTHWEST,
)
BRIDGE_DELTAS = tuple(
    (dx, dy)
    for dx in range(-3, 4)
    for dy in range(-3, 4)
    if 1 < dx * dx + dy * dy <= 9
)
BUILDER_PATH_OFFSETS = (
    (0, -1, 10),
    (1, 0, 10),
    (0, 1, 10),
    (-1, 0, 10),
    (1, -1, 14),
    (1, 1, 14),
    (-1, 1, 14),
    (-1, -1, 14),
)
CARDINAL_PATH_OFFSETS = (
    (0, -1, 10),
    (1, 0, 10),
    (0, 1, 10),
    (-1, 0, 10),
)


ROTATION_ORDER = list(ALL_DIRECTIONS)
ROTATION_INDEX = {direction: index for index, direction in enumerate(ROTATION_ORDER)}
DIR_TO_DELTA = {
    Direction.NORTH: (0, -1),
    Direction.NORTHEAST: (1, -1),
    Direction.EAST: (1, 0),
    Direction.SOUTHEAST: (1, 1),
    Direction.SOUTH: (0, 1),
    Direction.SOUTHWEST: (-1, 1),
    Direction.WEST: (-1, 0),
    Direction.NORTHWEST: (-1, -1),
    Direction.CENTRE: (0, 0),
}
DELTA_TO_DIR = {delta: direction for direction, delta in DIR_TO_DELTA.items()}

WALKABLE_BUILDINGS = frozenset({
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE,
    EntityType.ROAD,
})
ENEMY_REPLACEABLE_ROUTE_BUILDINGS = frozenset({
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.ROAD,
})
ALLY_REPLACEABLE_ROUTE_BUILDINGS = frozenset({
    EntityType.ROAD,
    EntityType.MARKER,
})
ORE_OCCUPYING_BUILDINGS = frozenset({
    EntityType.HARVESTER,
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH,
    EntityType.LAUNCHER,
    EntityType.BARRIER,
    EntityType.FOUNDRY,
    EntityType.CORE,
})
ORE_ENVIRONMENTS = frozenset({
    Environment.ORE_TITANIUM,
    Environment.ORE_AXIONITE,
})

STATE_WANDER = "wander"
STATE_TRAVEL = "travel"
STATE_PREP = "prep"
STATE_BUILD_ROUTE = "build_route"
STATE_SPLITTER_SENTINELS = "splitter_sentinels"
STATE_ATTACK_SENTINEL = "attack_sentinel"

STATE_HUNT_WANDER = "hunt_wander"
STATE_HUNT_TRAVEL = "hunt_travel"
STATE_HUNT_DESTROY = "hunt_destroy"

ROLE_MINER = "miner"
ROLE_GUARDIAN = "guardian"
ROLE_ATTACKER = "attacker"
ROLE_CORE_SIEGE_ATTACKER = "core_siege_attacker"
ROLE_ROUTE_ATTACKER = ROLE_CORE_SIEGE_ATTACKER
ROLE_HUNTER = "hunter"
ROLE_AXONITE_HUNTER = "axonite_hunter"

AX_STATE_SEEK_AXIONITE = "ax_seek_axionite"
AX_STATE_BUILD_FOUNDRY = "ax_build_foundry"
AX_STATE_ROUTE_TITANIUM = "ax_route_titanium"
AX_STATE_VALIDATE_CONVEYOR = "ax_validate_conveyor"
AX_STATE_ROUTE_CORE = "ax_route_core"

GUARD_IDLE = "guard_idle"
GUARD_CORE_RESPONSE = "guard_core_response"
GUARD_RETURN_HEAL = "guard_return_heal"
GUARD_REPAIR = "guard_repair"

ATTACK_TI_THRESHOLD = 700
ATTACK_ROLE_MIN_ROUND = 40
ATTACKER_COUNT = 2
ATTACK_RALLY_TURNS = 24
INITIAL_RUSHER_MAX_ROUND = 12
ATTACK_PAIR_MAX_DIST_SQ = 8
ATTACK_PAIR_CATCHUP_DIST_SQ = 18
ATTACK_CORE_APPROACH_DIST_SQ = 40
ATTACK_STUCK_LIMIT = 16
ATTACK_ROUTE_GOAL_LIMIT = 8
ATTACK_BREAK_HEAL_STALL_LIMIT = 2

ATTACK_PHASE_RALLY = "attack_rally"
ATTACK_PHASE_CENTER = "attack_center"
ATTACK_PHASE_WANDER = "attack_wander"
ATTACK_PHASE_CHAIN = "attack_chain"
ATTACK_PHASE_BUILD_SENTINEL = "attack_build_sentinel"
ATTACK_PHASE_SUPPORT_SENTINEL = "attack_support_sentinel"
ATTACK_PHASE_CORE = "attack_core"
ATTACK_PHASE_CUT_TURRET = "attack_cut_turret"
ATTACK_PHASE_CUT_CORE_FEEDER = "attack_cut_core_feeder"
ATTACK_PHASE_BUILD_GUNNER = "attack_build_gunner"
ATTACK_PHASE_SUPPORT_GUNNER = "attack_support_gunner"
ATTACK_TARGET_TURRET_FEEDER = "attack_turret_feeder"
ATTACK_TARGET_CORE_FEEDER = "attack_core_feeder"

SYMMETRY_VERTICAL = 1
SYMMETRY_HORIZONTAL = 2
SYMMETRY_ROTATIONAL = 3

# ── Raider phases ──────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────


TARGET_ORE = "ore"
TARGET_ENEMY_HARVESTER = "enemy_harvester"
TARGET_ATTACK_TITANIUM = "attack_titanium"
TARGET_ATTACK_ENEMY_ROUTE = "attack_enemy_route"
TARGET_AXIONITE_ORE = "axionite_ore"
TARGET_AXIONITE_LINK = "axionite_link"
TARGET_FOUNDRY_ROUTE = "foundry_route"

GUARD_TARGET_DESTROY_ALLY = "destroy_ally_supply"
GUARD_TARGET_DESTROY_ALLY_HARVESTER = "destroy_ally_harvester"
GUARD_TARGET_FIRE_ENEMY = "fire_enemy_supply"
GUARD_TARGET_BUILD_GUNNER = "build_gunner"

EDGE_CONVEYOR = 1
EDGE_BRIDGE = 2
BRIDGE_EDGE_COST = 8

TARGET_STUCK_LIMIT = 10
MAX_ENTRY_ATTEMPTS = 4
MAX_FOUNDRY_ROUTE_ENTRY_ATTEMPTS = 2
MAX_ORE_TARGET_ATTEMPTS = 5
MAX_ENEMY_TARGET_ATTEMPTS = 2
BUILDER_PATH_MAX_NODES = 3000
ROUTE_PATH_MAX_NODES = 3000
GUARDIAN_IDLE_CAP = 4
GUARDIAN_REPAIR_COUNT = 2
GUARDIAN_SEARCH_STEP_LIMIT = 18
NEAR_CORE_REPAIR_DIST_SQ = 10
NEAR_CORE_DEFENDER_DIST_SQ = 25
OFFSCREEN_SCOUT_COUNT = 2
INITIAL_MINER_COUNT = 4
INITIAL_DEFENDER_COUNT = 1
HUNTER_FAST_INTERVAL = 50
HUNTER_SLOW_INTERVAL = 50
AXONITE_HUNTER_COUNT = 4
AXONITE_CONVEYOR_VALIDATE_ROUNDS = 5
AXONITE_CONVEYOR_EMPTY_LIMIT = 20

TURRET_TYPES = frozenset({
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH,
})
DIRECT_SUPPLY_BUILDINGS = frozenset({
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.ARMOURED_CONVEYOR,
})
THREAT_FEED_BUILDINGS = frozenset({
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.HARVESTER,
    EntityType.FOUNDRY,
})
REPAIRABLE_NEAR_CORE_BUILDINGS = frozenset({
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
})
CONVEYOR_SPLITTER_BRIDGE = frozenset({
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
})
CONVEYOR_SPLITTER_BRIDGE_ROAD = frozenset({
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.ROAD,
})
CARDINAL_DIRECTIONS_SET = frozenset(CARDINAL_DIRECTIONS)
ATTACK_TARGET_PRIORITIES = {
    EntityType.BUILDER_BOT: 0,
    EntityType.GUNNER: 1,
    EntityType.SENTINEL: 1,
    EntityType.BREACH: 1,
    EntityType.CORE: 2,
    EntityType.HARVESTER: 3,
    EntityType.FOUNDRY: 4,
    EntityType.CONVEYOR: 5,
    EntityType.SPLITTER: 6,
    EntityType.BRIDGE: 7,
    EntityType.ARMOURED_CONVEYOR: 8,
    EntityType.ROAD: 9,
    EntityType.BARRIER: 10,
}

COLOR_ORE = (0, 220, 255)
COLOR_ENEMY = (255, 90, 90)
COLOR_ROUTE = (255, 210, 0)
COLOR_BRIDGE = (175, 100, 255)
COLOR_STAGE = (70, 255, 120)
COLOR_SENTINEL = (255, 140, 0)
COLOR_FAILED = (255, 0, 0)
COLOR_WANDER = (255, 255, 255)
COLOR_STUCK = (255, 0, 255)
COLOR_ORE_CANDIDATE = (0, 150, 255)
COLOR_ORE_BLOCKED = (140, 60, 60)
COLOR_ORE_ATTEMPT = (0, 255, 180)
COLOR_WAIT = (255, 105, 180)
COLOR_CORE_THREAT = (255, 64, 64)
COLOR_REPAIR = (0, 255, 200)
COLOR_TURRET_TARGET = (0, 255, 255)
COLOR_TURRET_BLOCKED = (255, 0, 255)
COLOR_MARKER_INFO = (150, 220, 255)
COLOR_NEUTRALIZED_THREAT = (255, 180, 0)
COLOR_TEMP_GUARDIAN = (255, 255, 0)
COLOR_AXIONITE = (160, 80, 255)
COLOR_AXIONITE_SOURCE = (190, 80, 255)
COLOR_AXIONITE_ATTEMPT = (230, 120, 255)
COLOR_AXIONITE_FOUNDRY_SITE = (255, 180, 255)
COLOR_AXIONITE_READY_FOUNDRY = (80, 255, 120)
COLOR_AXIONITE_ROUTE_GOAL = (0, 255, 220)
COLOR_AXIONITE_TITANIUM_CONVEYOR = (40, 220, 255)
COLOR_AXIONITE_UNKNOWN_CONVEYOR = (120, 180, 220)
COLOR_AXIONITE_BAD_CONVEYOR = (255, 45, 120)
COLOR_AXIONITE_VALIDATE = (255, 255, 80)
COLOR_AXIONITE_EMPTY_WAIT = (170, 170, 170)
COLOR_ROLE_MINER = (0, 220, 255)
COLOR_ROLE_GUARDIAN = (255, 210, 0)
COLOR_ROLE_ATTACKER = (255, 90, 90)
COLOR_ROLE_CORE_SIEGE_ATTACKER = (255, 150, 0)
COLOR_ROLE_ROUTE_ATTACKER = COLOR_ROLE_CORE_SIEGE_ATTACKER
COLOR_ROLE_HUNTER = (180, 0, 255)
COLOR_ROLE_AXONITE = (255, 120, 255)


def pos_distance_sq(a: Position, b: Position) -> int:
    return a.distance_squared(b)


def manhattan(a: Position, b: Position) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def chebyshev(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def rotate_direction(direction: Direction, steps: int) -> Direction:
    if direction == Direction.CENTRE:
        return Direction.CENTRE
    return ROTATION_ORDER[(ROTATION_INDEX[direction] + steps) % len(ROTATION_ORDER)]


def opposite(direction: Direction) -> Direction:
    return rotate_direction(direction, 4)


def left_cardinal(direction: Direction) -> Direction:
    if direction == Direction.NORTH:
        return Direction.WEST
    if direction == Direction.WEST:
        return Direction.SOUTH
    if direction == Direction.SOUTH:
        return Direction.EAST
    return Direction.NORTH


def right_cardinal(direction: Direction) -> Direction:
    if direction == Direction.NORTH:
        return Direction.EAST
    if direction == Direction.EAST:
        return Direction.SOUTH
    if direction == Direction.SOUTH:
        return Direction.WEST
    return Direction.NORTH


def add_delta(pos: Position, dx: int, dy: int) -> Position:
    return Position(pos.x + dx, pos.y + dy)


def resource_matches(resource: ResourceType | str | None, expected: ResourceType) -> bool:
    if resource == expected:
        return True
    value = getattr(resource, "value", resource)
    return value == expected.value


def cardinal_direction_between(a: Position, b: Position) -> Direction | None:
    dx = b.x - a.x
    dy = b.y - a.y
    if dx == 1 and dy == 0:
        return Direction.EAST
    if dx == -1 and dy == 0:
        return Direction.WEST
    if dx == 0 and dy == 1:
        return Direction.SOUTH
    if dx == 0 and dy == -1:
        return Direction.NORTH
    return None


class Player:
    def __init__(self):
        self.width: int | None = None
        self.height: int | None = None
        self.my_team = None
        self.core_pos: Position | None = None
        self.core_goals: list[int] = []
        self.core_goal_dir: dict[int, Direction] = {}
        self.astar_stamp = 0
        self.astar_seen: list[int] = []
        self.astar_closed: list[int] = []
        self.astar_g: list[int] = []
        self.astar_parent: list[int] = []
        self.astar_step: list[int] = []
        self.known_env: list[Environment | None] = []
        self.known_building_type: list[EntityType | None] = []
        self.known_building_mine: list[bool | None] = []
        self.known_builder_present: list[bool] = []
        self.known_builder_round: list[int] = []
        self.current_round = 0

        self.spawn_order = [
            Direction.NORTH,
            Direction.EAST,
            Direction.SOUTH,
            Direction.WEST,
        ]
        self.spawned_directions: set[Direction] = set()
        self.initial_defender_spawned = False
        self.last_core_hp: int | None = None
        self.attack_wave_started = False
        self.attackers_spawned = 0
        self.extra_attackers_spawned = 0
        self.axonite_hunters_spawned = 0
        self.axonite_hunter_slots_used: set[int] = set()

        self.role: str | None = None
        self.temporary_guardian = False
        self.home_wait_idx: int | None = None
        self.guard_mode = GUARD_IDLE
        self.guard_turret_idx: int | None = None
        self.guard_target_kind: str | None = None
        self.guard_target_idx: int | None = None
        self.guard_build_idx: int | None = None
        self.guard_build_facing: Direction | None = None
        self.guard_search_dir: Direction | None = None
        self.guard_search_steps = 0

        # ── Raider state (completely rewritten) ────────────────────────────────
        # ──────────────────────────────────────────────────────────────────────

        self.primary_direction: Direction | None = None
        self.state = STATE_WANDER
        self.target_kind: str | None = None
        self.target_idx: int | None = None
        self.entry_idx: int | None = None
        self.stage_idx: int | None = None
        self.route_nodes: list[int] = []
        self.route_edges: list[int] = []
        self.route_build_index = 0
        self.pending_ore_sentinels: list[int] = []
        self.pending_ore_outward_sentinel_idx: int | None = None
        self.pending_splitter_sentinels: list[int] = []
        self.final_splitter_idx: int | None = None
        self.occupied_titanium: set[int] = set()
        self.occupied_axionite: set[int] = set()
        self.bad_targets: set[tuple[str, int]] = set()
        self.last_failed_idx: int | None = None
        self.move_path: list[int] = []
        self.move_goal_signature: tuple[int, ...] = ()
        self.last_position_idx: int | None = None
        self.stuck_rounds = 0
        self.waiting_for_titanium = False
        self.route_ready = False
        self.debug_candidate_ores: list[int] = []
        self.debug_blocked_ores: list[int] = []
        self.debug_attempted_ores: list[int] = []
        self.route_goal_indices: list[int] = []
        self.route_goal_dir: dict[int, Direction] = {}
        self.route_allow_splitter = True
        self.route_enable_ore_defenses = True

        self.attack_phase = ATTACK_PHASE_RALLY
        self.attack_spawn_round = 0
        self.attack_symmetry_candidates: list[int] = []
        self.attack_symmetry: int | None = None
        self.attack_enemy_core_pos: Position | None = None
        self.attack_target_idx: int | None = None
        self.attack_target_kind: str | None = None
        self.attack_build_idx: int | None = None
        self.attack_anchor_idx: int | None = None
        self.attack_gunner_dir: Direction | None = None
        self.attack_sentinel_idx: int | None = None
        self.attack_sentinel_dir: Direction | None = None
        self.attack_feeder_idx: int | None = None
        self.attack_direct_feed = False
        self.attack_route_goal_plan: dict[int, tuple[int, Direction]] = {}
        self.attack_debug_core_tiles: list[int] = []
        self.attack_debug_sentinel_options: list[int] = []
        self.attack_break_idx: int | None = None
        self.attack_break_last_hp: int | None = None
        self.attack_break_stall_rounds = 0
        self.attack_last_hp: int | None = None
        self.attack_last_position_idx: int | None = None
        self.attack_stuck_rounds = 0
        self.hunt_debug_targets: list[int] = []
        self.hunt_debug_goal_idx: int | None = None
        self.hunt_debug_state: str | None = None
        self.ax_state = AX_STATE_SEEK_AXIONITE
        self.axionite_harvester_idx: int | None = None
        self.axionite_foundry_idx: int | None = None
        self.seen_ally_conveyors: set[int] = set()
        self.seen_ally_titanium_conveyors: set[int] = set()
        self.seen_ally_axionite_conveyors: set[int] = set()
        self.bad_axonite_foundry_sites: set[int] = set()
        self.axionite_conveyor_validate_rounds = 0
        self.axionite_conveyor_empty_rounds = 0

    def run(self, c: Controller) -> None:
        self.ensure_setup(c)
        entity_type = c.get_entity_type()
        if entity_type == EntityType.CORE:
            self.run_core(c)
        elif entity_type == EntityType.BUILDER_BOT:
            self.run_builder(c)
        elif entity_type == EntityType.GUNNER:
            self.run_gunner(c)
        elif entity_type == EntityType.SENTINEL:
            self.run_sentinel(c)

    def ensure_setup(self, c: Controller) -> None:
        if self.width is None:
            self.width = c.get_map_width()
            self.height = c.get_map_height()
            total = self.width * self.height
            self.astar_seen = [0] * total
            self.astar_closed = [0] * total
            self.astar_g = [0] * total
            self.astar_parent = [-1] * total
            self.astar_step = [0] * total
            self.known_env = [None] * total
            self.known_building_type = [None] * total
            self.known_building_mine = [None] * total
            self.known_builder_present = [False] * total
            self.known_builder_round = [0] * total
        if self.my_team is None:
            self.my_team = c.get_team()
        self.current_round = c.get_current_round()
        self.refresh_vision_cache(c)
        if c.get_entity_type() == EntityType.CORE:
            self.core_pos = c.get_position()
            self.ensure_core_goals()
        elif self.core_pos is None:
            self.core_pos = self.find_allied_core(c)
            if self.core_pos is not None:
                self.ensure_core_goals()

    def ensure_core_goals(self) -> None:
        if self.core_pos is None or self.core_goals:
            return
        center = self.core_pos
        goals: list[int] = []
        goal_dir: dict[int, Direction] = {}
        candidates = []
        for x in range(center.x - 1, center.x + 2):
            candidates.append((Position(x, center.y - 2), Direction.SOUTH))
            candidates.append((Position(x, center.y + 2), Direction.NORTH))
        for y in range(center.y - 1, center.y + 2):
            candidates.append((Position(center.x - 2, y), Direction.EAST))
            candidates.append((Position(center.x + 2, y), Direction.WEST))
        seen: set[int] = set()
        for pos, direction in candidates:
            if not self.in_bounds(pos):
                continue
            idx = self.pos_to_idx(pos)
            if idx in seen:
                continue
            seen.add(idx)
            goals.append(idx)
            goal_dir[idx] = direction
        self.core_goals = goals
        self.core_goal_dir = goal_dir

    def refresh_vision_cache(self, c: Controller) -> None:
        for pos in c.get_nearby_tiles():
            idx = self.pos_to_idx(pos)
            env = c.get_tile_env(pos)
            self.known_env[idx] = env
            building_id = c.get_tile_building_id(pos)
            if building_id is None:
                self.known_building_type[idx] = None
                self.known_building_mine[idx] = None
            else:
                building_type = c.get_entity_type(building_id)
                building_mine = c.get_team(building_id) == self.my_team
                self.known_building_type[idx] = building_type
                self.known_building_mine[idx] = building_mine
                if building_mine and building_type == EntityType.CONVEYOR:
                    self.seen_ally_conveyors.add(idx)
                    try:
                        stored = c.get_stored_resource(building_id)
                    except Exception:
                        stored = None
                    if resource_matches(stored, ResourceType.TITANIUM):
                        self.seen_ally_titanium_conveyors.add(idx)
                    elif resource_matches(stored, ResourceType.RAW_AXIONITE) or resource_matches(
                        stored, ResourceType.REFINED_AXIONITE
                    ):
                        self.seen_ally_axionite_conveyors.add(idx)
            self.known_builder_present[idx] = c.get_tile_builder_bot_id(pos) is not None
            self.known_builder_round[idx] = self.current_round
            if env in ORE_ENVIRONMENTS:
                occupied = self.visible_ore_is_occupied(c, pos, building_id)
                if env == Environment.ORE_TITANIUM:
                    if occupied:
                        self.occupied_titanium.add(idx)
                    else:
                        self.occupied_titanium.discard(idx)
                else:
                    if occupied:
                        self.occupied_axionite.add(idx)
                    else:
                        self.occupied_axionite.discard(idx)

    def visible_ore_is_occupied(
        self, c: Controller, ore_pos: Position, building_id: int | None = None
    ) -> bool:
        if c.get_tile_env(ore_pos) not in ORE_ENVIRONMENTS:
            return False
        if c.get_tile_builder_bot_id(ore_pos) is not None:
            return True
        if building_id is None:
            building_id = c.get_tile_building_id(ore_pos)
        if building_id is None:
            return False
        building_type = c.get_entity_type(building_id)
        if building_type in {EntityType.MARKER, EntityType.ROAD}:
            return False
        if building_type == EntityType.ARMOURED_CONVEYOR:
            return True
        if building_type in ORE_OCCUPYING_BUILDINGS:
            return True
        return c.get_team(building_id) == self.my_team and building_type in CONVEYOR_SPLITTER_BRIDGE

    def visible_titanium_is_occupied(
        self, c: Controller, ore_pos: Position, building_id: int | None = None
    ) -> bool:
        return self.visible_ore_is_occupied(c, ore_pos, building_id)

    def is_axionite_occupied(self, c: Controller, ore_pos: Position) -> bool:
        if c.get_tile_env(ore_pos) != Environment.ORE_AXIONITE:
            return True
        if self.pos_to_idx(ore_pos) in self.occupied_axionite:
            return True
        return self.visible_ore_is_occupied(c, ore_pos)

    def clear_route_preferences(self) -> None:
        self.route_goal_indices = []
        self.route_goal_dir = {}
        self.route_allow_splitter = True
        self.route_enable_ore_defenses = True

    def configure_core_route_preferences(self, allow_splitter: bool = True) -> None:
        self.route_goal_indices = []
        self.route_goal_dir = {}
        self.route_allow_splitter = allow_splitter
        self.route_enable_ore_defenses = True

    def current_route_goals(self) -> list[int]:
        return self.route_goal_indices if self.route_goal_indices else self.core_goals

    def current_route_goal_dir(self) -> dict[int, Direction]:
        return self.route_goal_dir if self.route_goal_dir else self.core_goal_dir

    def foundry_route_goals(self) -> tuple[list[int], dict[int, Direction]]:
        if self.axionite_foundry_idx is None:
            return [], {}
        foundry_pos = self.idx_to_pos(self.axionite_foundry_idx)
        goals: list[int] = []
        goal_dir: dict[int, Direction] = {}
        for direction in CARDINAL_DIRECTIONS:
            pos = foundry_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            idx = self.pos_to_idx(pos)
            goals.append(idx)
            goal_dir[idx] = pos.direction_to(foundry_pos)
        return goals, goal_dir

    def configure_foundry_route_preferences(self) -> bool:
        goals, goal_dir = self.foundry_route_goals()
        if not goals:
            return False
        self.route_goal_indices = goals
        self.route_goal_dir = goal_dir
        self.route_allow_splitter = False
        self.route_enable_ore_defenses = False
        return True

    def run_core(self, c: Controller) -> None:
        core_pos = c.get_position()
        self.core_pos = core_pos
        self.ensure_core_goals()
        core_id = c.get_tile_building_id(core_pos)
        core_hp = c.get_hp(core_id) if core_id is not None else None
        core_damaged = core_id is not None and core_hp < c.get_max_hp(core_id)
        core_took_damage = (
            core_hp is not None
            and self.last_core_hp is not None
            and core_hp < self.last_core_hp
        )
        if core_hp is not None:
            self.last_core_hp = core_hp

        attackers, _ = self.classify_enemy_turrets_attacking_core(c, core_pos)

        damaged_near_core = self.find_damaged_near_core_buildings(c)
        idle_guardians = self.count_idle_guardians(c)
        required_guardians = 0
        if attackers:
            required_guardians += len(attackers)
        elif core_damaged and core_took_damage:
            required_guardians += OFFSCREEN_SCOUT_COUNT
        if damaged_near_core:
            required_guardians += GUARDIAN_REPAIR_COUNT
        required_guardians = min(required_guardians, GUARDIAN_IDLE_CAP, len(self.guardian_wait_positions()))

        if idle_guardians < required_guardians:
            for direction in self.pick_guardian_spawn_directions(attackers, core_damaged, damaged_near_core):
                spawn_pos = core_pos.add(direction)
                if c.can_spawn(spawn_pos):
                    c.spawn_builder(spawn_pos)
                    return

        if self.spawn_initial_defender(c):
            return
        if self.spawn_initial_miners(c):
            return
        if self.spawn_attackers_if_ready(c):
            return
        if self.spawn_axonite_hunter(c):
            return
        if self.spawn_hunter(c):
            return
        self.spawn_regular_builder(c)

    def run_builder(self, c: Controller) -> None:
        if self.core_pos is None:
            self.core_pos = self.find_allied_core(c)
            if self.core_pos is not None:
                self.ensure_core_goals()
        if self.role is None:
            self.initialize_builder_role(c)
        if self.role == ROLE_ATTACKER:
            took_action = self.run_attacker(c)
            self.draw_debug(c)
            self.update_attack_stuck(c, took_action)
            return
        if self.role == ROLE_CORE_SIEGE_ATTACKER:
            took_action = self.run_route_attacker(c)
            self.draw_debug(c)
            self.update_attack_stuck(c, took_action)
            return
        if self.role == ROLE_HUNTER:
            self.run_hunter(c)
            self.draw_debug(c)
            return
        if self.role == ROLE_AXONITE_HUNTER:
            self.run_axonite_hunter(c)
            self.draw_debug(c)
            return
        if self.role == ROLE_MINER:
            self.try_promote_miner_to_emergency_guardian(c)
        if self.role == ROLE_GUARDIAN:
            self.run_guardian(c)
            self.draw_debug(c)
            return
        if self.primary_direction is None and self.core_pos is not None:
            self.primary_direction = self.infer_primary_direction(c.get_position())
        self.configure_core_route_preferences()
        self.waiting_for_titanium = False

        took_action = False

        if self.state == STATE_WANDER:
            if self.acquire_target(c):
                self.clear_move_path()
            else:
                took_action = self.wander_step(c)

        if not took_action and self.state == STATE_TRAVEL:
            took_action = self.handle_travel(c)
        if not took_action and self.state == STATE_PREP:
            took_action = self.handle_prep(c)
        if not took_action and self.state == STATE_BUILD_ROUTE:
            took_action = self.handle_build_route(c)
        if not took_action and self.state == STATE_SPLITTER_SENTINELS:
            took_action = self.handle_splitter_sentinels(c)

        self.draw_debug(c)
        self.update_stuck(c, took_action)

    def spawn_regular_builder(self, c: Controller) -> None:
        for direction in self.spawn_order:
            if direction in self.spawned_directions:
                continue
            spawn_pos = self.core_pos.add(direction)
            if c.can_spawn(spawn_pos):
                c.spawn_builder(spawn_pos)
                self.spawned_directions.add(direction)
                return

    def spawn_initial_defender(self, c: Controller) -> bool:
        if self.initial_defender_spawned:
            return False
        direction = self.defender_spawn_direction()
        if direction is None:
            self.initial_defender_spawned = True
            return False
        spawn_pos = self.core_pos.add(direction)
        if not c.can_spawn(spawn_pos):
            return False
        c.spawn_builder(spawn_pos)
        self.initial_defender_spawned = True
        return True

    def spawn_initial_miners(self, c: Controller) -> bool:
        if len(self.spawned_directions) >= INITIAL_MINER_COUNT:
            return False
        for direction in self.spawn_order:
            if direction in self.spawned_directions:
                continue
            spawn_pos = self.core_pos.add(direction)
            if c.can_spawn(spawn_pos):
                c.spawn_builder(spawn_pos)
                self.spawned_directions.add(direction)
                return True
        return False

    def hunter_spawn_position(self) -> Position | None:
        ordered = self.guardian_slot_order()
        if len(ordered) >= 3:
            return ordered[2]
        return None

    def axonite_spawn_positions(self) -> list[Position]:
        ordered = self.guardian_slot_order()
        preferred_indices = (1, 3, 2, 0)
        positions: list[Position] = []
        for index in preferred_indices:
            if index < len(ordered):
                positions.append(ordered[index])
        return positions[:AXONITE_HUNTER_COUNT]

    def is_hunter_spawn_position(self, pos: Position) -> bool:
        spawn_pos = self.hunter_spawn_position()
        return spawn_pos is not None and pos == spawn_pos

    def is_axonite_spawn_position(self, pos: Position) -> bool:
        if self.current_round <= INITIAL_RUSHER_MAX_ROUND:
            return False
        for candidate in self.axonite_spawn_positions():
            if pos == candidate:
                return True
        return False

    def should_spawn_hunter(self, c: Controller) -> bool:
        titanium, _ = c.get_global_resources()
        if titanium <= 2000 or c.get_unit_count() >= 50:
            return False
        interval = HUNTER_SLOW_INTERVAL if titanium > 3000 else HUNTER_FAST_INTERVAL
        return self.current_round % interval == 0

    def spawn_axonite_hunter(self, c: Controller) -> bool:
        titanium, _ = c.get_global_resources()
        if (
            titanium <= 1000
            or self.axonite_hunters_spawned >= AXONITE_HUNTER_COUNT
            or c.get_unit_count() >= 50
        ):
            return False
        for pos in self.axonite_spawn_positions():
            idx = self.pos_to_idx(pos)
            if idx in self.axonite_hunter_slots_used:
                continue
            if c.can_spawn(pos):
                c.spawn_builder(pos)
                self.axonite_hunter_slots_used.add(idx)
                self.axonite_hunters_spawned += 1
                return True
        return False

    def spawn_hunter(self, c: Controller) -> bool:
        if not self.should_spawn_hunter(c):
            return False
        role = ROLE_ATTACKER if self.extra_attackers_spawned % 2 == 0 else ROLE_CORE_SIEGE_ATTACKER
        for spawn_pos in self.attack_spawn_positions_for_role(role):
            if c.can_spawn(spawn_pos):
                c.spawn_builder(spawn_pos)
                self.extra_attackers_spawned += 1
                return True
        return False

    # ── Harvester Hunter ──────────────────────────────────────────────────

    def run_hunter(self, c: Controller) -> None:
        self.refresh_vision_cache(c)
        pos = c.get_position()
        self.hunt_debug_targets = []
        self.hunt_debug_goal_idx = None
        self.hunt_debug_state = self.hunt_state

        if self.hunt_state == STATE_HUNT_WANDER:
            target = self.hunter_find_enemy_harvester(c)
            if target is not None:
                self.hunt_target_pos = target
                self.hunt_state = STATE_HUNT_TRAVEL
                self.clear_move_path()
            else:
                self.wander_step(c)
            return

        if self.hunt_state == STATE_HUNT_TRAVEL:
            if self.hunt_target_pos is None:
                self.hunt_state = STATE_HUNT_WANDER
                return
            goals = self.action_access_goals(c, self.hunt_target_pos, allow_target_tile=True)
            current_idx = self.pos_to_idx(pos)
            if goals:
                self.hunt_debug_targets = sorted(goals)
                self.hunt_debug_goal_idx = min(
                    goals,
                    key=lambda idx: (
                        manhattan(pos, self.idx_to_pos(idx)),
                        self.pos_to_idx(self.idx_to_pos(idx)),
                    ),
                )
            if current_idx in goals:
                self.hunt_state = STATE_HUNT_DESTROY
                self.hunt_debug_state = self.hunt_state
                self.hunt_sentinels_placed = 0
                return
            # Check if harvester is still there
            if c.is_in_vision(self.hunt_target_pos):
                bid = c.get_tile_building_id(self.hunt_target_pos)
                if bid is None or c.get_entity_type(bid) != EntityType.HARVESTER or c.get_team(bid) == self.my_team:
                    self.hunt_target_pos = None
                    self.hunt_state = STATE_HUNT_WANDER
                    self.clear_move_path()
                    return
            self.move_toward_any(c, goals)
            return

        if self.hunt_state == STATE_HUNT_DESTROY:
            if self.hunt_target_pos is None:
                self.hunt_state = STATE_HUNT_WANDER
                return
            current_idx = self.pos_to_idx(pos)

            enemy_supply_targets = self.find_direct_walkable_feeders(c, self.hunt_target_pos)
            self.hunt_debug_targets = [self.pos_to_idx(target) for target in enemy_supply_targets]
            if enemy_supply_targets:
                self.hunt_debug_goal_idx = self.pos_to_idx(enemy_supply_targets[0])

            # Step 2: If there are supply targets, move onto one and fire
            if enemy_supply_targets:
                if any(current_idx == self.pos_to_idx(target) for target in enemy_supply_targets):
                    if c.can_fire(pos):
                        c.fire(pos)
                    return
                # Move onto the nearest enemy supply tile
                self.move_toward_any(c, {self.pos_to_idx(target) for target in enemy_supply_targets})
                return

            # Step 3: All supply destroyed — place up to 2 sentinels
            self.occupied_titanium.add(self.pos_to_idx(self.hunt_target_pos))
            if self.hunt_sentinels_placed < 2:
                for direction in CARDINAL_DIRECTIONS:
                    spos = self.hunt_target_pos.add(direction)
                    if not self.in_bounds(spos):
                        continue
                    sentinel_dir = self.hunter_sentinel_facing(spos)
                    if c.can_build_sentinel(spos, sentinel_dir):
                        c.build_sentinel(spos, sentinel_dir)
                        self.hunt_sentinels_placed += 1
                        return
                # If can't build sentinel from here, move closer
                vantage = self.build_vantage_goals(self.hunt_target_pos)
                if current_idx not in vantage:
                    if self.move_toward_any(c, vantage):
                        return

            # Done with this target, go find another
            self.hunt_target_pos = None
            self.hunt_state = STATE_HUNT_WANDER
            self.clear_move_path()
            return

    def hunter_find_enemy_harvester(self, c: Controller) -> Position | None:
        pos = c.get_position()
        best_pos = None
        best_dist = 999999
        for entity_id in c.get_nearby_buildings():
            try:
                etype = c.get_entity_type(entity_id)
                eteam = c.get_team(entity_id)
                if etype == EntityType.HARVESTER and eteam != self.my_team:
                    epos = c.get_position(entity_id)
                    dist = pos_distance_sq(pos, epos)
                    if dist < best_dist:
                        best_dist = dist
                        best_pos = epos
            except Exception:
                continue
        return best_pos

    def hunter_sentinel_facing(self, sentinel_pos: Position) -> Direction:
        enemy_core = self.current_enemy_core_guess()
        if enemy_core is not None:
            facing = sentinel_pos.direction_to(enemy_core)
            if facing != Direction.CENTRE:
                return facing
        if self.core_pos is not None:
            away = opposite(sentinel_pos.direction_to(self.core_pos))
            if away != Direction.CENTRE:
                return away
        return Direction.NORTH

    def has_allied_building_at(
        self, c: Controller, idx: int | None, entity_type: EntityType
    ) -> bool:
        if idx is None:
            return False
        pos = self.idx_to_pos(idx)
        if not c.is_in_vision(pos):
            return True
        building_id = c.get_tile_building_id(pos)
        if building_id is None:
            return False
        return c.get_team(building_id) == self.my_team and c.get_entity_type(building_id) == entity_type

    def has_axonite_source_at(self, c: Controller, idx: int | None) -> bool:
        if idx is None:
            return False
        pos = self.idx_to_pos(idx)
        if not c.is_in_vision(pos):
            return True
        if c.get_tile_env(pos) != Environment.ORE_AXIONITE:
            return False
        building_id = c.get_tile_building_id(pos)
        return building_id is not None and c.get_entity_type(building_id) == EntityType.HARVESTER

    def reset_axonite_mission(self, revert_role: bool = False) -> None:
        self.ax_state = AX_STATE_SEEK_AXIONITE
        self.axionite_harvester_idx = None
        self.axionite_foundry_idx = None
        self.axionite_conveyor_validate_rounds = 0
        self.axionite_conveyor_empty_rounds = 0
        self.reset_target()
        if revert_role:
            self.role = ROLE_MINER

    def run_axonite_hunter(self, c: Controller) -> None:
        if self.primary_direction is None and self.core_pos is not None:
            self.primary_direction = self.infer_primary_direction(c.get_position())
        self.waiting_for_titanium = False

        if self.ax_state != AX_STATE_SEEK_AXIONITE and not self.has_axonite_source_at(c, self.axionite_harvester_idx):
            self.reset_axonite_mission()

        if self.ax_state == AX_STATE_BUILD_FOUNDRY:
            self.handle_axonite_foundry(c)
            return

        if self.ax_state == AX_STATE_VALIDATE_CONVEYOR:
            self.handle_axonite_conveyor_validation(c)
            return

        if self.ax_state == AX_STATE_ROUTE_TITANIUM:
            if not self.configure_axonite_link_route_preferences(c):
                self.wander_step(c)
                self.update_stuck(c, True)
                return
        else:
            self.configure_core_route_preferences(allow_splitter=False)

        took_action = False
        if self.state == STATE_WANDER:
            if self.ax_state == AX_STATE_ROUTE_TITANIUM:
                if self.axionite_harvester_idx is not None and self.plan_target(
                    c, TARGET_AXIONITE_LINK, self.idx_to_pos(self.axionite_harvester_idx)
                ):
                    self.clear_move_path()
                else:
                    took_action = self.wander_step(c)
            elif self.ax_state == AX_STATE_SEEK_AXIONITE:
                if self.acquire_axionite_target(c):
                    self.clear_move_path()
                else:
                    took_action = self.wander_step(c)
            else:
                if self.acquire_target(c):
                    self.clear_move_path()
                else:
                    took_action = self.wander_step(c)

        if not took_action and self.state == STATE_TRAVEL:
            took_action = self.handle_travel(c)
        if not took_action and self.state == STATE_PREP:
            took_action = self.handle_prep(c)
        if not took_action and self.state == STATE_BUILD_ROUTE:
            took_action = self.handle_build_route(c)
        if not took_action and self.state == STATE_SPLITTER_SENTINELS:
            took_action = self.handle_splitter_sentinels(c)

        self.update_stuck(c, took_action)

    def acquire_axionite_target(self, c: Controller) -> bool:
        self.debug_candidate_ores = []
        self.debug_blocked_ores = []
        self.debug_attempted_ores = []

        ore_candidates: list[tuple[int, int, Position]] = []
        for tile in c.get_nearby_tiles():
            idx = self.pos_to_idx(tile)
            if idx in self.occupied_axionite or (TARGET_AXIONITE_ORE, idx) in self.bad_targets:
                if len(self.debug_blocked_ores) < 10:
                    self.debug_blocked_ores.append(idx)
                continue
            status = self.axionite_target_status(c, tile)
            if status is None:
                if len(self.debug_blocked_ores) < 10:
                    self.debug_blocked_ores.append(idx)
                continue
            ore_candidates.append((chebyshev(c.get_position(), tile), manhattan(c.get_position(), tile), tile))
        ore_candidates.sort()
        self.debug_candidate_ores = [
            self.pos_to_idx(pos) for _, _, pos in ore_candidates[:MAX_ORE_TARGET_ATTEMPTS]
        ]
        for _, _, ore_pos in ore_candidates[:MAX_ORE_TARGET_ATTEMPTS]:
            self.debug_attempted_ores.append(self.pos_to_idx(ore_pos))
            if self.plan_target(c, TARGET_AXIONITE_ORE, ore_pos):
                return True
        return False

    def axionite_target_status(self, c: Controller, tile: Position) -> str | None:
        if c.get_tile_env(tile) != Environment.ORE_AXIONITE:
            return None
        if c.get_tile_builder_bot_id(tile) is not None:
            return None
        building_id = c.get_tile_building_id(tile)
        if building_id is None:
            return "free"
        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)
        if building_type == EntityType.HARVESTER and building_team != self.my_team:
            return "enemy_harvester"
        if building_type in {EntityType.MARKER, EntityType.ROAD}:
            return "free"
        return None

    def reset_axonite_conveyor_validation(self) -> None:
        self.axionite_conveyor_validate_rounds = 0
        self.axionite_conveyor_empty_rounds = 0

    def configure_axonite_link_route_preferences(self, c: Controller) -> bool:
        if self.axionite_foundry_idx is None:
            self.axionite_foundry_idx = self.choose_axonite_foundry_conveyor(c)
            self.reset_axonite_conveyor_validation()
        if self.axionite_foundry_idx is None:
            return False
        goals, goal_dir = self.axionite_link_route_goals(c, self.axionite_foundry_idx)
        if not goals:
            self.bad_axonite_foundry_sites.add(self.axionite_foundry_idx)
            self.axionite_foundry_idx = None
            self.reset_axonite_conveyor_validation()
            return False
        self.route_goal_indices = goals
        self.route_goal_dir = goal_dir
        self.route_allow_splitter = False
        self.route_enable_ore_defenses = False
        return True

    def choose_axonite_foundry_conveyor(self, c: Controller) -> int | None:
        if self.axionite_harvester_idx is None:
            return None
        harvester_pos = self.idx_to_pos(self.axionite_harvester_idx)
        current_pos = c.get_position()
        candidates: list[tuple[tuple[int, int, int, int, int], int]] = []
        for idx in self.seen_ally_conveyors:
            if idx in self.bad_axonite_foundry_sites or idx in self.seen_ally_axionite_conveyors:
                continue
            pos = self.idx_to_pos(idx)
            if not self.in_bounds(pos):
                continue
            building_type = self.known_building_type[idx]
            if building_type is not None and building_type != EntityType.CONVEYOR:
                continue
            building_mine = self.known_building_mine[idx]
            if building_mine is False:
                continue
            goals, _ = self.axionite_link_route_goals(c, idx)
            if not goals:
                continue
            core_dist = manhattan(pos, self.core_pos) if self.core_pos is not None else 0
            score = (
                0 if idx in self.seen_ally_titanium_conveyors else 1,
                0 if self.near_known_titanium_source(idx) else 1,
                manhattan(harvester_pos, pos),
                -core_dist,
                manhattan(current_pos, pos),
            )
            candidates.append((score, idx))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1]

    def near_known_titanium_source(self, idx: int) -> bool:
        pos = self.idx_to_pos(idx)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy > 9:
                    continue
                candidate = Position(pos.x + dx, pos.y + dy)
                if not self.in_bounds(candidate):
                    continue
                candidate_idx = self.pos_to_idx(candidate)
                if self.known_env[candidate_idx] == Environment.ORE_TITANIUM:
                    return True
        return False

    def axionite_link_route_goals(
        self, c: Controller, foundry_idx: int
    ) -> tuple[list[int], dict[int, Direction]]:
        foundry_pos = self.idx_to_pos(foundry_idx)
        toward = self.idx_to_pos(self.axionite_harvester_idx) if self.axionite_harvester_idx is not None else None
        goals: list[int] = []
        goal_dir: dict[int, Direction] = {}
        for direction in self.ordered_cardinals_toward(foundry_pos, toward):
            pos = foundry_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            if not self.route_tile_ok(c, pos):
                continue
            idx = self.pos_to_idx(pos)
            goals.append(idx)
            goal_dir[idx] = pos.direction_to(foundry_pos)
        return goals, goal_dir

    def observe_axonite_foundry_conveyor(self, c: Controller) -> str:
        if self.axionite_foundry_idx is None:
            return "bad"
        pos = self.idx_to_pos(self.axionite_foundry_idx)
        if not c.is_in_vision(pos):
            return "unseen"
        building_id = c.get_tile_building_id(pos)
        if building_id is None:
            return "bad"
        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)
        if building_type == EntityType.FOUNDRY and building_team == self.my_team:
            return "done"
        if building_team != self.my_team or building_type != EntityType.CONVEYOR:
            return "bad"
        try:
            stored = c.get_stored_resource(building_id)
        except Exception:
            stored = None
        if resource_matches(stored, ResourceType.TITANIUM):
            self.seen_ally_titanium_conveyors.add(self.axionite_foundry_idx)
            self.axionite_conveyor_validate_rounds += 1
            self.axionite_conveyor_empty_rounds = 0
            return "titanium"
        if resource_matches(stored, ResourceType.RAW_AXIONITE) or resource_matches(
            stored, ResourceType.REFINED_AXIONITE
        ):
            self.seen_ally_axionite_conveyors.add(self.axionite_foundry_idx)
            return "bad"
        self.axionite_conveyor_empty_rounds += 1
        if (
            self.axionite_conveyor_validate_rounds == 0
            and self.axionite_conveyor_empty_rounds > AXONITE_CONVEYOR_EMPTY_LIMIT
        ):
            return "bad"
        return "empty"

    def abandon_axonite_foundry_conveyor(self) -> None:
        if self.axionite_foundry_idx is not None:
            self.bad_axonite_foundry_sites.add(self.axionite_foundry_idx)
        self.axionite_foundry_idx = None
        self.reset_axonite_conveyor_validation()
        self.ax_state = AX_STATE_ROUTE_TITANIUM
        self.reset_target()

    def handle_axonite_conveyor_validation(self, c: Controller) -> bool:
        if self.axionite_foundry_idx is None:
            self.ax_state = AX_STATE_ROUTE_TITANIUM
            return False
        foundry_pos = self.idx_to_pos(self.axionite_foundry_idx)
        if pos_distance_sq(c.get_position(), foundry_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(foundry_pos))
        status = self.observe_axonite_foundry_conveyor(c)
        if status == "done":
            self.reset_axonite_mission(revert_role=True)
            return False
        if status == "bad":
            self.abandon_axonite_foundry_conveyor()
            return False
        if self.axionite_conveyor_validate_rounds < AXONITE_CONVEYOR_VALIDATE_ROUNDS:
            return False
        self.ax_state = AX_STATE_BUILD_FOUNDRY
        return self.handle_axonite_foundry(c)

    def axonite_foundry_site_priority(self, c: Controller, pos: Position) -> int | None:
        if not c.is_in_vision(pos):
            return None
        env = c.get_tile_env(pos)
        if env in ORE_ENVIRONMENTS or env == Environment.WALL:
            return None
        building_id = c.get_tile_building_id(pos)
        if building_id is None:
            return 1
        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)
        if building_type == EntityType.FOUNDRY and building_team == self.my_team:
            return 0
        if building_type == EntityType.MARKER:
            return 1
        if building_team == self.my_team and building_type in {EntityType.ROAD, EntityType.BARRIER}:
            return 2
        if building_team != self.my_team and (
            building_type == EntityType.ROAD or building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS
        ):
            return 3
        return None

    def choose_axonite_foundry_site(self, c: Controller) -> int | None:
        if self.axionite_harvester_idx is None:
            return None
        harvester_pos = self.idx_to_pos(self.axionite_harvester_idx)
        candidates: list[tuple[tuple[int, int, int], int]] = []
        for direction in CARDINAL_DIRECTIONS:
            pos = harvester_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            priority = self.axonite_foundry_site_priority(c, pos)
            if priority is None:
                continue
            idx = self.pos_to_idx(pos)
            score = (
                priority,
                manhattan(pos, self.core_pos) if self.core_pos is not None else 0,
                idx,
            )
            candidates.append((score, idx))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1]

    def prepare_foundry_site(self, c: Controller, foundry_pos: Position) -> tuple[str, bool]:
        foundry_idx = self.pos_to_idx(foundry_pos)
        current_idx = self.pos_to_idx(c.get_position())
        builder_id = c.get_tile_builder_bot_id(foundry_pos)
        if builder_id is not None and current_idx != foundry_idx:
            return "wait", False

        building_id = c.get_tile_building_id(foundry_pos)
        if building_id is None:
            env = c.get_tile_env(foundry_pos)
            if env == Environment.EMPTY:
                return "ready", False
            return "blocked", False

        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)
        if building_type == EntityType.FOUNDRY and building_team == self.my_team:
            return "done", False
        if building_type == EntityType.MARKER:
            return "ready", False
        replaceable_allied = {EntityType.ROAD, EntityType.BARRIER}
        if self.role == ROLE_AXONITE_HUNTER and self.axionite_foundry_idx == foundry_idx:
            replaceable_allied = replaceable_allied | {EntityType.CONVEYOR}
        if building_team == self.my_team and building_type in replaceable_allied:
            if c.can_destroy(foundry_pos):
                c.destroy(foundry_pos)
                return "wait", True
            return "wait", False
        if building_team != self.my_team and (
            building_type == EntityType.ROAD or building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS
        ):
            if current_idx == foundry_idx:
                if c.can_fire(c.get_position()):
                    c.fire(c.get_position())
                    return "wait", True
                return "wait", False
            return "wait", self.move_toward_any(c, {foundry_idx})
        return "blocked", False

    def handle_axonite_foundry(self, c: Controller) -> bool:
        site_idx = self.axionite_foundry_idx
        if site_idx is None:
            self.ax_state = AX_STATE_ROUTE_TITANIUM
            return False
        self.axionite_foundry_idx = site_idx
        foundry_pos = self.idx_to_pos(site_idx)

        if pos_distance_sq(c.get_position(), foundry_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(foundry_pos))

        site_status, acted = self.prepare_foundry_site(c, foundry_pos)
        if site_status == "done":
            self.reset_axonite_mission(revert_role=True)
            return acted
        if site_status == "blocked":
            self.abandon_axonite_foundry_conveyor()
            return acted
        if site_status == "wait":
            return acted

        if self.pos_to_idx(c.get_position()) == site_idx:
            return self.move_off_current_tile(c, self.build_vantage_goals(foundry_pos))

        if c.can_build_foundry(foundry_pos):
            c.build_foundry(foundry_pos)
            self.reset_axonite_mission(revert_role=True)
            return True

        self.wait_for_titanium_shortage(c, "get_foundry_cost")
        return False

    def spawn_attackers_if_ready(self, c: Controller) -> bool:
        titanium, _ = c.get_global_resources()
        if titanium > ATTACK_TI_THRESHOLD:
            self.attack_wave_started = True
        if not self.attack_wave_started or self.attackers_spawned >= ATTACKER_COUNT:
            return False
        role = ROLE_ATTACKER if self.attackers_spawned == 0 else ROLE_CORE_SIEGE_ATTACKER
        for spawn_pos in self.attack_spawn_positions_for_role(role):
            if c.can_spawn(spawn_pos):
                c.spawn_builder(spawn_pos)
                self.attackers_spawned += 1
                return True
        return False

    def attack_spawn_directions(self) -> list[Direction]:
        if self.core_pos is None:
            return [Direction.EAST, Direction.WEST, Direction.SOUTH, Direction.NORTH]
        center = self.get_map_center()
        dx = center.x - self.core_pos.x
        dy = center.y - self.core_pos.y
        horizontal = Direction.EAST if dx >= 0 else Direction.WEST
        vertical = Direction.SOUTH if dy >= 0 else Direction.NORTH
        if abs(dx) >= abs(dy):
            ordered = [horizontal, vertical, opposite(vertical), opposite(horizontal)]
        else:
            ordered = [vertical, horizontal, opposite(horizontal), opposite(vertical)]
        result: list[Direction] = []
        for direction in ordered:
            if direction != Direction.CENTRE and direction not in result:
                result.append(direction)
        return result

    def is_attack_spawn_position(self, pos: Position) -> bool:
        if self.core_pos is None:
            return False
        return any(pos == self.core_pos.add(direction) for direction in self.attack_spawn_directions())

    def attack_spawn_role_for_position(self, pos: Position) -> str | None:
        if self.core_pos is None:
            return None
        for index, direction in enumerate(self.attack_spawn_directions()):
            if pos == self.core_pos.add(direction):
                return ROLE_ATTACKER if index % 2 == 0 else ROLE_CORE_SIEGE_ATTACKER
        return None

    def attack_spawn_positions_for_role(self, role: str) -> list[Position]:
        if self.core_pos is None:
            return []
        want_route = role == ROLE_CORE_SIEGE_ATTACKER
        positions: list[Position] = []
        for index, direction in enumerate(self.attack_spawn_directions()):
            if (index % 2 == 1) == want_route:
                positions.append(self.core_pos.add(direction))
        return positions

    def initialize_builder_role(self, c: Controller) -> None:
        if self.core_pos is None:
            self.role = ROLE_MINER
            return
        pos = c.get_position()
        if self.is_initial_rusher_position(pos):
            self.role = ROLE_ATTACKER
            self.initialize_attacker(c)
            return
        if self.is_emergency_guardian_spawn(c, pos):
            self.role = ROLE_GUARDIAN
            self.home_wait_idx = self.pos_to_idx(pos)
            self.guard_mode = GUARD_IDLE
            self.guard_search_dir = self.guardian_home_direction()
            return
        if self.is_axonite_spawn_position(pos):
            self.role = ROLE_AXONITE_HUNTER
            self.ax_state = AX_STATE_SEEK_AXIONITE
            self.axionite_harvester_idx = None
            self.axionite_foundry_idx = None
            self.reset_target()
            return
        if self.is_hunter_spawn_position(pos):
            self.role = ROLE_ATTACKER
            self.initialize_attacker(c)
            return
        if self.is_extra_rusher_position(c, pos):
            self.role = self.attack_spawn_role_for_position(pos) or ROLE_ATTACKER
            self.initialize_attacker(c)
            return
        if pos == self.initial_defender_position():
            self.role = ROLE_GUARDIAN
            self.home_wait_idx = self.pos_to_idx(pos)
            self.guard_mode = GUARD_IDLE
            self.guard_search_dir = self.core_pos.direction_to(pos)
            return
        if abs(pos.x - self.core_pos.x) == 1 and abs(pos.y - self.core_pos.y) == 1:
            if self.is_core_damaged(c) or self.find_damaged_near_core_buildings(c):
                self.role = ROLE_GUARDIAN
                self.home_wait_idx = self.pos_to_idx(pos)
                self.guard_mode = GUARD_IDLE
                self.guard_search_dir = self.core_pos.direction_to(pos)
                return
            self.role = ROLE_GUARDIAN
            self.home_wait_idx = self.pos_to_idx(pos)
            self.guard_mode = GUARD_IDLE
            self.guard_search_dir = self.core_pos.direction_to(pos)
            return
        self.role = ROLE_MINER

    def initialize_attacker(self, c: Controller) -> None:
        self.reset_target()
        self.attack_phase = ATTACK_PHASE_CENTER
        self.attack_spawn_round = self.current_round
        self.attack_symmetry_candidates = []
        self.attack_symmetry = None
        self.attack_enemy_core_pos = None
        self.attack_target_idx = None
        self.attack_target_kind = None
        self.attack_build_idx = None
        self.attack_anchor_idx = None
        self.attack_gunner_dir = None
        self.attack_sentinel_idx = None
        self.attack_sentinel_dir = None
        self.attack_feeder_idx = None
        self.attack_direct_feed = False
        self.attack_route_goal_plan = {}
        self.attack_debug_core_tiles = []
        self.attack_debug_sentinel_options = []
        self.attack_break_idx = None
        self.attack_break_last_hp = None
        self.attack_break_stall_rounds = 0
        self.attack_last_hp = c.get_hp()
        self.attack_last_position_idx = self.pos_to_idx(c.get_position())
        self.attack_stuck_rounds = 0
        self.ensure_attack_symmetry_candidates()

    def is_initial_rusher_position(self, pos: Position) -> bool:
        return False

    def is_extra_rusher_position(self, c: Controller, pos: Position) -> bool:
        if self.current_round <= INITIAL_RUSHER_MAX_ROUND:
            return False
        if not self.is_attack_spawn_position(pos):
            return False
        if self.is_core_damaged(c) or self.find_damaged_near_core_buildings(c):
            return False
        return True

    def is_emergency_guardian_spawn(self, c: Controller, pos: Position) -> bool:
        if self.core_pos is None:
            return False
        if not (self.is_core_damaged(c) or self.find_damaged_near_core_buildings(c)):
            return False
        return chebyshev(pos, self.core_pos) == 1

    def run_attacker(self, c: Controller) -> bool:
        self.waiting_for_titanium = False
        self.configure_attack_defaults()
        self.ensure_attack_symmetry_candidates()
        self.update_attack_symmetry(c)

        current_hp = c.get_hp()
        took_damage = self.attack_last_hp is not None and current_hp < self.attack_last_hp
        self.attack_last_hp = current_hp

        if self.attack_phase == ATTACK_PHASE_SUPPORT_SENTINEL:
            self.finish_attack_sentinel_placement()

        if took_damage and self.try_heal_attack_unit(c, urgent=True):
            return True

        enemy_core = self.current_enemy_core_guess()
        if not self.attack_core_is_known() or enemy_core is None:
            self.attack_phase = ATTACK_PHASE_CENTER
            return self.seek_enemy_core_for_attack(c)

        if self.state == STATE_WANDER:
            self.attack_phase = ATTACK_PHASE_WANDER
            if self.acquire_attack_titanium_target(c):
                self.clear_move_path()
                return False
            if pos_distance_sq(c.get_position(), enemy_core) > 80:
                return self.move_attacker_toward(c, enemy_core)
            return self.wander_step(c)

        if self.state == STATE_TRAVEL:
            self.attack_phase = ATTACK_PHASE_CHAIN
            return self.handle_travel(c)
        if self.state == STATE_PREP:
            self.attack_phase = ATTACK_PHASE_CHAIN
            return self.handle_prep(c)
        if self.state == STATE_BUILD_ROUTE:
            self.attack_phase = ATTACK_PHASE_CHAIN
            return self.handle_build_route(c)
        if self.state == STATE_ATTACK_SENTINEL:
            self.attack_phase = ATTACK_PHASE_BUILD_SENTINEL
            return self.handle_attack_build_sentinel(c)

        self.reset_target()
        self.attack_phase = ATTACK_PHASE_WANDER
        return False

    def run_route_attacker(self, c: Controller) -> bool:
        self.waiting_for_titanium = False
        self.configure_attack_defaults()
        self.ensure_attack_symmetry_candidates()
        self.update_attack_symmetry(c)

        current_hp = c.get_hp()
        took_damage = self.attack_last_hp is not None and current_hp < self.attack_last_hp
        self.attack_last_hp = current_hp

        if self.attack_phase == ATTACK_PHASE_SUPPORT_SENTINEL:
            self.finish_attack_sentinel_placement()

        if took_damage and self.try_heal_attack_unit(c, urgent=True):
            return True

        enemy_core = self.current_enemy_core_guess()
        if not self.attack_core_is_known() or enemy_core is None:
            self.attack_phase = ATTACK_PHASE_CENTER
            return self.seek_enemy_core_for_attack(c)

        if self.state == STATE_WANDER:
            self.attack_phase = ATTACK_PHASE_WANDER
            if self.acquire_attack_enemy_route_target(c):
                self.clear_move_path()
                return False
            if self.follow_visible_enemy_route(c, enemy_core):
                return True
            return self.approach_enemy_core(c, enemy_core)

        if self.state == STATE_ATTACK_SENTINEL:
            self.attack_phase = ATTACK_PHASE_BUILD_SENTINEL
            return self.handle_attack_build_sentinel(c)

        self.reset_target()
        self.attack_phase = ATTACK_PHASE_WANDER
        return False

    def configure_attack_defaults(self) -> None:
        self.route_allow_splitter = False
        self.route_enable_ore_defenses = False

    def attack_core_is_known(self) -> bool:
        return self.attack_enemy_core_pos is not None or self.attack_symmetry is not None

    def seek_enemy_core_for_attack(self, c: Controller) -> bool:
        center = self.get_map_center()
        if pos_distance_sq(c.get_position(), center) > 4:
            return self.move_attacker_toward(c, center)
        if self.attack_symmetry_candidates:
            self.attack_symmetry = self.attack_symmetry_candidates[0]
            self.attack_enemy_core_pos = self.transform_by_symmetry(self.core_pos, self.attack_symmetry)
            self.attack_phase = ATTACK_PHASE_WANDER
            return False
        return self.wander_step(c)

    def acquire_attack_titanium_target(self, c: Controller) -> bool:
        self.debug_candidate_ores = []
        self.debug_blocked_ores = []
        self.debug_attempted_ores = []
        self.attack_debug_sentinel_options = []

        enemy_core = self.current_enemy_core_guess()
        if enemy_core is None:
            return False

        my_pos = c.get_position()
        candidates: list[tuple[tuple[int, int, int, int], Position]] = []
        for tile in c.get_nearby_tiles():
            status = self.attack_titanium_status(c, tile)
            if status is None:
                continue
            idx = self.pos_to_idx(tile)
            if (TARGET_ATTACK_TITANIUM, idx) in self.bad_targets:
                if len(self.debug_blocked_ores) < 10:
                    self.debug_blocked_ores.append(idx)
                continue
            score = (
                0 if status == "enemy_harvester" else 1,
                manhattan(my_pos, tile),
                idx,
                0,
            )
            candidates.append((score, tile))

        candidates.sort(key=lambda item: item[0])
        self.debug_candidate_ores = [
            self.pos_to_idx(pos) for _, pos in candidates[:MAX_ORE_TARGET_ATTEMPTS]
        ]
        for _, ore_pos in candidates[:MAX_ORE_TARGET_ATTEMPTS]:
            self.debug_attempted_ores.append(self.pos_to_idx(ore_pos))
            if self.plan_attack_titanium_target(c, ore_pos):
                return True
        return False

    def attack_titanium_status(self, c: Controller, tile: Position) -> str | None:
        if c.get_tile_env(tile) != Environment.ORE_TITANIUM:
            return None
        if c.get_tile_builder_bot_id(tile) is not None:
            return None
        building_id = c.get_tile_building_id(tile)
        if building_id is None:
            return "free"
        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)
        if building_type == EntityType.HARVESTER and building_team != self.my_team:
            return "enemy_harvester"
        if building_type in {EntityType.MARKER, EntityType.ROAD}:
            return "free"
        return None

    def plan_attack_titanium_target(self, c: Controller, target_pos: Position) -> bool:
        target_idx = self.pos_to_idx(target_pos)
        self.reset_attack_build_plan()
        plan = self.choose_entry_stage(c, target_pos)
        if plan is None:
            self.mark_bad_target(TARGET_ATTACK_TITANIUM, target_idx)
            return False
        entry_idx, stage_idx = plan

        self.target_kind = TARGET_ATTACK_TITANIUM
        self.target_idx = target_idx
        self.entry_idx = entry_idx
        self.stage_idx = stage_idx
        self.route_nodes = []
        self.route_edges = []
        self.route_build_index = 0
        self.pending_ore_sentinels = []
        self.pending_ore_outward_sentinel_idx = None
        self.pending_splitter_sentinels = []
        self.final_splitter_idx = None
        self.route_ready = False
        self.state = STATE_TRAVEL
        self.move_path = []
        self.move_goal_signature = ()
        return True

    def acquire_attack_enemy_route_target(self, c: Controller) -> bool:
        enemy_core = self.current_enemy_core_guess()
        if enemy_core is None:
            return False

        candidates: list[tuple[tuple[int, int, int, int], Position, Direction]] = []
        for route_pos in self.visible_enemy_route_positions(c):
            route_idx = self.pos_to_idx(route_pos)
            if (TARGET_ATTACK_ENEMY_ROUTE, route_idx) in self.bad_targets:
                continue
            if c.get_tile_builder_bot_id(route_pos) is not None:
                continue
            if abs(route_pos.x - enemy_core.x) <= 1 and abs(route_pos.y - enemy_core.y) <= 1:
                continue
            sentinel_dir = self.choose_attack_sentinel_facing(c, route_pos, enemy_core)
            if sentinel_dir is None:
                continue
            if not self.can_turret_hit_core(c, route_pos, sentinel_dir, EntityType.SENTINEL, enemy_core):
                continue
            if not self.attack_sentinel_site_plannable(route_pos):
                continue
            score = (
                -manhattan(route_pos, enemy_core),
                -pos_distance_sq(route_pos, enemy_core),
                pos_distance_sq(c.get_position(), route_pos),
                route_idx,
            )
            candidates.append((score, route_pos, sentinel_dir))
        if not candidates:
            return False
        candidates.sort(key=lambda item: item[0])
        _, route_pos, sentinel_dir = candidates[0]
        return self.plan_attack_enemy_route_target(c, route_pos, sentinel_dir)

    def plan_attack_enemy_route_target(
        self, c: Controller, route_pos: Position, sentinel_dir: Direction
    ) -> bool:
        route_idx = self.pos_to_idx(route_pos)
        self.reset_attack_build_plan()
        self.target_kind = TARGET_ATTACK_ENEMY_ROUTE
        self.target_idx = route_idx
        self.entry_idx = None
        self.stage_idx = None
        self.route_nodes = []
        self.route_edges = []
        self.route_build_index = 0
        self.route_ready = True
        self.attack_sentinel_idx = route_idx
        self.attack_sentinel_dir = sentinel_dir
        self.attack_feeder_idx = None
        self.attack_direct_feed = True
        enemy_core = self.current_enemy_core_guess()
        self.attack_debug_core_tiles = (
            [] if enemy_core is None else [self.pos_to_idx(pos) for pos in self.get_core_footprint(enemy_core)]
        )
        self.attack_debug_sentinel_options = [route_idx]
        self.state = STATE_ATTACK_SENTINEL
        self.clear_move_path()
        return True

    def follow_visible_enemy_route(self, c: Controller, enemy_core: Position) -> bool:
        route_positions = self.visible_enemy_route_positions(c)
        if not route_positions:
            return False
        my_pos = c.get_position()
        route_positions.sort(
            key=lambda pos: (
                manhattan(pos, enemy_core),
                pos_distance_sq(my_pos, pos),
                self.pos_to_idx(pos),
            )
        )
        target_pos = route_positions[0]
        if target_pos == my_pos:
            return self.move_attacker_toward(c, enemy_core)
        return self.move_toward_any(c, {self.pos_to_idx(target_pos)})

    def visible_enemy_route_positions(self, c: Controller) -> list[Position]:
        positions: list[Position] = []
        seen: set[int] = set()
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            building_type = c.get_entity_type(building_id)
            if building_type not in ENEMY_REPLACEABLE_ROUTE_BUILDINGS or building_type == EntityType.ROAD:
                continue
            pos = c.get_position(building_id)
            idx = self.pos_to_idx(pos)
            if idx in seen:
                continue
            seen.add(idx)
            positions.append(pos)
        return positions

    def reset_attack_build_plan(self) -> None:
        self.attack_sentinel_idx = None
        self.attack_sentinel_dir = None
        self.attack_feeder_idx = None
        self.attack_direct_feed = False
        self.attack_route_goal_plan = {}
        self.attack_debug_core_tiles = []
        self.attack_debug_sentinel_options = []

    def configure_attack_route_for_target(self, c: Controller, target_pos: Position) -> bool:
        self.configure_attack_defaults()
        self.route_goal_indices = []
        self.route_goal_dir = {}
        self.attack_route_goal_plan = {}
        enemy_core = self.current_enemy_core_guess()
        if enemy_core is None:
            return False
        self.attack_debug_core_tiles = [self.pos_to_idx(pos) for pos in self.get_core_footprint(enemy_core)]

        direct_plan = self.choose_attack_direct_sentinel(c, target_pos, enemy_core)
        if direct_plan is not None:
            sentinel_pos, sentinel_dir = direct_plan
            self.attack_sentinel_idx = self.pos_to_idx(sentinel_pos)
            self.attack_sentinel_dir = sentinel_dir
            self.attack_feeder_idx = self.pos_to_idx(target_pos)
            self.attack_direct_feed = True
            return True

        goal_plan = self.choose_attack_route_goals(c, target_pos, enemy_core)
        if not goal_plan:
            return False
        self.route_goal_indices = sorted(goal_plan)
        self.route_goal_dir = {
            feeder_idx: self.idx_to_pos(feeder_idx).direction_to(self.idx_to_pos(plan[0]))
            for feeder_idx, plan in goal_plan.items()
        }
        self.attack_route_goal_plan = goal_plan
        return True

    def choose_attack_direct_sentinel(
        self, c: Controller, target_pos: Position, enemy_core: Position
    ) -> tuple[Position, Direction] | None:
        best: tuple[tuple[int, int, int], Position, Direction] | None = None
        for feed_dir in CARDINAL_DIRECTIONS:
            sentinel_pos = target_pos.add(feed_dir)
            if abs(sentinel_pos.x - enemy_core.x) <= 1 and abs(sentinel_pos.y - enemy_core.y) <= 1:
                continue
            if not self.attack_sentinel_site_plannable(sentinel_pos):
                continue
            sentinel_dir = self.choose_attack_sentinel_facing(c, sentinel_pos, enemy_core)
            if sentinel_dir is None:
                continue
            if not self.sentinel_feed_allowed(target_pos, sentinel_pos, sentinel_dir):
                continue
            score = (
                manhattan(sentinel_pos, enemy_core),
                pos_distance_sq(sentinel_pos, enemy_core),
                self.pos_to_idx(sentinel_pos),
            )
            if best is None or score < best[0]:
                best = (score, sentinel_pos, sentinel_dir)
        if best is None:
            return None
        return best[1], best[2]

    def choose_attack_route_goals(
        self, c: Controller, target_pos: Position, enemy_core: Position
    ) -> dict[int, tuple[int, Direction]]:
        goal_plan: dict[int, tuple[int, Direction]] = {}
        goal_score: dict[int, tuple[int, int, int, int]] = {}
        target_idx = self.pos_to_idx(target_pos)
        core_tiles = self.get_core_footprint(enemy_core)
        candidates: list[tuple[tuple[int, int, int], Position]] = []

        for dy in range(-7, 8):
            for dx in range(-7, 8):
                sentinel_pos = Position(enemy_core.x + dx, enemy_core.y + dy)
                if not self.in_bounds(sentinel_pos):
                    continue
                if abs(dx) <= 1 and abs(dy) <= 1:
                    continue
                if not any(pos_distance_sq(sentinel_pos, core_tile) <= 32 for core_tile in core_tiles):
                    continue
                if not self.attack_sentinel_site_plannable(sentinel_pos):
                    continue
                candidates.append((
                    (
                        manhattan(target_pos, sentinel_pos),
                        manhattan(sentinel_pos, enemy_core),
                        self.pos_to_idx(sentinel_pos),
                    ),
                    sentinel_pos,
                ))

        candidates.sort(key=lambda item: item[0])
        for _, sentinel_pos in candidates[:32]:
            sentinel_dir = self.choose_attack_sentinel_facing(c, sentinel_pos, enemy_core, core_tiles)
            if sentinel_dir is None:
                continue
            sentinel_idx = self.pos_to_idx(sentinel_pos)
            if len(self.attack_debug_sentinel_options) < 16:
                self.attack_debug_sentinel_options.append(sentinel_idx)

            for feed_dir in CARDINAL_DIRECTIONS:
                feeder_pos = sentinel_pos.add(feed_dir)
                if not self.in_bounds(feeder_pos):
                    continue
                feeder_idx = self.pos_to_idx(feeder_pos)
                if feeder_idx == target_idx:
                    continue
                if not self.sentinel_feed_allowed(feeder_pos, sentinel_pos, sentinel_dir):
                    continue
                if not self.attack_feeder_tile_plannable(c, feeder_pos, enemy_core):
                    continue
                score = (
                    manhattan(target_pos, feeder_pos),
                    manhattan(feeder_pos, enemy_core),
                    sentinel_idx,
                    feeder_idx,
                )
                if feeder_idx not in goal_score or score < goal_score[feeder_idx]:
                    goal_score[feeder_idx] = score
                    goal_plan[feeder_idx] = (sentinel_idx, sentinel_dir)
            if len(goal_plan) >= ATTACK_ROUTE_GOAL_LIMIT:
                break

        if len(goal_plan) <= ATTACK_ROUTE_GOAL_LIMIT:
            return goal_plan
        return {
            feeder_idx: goal_plan[feeder_idx]
            for _, feeder_idx in sorted(
                (score, feeder_idx) for feeder_idx, score in goal_score.items()
            )[:ATTACK_ROUTE_GOAL_LIMIT]
        }

    def choose_attack_sentinel_facing(
        self,
        c: Controller,
        sentinel_pos: Position,
        enemy_core: Position,
        core_tiles: list[Position] | None = None,
    ) -> Direction | None:
        preferred = sentinel_pos.direction_to(enemy_core)
        directions: list[Direction] = []
        if preferred != Direction.CENTRE:
            directions.extend(
                [
                    preferred,
                    preferred.rotate_left(),
                    preferred.rotate_right(),
                    preferred.rotate_left().rotate_left(),
                    preferred.rotate_right().rotate_right(),
                ]
            )
        directions.extend(ALL_DIRECTIONS)

        seen: set[Direction] = set()
        if core_tiles is None:
            core_tiles = self.get_core_footprint(enemy_core)
        for direction in directions:
            if direction == Direction.CENTRE or direction in seen:
                continue
            seen.add(direction)
            for core_tile in core_tiles:
                if self.sentinel_geometry_hits(sentinel_pos, direction, core_tile):
                    return direction
        return None

    def sentinel_geometry_hits(
        self, sentinel_pos: Position, sentinel_dir: Direction, target: Position
    ) -> bool:
        dx = target.x - sentinel_pos.x
        dy = target.y - sentinel_pos.y
        if dx == 0 and dy == 0:
            return False
        if dx * dx + dy * dy > 32:
            return False
        step_x, step_y = DIR_TO_DELTA[sentinel_dir]
        if step_x == 0 and step_y == 0:
            return False
        if step_x == 0:
            return dy * step_y > 0 and abs(dx) <= 1
        if step_y == 0:
            return dx * step_x > 0 and abs(dy) <= 1
        forward_x = dx * step_x
        forward_y = dy * step_y
        return forward_x >= 0 and forward_y >= 0 and forward_x + forward_y > 0 and abs(forward_x - forward_y) <= 1

    def sentinel_feed_allowed(
        self, feeder_pos: Position, sentinel_pos: Position, sentinel_dir: Direction
    ) -> bool:
        feed_side = sentinel_pos.direction_to(feeder_pos)
        if feed_side not in CARDINAL_DIRECTIONS_SET:
            return False
        if sentinel_dir not in CARDINAL_DIRECTIONS_SET:
            return True
        return feed_side != sentinel_dir

    def attack_sentinel_site_plannable(self, pos: Position) -> bool:
        if not self.in_bounds(pos):
            return False
        idx = self.pos_to_idx(pos)
        env = self.known_env[idx]
        if env == Environment.WALL:
            return False
        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        if building_type is None:
            return True
        if building_type == EntityType.MARKER:
            return True
        if building_mine and building_type in {EntityType.ROAD, EntityType.BARRIER, EntityType.SENTINEL}:
            return True
        if building_mine is False and (
            building_type == EntityType.ROAD or building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS
        ):
            return True
        return False

    def attack_feeder_tile_plannable(
        self, c: Controller, feeder_pos: Position, enemy_core: Position
    ) -> bool:
        if abs(feeder_pos.x - enemy_core.x) <= 1 and abs(feeder_pos.y - enemy_core.y) <= 1:
            return False
        return self.route_tile_ok(c, feeder_pos)

    def ensure_attack_symmetry_candidates(self) -> None:
        if self.core_pos is None or self.attack_symmetry_candidates or self.attack_symmetry is not None:
            return
        seen_enemy_positions: set[int] = set()
        for symmetry in (SYMMETRY_VERTICAL, SYMMETRY_HORIZONTAL, SYMMETRY_ROTATIONAL):
            enemy_core = self.transform_by_symmetry(self.core_pos, symmetry)
            if not self.in_bounds(enemy_core) or enemy_core == self.core_pos:
                continue
            idx = self.pos_to_idx(enemy_core)
            if idx in seen_enemy_positions:
                continue
            seen_enemy_positions.add(idx)
            self.attack_symmetry_candidates.append(symmetry)
        if not self.attack_symmetry_candidates:
            self.attack_symmetry_candidates.append(SYMMETRY_ROTATIONAL)
        if len(self.attack_symmetry_candidates) == 1:
            self.attack_symmetry = self.attack_symmetry_candidates[0]
            self.attack_enemy_core_pos = self.transform_by_symmetry(self.core_pos, self.attack_symmetry)

    def transform_by_symmetry(self, pos: Position, symmetry: int) -> Position:
        if symmetry == SYMMETRY_VERTICAL:
            return Position(self.width - 1 - pos.x, pos.y)
        if symmetry == SYMMETRY_HORIZONTAL:
            return Position(pos.x, self.height - 1 - pos.y)
        return Position(self.width - 1 - pos.x, self.height - 1 - pos.y)

    def update_attack_symmetry(self, c: Controller) -> None:
        visible_enemy_core = self.find_visible_enemy_core(c)
        if visible_enemy_core is not None:
            self.attack_enemy_core_pos = visible_enemy_core
            matching = [
                symmetry
                for symmetry in self.attack_symmetry_candidates
                if self.transform_by_symmetry(self.core_pos, symmetry) == visible_enemy_core
            ]
            if matching:
                self.attack_symmetry = matching[0]
                self.attack_symmetry_candidates = [matching[0]]
            return

        if self.attack_symmetry is not None or len(self.attack_symmetry_candidates) <= 1:
            if self.attack_symmetry is None and self.attack_symmetry_candidates:
                self.attack_symmetry = self.attack_symmetry_candidates[0]
                self.attack_enemy_core_pos = self.transform_by_symmetry(self.core_pos, self.attack_symmetry)
            return

        surviving: list[int] = []
        for symmetry in self.attack_symmetry_candidates:
            if self.symmetry_still_possible(c, symmetry):
                surviving.append(symmetry)
        if surviving:
            self.attack_symmetry_candidates = surviving
        if len(self.attack_symmetry_candidates) == 1:
            self.attack_symmetry = self.attack_symmetry_candidates[0]
            self.attack_enemy_core_pos = self.transform_by_symmetry(self.core_pos, self.attack_symmetry)

    def symmetry_still_possible(self, c: Controller, symmetry: int) -> bool:
        for pos in c.get_nearby_tiles():
            mirrored = self.transform_by_symmetry(pos, symmetry)
            if not self.in_bounds(mirrored):
                return False
            mirrored_idx = self.pos_to_idx(mirrored)
            mirrored_env = self.known_env[mirrored_idx]
            if mirrored_env is not None and mirrored_env != c.get_tile_env(pos):
                return False

        predicted_core = self.transform_by_symmetry(self.core_pos, symmetry)
        if self.is_tile_visible_this_round(predicted_core):
            building_id = c.get_tile_building_id(predicted_core)
            if building_id is None:
                return False
            if c.get_entity_type(building_id) != EntityType.CORE or c.get_team(building_id) == self.my_team:
                return False
        return True

    def find_visible_enemy_core(self, c: Controller) -> Position | None:
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            if c.get_entity_type(building_id) == EntityType.CORE:
                return c.get_position(building_id)
        return None

    def current_enemy_core_guess(self) -> Position | None:
        if self.attack_enemy_core_pos is not None:
            return self.attack_enemy_core_pos
        self.ensure_attack_symmetry_candidates()
        symmetry = self.attack_symmetry
        if symmetry is None and self.attack_symmetry_candidates:
            symmetry = self.attack_symmetry_candidates[0]
        if symmetry is None or self.core_pos is None:
            return None
        return self.transform_by_symmetry(self.core_pos, symmetry)

    def keep_attack_pair_together(self, c: Controller, target: Position) -> bool:
        partner = self.find_attack_partner(c)
        if partner is None:
            return False
        distance = pos_distance_sq(c.get_position(), partner)
        if distance <= ATTACK_PAIR_MAX_DIST_SQ:
            return False
        my_dist = manhattan(c.get_position(), target)
        partner_dist = manhattan(partner, target)
        if distance >= ATTACK_PAIR_CATCHUP_DIST_SQ and my_dist + 2 < partner_dist:
            return self.move_attacker_toward(c, partner)
        return False

    def find_attack_partner(self, c: Controller) -> Position | None:
        my_id = c.get_id()
        my_pos = c.get_position()
        candidates: list[tuple[int, int, Position]] = []
        for unit_id in c.get_nearby_units():
            if unit_id == my_id:
                continue
            if c.get_team(unit_id) != self.my_team:
                continue
            if c.get_entity_type(unit_id) != EntityType.BUILDER_BOT:
                continue
            pos = c.get_position(unit_id)
            if self.core_pos is not None and pos_distance_sq(pos, self.core_pos) <= 2:
                continue
            if self.core_pos is not None and pos in self.guardian_wait_positions():
                if pos_distance_sq(my_pos, self.core_pos) > 18:
                    continue
            candidates.append((pos_distance_sq(my_pos, pos), manhattan(my_pos, pos), pos))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][2]

    def move_attacker_toward(self, c: Controller, target: Position) -> bool:
        if not self.in_bounds(target):
            return False
        target_idx = self.pos_to_idx(target)
        if self.builder_tile_ok(c, target):
            goals = {target_idx}
        else:
            goals = self.action_access_goals(c, target, allow_target_tile=False)
        if not goals:
            goals = self.nearby_walk_goals(target, radius=2)
        return self.move_toward_any(c, goals)

    def nearby_walk_goals(self, target: Position, radius: int) -> set[int]:
        goals: set[int] = set()
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                pos = Position(target.x + dx, target.y + dy)
                if not self.in_bounds(pos):
                    continue
                if dx * dx + dy * dy > radius * radius:
                    continue
                if self.builder_tile_ok_for_known_state(pos):
                    goals.add(self.pos_to_idx(pos))
        return goals

    def builder_tile_ok_for_known_state(self, pos: Position) -> bool:
        idx = self.pos_to_idx(pos)
        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        env = self.known_env[idx]
        if building_type is not None:
            if building_type == EntityType.MARKER:
                return env != Environment.WALL
            if building_type in WALKABLE_BUILDINGS:
                return True
            if building_type == EntityType.CORE and building_mine:
                return True
            return False
        return env != Environment.WALL and env not in ORE_ENVIRONMENTS

    def approach_enemy_core(self, c: Controller, enemy_core: Position) -> bool:
        if self.is_tile_visible_this_round(enemy_core):
            building_id = c.get_tile_building_id(enemy_core)
            if (
                building_id is None
                or c.get_entity_type(building_id) != EntityType.CORE
                or c.get_team(building_id) == self.my_team
            ):
                self.reject_current_attack_symmetry()
                return self.move_attacker_toward(c, self.get_map_center())
        goals = self.enemy_core_approach_goals(c, enemy_core)
        if goals:
            return self.move_toward_any(c, goals)
        return self.move_attacker_toward(c, enemy_core)

    def reject_current_attack_symmetry(self) -> None:
        guess = self.current_enemy_core_guess()
        if guess is None:
            return
        self.attack_symmetry_candidates = [
            symmetry
            for symmetry in self.attack_symmetry_candidates
            if self.transform_by_symmetry(self.core_pos, symmetry) != guess
        ]
        self.attack_symmetry = None
        self.attack_enemy_core_pos = None
        self.attack_phase = ATTACK_PHASE_CENTER
        self.clear_move_path()

    def enemy_core_approach_goals(self, c: Controller, enemy_core: Position) -> set[int]:
        core_tiles = {self.pos_to_idx(pos) for pos in self.get_core_footprint(enemy_core)}
        goals: set[int] = set()
        for core_tile in self.get_core_footprint(enemy_core):
            for direction in ALL_DIRECTIONS:
                pos = core_tile.add(direction)
                if not self.in_bounds(pos):
                    continue
                idx = self.pos_to_idx(pos)
                if idx in core_tiles:
                    continue
                if self.builder_tile_ok(c, pos):
                    goals.add(idx)
        return goals

    def find_enemy_core_feeder(self, c: Controller, enemy_core: Position) -> Position | None:
        core_tiles = self.get_core_footprint(enemy_core)
        best: tuple[tuple[int, int, int], Position] | None = None
        fallback: tuple[tuple[int, int, int], Position] | None = None
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            building_type = c.get_entity_type(building_id)
            if building_type not in CONVEYOR_SPLITTER_BRIDGE:
                continue
            feeder_pos = c.get_position(building_id)
            feeds_core = False
            adjacent = 0
            for core_tile in core_tiles:
                if chebyshev(feeder_pos, core_tile) == 1:
                    facing = feeder_pos.direction_to(core_tile)
                    try:
                        if c.can_fire_from(feeder_pos, facing, EntityType.GUNNER, core_tile):
                            score = (
                                1,
                                manhattan(c.get_position(), feeder_pos),
                                self.pos_to_idx(feeder_pos),
                            )
                            if fallback is None or score < fallback[0]:
                                fallback = (score, feeder_pos)
                    except Exception:
                        pass
                if self.directly_feeds_position(c, feeder_pos, building_id, core_tile):
                    feeds_core = True
                    if chebyshev(feeder_pos, core_tile) == 1:
                        adjacent = 1
                    break
            if not feeds_core:
                continue
            score = (
                0 if adjacent else 1,
                manhattan(c.get_position(), feeder_pos),
                self.pos_to_idx(feeder_pos),
            )
            if best is None or score < best[0]:
                best = (score, feeder_pos)
        if best is not None:
            return best[1]
        return None if fallback is None else fallback[1]

    def is_adjacent_to_enemy_core(self, pos: Position, enemy_core: Position) -> bool:
        core_tiles = self.get_core_footprint(enemy_core)
        for core_tile in core_tiles:
            if pos == core_tile:
                return False
        return any(chebyshev(pos, core_tile) == 1 for core_tile in core_tiles)

    def find_enemy_core_adjacent_feeder(self, c: Controller, enemy_core: Position) -> Position | None:
        core_tiles = self.get_core_footprint(enemy_core)
        best: tuple[tuple[int, int, int], Position] | None = None
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            building_type = c.get_entity_type(building_id)
            if building_type not in CONVEYOR_SPLITTER_BRIDGE:
                continue
            feeder_pos = c.get_position(building_id)
            if not any(chebyshev(feeder_pos, core_tile) == 1 for core_tile in core_tiles):
                continue
            if not any(
                self.directly_feeds_position(c, feeder_pos, building_id, core_tile)
                for core_tile in core_tiles
            ):
                continue
            score = (
                manhattan(c.get_position(), feeder_pos),
                pos_distance_sq(c.get_position(), feeder_pos),
                self.pos_to_idx(feeder_pos),
            )
            if best is None or score < best[0]:
                best = (score, feeder_pos)
        return None if best is None else best[1]

    def find_damaged_attack_gunner(self, c: Controller, enemy_core: Position) -> Position | None:
        best: tuple[tuple[int, int, int], Position] | None = None
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) != self.my_team:
                continue
            if c.get_entity_type(building_id) != EntityType.GUNNER:
                continue
            gunner_pos = c.get_position(building_id)
            if not self.is_adjacent_to_enemy_core(gunner_pos, enemy_core):
                continue
            missing_hp = c.get_max_hp(building_id) - c.get_hp(building_id)
            if missing_hp <= 0:
                continue
            score = (
                -missing_hp,
                manhattan(c.get_position(), gunner_pos),
                self.pos_to_idx(gunner_pos),
            )
            if best is None or score < best[0]:
                best = (score, gunner_pos)
        return None if best is None else best[1]

    def find_turret_supply_target(self, c: Controller, only_threatening: bool) -> Position | None:
        best: tuple[tuple[int, int], Position] | None = None
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            turret_type = c.get_entity_type(building_id)
            if turret_type not in TURRET_TYPES:
                continue
            turret_pos = c.get_position(building_id)
            if only_threatening:
                try:
                    turret_dir = c.get_direction(building_id)
                    if not c.can_fire_from(turret_pos, turret_dir, turret_type, c.get_position()):
                        continue
                except Exception:
                    continue
            feeder = self.find_direct_walkable_feeder(c, turret_pos)
            if feeder is None:
                continue
            score = (manhattan(c.get_position(), feeder), self.pos_to_idx(feeder))
            if best is None or score < best[0]:
                best = (score, feeder)
        return None if best is None else best[1]

    def find_direct_walkable_feeder(self, c: Controller, target_pos: Position) -> Position | None:
        best: tuple[tuple[int, int], Position] | None = None
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            building_type = c.get_entity_type(building_id)
            if building_type not in CONVEYOR_SPLITTER_BRIDGE:
                continue
            feeder_pos = c.get_position(building_id)
            if not self.directly_feeds_position(c, feeder_pos, building_id, target_pos):
                continue
            score = (manhattan(c.get_position(), feeder_pos), self.pos_to_idx(feeder_pos))
            if best is None or score < best[0]:
                best = (score, feeder_pos)
        return None if best is None else best[1]

    def find_direct_walkable_feeders(self, c: Controller, target_pos: Position) -> list[Position]:
        feeders: list[tuple[tuple[int, int, int], Position]] = []
        seen: set[int] = set()
        my_pos = c.get_position()
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            building_type = c.get_entity_type(building_id)
            if building_type not in CONVEYOR_SPLITTER_BRIDGE:
                continue
            feeder_pos = c.get_position(building_id)
            feeder_idx = self.pos_to_idx(feeder_pos)
            if feeder_idx in seen:
                continue
            if not self.directly_feeds_position(c, feeder_pos, building_id, target_pos):
                continue
            seen.add(feeder_idx)
            score = (
                0 if chebyshev(feeder_pos, target_pos) == 1 else 1,
                manhattan(my_pos, feeder_pos),
                feeder_idx,
            )
            feeders.append((score, feeder_pos))
        feeders.sort(key=lambda item: item[0])
        return [pos for _, pos in feeders]

    def begin_attack_destroy(self, target_pos: Position, target_kind: str, phase: str) -> None:
        self.attack_target_idx = self.pos_to_idx(target_pos)
        self.attack_target_kind = target_kind
        self.attack_phase = phase
        self.clear_move_path()

    def handle_attack_destroy_target(self, c: Controller, next_phase: str) -> bool:
        if self.attack_target_idx is None:
            self.attack_phase = next_phase
            return False
        target_pos = self.idx_to_pos(self.attack_target_idx)
        current_idx = self.pos_to_idx(c.get_position())

        if not self.is_tile_visible_this_round(target_pos):
            return self.move_attacker_toward(c, target_pos)

        building_id = c.get_tile_building_id(target_pos)
        if building_id is None:
            if self.attack_target_kind == ATTACK_TARGET_CORE_FEEDER:
                self.attack_build_idx = self.attack_target_idx
                self.attack_phase = ATTACK_PHASE_BUILD_GUNNER
            else:
                self.attack_phase = ATTACK_PHASE_CORE
            self.attack_target_idx = None
            self.attack_target_kind = None
            self.clear_move_path()
            return False

        if c.get_team(building_id) == self.my_team:
            self.attack_phase = next_phase
            self.attack_target_idx = None
            self.attack_target_kind = None
            return False

        building_type = c.get_entity_type(building_id)
        if building_type not in CONVEYOR_SPLITTER_BRIDGE_ROAD:
            self.attack_phase = next_phase
            self.attack_target_idx = None
            self.attack_target_kind = None
            return False

        if current_idx == self.attack_target_idx:
            if c.can_fire(c.get_position()):
                if self.attack_break_target_is_healed(c, target_pos):
                    self.attack_phase = next_phase
                    self.attack_target_idx = None
                    self.attack_target_kind = None
                    self.clear_move_path()
                    return False
                c.fire(c.get_position())
                return True
            self.wait_for_titanium_amount(c, 2)
            return False

        return self.move_toward_any(c, {self.attack_target_idx})

    def handle_attack_build_gunner(self, c: Controller) -> bool:
        if self.attack_build_idx is None:
            self.attack_phase = ATTACK_PHASE_CORE
            return False
        build_pos = self.idx_to_pos(self.attack_build_idx)
        enemy_core = self.current_enemy_core_guess()
        if enemy_core is None:
            self.attack_phase = ATTACK_PHASE_CORE
            return False

        if self.is_tile_visible_this_round(build_pos):
            building_id = c.get_tile_building_id(build_pos)
            if building_id is not None:
                if c.get_team(building_id) == self.my_team and c.get_entity_type(building_id) == EntityType.GUNNER:
                    self.attack_phase = ATTACK_PHASE_SUPPORT_GUNNER
                    return False
                if c.get_team(building_id) != self.my_team:
                    self.begin_attack_destroy(build_pos, ATTACK_TARGET_CORE_FEEDER, ATTACK_PHASE_CUT_CORE_FEEDER)
                    return self.handle_attack_destroy_target(c, ATTACK_PHASE_BUILD_GUNNER)

        if self.pos_to_idx(c.get_position()) == self.attack_build_idx:
            return self.move_off_current_tile(c, self.build_vantage_goals(build_pos))

        if pos_distance_sq(c.get_position(), build_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(build_pos))

        builder_on_site = c.get_tile_builder_bot_id(build_pos)
        if builder_on_site is not None:
            return False

        facing = self.choose_attack_gunner_facing(c, build_pos, enemy_core)
        self.attack_gunner_dir = facing
        if c.can_build_gunner(build_pos, facing):
            c.build_gunner(build_pos, facing)
            if self.attack_anchor_idx is None:
                self.attack_anchor_idx = self.attack_build_idx
            self.attack_phase = ATTACK_PHASE_SUPPORT_GUNNER
            return True
        self.wait_for_titanium_shortage(c, "get_gunner_cost")
        return False

    def choose_attack_gunner_facing(self, c: Controller, build_pos: Position, enemy_core: Position) -> Direction:
        best_dir = build_pos.direction_to(enemy_core)
        if best_dir == Direction.CENTRE:
            best_dir = Direction.NORTH
        for core_tile in sorted(
            self.get_core_footprint(enemy_core),
            key=lambda pos: (pos_distance_sq(build_pos, pos), manhattan(build_pos, pos)),
        ):
            direction = build_pos.direction_to(core_tile)
            if direction == Direction.CENTRE:
                continue
            try:
                if c.can_fire_from(build_pos, direction, EntityType.GUNNER, core_tile):
                    return direction
            except Exception:
                pass
        return best_dir

    def handle_attack_support_gunner(self, c: Controller) -> bool:
        if self.attack_build_idx is None:
            self.attack_phase = ATTACK_PHASE_CORE
            return False
        gunner_pos = self.idx_to_pos(self.attack_build_idx)
        enemy_core = self.current_enemy_core_guess()
        if enemy_core is None:
            self.attack_phase = ATTACK_PHASE_CORE
            return False

        damaged_gunner = self.find_damaged_attack_gunner(c, enemy_core)
        if damaged_gunner is not None:
            self.attack_build_idx = self.pos_to_idx(damaged_gunner)
            gunner_pos = damaged_gunner

        if self.attack_anchor_idx is not None:
            anchor_pos = self.idx_to_pos(self.attack_anchor_idx)
            if not self.is_tile_visible_this_round(anchor_pos):
                return self.move_attacker_toward(c, anchor_pos)

        if not self.is_tile_visible_this_round(gunner_pos):
            return self.move_attacker_toward(c, gunner_pos)

        building_id = c.get_tile_building_id(gunner_pos)
        if building_id is None:
            self.attack_phase = ATTACK_PHASE_BUILD_GUNNER
            return self.handle_attack_build_gunner(c)
        if c.get_team(building_id) == self.my_team and c.get_entity_type(building_id) == EntityType.GUNNER:
            if c.can_heal(gunner_pos):
                c.heal(gunner_pos)
                return True
            if damaged_gunner is None and self.is_turret_still_supplied(c, gunner_pos):
                feeder = self.find_enemy_core_adjacent_feeder(c, enemy_core)
                if feeder is not None and feeder != gunner_pos:
                    self.begin_attack_destroy(feeder, ATTACK_TARGET_CORE_FEEDER, ATTACK_PHASE_CUT_CORE_FEEDER)
                    return self.handle_attack_destroy_target(c, ATTACK_PHASE_BUILD_GUNNER)
            if self.is_turret_still_supplied(c, gunner_pos):
                if self.try_heal_attack_support_targets(c, gunner_pos):
                    return True
                if pos_distance_sq(c.get_position(), gunner_pos) > 2:
                    return self.move_toward_any(c, self.action_access_goals(c, gunner_pos, allow_target_tile=False))
                return False
            if pos_distance_sq(c.get_position(), gunner_pos) > 2:
                return self.move_toward_any(c, self.action_access_goals(c, gunner_pos, allow_target_tile=False))
            feeder = self.find_enemy_core_adjacent_feeder(c, enemy_core)
            if feeder is not None and feeder != gunner_pos:
                self.begin_attack_destroy(feeder, ATTACK_TARGET_CORE_FEEDER, ATTACK_PHASE_CUT_CORE_FEEDER)
                return self.handle_attack_destroy_target(c, ATTACK_PHASE_BUILD_GUNNER)
            return False
        if c.get_team(building_id) != self.my_team:
            self.begin_attack_destroy(gunner_pos, ATTACK_TARGET_CORE_FEEDER, ATTACK_PHASE_CUT_CORE_FEEDER)
            return self.handle_attack_destroy_target(c, ATTACK_PHASE_BUILD_GUNNER)

        self.attack_phase = ATTACK_PHASE_CORE
        return False

    def try_heal_attack_support_targets(self, c: Controller, gunner_pos: Position) -> bool:
        best: tuple[tuple[int, int, int, int], Position] | None = None
        my_pos = c.get_position()

        if c.can_heal(my_pos):
            my_missing = c.get_max_hp() - c.get_hp()
            if my_missing > 0:
                best = ((0, -my_missing, 0, 0), my_pos)

        if c.can_heal(gunner_pos):
            gunner_id = c.get_tile_building_id(gunner_pos)
            if gunner_id is not None and c.get_team(gunner_id) == self.my_team:
                missing = c.get_max_hp(gunner_id) - c.get_hp(gunner_id)
                if missing > 0:
                    best = ((-3, -missing, pos_distance_sq(my_pos, gunner_pos), self.pos_to_idx(gunner_pos)), gunner_pos)

        for feeder_id, feeder_pos in self.find_turret_feeders(c, gunner_pos):
            if c.get_team(feeder_id) != self.my_team or not c.can_heal(feeder_pos):
                continue
            missing = c.get_max_hp(feeder_id) - c.get_hp(feeder_id)
            if missing <= 0:
                continue
            score = (-2, -missing, pos_distance_sq(my_pos, feeder_pos), self.pos_to_idx(feeder_pos))
            if best is None or score < best[0]:
                best = (score, feeder_pos)

        if best is None:
            return False
        c.heal(best[1])
        return True

    def try_heal_attack_unit(self, c: Controller, urgent: bool) -> bool:
        best: tuple[tuple[int, int, int], Position] | None = None
        for pos in c.get_nearby_tiles(2):
            if not c.can_heal(pos):
                continue
            priority = 0
            missing_hp = 0
            bot_id = c.get_tile_builder_bot_id(pos)
            if bot_id is not None and c.get_team(bot_id) == self.my_team:
                missing_hp = max(missing_hp, c.get_max_hp(bot_id) - c.get_hp(bot_id))
                priority = max(priority, 3)
            building_id = c.get_tile_building_id(pos)
            if building_id is not None and c.get_team(building_id) == self.my_team:
                building_type = c.get_entity_type(building_id)
                missing_hp = max(missing_hp, c.get_max_hp(building_id) - c.get_hp(building_id))
                if building_type in {EntityType.GUNNER, EntityType.SENTINEL}:
                    priority = max(priority, 4)
                elif building_type in WALKABLE_BUILDINGS:
                    priority = max(priority, 1)
            if priority == 0:
                continue
            if not urgent and priority < 3:
                continue
            score = (-priority, -missing_hp, pos_distance_sq(c.get_position(), pos))
            if best is None or score < best[0]:
                best = (score, pos)
        if best is None:
            return False
        c.heal(best[1])
        return True

    def update_attack_stuck(self, c: Controller, took_action: bool) -> None:
        current_idx = self.pos_to_idx(c.get_position())
        if took_action or self.waiting_for_titanium:
            self.attack_stuck_rounds = 0
        elif self.attack_last_position_idx == current_idx:
            self.attack_stuck_rounds += 1
        else:
            self.attack_stuck_rounds = 0
        self.attack_last_position_idx = current_idx
        if self.attack_stuck_rounds < ATTACK_STUCK_LIMIT:
            return
        self.attack_stuck_rounds = 0
        self.attack_target_idx = None
        self.attack_target_kind = None
        if self.attack_phase in {ATTACK_PHASE_CHAIN, ATTACK_PHASE_BUILD_SENTINEL}:
            self.mark_bad_target(self.target_kind, self.target_idx)
            self.reset_target()
            self.attack_phase = ATTACK_PHASE_WANDER
        self.clear_move_path()

    # ══════════════════════════════════════════════════════════════════════════
    #  GUARDIAN LOGIC (unchanged)
    # ══════════════════════════════════════════════════════════════════════════

    def run_guardian(self, c: Controller) -> None:
        self.waiting_for_titanium = False
        if self.temporary_guardian and self.guard_mode == GUARD_RETURN_HEAL:
            if self.core_pos is not None and self.is_core_damaged(c):
                if self.try_activate_guardian_threat_response(c):
                    return
            self.revert_temporary_guardian_to_miner()
            return
        if self.home_wait_idx is None:
            self.home_wait_idx = self.pos_to_idx(c.get_position())

        if self.guard_mode == GUARD_IDLE:
            if self.start_guardian_core_response(c):
                return
            if self.start_guardian_repair(c):
                return
            if self.heal_allied_core_if_possible(c):
                return
            home_idx = self.home_wait_idx
            if home_idx is not None and self.pos_to_idx(c.get_position()) != home_idx:
                self.move_toward_any(c, {home_idx})
            return

        if self.guard_mode == GUARD_CORE_RESPONSE:
            self.handle_guardian_core_response(c)
            return

        if self.guard_mode == GUARD_REPAIR:
            self.handle_guardian_repair(c)
            return

        if self.guard_mode == GUARD_RETURN_HEAL:
            self.handle_guardian_return_and_heal(c)
            return

        home_idx = self.home_wait_idx
        if home_idx is not None and self.pos_to_idx(c.get_position()) != home_idx:
            self.move_toward_any(c, {home_idx})

    def start_guardian_core_response(self, c: Controller) -> bool:
        if self.core_pos is None or not self.is_core_damaged(c):
            return False
        if self.try_activate_guardian_threat_response(c):
            return True
        scout_dir = self.guardian_default_search_direction(c.get_position())
        if scout_dir is None:
            return False
        self.begin_guardian_core_response(None, scout_dir)
        self.handle_guardian_core_response(c)
        return True

    def try_activate_guardian_threat_response(self, c: Controller) -> bool:
        visible_turrets = self.find_visible_turrets_attacking_core_from_guardian(c)
        selected_turret = self.select_guardian_visible_turret(visible_turrets)
        if selected_turret is not None:
            self.begin_guardian_core_response(selected_turret, self.core_pos.direction_to(selected_turret))
            self.handle_guardian_core_response(c)
            return True
        return False

    def start_guardian_repair(self, c: Controller) -> bool:
        damaged = self.find_damaged_near_core_buildings(c)
        if not damaged:
            return False
        target_pos = damaged[0]
        if not self.is_selected_guardian_for(c, target_pos, GUARDIAN_REPAIR_COUNT):
            return False
        self.guard_mode = GUARD_REPAIR
        self.guard_target_idx = self.pos_to_idx(target_pos)
        self.clear_move_path()
        self.handle_guardian_repair(c)
        return True

    def handle_guardian_core_response(self, c: Controller) -> bool:
        turret_pos = self.get_guardian_visible_turret(c)
        if turret_pos is None:
            if self.guard_target_kind is not None:
                return self.execute_guardian_response(c, None)
            if self.guard_search_dir is None:
                self.guard_mode = GUARD_RETURN_HEAL
                return False
            if self.guard_search_steps >= GUARDIAN_SEARCH_STEP_LIMIT:
                self.guard_mode = GUARD_RETURN_HEAL
                return False
            self.guard_search_steps += 1
            return self.move_in_preferred_direction(c, self.guard_search_dir)

        self.guard_turret_idx = self.pos_to_idx(turret_pos)

        if self.guard_target_kind is None:
            response = self.choose_guardian_response(c, turret_pos)
            if response is None:
                if self.guard_search_steps >= GUARDIAN_SEARCH_STEP_LIMIT:
                    self.guard_mode = GUARD_RETURN_HEAL
                    return False
                self.guard_search_steps += 1
                probe_goals = self.turret_probe_goals(c, turret_pos)
                if probe_goals:
                    return self.move_toward_any(c, probe_goals)
                self.guard_mode = GUARD_RETURN_HEAL
                return False
            self.guard_search_steps = 0
            self.guard_target_kind, self.guard_target_idx, self.guard_build_idx, self.guard_build_facing = response
        else:
            self.guard_search_steps = 0

        return self.execute_guardian_response(c, turret_pos)

    def handle_guardian_repair(self, c: Controller) -> bool:
        if self.guard_target_idx is None:
            return False
        target_pos = self.idx_to_pos(self.guard_target_idx)
        building_id = c.get_tile_building_id(target_pos)
        if building_id is None or c.get_team(building_id) != self.my_team:
            self.guard_mode = GUARD_IDLE
            return False
        if c.get_entity_type(building_id) not in REPAIRABLE_NEAR_CORE_BUILDINGS:
            self.guard_mode = GUARD_IDLE
            return False
        if c.get_hp(building_id) >= c.get_max_hp(building_id):
            next_targets = self.find_damaged_near_core_buildings(c)
            if not next_targets:
                self.guard_mode = GUARD_IDLE
                return False
            self.guard_target_idx = self.pos_to_idx(next_targets[0])
            target_pos = self.idx_to_pos(self.guard_target_idx)
        if c.can_heal(target_pos):
            c.heal(target_pos)
            return True
        return self.move_toward_any(c, self.action_access_goals(c, target_pos, allow_target_tile=True))

    def handle_guardian_return_and_heal(self, c: Controller) -> bool:
        if self.core_pos is not None and self.is_core_damaged(c):
            if self.try_activate_guardian_threat_response(c):
                return True
        if self.heal_allied_core_if_possible(c):
            return True
        if self.is_core_damaged(c):
            for core_tile in self.get_core_footprint(self.core_pos):
                if c.can_heal(core_tile):
                    c.heal(core_tile)
                    return True
            return self.move_toward_any(c, {self.pos_to_idx(pos) for pos in self.guardian_wait_positions()})
        if self.home_wait_idx is not None and self.pos_to_idx(c.get_position()) != self.home_wait_idx:
            return self.move_toward_any(c, {self.home_wait_idx})
        self.guard_mode = GUARD_IDLE
        return False

    def begin_guardian_core_response(
        self, turret_pos: Position | None, search_dir: Direction | None
    ) -> None:
        self.guard_mode = GUARD_CORE_RESPONSE
        self.guard_turret_idx = None if turret_pos is None else self.pos_to_idx(turret_pos)
        self.guard_target_kind = None
        self.guard_target_idx = None
        self.guard_build_idx = None
        self.guard_build_facing = None
        self.guard_search_dir = search_dir
        self.guard_search_steps = 0
        self.clear_move_path()

    def choose_guardian_response(
        self, c: Controller, turret_pos: Position
    ) -> tuple[str, int | None, int | None, Direction | None] | None:
        allied_destroy: Position | None = None
        allied_harvester: Position | None = None
        enemy_supply: Position | None = None
        enemy_harvester: Position | None = None
        seen_feeders: set[int] = set()

        for direction in ALL_DIRECTIONS:
            adj = turret_pos.add(direction)
            if not self.in_bounds(adj):
                continue
            if not self.is_tile_visible_this_round(adj):
                continue
            building_id = c.get_tile_building_id(adj)
            if building_id is None:
                continue
            building_type = c.get_entity_type(building_id)
            building_team = c.get_team(building_id)
            if not self.directly_feeds_turret(c, adj, building_id, turret_pos):
                continue
            seen_feeders.add(self.pos_to_idx(adj))
            if building_team == self.my_team:
                if building_type == EntityType.HARVESTER:
                    allied_harvester = adj
                elif building_type in DIRECT_SUPPLY_BUILDINGS:
                    allied_destroy = adj
            elif building_type == EntityType.HARVESTER:
                enemy_harvester = adj
            elif building_type in DIRECT_SUPPLY_BUILDINGS:
                enemy_supply = adj

        for building_id in c.get_nearby_buildings():
            if c.get_entity_type(building_id) != EntityType.BRIDGE:
                continue
            feeder_pos = c.get_position(building_id)
            feeder_idx = self.pos_to_idx(feeder_pos)
            if feeder_idx in seen_feeders:
                continue
            if not self.directly_feeds_turret(c, feeder_pos, building_id, turret_pos):
                continue
            building_team = c.get_team(building_id)
            seen_feeders.add(feeder_idx)
            if building_team == self.my_team:
                allied_destroy = feeder_pos
            else:
                enemy_supply = feeder_pos

        if allied_harvester is not None:
            return GUARD_TARGET_DESTROY_ALLY_HARVESTER, self.pos_to_idx(allied_harvester), None, None
        if allied_destroy is not None:
            return GUARD_TARGET_DESTROY_ALLY, self.pos_to_idx(allied_destroy), None, None
        if enemy_harvester is not None:
            gunner_site = self.choose_enemy_harvester_gunner_site(c, turret_pos, enemy_harvester)
            if gunner_site is not None:
                build_idx, facing = gunner_site
                return GUARD_TARGET_BUILD_GUNNER, self.pos_to_idx(enemy_harvester), build_idx, facing
        if enemy_supply is not None:
            return GUARD_TARGET_FIRE_ENEMY, self.pos_to_idx(enemy_supply), None, None
        return None

    def execute_guardian_response(self, c: Controller, turret_pos: Position | None) -> bool:
        if self.guard_target_kind in {
            GUARD_TARGET_DESTROY_ALLY,
            GUARD_TARGET_DESTROY_ALLY_HARVESTER,
        }:
            if self.guard_target_idx is None:
                return False
            target_pos = self.idx_to_pos(self.guard_target_idx)
            if not self.is_tile_visible_this_round(target_pos):
                return self.move_toward_any(c, self.action_access_goals(c, target_pos, allow_target_tile=True))
            building_id = c.get_tile_building_id(target_pos)
            if building_id is None or c.get_team(building_id) != self.my_team:
                self.finish_guardian_response()
                return False
            if pos_distance_sq(c.get_position(), target_pos) <= 2 and c.can_destroy(target_pos):
                c.destroy(target_pos)
                self.finish_guardian_response()
                return True
            return self.move_toward_any(c, self.action_access_goals(c, target_pos, allow_target_tile=True))

        if self.guard_target_kind == GUARD_TARGET_FIRE_ENEMY:
            if self.guard_target_idx is None:
                return False
            target_pos = self.idx_to_pos(self.guard_target_idx)
            if not self.is_tile_visible_this_round(target_pos):
                return self.move_toward_any(c, {self.guard_target_idx})
            building_id = c.get_tile_building_id(target_pos)
            if building_id is None or c.get_team(building_id) == self.my_team:
                self.finish_guardian_response()
                return False
            if self.pos_to_idx(c.get_position()) == self.guard_target_idx:
                if c.can_fire(c.get_position()):
                    c.fire(c.get_position())
                    if c.get_tile_building_id(target_pos) is None:
                        self.finish_guardian_response()
                    return True
                self.wait_for_titanium_amount(c, 2)
                return False
            return self.move_toward_any(c, {self.guard_target_idx})

        if self.guard_target_kind == GUARD_TARGET_BUILD_GUNNER:
            if self.guard_build_idx is None or self.guard_build_facing is None:
                self.finish_guardian_response()
                return False
            build_pos = self.idx_to_pos(self.guard_build_idx)
            current_idx = self.pos_to_idx(c.get_position())
            if not self.is_tile_visible_this_round(build_pos):
                return self.move_toward_any(c, self.build_vantage_goals(build_pos))
            building_id = c.get_tile_building_id(build_pos)
            if building_id is not None:
                building_type = c.get_entity_type(building_id)
                if c.get_team(building_id) == self.my_team and building_type == EntityType.GUNNER:
                    self.finish_guardian_response()
                    return False
                if building_type != EntityType.MARKER:
                    self.finish_guardian_response()
                    return False
            if current_idx == self.guard_build_idx:
                return self.move_off_current_tile(c, self.build_vantage_goals(build_pos))
            if pos_distance_sq(c.get_position(), build_pos) > 2:
                return self.move_toward_any(c, self.build_vantage_goals(build_pos))
            if c.get_tile_builder_bot_id(build_pos) is not None:
                return False
            if c.can_build_gunner(build_pos, self.guard_build_facing):
                c.build_gunner(build_pos, self.guard_build_facing)
                self.finish_guardian_response()
                return True
            self.wait_for_titanium_shortage(c, "get_gunner_cost")
            return False

        return False

    def finish_guardian_response(self) -> None:
        self.guard_mode = GUARD_RETURN_HEAL
        self.guard_target_kind = None
        self.guard_target_idx = None
        self.guard_build_idx = None
        self.guard_build_facing = None
        self.guard_search_steps = 0
        self.clear_move_path()

    def try_promote_miner_to_emergency_guardian(self, c: Controller) -> bool:
        guardian_plan = self.emergency_guardian_plan(c)
        if guardian_plan is None:
            return False
        turret_pos, search_dir = guardian_plan
        self.activate_emergency_guardian(c, turret_pos, search_dir)
        return True

    def emergency_guardian_plan(
        self, c: Controller
    ) -> tuple[Position | None, Direction | None] | None:
        if self.core_pos is None or self.temporary_guardian:
            return None
        if not self.is_core_damaged(c):
            return None
        if pos_distance_sq(c.get_position(), self.core_pos) > NEAR_CORE_DEFENDER_DIST_SQ:
            return None
        visible_turrets = self.find_visible_turrets_attacking_core_from_guardian(c)
        if visible_turrets:
            limit = min(len(visible_turrets), 2)
            for turret_pos in visible_turrets:
                if self.is_selected_emergency_guardian(c, turret_pos, limit):
                    return turret_pos, self.core_pos.direction_to(turret_pos)
            return None
        directions = self.offscreen_scout_directions()
        if not directions:
            return None
        target = self.core_pos.add(self.guardian_default_search_direction(c.get_position()) or directions[0])
        if not self.is_selected_emergency_guardian(c, target, len(directions)):
            return None
        return None, self.guardian_default_search_direction(c.get_position())

    def is_selected_emergency_guardian(self, c: Controller, target_pos: Position, limit: int) -> bool:
        my_idx = self.pos_to_idx(c.get_position())
        candidates: list[Position] = []
        guardian_slots = {self.pos_to_idx(pos) for pos in self.guardian_wait_positions()}
        for entity_id in c.get_nearby_entities():
            if c.get_team(entity_id) != self.my_team:
                continue
            if c.get_entity_type(entity_id) != EntityType.BUILDER_BOT:
                continue
            pos = c.get_position(entity_id)
            idx = self.pos_to_idx(pos)
            if idx in guardian_slots:
                continue
            if self.core_pos is not None and pos_distance_sq(pos, self.core_pos) > NEAR_CORE_DEFENDER_DIST_SQ:
                continue
            candidates.append(pos)
        if (
            my_idx not in {self.pos_to_idx(pos) for pos in candidates}
            and self.core_pos is not None
            and pos_distance_sq(c.get_position(), self.core_pos) <= NEAR_CORE_DEFENDER_DIST_SQ
        ):
            candidates.append(c.get_position())
        candidates.sort(
            key=lambda pos: (
                pos_distance_sq(pos, target_pos),
                pos_distance_sq(pos, self.core_pos) if self.core_pos is not None else 0,
                pos.y,
                pos.x,
            )
        )
        chosen = {self.pos_to_idx(pos) for pos in candidates[:limit]}
        return my_idx in chosen

    def activate_emergency_guardian(
        self, c: Controller, turret_pos: Position | None, search_dir: Direction | None
    ) -> None:
        self.reset_target()
        self.role = ROLE_GUARDIAN
        self.temporary_guardian = True
        self.home_wait_idx = self.pos_to_idx(c.get_position())
        if search_dir is None and turret_pos is not None:
            search_dir = self.core_pos.direction_to(turret_pos)
        self.begin_guardian_core_response(turret_pos, search_dir)

    def revert_temporary_guardian_to_miner(self) -> None:
        self.role = ROLE_MINER
        self.temporary_guardian = False
        self.home_wait_idx = None
        self.guard_mode = GUARD_IDLE
        self.guard_turret_idx = None
        self.guard_target_kind = None
        self.guard_target_idx = None
        self.guard_build_idx = None
        self.guard_build_facing = None
        self.guard_search_dir = None
        self.guard_search_steps = 0
        self.clear_move_path()

    def directly_feeds_turret(
        self, c: Controller, feeder_pos: Position, building_id: int, turret_pos: Position
    ) -> bool:
        return self.directly_feeds_position(c, feeder_pos, building_id, turret_pos)

    def directly_feeds_position(
        self, c: Controller, feeder_pos: Position, building_id: int, target_pos: Position
    ) -> bool:
        building_type = c.get_entity_type(building_id)
        if building_type == EntityType.BRIDGE:
            return c.get_bridge_target(building_id) == target_pos
        if building_type in {EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR}:
            return feeder_pos.add(c.get_direction(building_id)) == target_pos
        if building_type == EntityType.SPLITTER:
            facing = c.get_direction(building_id)
            return target_pos in {
                feeder_pos.add(facing),
                feeder_pos.add(left_cardinal(facing)),
                feeder_pos.add(right_cardinal(facing)),
            }
        if building_type in {EntityType.HARVESTER, EntityType.FOUNDRY}:
            return chebyshev(feeder_pos, target_pos) == 1
        return False

    def find_turret_feeders(
        self, c: Controller, turret_pos: Position
    ) -> list[tuple[int, Position]]:
        feeders: list[tuple[int, Position]] = []
        seen: set[int] = set()

        for direction in ALL_DIRECTIONS:
            feeder_pos = turret_pos.add(direction)
            if not self.in_bounds(feeder_pos) or not self.is_tile_visible_this_round(feeder_pos):
                continue
            building_id = c.get_tile_building_id(feeder_pos)
            if building_id is None:
                continue
            if not self.directly_feeds_turret(c, feeder_pos, building_id, turret_pos):
                continue
            feeder_idx = self.pos_to_idx(feeder_pos)
            seen.add(feeder_idx)
            feeders.append((building_id, feeder_pos))

        for building_id in c.get_nearby_buildings():
            if c.get_entity_type(building_id) != EntityType.BRIDGE:
                continue
            feeder_pos = c.get_position(building_id)
            feeder_idx = self.pos_to_idx(feeder_pos)
            if feeder_idx in seen:
                continue
            if not self.directly_feeds_turret(c, feeder_pos, building_id, turret_pos):
                continue
            feeders.append((building_id, feeder_pos))

        return feeders

    def is_turret_still_supplied(
        self, c: Controller, turret_pos: Position
    ) -> bool:
        for building_id, _ in self.find_turret_feeders(c, turret_pos):
            if c.get_entity_type(building_id) in THREAT_FEED_BUILDINGS:
                return True
        return False

    def classify_enemy_turrets_attacking_core(
        self, c: Controller, core_pos: Position
    ) -> tuple[list[tuple[int, Position]], list[tuple[int, Position]]]:
        active_attackers: list[tuple[int, int, int, Position]] = []
        neutralized_attackers: list[tuple[int, int, int, Position]] = []
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            entity_type = c.get_entity_type(building_id)
            if entity_type not in TURRET_TYPES:
                continue
            turret_pos = c.get_position(building_id)
            turret_dir = c.get_direction(building_id)
            if not self.can_turret_hit_core(c, turret_pos, turret_dir, entity_type, core_pos):
                continue
            record = (
                pos_distance_sq(core_pos, turret_pos),
                manhattan(core_pos, turret_pos),
                building_id,
                turret_pos,
            )
            if self.is_turret_still_supplied(c, turret_pos):
                active_attackers.append(record)
            else:
                neutralized_attackers.append(record)

        active_attackers.sort()
        neutralized_attackers.sort()
        return (
            [(building_id, turret_pos) for _, _, building_id, turret_pos in active_attackers],
            [(building_id, turret_pos) for _, _, building_id, turret_pos in neutralized_attackers],
        )

    def choose_guardian_gunner_site(
        self, c: Controller, turret_pos: Position
    ) -> tuple[int, Direction] | None:
        best: tuple[tuple[int, int, int], int, Direction] | None = None
        current_pos = c.get_position()
        for facing in ALL_DIRECTIONS:
            dx, dy = DIR_TO_DELTA[facing]
            if dx == 0 and dy == 0:
                continue
            for dist in range(1, 6):
                build_pos = Position(turret_pos.x - dx * dist, turret_pos.y - dy * dist)
                if not self.in_bounds(build_pos):
                    continue
                if not c.can_fire_from(build_pos, facing, EntityType.GUNNER, turret_pos):
                    continue
                if not self.is_tile_visible_this_round(build_pos):
                    continue
                building_id = c.get_tile_building_id(build_pos)
                if building_id is not None and c.get_entity_type(building_id) != EntityType.MARKER:
                    continue
                goals = self.action_access_goals(c, build_pos, allow_target_tile=False)
                if not goals:
                    continue
                score = (
                    dist,
                    min(chebyshev(current_pos, self.idx_to_pos(idx)) for idx in goals),
                    chebyshev(current_pos, build_pos),
                )
                build_idx = self.pos_to_idx(build_pos)
                if best is None or score < best[0]:
                    best = (score, build_idx, facing)
        if best is None:
            return None
        return best[1], best[2]

    def choose_enemy_harvester_gunner_site(
        self, c: Controller, turret_pos: Position, harvester_pos: Position
    ) -> tuple[int, Direction] | None:
        best: tuple[tuple[int, int, int], int, Direction] | None = None
        current_pos = c.get_position()
        my_idx = self.pos_to_idx(current_pos)
        for direction in ALL_DIRECTIONS:
            build_pos = harvester_pos.add(direction)
            if build_pos == turret_pos or not self.in_bounds(build_pos):
                continue
            if not self.is_tile_visible_this_round(build_pos):
                continue
            builder_id = c.get_tile_builder_bot_id(build_pos)
            if builder_id is not None and self.pos_to_idx(build_pos) != my_idx:
                continue
            building_id = c.get_tile_building_id(build_pos)
            if building_id is not None and c.get_entity_type(building_id) != EntityType.MARKER:
                continue
            facing = build_pos.direction_to(turret_pos)
            if facing == Direction.CENTRE:
                continue
            try:
                if not c.can_fire_from(build_pos, facing, EntityType.GUNNER, turret_pos):
                    continue
            except Exception:
                continue
            goals = self.action_access_goals(c, build_pos, allow_target_tile=False)
            if not goals:
                continue
            score = (
                min(chebyshev(current_pos, self.idx_to_pos(idx)) for idx in goals),
                manhattan(current_pos, build_pos),
                self.pos_to_idx(build_pos),
            )
            build_idx = self.pos_to_idx(build_pos)
            if best is None or score < best[0]:
                best = (score, build_idx, facing)
        if best is None:
            return None
        return best[1], best[2]

    def get_guardian_visible_turret(self, c: Controller) -> Position | None:
        fallback: Position | None = None
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            if c.get_entity_type(building_id) not in TURRET_TYPES:
                continue
            pos = c.get_position(building_id)
            if not self.is_turret_still_supplied(c, pos):
                continue
            idx = self.pos_to_idx(pos)
            if self.guard_turret_idx is not None and idx == self.guard_turret_idx:
                return pos
            if fallback is None:
                fallback = pos
        return fallback

    def find_visible_turrets_attacking_core_from_guardian(self, c: Controller) -> list[Position]:
        _, core_pos = self.find_visible_allied_core(c)
        if core_pos is None:
            return []
        attackers: list[tuple[int, int, Position]] = []
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            entity_type = c.get_entity_type(building_id)
            if entity_type not in TURRET_TYPES:
                continue
            turret_pos = c.get_position(building_id)
            turret_dir = c.get_direction(building_id)
            if not self.can_turret_hit_core(c, turret_pos, turret_dir, entity_type, core_pos):
                continue
            if not self.is_turret_still_supplied(c, turret_pos):
                continue
            attackers.append(
                (
                    pos_distance_sq(core_pos, turret_pos),
                    manhattan(core_pos, turret_pos),
                    turret_pos,
                )
            )
        attackers.sort()
        return [pos for _, _, pos in attackers]

    def is_tile_visible_this_round(self, pos: Position) -> bool:
        if not self.in_bounds(pos):
            return False
        idx = self.pos_to_idx(pos)
        return self.known_builder_round[idx] == self.current_round

    def select_guardian_visible_turret(self, visible_turrets: list[Position]) -> Position | None:
        if not visible_turrets:
            return None
        slot_rank = self.guardian_slot_rank()
        if slot_rank >= len(visible_turrets):
            return None
        return visible_turrets[slot_rank]

    def guardian_wait_positions(self) -> list[Position]:
        if self.core_pos is None:
            return []
        positions: list[Position] = []
        for dy in (-1, 1):
            for dx in (-1, 1):
                pos = Position(self.core_pos.x + dx, self.core_pos.y + dy)
                if self.in_bounds(pos):
                    positions.append(pos)
        return positions

    def guardian_slot_order(self) -> list[Position]:
        return sorted(self.guardian_wait_positions(), key=lambda pos: (pos.y, pos.x))

    def guardian_assignment_positions(self) -> list[Position]:
        if self.core_pos is None:
            return []
        positions = {self.pos_to_idx(pos): pos for pos in self.guardian_wait_positions()}
        for direction in ALL_DIRECTIONS:
            if direction == Direction.CENTRE:
                continue
            pos = self.core_pos.add(direction)
            if self.in_bounds(pos):
                positions[self.pos_to_idx(pos)] = pos
        return sorted(positions.values(), key=lambda pos: (pos.y, pos.x))

    def defender_spawn_direction(self) -> Direction | None:
        defender_pos = self.initial_defender_position()
        if defender_pos is None:
            return None
        return self.core_pos.direction_to(defender_pos)

    def initial_defender_position(self) -> Position | None:
        ordered = self.guardian_slot_order()
        return ordered[0] if ordered else None

    def guardian_slot_rank(self) -> int:
        if self.home_wait_idx is None:
            return 0
        ordered = self.guardian_assignment_positions()
        for index, pos in enumerate(ordered):
            if self.pos_to_idx(pos) == self.home_wait_idx:
                return index
        return 0

    def guardian_command_positions(self) -> list[Position]:
        if self.core_pos is None:
            return []
        positions: list[Position] = []
        for dy in (-2, 2):
            for dx in (-2, 2):
                pos = Position(self.core_pos.x + dx, self.core_pos.y + dy)
                if self.in_bounds(pos):
                    positions.append(pos)
        return positions

    def count_idle_guardians(self, c: Controller) -> int:
        count = 0
        for pos in self.guardian_wait_positions():
            bot_id = c.get_tile_builder_bot_id(pos)
            if bot_id is None:
                continue
            if c.get_team(bot_id) == self.my_team:
                count += 1
        return count

    def pick_guardian_spawn_directions(
        self, attackers: list[tuple[int, Position]], core_damaged: bool, damaged_near_core: list[Position]
    ) -> list[Direction]:
        directions: list[Direction] = []
        seen: set[Direction] = set()

        def add(direction: Direction | None) -> None:
            if direction is None or direction == Direction.CENTRE or direction in seen:
                return
            seen.add(direction)
            directions.append(direction)

        for _, turret_pos in attackers:
            add(self.core_pos.direction_to(turret_pos))
        if core_damaged and not attackers:
            for direction in self.offscreen_scout_directions():
                add(direction)
        for target in damaged_near_core:
            add(self.core_pos.direction_to(target))
        for slot in self.guardian_slot_order():
            add(self.core_pos.direction_to(slot))
        return directions

    def place_core_threat_marker(self, c: Controller, turret_pos: Position) -> None:
        total = self.width * self.height
        marker_value = self.current_round * total + self.pos_to_idx(turret_pos)
        for pos in sorted(
            self.guardian_command_positions(),
            key=lambda marker_pos: pos_distance_sq(marker_pos, turret_pos),
        ):
            if c.can_place_marker(pos):
                c.place_marker(pos, marker_value)
                return

    def place_offscreen_scout_marker(self, c: Controller) -> None:
        total = self.width * self.height
        direction = self.select_offscreen_scout_direction(prefer_first=True)
        if direction is None or self.core_pos is None:
            return
        marker_target = self.core_pos.add(direction)
        if not self.in_bounds(marker_target):
            marker_target = self.core_pos
        marker_value = self.current_round * total + self.pos_to_idx(marker_target)
        for pos in self.guardian_command_positions():
            if c.can_place_marker(pos):
                c.place_marker(pos, marker_value)
                return

    def read_latest_core_threat_marker(self, c: Controller) -> Position | None:
        total = self.width * self.height
        best_round = -1
        best_idx: int | None = None
        for pos in self.guardian_command_positions():
            if not self.is_tile_visible_this_round(pos):
                continue
            building_id = c.get_tile_building_id(pos)
            if building_id is None:
                continue
            if c.get_team(building_id) != self.my_team or c.get_entity_type(building_id) != EntityType.MARKER:
                continue
            marker_value = c.get_marker_value(building_id)
            marker_round = marker_value // total
            target_idx = marker_value % total
            if marker_round > best_round and 0 <= target_idx < total:
                best_round = marker_round
                best_idx = target_idx
        if best_idx is None or best_round < self.current_round - 6:
            return None
        return self.idx_to_pos(best_idx)

    def select_offscreen_scout_direction(self, prefer_first: bool = False) -> Direction | None:
        directions = self.offscreen_scout_directions()
        if not directions:
            return None
        if prefer_first:
            return directions[0]
        slot_rank = self.guardian_slot_rank()
        return directions[slot_rank % len(directions)]

    def offscreen_scout_directions(self) -> list[Direction]:
        if self.core_pos is None:
            return []
        center_x = (self.width - 1) / 2
        center_y = (self.height - 1) / 2
        dx = center_x - self.core_pos.x
        dy = center_y - self.core_pos.y
        if abs(dx) >= abs(dy):
            primary = Direction.EAST if dx >= 0 else Direction.WEST
        else:
            primary = Direction.SOUTH if dy >= 0 else Direction.NORTH
        return [primary, opposite(primary)]

    def guardian_home_direction(self) -> Direction | None:
        if self.core_pos is None or self.home_wait_idx is None:
            return None
        direction = self.core_pos.direction_to(self.idx_to_pos(self.home_wait_idx))
        return direction if direction in CARDINAL_DIRECTIONS_SET else None

    def guardian_default_search_direction(self, pos: Position) -> Direction | None:
        home_dir = self.guardian_home_direction()
        if home_dir is not None:
            return home_dir
        directions = self.offscreen_scout_directions()
        if not directions:
            return None
        if self.core_pos is None:
            return directions[0]
        preferred = self.infer_primary_direction(pos)
        if preferred in directions:
            return preferred
        return directions[self.guardian_slot_rank() % len(directions)]

    def is_selected_guardian_for(self, c: Controller, target_pos: Position, limit: int) -> bool:
        if self.home_wait_idx is None:
            return True
        occupied_slots: list[Position] = []
        for slot in self.guardian_wait_positions():
            if not self.is_tile_visible_this_round(slot):
                continue
            bot_id = c.get_tile_builder_bot_id(slot)
            if bot_id is None:
                continue
            if c.get_team(bot_id) == self.my_team:
                occupied_slots.append(slot)
        if not occupied_slots:
            return True
        occupied_slots.sort(
            key=lambda slot: (
                pos_distance_sq(slot, target_pos),
                manhattan(slot, target_pos),
                slot.y,
                slot.x,
            )
        )
        chosen = {self.pos_to_idx(slot) for slot in occupied_slots[:limit]}
        return self.home_wait_idx in chosen

    def action_access_goals(
        self, c: Controller, target_pos: Position, allow_target_tile: bool
    ) -> set[int]:
        goals: set[int] = set()
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                pos = Position(target_pos.x + dx, target_pos.y + dy)
                if not self.in_bounds(pos):
                    continue
                if pos_distance_sq(pos, target_pos) > 2:
                    continue
                if not allow_target_tile and pos == target_pos:
                    continue
                if self.builder_tile_ok(c, pos):
                    goals.add(self.pos_to_idx(pos))
        return goals

    def move_in_preferred_direction(self, c: Controller, preferred_dir: Direction) -> bool:
        directions = [preferred_dir]
        if preferred_dir != Direction.CENTRE:
            directions.extend(
                [
                    preferred_dir.rotate_left(),
                    preferred_dir.rotate_right(),
                    preferred_dir.rotate_left().rotate_left(),
                    preferred_dir.rotate_right().rotate_right(),
                ]
            )
        seen: set[Direction] = set()
        for direction in directions:
            if direction == Direction.CENTRE or direction in seen:
                continue
            seen.add(direction)
            next_pos = c.get_position().add(direction)
            if not self.in_bounds(next_pos):
                continue
            if self.try_move_into(c, next_pos, direction):
                return True
        for direction in ALL_DIRECTIONS:
            if direction in seen:
                continue
            next_pos = c.get_position().add(direction)
            if not self.in_bounds(next_pos):
                continue
            if self.try_move_into(c, next_pos, direction):
                return True
        return False

    def heal_allied_core_if_possible(self, c: Controller) -> bool:
        if self.core_pos is None:
            return False
        for core_tile in self.get_core_footprint(self.core_pos):
            if c.can_heal(core_tile):
                c.heal(core_tile)
                return True
        return False

    def is_core_damaged(self, c: Controller) -> bool:
        core_id, _ = self.find_visible_allied_core(c)
        if core_id is None:
            return False
        return c.get_hp(core_id) < c.get_max_hp(core_id)

    def find_visible_allied_core(self, c: Controller) -> tuple[int | None, Position | None]:
        for building_id in c.get_nearby_buildings():
            if c.get_entity_type(building_id) != EntityType.CORE:
                continue
            if c.get_team(building_id) != self.my_team:
                continue
            return building_id, c.get_position(building_id)
        return None, None

    def find_enemy_turrets_attacking_core(
        self, c: Controller, core_pos: Position
    ) -> list[tuple[int, Position]]:
        attackers, _ = self.classify_enemy_turrets_attacking_core(c, core_pos)
        return attackers

    def can_turret_hit_core(
        self,
        c: Controller,
        turret_pos: Position,
        turret_dir: Direction,
        turret_type: EntityType,
        core_pos: Position,
    ) -> bool:
        for tile in self.get_core_footprint(core_pos):
            if c.can_fire_from(turret_pos, turret_dir, turret_type, tile):
                return True
        return False

    def get_core_footprint(self, core_pos: Position) -> list[Position]:
        footprint: list[Position] = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                pos = Position(core_pos.x + dx, core_pos.y + dy)
                if self.in_bounds(pos):
                    footprint.append(pos)
        return footprint

    def find_damaged_near_core_buildings(self, c: Controller) -> list[Position]:
        if self.core_pos is None:
            return []
        damaged: list[tuple[int, int, Position]] = []
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) != self.my_team:
                continue
            entity_type = c.get_entity_type(building_id)
            if entity_type not in REPAIRABLE_NEAR_CORE_BUILDINGS:
                continue
            pos = c.get_position(building_id)
            if pos_distance_sq(pos, self.core_pos) > NEAR_CORE_REPAIR_DIST_SQ:
                continue
            hp = c.get_hp(building_id)
            max_hp = c.get_max_hp(building_id)
            if hp >= max_hp:
                continue
            damaged.append((max_hp - hp, pos_distance_sq(pos, self.core_pos), pos))
        damaged.sort(key=lambda item: (-item[0], item[1]))
        return [pos for _, _, pos in damaged]

    def run_sentinel(self, c: Controller) -> None:
        core_target = self.find_sentinel_core_target(c)
        if core_target is not None:
            c.fire(core_target)
            return

        best_target: Position | None = None
        blocked_target: Position | None = None
        for _, target_pos in self.collect_all_enemy_targets(c, include_roads=False):
            if c.can_fire(target_pos):
                best_target = target_pos
                break
            if blocked_target is None:
                blocked_target = target_pos
        self.draw_turret_debug(c, best_target, blocked_target)
        if best_target is not None and c.can_fire(best_target):
            c.fire(best_target)

    def find_sentinel_core_target(self, c: Controller) -> Position | None:
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            if c.get_entity_type(building_id) != EntityType.CORE:
                continue
            for target_pos in self.get_core_footprint(c.get_position(building_id)):
                if c.can_fire(target_pos):
                    return target_pos

        for target_pos in c.get_attackable_tiles():
            building_id = c.get_tile_building_id(target_pos)
            if building_id is None:
                continue
            if c.get_team(building_id) != self.my_team and c.get_entity_type(building_id) == EntityType.CORE:
                if c.can_fire(target_pos):
                    return target_pos
        return None

    def run_gunner(self, c: Controller) -> None:
        current_dir = c.get_direction()
        core_shot = self.find_close_enemy_core_shot(c, current_dir)
        if core_shot is not None:
            desired_dir, desired_pos = core_shot
            self.draw_turret_debug(c, desired_pos, None, desired_dir)
            if c.get_action_cooldown() != 0:
                return
            if desired_dir == current_dir and c.can_fire(desired_pos):
                c.fire(desired_pos)
                return
            if desired_dir != current_dir and c.can_rotate(desired_dir):
                c.rotate(desired_dir)
            return

        best_any: tuple[tuple[int, ...], Direction, Position] | None = None
        blocked_target: Position | None = None

        for target_score, target_pos in self.collect_all_enemy_targets(c):
            if blocked_target is None and not c.can_fire_from(c.get_position(), current_dir, EntityType.GUNNER, target_pos):
                blocked_target = target_pos
            for direction in ALL_DIRECTIONS:
                if not c.can_fire_from(c.get_position(), direction, EntityType.GUNNER, target_pos):
                    continue
                score = target_score + (0 if direction == current_dir else 1,)
                if best_any is None or score < best_any[0]:
                    best_any = (score, direction, target_pos)

        desired_pos = best_any[2] if best_any is not None else None
        desired_dir = best_any[1] if best_any is not None else None
        self.draw_turret_debug(c, desired_pos, blocked_target, desired_dir)

        if best_any is None or c.get_action_cooldown() != 0:
            return
        if desired_dir == current_dir and desired_pos is not None and c.can_fire(desired_pos):
            c.fire(desired_pos)
            return
        if desired_dir is not None and desired_dir != current_dir and c.can_rotate(desired_dir):
            c.rotate(desired_dir)

    def find_close_enemy_core_shot(
        self, c: Controller, current_dir: Direction
    ) -> tuple[Direction, Position] | None:
        best: tuple[tuple[int, int, int, int], Direction, Position] | None = None
        for building_id in c.get_nearby_buildings():
            if c.get_team(building_id) == self.my_team:
                continue
            if c.get_entity_type(building_id) != EntityType.CORE:
                continue
            core_pos = c.get_position(building_id)
            if pos_distance_sq(c.get_position(), core_pos) > 13:
                continue
            for core_tile in self.get_core_footprint(core_pos):
                for direction in ALL_DIRECTIONS:
                    if not c.can_fire_from(c.get_position(), direction, EntityType.GUNNER, core_tile):
                        continue
                    score = (
                        0 if direction == current_dir else 1,
                        pos_distance_sq(c.get_position(), core_tile),
                        core_tile.y,
                        core_tile.x,
                    )
                    if best is None or score < best[0]:
                        best = (score, direction, core_tile)
        return None if best is None else (best[1], best[2])

    def collect_all_enemy_targets(
        self, c: Controller, include_roads: bool = True
    ) -> list[tuple[tuple[int, ...], Position]]:
        seen: dict[tuple[int, int], tuple[tuple[int, ...], Position]] = {}
        for entity_id in c.get_nearby_entities():
            if c.get_team(entity_id) == self.my_team:
                continue
            entity_type = c.get_entity_type(entity_id)
            if entity_type == EntityType.MARKER:
                continue
            if not include_roads and entity_type == EntityType.ROAD:
                continue
            pos = c.get_position(entity_id)
            score = (
                self.get_attack_target_priority(entity_type),
                manhattan(c.get_position(), pos),
                pos.y,
                pos.x,
            )
            key = (pos.x, pos.y)
            if key not in seen or score < seen[key][0]:
                seen[key] = (score, pos)
        targets = list(seen.values())
        targets.sort(key=lambda item: item[0])
        return targets

    def draw_turret_debug(
        self,
        c: Controller,
        target_pos: Position | None = None,
        blocked_pos: Position | None = None,
        facing_dir: Direction | None = None,
    ) -> None:
        return

    def get_attack_target_priority(self, entity_type: EntityType) -> int:
        return ATTACK_TARGET_PRIORITIES.get(entity_type, 11)

    def acquire_target(self, c: Controller) -> bool:
        self.debug_candidate_ores = []
        self.debug_blocked_ores = []
        self.debug_attempted_ores = []

        ore_candidates: list[tuple[int, int, Position]] = []
        for tile in c.get_nearby_tiles():
            if c.get_tile_env(tile) != Environment.ORE_TITANIUM:
                continue
            idx = self.pos_to_idx(tile)
            if idx in self.occupied_titanium:
                if len(self.debug_blocked_ores) < 10:
                    self.debug_blocked_ores.append(idx)
                continue
            if (TARGET_ORE, idx) in self.bad_targets:
                if len(self.debug_blocked_ores) < 10:
                    self.debug_blocked_ores.append(idx)
                continue
            if self.is_titanium_occupied(c, tile):
                if len(self.debug_blocked_ores) < 10:
                    self.debug_blocked_ores.append(idx)
                continue
            score = chebyshev(c.get_position(), tile)
            ore_candidates.append((score, manhattan(c.get_position(), tile), tile))
        ore_candidates.sort()
        self.debug_candidate_ores = [
            self.pos_to_idx(pos) for _, _, pos in ore_candidates[:MAX_ORE_TARGET_ATTEMPTS]
        ]
        for _, _, ore_pos in ore_candidates[:MAX_ORE_TARGET_ATTEMPTS]:
            self.debug_attempted_ores.append(self.pos_to_idx(ore_pos))
            if self.plan_target(c, TARGET_ORE, ore_pos):
                return True

        enemy_candidates: list[tuple[int, int, Position]] = []
        for building_id in c.get_nearby_buildings():
            if c.get_entity_type(building_id) != EntityType.HARVESTER:
                continue
            if c.get_team(building_id) == self.my_team:
                continue
            pos = c.get_position(building_id)
            if c.get_tile_env(pos) != Environment.ORE_TITANIUM:
                continue
            idx = self.pos_to_idx(pos)
            if (TARGET_ENEMY_HARVESTER, idx) in self.bad_targets:
                continue
            score = chebyshev(c.get_position(), pos)
            enemy_candidates.append((score, manhattan(c.get_position(), pos), pos))
        enemy_candidates.sort()
        for _, _, harvester_pos in enemy_candidates[:MAX_ENEMY_TARGET_ATTEMPTS]:
            if self.plan_target(c, TARGET_ENEMY_HARVESTER, harvester_pos):
                return True
        return False

    def plan_target(self, c: Controller, target_kind: str, target_pos: Position) -> bool:
        target_idx = self.pos_to_idx(target_pos)
        plan = self.choose_entry_stage(c, target_pos)
        if plan is None:
            self.mark_bad_target(target_kind, target_idx)
            return False
        entry_idx, stage_idx = plan
        goals = self.initial_travel_goals(c, target_kind, target_pos, stage_idx)
        path = self.find_builder_path(c, self.pos_to_idx(c.get_position()), goals)
        if not path:
            path = []

        self.target_kind = target_kind
        self.target_idx = target_idx
        self.entry_idx = entry_idx
        self.stage_idx = stage_idx
        self.route_nodes = []
        self.route_edges = []
        self.route_build_index = 0
        self.pending_ore_sentinels = []
        self.pending_ore_outward_sentinel_idx = None
        self.pending_splitter_sentinels = []
        self.final_splitter_idx = None
        self.route_ready = False
        self.state = STATE_TRAVEL
        self.move_path = path
        self.move_goal_signature = tuple(sorted(goals))
        return True

    def ordered_cardinals_toward(self, origin: Position, target: Position | None) -> list[Direction]:
        if target is None:
            return list(CARDINAL_DIRECTIONS)
        dx = target.x - origin.x
        dy = target.y - origin.y
        horizontal = Direction.EAST if dx >= 0 else Direction.WEST
        vertical = Direction.SOUTH if dy >= 0 else Direction.NORTH
        if abs(dx) >= abs(dy):
            ordered = [horizontal, vertical, opposite(horizontal), opposite(vertical)]
        else:
            ordered = [vertical, horizontal, opposite(vertical), opposite(horizontal)]
        result: list[Direction] = []
        for direction in ordered:
            if direction not in result:
                result.append(direction)
        return result

    def ring_positions_for_target(self, target_pos: Position) -> list[Position]:
        directions = CARDINAL_DIRECTIONS
        if self.target_kind == TARGET_FOUNDRY_ROUTE:
            directions = tuple(self.ordered_cardinals_toward(target_pos, self.core_pos))
        elif self.target_kind == TARGET_AXIONITE_LINK and self.axionite_foundry_idx is not None:
            directions = tuple(self.ordered_cardinals_toward(target_pos, self.idx_to_pos(self.axionite_foundry_idx)))
        positions: list[Position] = []
        for direction in directions:
            pos = target_pos.add(direction)
            if self.in_bounds(pos):
                positions.append(pos)
        return positions

    def foundry_route_entry_ok(self, pos: Position) -> bool:
        if self.target_kind != TARGET_FOUNDRY_ROUTE:
            return True
        if self.axionite_harvester_idx is not None and self.pos_to_idx(pos) == self.axionite_harvester_idx:
            return False
        idx = self.pos_to_idx(pos)
        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        if building_mine and building_type in DIRECT_SUPPLY_BUILDINGS:
            return False
        return True

    def choose_entry_stage(self, c: Controller, target_pos: Position) -> tuple[int, int] | None:
        ring_positions = self.ring_positions_for_target(target_pos)

        ring_positions.sort(
            key=lambda pos: (
                0 if self.entry_tile_ok(c, pos) else 1,
                0 if self.foundry_route_entry_ok(pos) else 1,
                manhattan(pos, self.core_pos) if self.core_pos is not None else 0,
                chebyshev(pos, c.get_position()),
            )
        )

        for entry_pos in ring_positions:
            if not self.entry_tile_ok(c, entry_pos):
                continue
            if not self.foundry_route_entry_ok(entry_pos):
                continue
            entry_idx = self.pos_to_idx(entry_pos)
            stage_idx = self.choose_stage_idx(c, target_pos, entry_idx)
            return entry_idx, stage_idx
        return None

    def choose_stage_idx(self, c: Controller, target_pos: Position, entry_idx: int) -> int:
        entry_pos = self.idx_to_pos(entry_idx)
        options: list[tuple[int, int]] = []
        for direction in ALL_DIRECTIONS:
            pos = target_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            idx = self.pos_to_idx(pos)
            if idx == entry_idx:
                continue
            if pos_distance_sq(pos, entry_pos) > 2:
                continue
            if not self.builder_tile_ok(c, pos):
                continue
            score = chebyshev(pos, c.get_position())
            options.append((score, idx))
        if options:
            options.sort()
            return options[0][1]
        return entry_idx

    def ensure_route_plan(self, c: Controller) -> bool:
        if self.route_ready:
            return True
        if self.target_idx is None:
            return False
        plan = self.choose_route_plan(c, self.idx_to_pos(self.target_idx))
        if plan is None:
            self.mark_bad_target(self.target_kind, self.target_idx)
            self.reset_target()
            return False
        entry_idx, stage_idx, route_nodes, route_edges = plan
        self.entry_idx = entry_idx
        self.stage_idx = stage_idx
        self.route_nodes = route_nodes
        self.route_edges = route_edges
        self.route_build_index = 0
        self.route_ready = True
        if self.role == ROLE_ATTACKER and self.target_kind == TARGET_ATTACK_TITANIUM:
            self.apply_attack_route_goal(route_nodes[-1])
        return True

    def apply_attack_route_goal(self, feeder_idx: int) -> None:
        plan = self.attack_route_goal_plan.get(feeder_idx)
        if plan is None:
            return
        sentinel_idx, sentinel_dir = plan
        self.attack_feeder_idx = feeder_idx
        self.attack_sentinel_idx = sentinel_idx
        self.attack_sentinel_dir = sentinel_dir

    def choose_route_plan(
        self, c: Controller, target_pos: Position
    ) -> tuple[int, int, list[int], list[int]] | None:
        if self.core_pos is None:
            return None

        ring_positions = self.ring_positions_for_target(target_pos)

        ring_positions.sort(
            key=lambda pos: (
                0 if self.foundry_route_entry_ok(pos) else 1,
                manhattan(pos, self.core_pos),
                chebyshev(pos, c.get_position()),
            )
        )

        plan_start = time.perf_counter()
        attempts = 0
        max_attempts = MAX_FOUNDRY_ROUTE_ENTRY_ATTEMPTS if self.target_kind == TARGET_FOUNDRY_ROUTE else MAX_ENTRY_ATTEMPTS
        for entry_pos in ring_positions:
            if self.target_kind == TARGET_FOUNDRY_ROUTE and time.perf_counter() - plan_start > 0.018:
                break
            if not self.route_tile_ok(c, entry_pos):
                continue
            if not self.foundry_route_entry_ok(entry_pos):
                continue
            attempts += 1
            if attempts > max_attempts:
                break
            entry_idx = self.pos_to_idx(entry_pos)
            route = self.find_route_path(c, entry_idx)
            if route is None:
                continue
            route_nodes, route_edges = route
            stage_idx = self.choose_stage_idx(c, target_pos, entry_idx)
            return entry_idx, stage_idx, route_nodes, route_edges
        return None

    def initial_travel_goals(
        self, c: Controller, target_kind: str, target_pos: Position, stage_idx: int
    ) -> set[int]:
        target_idx = self.pos_to_idx(target_pos)
        building_type = self.known_building_type[target_idx]
        building_mine = self.known_building_mine[target_idx]
        if target_kind == TARGET_ORE and building_type is not None:
            if building_type == EntityType.ROAD:
                return {target_idx}
            if building_mine is False and building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
                return {target_idx}
        return {stage_idx}

    def handle_travel(self, c: Controller) -> bool:
        if self.target_idx is None:
            self.reset_target()
            return False
        target_pos = self.idx_to_pos(self.target_idx)
        goals = self.initial_travel_goals(c, self.target_kind, target_pos, self.stage_idx)
        if self.pos_to_idx(c.get_position()) in goals:
            self.state = STATE_PREP
            self.clear_move_path()
            return False
        moved = self.move_toward_any(c, goals)
        if not moved and not self.find_builder_path(c, self.pos_to_idx(c.get_position()), goals):
            self.mark_bad_target(self.target_kind, self.target_idx)
            self.reset_target()
        return moved

    def handle_prep(self, c: Controller) -> bool:
        if self.target_idx is None:
            self.reset_target()
            return False
        if self.target_kind == TARGET_AXIONITE_ORE:
            return self.prepare_axionite_target(c)
        if self.target_kind == TARGET_AXIONITE_LINK:
            return self.prepare_axonite_link_route(c)
        if self.target_kind == TARGET_FOUNDRY_ROUTE:
            return self.prepare_foundry_route(c)
        if self.target_kind == TARGET_ATTACK_TITANIUM:
            return self.prepare_attack_titanium_target(c)
        if self.target_kind == TARGET_ORE:
            return self.prepare_ore_target(c)
        return self.prepare_enemy_harvester(c)

    def prepare_axionite_target(self, c: Controller) -> bool:
        ore_pos = self.idx_to_pos(self.target_idx)
        building_id = c.get_tile_building_id(ore_pos)
        current_idx = self.pos_to_idx(c.get_position())
        ore_idx = self.target_idx

        if building_id is not None:
            building_type = c.get_entity_type(building_id)
            building_team = c.get_team(building_id)
            if building_type == EntityType.HARVESTER:
                self.axionite_harvester_idx = ore_idx
                self.occupied_axionite.add(ore_idx)
                self.ax_state = AX_STATE_ROUTE_TITANIUM
                self.reset_target()
                return False
            if building_type == EntityType.ROAD and building_team == self.my_team:
                if current_idx != ore_idx and pos_distance_sq(c.get_position(), ore_pos) <= 2 and c.can_destroy(ore_pos):
                    c.destroy(ore_pos)
                    return True
                return self.move_toward_any(c, {self.stage_idx})
            if building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS or (
                building_type == EntityType.ROAD and building_team != self.my_team
            ):
                if current_idx == ore_idx:
                    if c.can_fire(c.get_position()):
                        c.fire(c.get_position())
                        return True
                    return False
                return self.move_toward_any(c, {ore_idx})
            self.mark_bad_target(TARGET_AXIONITE_ORE, ore_idx)
            self.reset_target()
            return False

        if current_idx == ore_idx:
            return self.move_off_current_tile(c, {self.stage_idx})
        if current_idx != self.stage_idx:
            return self.move_toward_any(c, {self.stage_idx})
        if c.can_build_harvester(ore_pos):
            c.build_harvester(ore_pos)
            self.axionite_harvester_idx = ore_idx
            self.occupied_axionite.add(ore_idx)
            self.ax_state = AX_STATE_ROUTE_TITANIUM
            self.reset_target()
            return True
        if self.wait_for_titanium_shortage(c, "get_harvester_cost"):
            return False
        self.mark_bad_target(TARGET_AXIONITE_ORE, ore_idx)
        self.reset_target()
        return False

    def prepare_foundry_route(self, c: Controller) -> bool:
        if not self.has_allied_building_at(c, self.target_idx, EntityType.FOUNDRY):
            self.ax_state = AX_STATE_BUILD_FOUNDRY
            self.reset_target()
            return False
        if self.pos_to_idx(c.get_position()) != self.stage_idx:
            return self.move_toward_any(c, {self.stage_idx})
        if not self.ensure_route_plan(c):
            return False
        self.state = STATE_BUILD_ROUTE
        return False

    def prepare_axonite_link_route(self, c: Controller) -> bool:
        if not self.has_axonite_source_at(c, self.target_idx):
            self.reset_axonite_mission()
            return False
        if self.axionite_foundry_idx is None or not self.configure_axonite_link_route_preferences(c):
            self.ax_state = AX_STATE_ROUTE_TITANIUM
            self.reset_target()
            return False
        if self.pos_to_idx(c.get_position()) != self.stage_idx:
            return self.move_toward_any(c, {self.stage_idx})
        if not self.ensure_route_plan(c):
            return False
        self.state = STATE_BUILD_ROUTE
        return False

    def prepare_ore_target(self, c: Controller) -> bool:
        ore_pos = self.idx_to_pos(self.target_idx)
        building_id = c.get_tile_building_id(ore_pos)
        current_idx = self.pos_to_idx(c.get_position())
        ore_idx = self.target_idx

        if building_id is not None:
            building_type = c.get_entity_type(building_id)
            building_team = c.get_team(building_id)
            if building_type == EntityType.HARVESTER:
                if building_team == self.my_team:
                    if current_idx == ore_idx:
                        return self.move_off_current_tile(c, {self.stage_idx})
                    if current_idx != self.stage_idx:
                        return self.move_toward_any(c, {self.stage_idx})
                    self.state = STATE_BUILD_ROUTE
                else:
                    self.mark_bad_target(TARGET_ORE, ore_idx)
                    self.reset_target()
                return False
            if building_type == EntityType.ROAD and building_team == self.my_team:
                if current_idx != ore_idx and pos_distance_sq(c.get_position(), ore_pos) <= 2 and c.can_destroy(ore_pos):
                    c.destroy(ore_pos)
                    return True
                return self.move_toward_any(c, {self.stage_idx})
            if building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS or (
                building_type == EntityType.ROAD and building_team != self.my_team
            ):
                if current_idx == ore_idx:
                    if c.can_fire(c.get_position()):
                        c.fire(c.get_position())
                        return True
                    return False
                return self.move_toward_any(c, {ore_idx})
            self.mark_bad_target(TARGET_ORE, ore_idx)
            self.reset_target()
            return False

        if current_idx == ore_idx:
            return self.move_off_current_tile(c, {self.stage_idx})

        if current_idx != self.stage_idx:
            return self.move_toward_any(c, {self.stage_idx})

        if not self.ensure_route_plan(c):
            return False

        if c.can_build_harvester(ore_pos):
            c.build_harvester(ore_pos)
            if (
                self.route_enable_ore_defenses
                and self.core_pos is not None
                and pos_distance_sq(self.core_pos, ore_pos) <= 250
            ):
                self.pending_ore_sentinels = self.compute_ore_sentinel_plan(ore_pos)
                self.pending_ore_outward_sentinel_idx = self.compute_ore_outward_sentinel_position(ore_pos)
            self.state = STATE_BUILD_ROUTE
            return True

        if c.get_tile_building_id(ore_pos) is not None:
            return False

        self.wait_for_titanium_shortage(c, "get_harvester_cost")
        return False

    def prepare_attack_titanium_target(self, c: Controller) -> bool:
        if self.target_idx is None:
            self.reset_target()
            return False
        ore_pos = self.idx_to_pos(self.target_idx)
        current_idx = self.pos_to_idx(c.get_position())
        ore_idx = self.target_idx

        if self.attack_sentinel_idx is None and not self.configure_attack_route_for_target(c, ore_pos):
            self.mark_bad_target(TARGET_ATTACK_TITANIUM, ore_idx)
            self.reset_target()
            return False

        building_id = c.get_tile_building_id(ore_pos)
        if building_id is not None:
            building_type = c.get_entity_type(building_id)
            building_team = c.get_team(building_id)
            if building_type == EntityType.HARVESTER:
                if self.attack_direct_feed:
                    self.state = STATE_ATTACK_SENTINEL
                    return False
                if not self.ensure_route_plan(c):
                    return False
                self.state = STATE_BUILD_ROUTE
                return False
            if building_type == EntityType.MARKER:
                pass
            elif building_type == EntityType.ROAD and building_team == self.my_team:
                if current_idx != ore_idx and pos_distance_sq(c.get_position(), ore_pos) <= 2 and c.can_destroy(ore_pos):
                    c.destroy(ore_pos)
                    return True
                return self.move_toward_any(c, {self.stage_idx})
            elif building_type == EntityType.ROAD and building_team != self.my_team:
                if current_idx == ore_idx:
                    if c.can_fire(c.get_position()):
                        if self.attack_break_target_is_healed(c, ore_pos):
                            self.mark_bad_target(TARGET_ATTACK_TITANIUM, ore_idx)
                            self.reset_target()
                            return False
                        c.fire(c.get_position())
                        return True
                    self.wait_for_titanium_amount(c, 2)
                    return False
                return self.move_toward_any(c, {ore_idx})
            else:
                self.mark_bad_target(TARGET_ATTACK_TITANIUM, ore_idx)
                self.reset_target()
                return False

        if current_idx == ore_idx:
            return self.move_off_current_tile(c, {self.stage_idx})
        if current_idx != self.stage_idx:
            return self.move_toward_any(c, {self.stage_idx})

        if not self.attack_direct_feed and not self.ensure_route_plan(c):
            return False

        if c.can_build_harvester(ore_pos):
            c.build_harvester(ore_pos)
            self.state = STATE_ATTACK_SENTINEL if self.attack_direct_feed else STATE_BUILD_ROUTE
            return True

        self.wait_for_titanium_shortage(c, "get_harvester_cost")
        return False

    def finish_attack_sentinel_placement(self) -> None:
        self.reset_target()
        self.reset_attack_break_tracking()
        self.attack_phase = ATTACK_PHASE_WANDER

    def handle_attack_build_sentinel(self, c: Controller) -> bool:
        if self.attack_sentinel_idx is None or self.attack_sentinel_dir is None:
            self.reset_target()
            return False
        sentinel_pos = self.idx_to_pos(self.attack_sentinel_idx)

        if pos_distance_sq(c.get_position(), sentinel_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(sentinel_pos))

        site_status, acted = self.prepare_sentinel_site(c, sentinel_pos)
        if site_status == "done":
            self.finish_attack_sentinel_placement()
            return acted
        if site_status == "blocked":
            self.mark_bad_target(self.target_kind, self.target_idx)
            self.reset_target()
            return acted
        if site_status == "wait":
            return acted

        if self.pos_to_idx(c.get_position()) == self.attack_sentinel_idx:
            return self.move_off_current_tile(c, self.build_vantage_goals(sentinel_pos))

        if c.can_build_sentinel(sentinel_pos, self.attack_sentinel_dir):
            c.build_sentinel(sentinel_pos, self.attack_sentinel_dir)
            self.finish_attack_sentinel_placement()
            return True

        self.wait_for_titanium_shortage(c, "get_sentinel_cost")
        return False

    def handle_attack_support_sentinel(self, c: Controller) -> bool:
        if self.attack_sentinel_idx is None:
            self.reset_target()
            self.attack_phase = ATTACK_PHASE_WANDER
            return False

        sentinel_pos = self.idx_to_pos(self.attack_sentinel_idx)
        if self.try_heal_attack_sentinel_network(c):
            return True

        if self.is_tile_visible_this_round(sentinel_pos):
            building_id = c.get_tile_building_id(sentinel_pos)
            if building_id is None:
                self.state = STATE_ATTACK_SENTINEL
                self.attack_phase = ATTACK_PHASE_BUILD_SENTINEL
                return self.handle_attack_build_sentinel(c)
            if c.get_team(building_id) != self.my_team or c.get_entity_type(building_id) != EntityType.SENTINEL:
                self.mark_bad_target(TARGET_ATTACK_TITANIUM, self.target_idx)
                self.reset_target()
                self.attack_phase = ATTACK_PHASE_WANDER
                return False

        goals = self.attack_support_goals()
        if goals and self.pos_to_idx(c.get_position()) not in goals:
            return self.move_toward_any(c, goals)
        return False

    def try_heal_attack_sentinel_network(self, c: Controller) -> bool:
        best: tuple[tuple[int, int, int, int], Position] | None = None
        my_pos = c.get_position()

        def consider(pos: Position, priority: int, entity_id: int | None = None) -> None:
            nonlocal best
            if not c.can_heal(pos):
                return
            missing = 1
            if entity_id is not None:
                missing = c.get_max_hp(entity_id) - c.get_hp(entity_id)
            elif pos == my_pos:
                missing = c.get_max_hp() - c.get_hp()
            score = (-priority, -missing, pos_distance_sq(my_pos, pos), self.pos_to_idx(pos))
            if best is None or score < best[0]:
                best = (score, pos)

        if c.get_hp() < c.get_max_hp():
            consider(my_pos, 4)

        important_indices: list[tuple[int, int]] = []
        if self.attack_sentinel_idx is not None:
            important_indices.append((self.attack_sentinel_idx, 6))
        if self.attack_feeder_idx is not None:
            important_indices.append((self.attack_feeder_idx, 5))
        for idx in reversed(self.route_nodes):
            if idx != self.attack_feeder_idx:
                important_indices.append((idx, 3))

        seen: set[int] = set()
        for idx, priority in important_indices:
            if idx in seen:
                continue
            seen.add(idx)
            pos = self.idx_to_pos(idx)
            if not self.in_bounds(pos) or not self.is_tile_visible_this_round(pos):
                continue
            building_id = c.get_tile_building_id(pos)
            if building_id is None or c.get_team(building_id) != self.my_team:
                continue
            building_type = c.get_entity_type(building_id)
            if building_type not in {EntityType.SENTINEL, EntityType.CONVEYOR, EntityType.BRIDGE, EntityType.SPLITTER, EntityType.HARVESTER}:
                continue
            if c.get_hp(building_id) < c.get_max_hp(building_id):
                consider(pos, priority, building_id)

        if best is None:
            return False
        c.heal(best[1])
        return True

    def attack_break_target_is_healed(self, c: Controller, target_pos: Position) -> bool:
        if self.role not in {ROLE_ATTACKER, ROLE_CORE_SIEGE_ATTACKER}:
            return False
        target_idx = self.pos_to_idx(target_pos)
        building_id = c.get_tile_building_id(target_pos)
        if building_id is None or c.get_team(building_id) == self.my_team:
            self.reset_attack_break_tracking()
            return False
        building_type = c.get_entity_type(building_id)
        if building_type not in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
            self.reset_attack_break_tracking()
            return False
        hp = c.get_hp(building_id)
        if self.attack_break_idx != target_idx:
            self.attack_break_idx = target_idx
            self.attack_break_last_hp = hp
            self.attack_break_stall_rounds = 0
            return False
        if self.attack_break_last_hp is not None and hp >= self.attack_break_last_hp:
            self.attack_break_stall_rounds += 1
        else:
            self.attack_break_stall_rounds = 0
        self.attack_break_last_hp = hp
        return self.attack_break_stall_rounds >= ATTACK_BREAK_HEAL_STALL_LIMIT

    def reset_attack_break_tracking(self) -> None:
        self.attack_break_idx = None
        self.attack_break_last_hp = None
        self.attack_break_stall_rounds = 0

    def attack_support_goals(self) -> set[int]:
        goals: set[int] = set()
        if self.attack_sentinel_idx is not None:
            goals.update(self.build_vantage_goals(self.idx_to_pos(self.attack_sentinel_idx)))
        if self.attack_feeder_idx is not None:
            goals.update(self.build_vantage_goals(self.idx_to_pos(self.attack_feeder_idx)))
        for idx in self.route_nodes[-3:]:
            goals.update(self.build_vantage_goals(self.idx_to_pos(idx)))
        return goals

    def prepare_enemy_harvester(self, c: Controller) -> bool:
        harvester_pos = self.idx_to_pos(self.target_idx)
        building_id = c.get_tile_building_id(harvester_pos)
        if building_id is None or c.get_entity_type(building_id) != EntityType.HARVESTER or c.get_team(building_id) == self.my_team:
            self.reset_target()
            return False

        for direction in ALL_DIRECTIONS:
            adj = harvester_pos.add(direction)
            if not self.in_bounds(adj):
                continue
            adj_building_id = c.get_tile_building_id(adj)
            if adj_building_id is None:
                continue
            adj_type = c.get_entity_type(adj_building_id)
            if adj_type not in CONVEYOR_SPLITTER_BRIDGE:
                continue
            if c.get_team(adj_building_id) == self.my_team:
                continue
            adj_idx = self.pos_to_idx(adj)
            if self.pos_to_idx(c.get_position()) == adj_idx:
                if c.can_fire(c.get_position()):
                    if self.attack_break_target_is_healed(c, adj):
                        self.mark_bad_target(self.target_kind, self.target_idx)
                        self.reset_target()
                        return False
                    c.fire(c.get_position())
                    return True
                self.wait_for_titanium_amount(c, 2)
                return False
            return self.move_toward_any(c, {adj_idx})

        if self.pos_to_idx(c.get_position()) != self.stage_idx:
            return self.move_toward_any(c, {self.stage_idx})

        if not self.ensure_route_plan(c):
            return False

        self.state = STATE_BUILD_ROUTE
        return False

    def wait_for_axonite_final_link_validation(self, c: Controller) -> bool | None:
        if (
            self.role != ROLE_AXONITE_HUNTER
            or self.ax_state != AX_STATE_ROUTE_TITANIUM
            or self.target_kind != TARGET_AXIONITE_LINK
            or not self.route_nodes
            or self.route_build_index < len(self.route_nodes) - 1
        ):
            return None
        if self.axionite_foundry_idx is None:
            self.abandon_axonite_foundry_conveyor()
            return False
        foundry_pos = self.idx_to_pos(self.axionite_foundry_idx)
        if pos_distance_sq(c.get_position(), foundry_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(foundry_pos))
        status = self.observe_axonite_foundry_conveyor(c)
        if status == "done":
            self.reset_axonite_mission(revert_role=True)
            return False
        if status == "bad":
            self.abandon_axonite_foundry_conveyor()
            return False
        if self.axionite_conveyor_validate_rounds < AXONITE_CONVEYOR_VALIDATE_ROUNDS:
            return False
        return None

    def handle_build_route(self, c: Controller) -> bool:
        if self.target_idx is None or self.entry_idx is None:
            self.reset_target()
            return False

        if not self.ensure_route_plan(c):
            return False

        if self.route_build_index >= len(self.route_nodes):
            if self.pending_splitter_sentinels:
                self.state = STATE_SPLITTER_SENTINELS
                return self.handle_splitter_sentinels(c)
            if self.target_kind == TARGET_ORE and self.pending_ore_sentinels:
                return self.place_next_ore_sentinel(c)
            if self.target_kind == TARGET_ORE and self.pending_ore_outward_sentinel_idx is not None:
                return self.place_ore_outward_sentinel(c)
            self.complete_active_route()
            return False

        axonite_wait = self.wait_for_axonite_final_link_validation(c)
        if axonite_wait is not None:
            return axonite_wait

        build_idx = self.route_nodes[self.route_build_index]
        build_pos = self.idx_to_pos(build_idx)
        current_idx = self.pos_to_idx(c.get_position())

        if current_idx == build_idx:
            build_tile_id = c.get_tile_building_id(build_pos)
            if build_tile_id is not None:
                build_tile_type = c.get_entity_type(build_tile_id)
                if c.get_team(build_tile_id) != self.my_team and build_tile_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
                    if c.can_fire(c.get_position()):
                        if self.attack_break_target_is_healed(c, build_pos):
                            self.mark_bad_target(self.target_kind, self.target_idx)
                            self.reset_target()
                            return False
                        c.fire(c.get_position())
                        return True
                    self.wait_for_titanium_amount(c, 2)
                    return False
            return self.move_off_current_tile(c, self.build_vantage_goals(build_pos))

        if pos_distance_sq(c.get_position(), build_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(build_pos))

        if not self.ensure_build_tile_clear(c, build_pos):
            return False

        if self.pos_to_idx(c.get_position()) == build_idx:
            return self.move_off_current_tile(c, self.build_vantage_goals(build_pos))

        built = self.build_route_piece(c, build_pos)
        if built:
            self.route_build_index += 1
            if self.route_build_index >= len(self.route_nodes):
                if self.pending_splitter_sentinels:
                    self.state = STATE_SPLITTER_SENTINELS
                elif self.target_kind == TARGET_ORE and (
                    self.pending_ore_sentinels or self.pending_ore_outward_sentinel_idx is not None
                ):
                    self.state = STATE_BUILD_ROUTE
                else:
                    self.complete_active_route()
            return True
        return False

    def handle_splitter_sentinels(self, c: Controller) -> bool:
        if not self.pending_splitter_sentinels:
            self.reset_target()
            return False
        if self.final_splitter_idx is None:
            self.reset_target()
            return False
        sentinel_idx = self.pending_splitter_sentinels[0]
        sentinel_pos = self.idx_to_pos(sentinel_idx)
        if pos_distance_sq(c.get_position(), sentinel_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(sentinel_pos))

        site_status, acted = self.prepare_sentinel_site(c, sentinel_pos)
        if site_status == "done":
            self.finish_splitter_sentinel()
            return acted
        if site_status == "blocked":
            self.finish_splitter_sentinel()
            return acted
        if site_status == "wait":
            return acted

        if self.pos_to_idx(c.get_position()) == sentinel_idx:
            return self.move_off_current_tile(c, self.build_vantage_goals(sentinel_pos))

        facing = self.choose_splitter_sentinel_facing(sentinel_pos)
        if c.can_build_sentinel(sentinel_pos, facing):
            c.build_sentinel(sentinel_pos, facing)
            self.finish_splitter_sentinel()
            return True

        self.wait_for_titanium_shortage(c, "get_sentinel_cost")
        return False

    def place_next_ore_sentinel(self, c: Controller) -> bool:
        ore_pos = self.idx_to_pos(self.target_idx)
        sentinel_idx = self.pending_ore_sentinels[0]
        sentinel_pos = self.idx_to_pos(sentinel_idx)

        if pos_distance_sq(c.get_position(), sentinel_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(sentinel_pos))

        site_status, acted = self.prepare_sentinel_site(c, sentinel_pos)
        if site_status == "done":
            self.finish_ore_sentinel()
            return acted
        if site_status == "blocked":
            self.finish_ore_sentinel()
            return acted
        if site_status == "wait":
            return acted

        if self.pos_to_idx(c.get_position()) == sentinel_idx:
            return self.move_off_current_tile(c, self.build_vantage_goals(sentinel_pos))

        facing = self.choose_ore_sentinel_facing(ore_pos, sentinel_pos)
        if c.can_build_sentinel(sentinel_pos, facing):
            c.build_sentinel(sentinel_pos, facing)
            self.finish_ore_sentinel()
            return True

        self.wait_for_titanium_shortage(c, "get_sentinel_cost")
        return False

    def build_route_piece(self, c: Controller, build_pos: Position) -> bool:
        node_index = self.route_build_index
        if node_index < len(self.route_edges):
            edge_kind = self.route_edges[node_index]
            if edge_kind == EDGE_BRIDGE:
                target_pos = self.idx_to_pos(self.route_nodes[node_index + 1])
                if c.can_build_bridge(build_pos, target_pos):
                    c.build_bridge(build_pos, target_pos)
                    return True
                self.wait_for_titanium_shortage(c, "get_bridge_cost")
                return False
            next_pos = self.idx_to_pos(self.route_nodes[node_index + 1])
            out_dir = cardinal_direction_between(build_pos, next_pos)
            if out_dir is None:
                return False
            if c.can_build_conveyor(build_pos, out_dir):
                c.build_conveyor(build_pos, out_dir)
                return True
            self.wait_for_titanium_shortage(c, "get_conveyor_cost")
            return False

        core_dir = self.current_route_goal_dir().get(self.route_nodes[-1])
        if core_dir is None:
            return False

        use_splitter = self.should_build_splitter()
        if use_splitter:
            if c.can_build_splitter(build_pos, core_dir):
                c.build_splitter(build_pos, core_dir)
                self.final_splitter_idx = self.route_nodes[-1]
                self.pending_splitter_sentinels = self.compute_splitter_sentinel_positions(build_pos, core_dir)
                return True
            self.wait_for_titanium_shortage(c, "get_splitter_cost")
            return False

        if c.can_build_conveyor(build_pos, core_dir):
            c.build_conveyor(build_pos, core_dir)
            return True
        self.wait_for_titanium_shortage(c, "get_conveyor_cost")
        return False

    def should_build_splitter(self) -> bool:
        if not self.route_allow_splitter:
            return False
        if len(self.route_nodes) < 2:
            return False
        final_idx = self.route_nodes[-1]
        core_dir = self.current_route_goal_dir().get(final_idx)
        if core_dir is None or self.route_edges[-1] != EDGE_CONVEYOR:
            return False
        final_pos = self.idx_to_pos(final_idx)
        previous_pos = self.idx_to_pos(self.route_nodes[-2])
        return previous_pos == final_pos.add(opposite(core_dir))

    def compute_ore_sentinel_plan(self, ore_pos: Position) -> list[int]:
        entry_dir = self.ore_entry_direction(ore_pos)
        if entry_dir is not None:
            positions: list[int] = []
            for side_dir in (left_cardinal(entry_dir), right_cardinal(entry_dir)):
                pos = ore_pos.add(side_dir)
                if self.in_bounds(pos):
                    positions.append(self.pos_to_idx(pos))
            return positions
        if self.core_pos is None:
            return []
        candidates = []
        for direction in CARDINAL_DIRECTIONS:
            pos = ore_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            idx = self.pos_to_idx(pos)
            if idx == self.entry_idx:
                continue
            score = (-manhattan(pos, self.core_pos), chebyshev(pos, ore_pos))
            candidates.append((score, idx))
        candidates.sort()
        return [idx for _, idx in candidates[:2]]

    def compute_ore_outward_sentinel_position(self, ore_pos: Position) -> int | None:
        entry_dir = self.ore_entry_direction(ore_pos)
        if entry_dir is not None:
            pos = ore_pos.add(opposite(entry_dir))
            return self.pos_to_idx(pos) if self.in_bounds(pos) else None
        sentinel_set = set(self.compute_ore_sentinel_plan(ore_pos))
        for direction in CARDINAL_DIRECTIONS:
            pos = ore_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            idx = self.pos_to_idx(pos)
            if idx == self.entry_idx or idx in sentinel_set:
                continue
            return idx
        return None

    def ore_entry_direction(self, ore_pos: Position) -> Direction | None:
        if self.entry_idx is None:
            return None
        return cardinal_direction_between(ore_pos, self.idx_to_pos(self.entry_idx))

    def choose_ore_sentinel_facing(self, ore_pos: Position, sentinel_pos: Position) -> Direction:
        if (
            self.pending_ore_outward_sentinel_idx is not None
            and self.pos_to_idx(sentinel_pos) == self.pending_ore_outward_sentinel_idx
        ):
            outward = ore_pos.direction_to(sentinel_pos)
            if outward != Direction.CENTRE:
                return outward

        outward = ore_pos.direction_to(sentinel_pos)
        if outward not in CARDINAL_DIRECTIONS_SET:
            return outward

        if self.core_pos is None:
            base_dir = outward
        elif pos_distance_sq(ore_pos, self.core_pos) <= 30:
            base_dir = outward
        else:
            base_dir = opposite(outward)

        options = [rotate_direction(base_dir, -1), rotate_direction(base_dir, 1)]
        if self.core_pos is None:
            return options[0]

        chooser = max if base_dir == outward else min
        return chooser(
            options,
            key=lambda direction: (
                pos_distance_sq(sentinel_pos.add(direction), self.core_pos),
                manhattan(sentinel_pos.add(direction), self.core_pos),
            ),
        )

    def choose_splitter_sentinel_facing(self, sentinel_pos: Position) -> Direction:
        splitter_pos = self.idx_to_pos(self.final_splitter_idx)
        side_dir = splitter_pos.direction_to(sentinel_pos)
        core_dir = self.core_goal_dir.get(self.final_splitter_idx)
        if core_dir is None:
            return side_dir
        away_from_core = opposite(core_dir)
        if side_dir == left_cardinal(core_dir):
            return rotate_direction(away_from_core, -1)
        if side_dir == right_cardinal(core_dir):
            return rotate_direction(away_from_core, 1)
        return side_dir

    def compute_splitter_sentinel_positions(self, splitter_pos: Position, core_dir: Direction) -> list[int]:
        positions: list[int] = []
        for side_dir in (left_cardinal(core_dir), right_cardinal(core_dir)):
            pos = splitter_pos.add(side_dir)
            if not self.in_bounds(pos):
                continue
            positions.append(self.pos_to_idx(pos))
        return positions

    def place_ore_outward_sentinel(self, c: Controller) -> bool:
        sentinel_pos = self.idx_to_pos(self.pending_ore_outward_sentinel_idx)
        sentinel_idx = self.pending_ore_outward_sentinel_idx
        current_idx = self.pos_to_idx(c.get_position())

        if pos_distance_sq(c.get_position(), sentinel_pos) > 2:
            return self.move_toward_any(c, self.build_vantage_goals(sentinel_pos))

        building_id = c.get_tile_building_id(sentinel_pos)
        if building_id is not None:
            building_type = c.get_entity_type(building_id)
            building_team = c.get_team(building_id)
            if building_type == EntityType.SENTINEL and building_team == self.my_team:
                self.pending_ore_outward_sentinel_idx = None
                return False
            if building_type == EntityType.MARKER:
                pass
            elif building_team == self.my_team and building_type == EntityType.ROAD:
                if c.can_destroy(sentinel_pos):
                    c.destroy(sentinel_pos)
                    return True
                return False
            elif building_type == EntityType.ROAD or building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
                if current_idx == sentinel_idx:
                    if c.can_fire(c.get_position()):
                        c.fire(c.get_position())
                        return True
                    return False
                return self.move_toward_any(c, {sentinel_idx})
            self.pending_ore_outward_sentinel_idx = None
            return False

        if c.get_tile_env(sentinel_pos) == Environment.WALL:
            self.pending_ore_outward_sentinel_idx = None
            return False
        if current_idx == sentinel_idx:
            return self.move_off_current_tile(c, self.build_vantage_goals(sentinel_pos))

        ore_pos = self.idx_to_pos(self.target_idx)
        facing = self.choose_ore_sentinel_facing(ore_pos, sentinel_pos)
        if c.can_build_sentinel(sentinel_pos, facing):
            c.build_sentinel(sentinel_pos, facing)
            self.pending_ore_outward_sentinel_idx = None
            return True
        self.wait_for_titanium_shortage(c, "get_sentinel_cost")
        return False

    def ensure_build_tile_clear(self, c: Controller, build_pos: Position) -> bool:
        building_id = c.get_tile_building_id(build_pos)
        current_idx = self.pos_to_idx(c.get_position())
        build_idx = self.pos_to_idx(build_pos)
        if building_id is None:
            return True

        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)

        if building_type in ALLY_REPLACEABLE_ROUTE_BUILDINGS and building_team == self.my_team:
            if pos_distance_sq(c.get_position(), build_pos) <= 2 and c.can_destroy(build_pos):
                c.destroy(build_pos)
                return False
            return False

        if building_team != self.my_team and building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
            if current_idx == build_idx:
                if c.can_fire(c.get_position()):
                    if self.attack_break_target_is_healed(c, build_pos):
                        self.mark_bad_target(self.target_kind, self.target_idx)
                        self.reset_target()
                        return False
                    c.fire(c.get_position())
                    return False
                self.wait_for_titanium_amount(c, 2)
                return False
            self.move_toward_any(c, {build_idx})
            return False

        if building_type == EntityType.MARKER:
            return True

        if self.route_build_index == 0:
            route = self.find_route_path(c, self.entry_idx)
            if route is not None:
                self.route_nodes, self.route_edges = route
                self.route_build_index = 0
                self.route_ready = True
                return False

        self.mark_bad_target(self.target_kind, self.target_idx)
        self.reset_target()
        return False

    def wander_step(self, c: Controller) -> bool:
        if self.primary_direction is None:
            self.primary_direction = Direction.NORTH

        current_pos = c.get_position()
        forward_pos = current_pos.add(self.primary_direction)
        if self.in_bounds(forward_pos) and self.builder_tile_ok(c, forward_pos):
            if self.try_move_into(c, forward_pos, self.primary_direction):
                return True

        turn = 1 if ((self.current_round + c.get_id() + current_pos.x + current_pos.y) & 1) == 0 else -1
        attempts = [turn, 2 * turn, 3 * turn, 4, -turn, -2 * turn, -3 * turn]
        for step in attempts:
            try_dir = rotate_direction(self.primary_direction, step)
            next_pos = current_pos.add(try_dir)
            if not self.in_bounds(next_pos):
                continue
            if not self.builder_tile_ok(c, next_pos):
                continue
            if self.try_move_into(c, next_pos, try_dir):
                self.primary_direction = try_dir
                return True
        return False

    def try_move_into(self, c: Controller, next_pos: Position, move_dir: Direction) -> bool:
        try:
            building_id = c.get_tile_building_id(next_pos)
            if building_id is None or c.get_entity_type(building_id) == EntityType.MARKER:
                if c.can_build_road(next_pos):
                    c.build_road(next_pos)
            if c.can_move(move_dir):
                c.move(move_dir)
                return True
        except Exception:
            self.clear_move_path()
        return False

    def move_off_current_tile(self, c: Controller, preferred_goals: set[int]) -> bool:
        current_idx = self.pos_to_idx(c.get_position())
        if current_idx in preferred_goals:
            preferred_goals = {idx for idx in preferred_goals if idx != current_idx}
        if not preferred_goals:
            for direction in ALL_DIRECTIONS:
                pos = c.get_position().add(direction)
                if not self.in_bounds(pos):
                    continue
                if self.builder_tile_ok(c, pos):
                    preferred_goals.add(self.pos_to_idx(pos))
        return self.move_toward_any(c, preferred_goals)

    def move_toward_any(self, c: Controller, goals: set[int]) -> bool:
        if not goals:
            return False
        current_idx = self.pos_to_idx(c.get_position())
        valid_goals = {
            idx
            for idx in goals
            if idx == current_idx or self.builder_tile_ok(c, self.idx_to_pos(idx))
        }
        if not valid_goals:
            return False
        if current_idx in valid_goals:
            self.clear_move_path()
            return False

        signature = tuple(sorted(valid_goals))
        if not self.move_path or self.move_goal_signature != signature or self.move_path[0] != current_idx:
            path = self.find_builder_path(c, current_idx, valid_goals)
            if not path:
                self.clear_move_path()
                return self.fallback_move_toward_any(c, valid_goals)
            self.move_path = path
            self.move_goal_signature = signature

        if len(self.move_path) < 2:
            self.clear_move_path()
            return self.fallback_move_toward_any(c, valid_goals)

        next_idx = self.move_path[1]
        next_pos = self.idx_to_pos(next_idx)
        move_dir = c.get_position().direction_to(next_pos)
        if self.try_move_into(c, next_pos, move_dir):
            self.move_path = self.move_path[1:]
            return True

        self.clear_move_path()
        return self.fallback_move_toward_any(c, valid_goals)

    def clear_move_path(self) -> None:
        self.move_path = []
        self.move_goal_signature = ()

    def fallback_move_toward_any(self, c: Controller, goals: set[int]) -> bool:
        if not goals:
            return False
        current_pos = c.get_position()
        goal_pos = self.closest_goal_position(goals, current_pos)
        preferred_dir = current_pos.direction_to(goal_pos)
        directions = [preferred_dir]
        if preferred_dir != Direction.CENTRE:
            directions.extend(
                [
                    preferred_dir.rotate_left(),
                    preferred_dir.rotate_right(),
                    preferred_dir.rotate_left().rotate_left(),
                    preferred_dir.rotate_right().rotate_right(),
                ]
            )

        seen: set[Direction] = set()
        for direction in directions:
            if direction == Direction.CENTRE or direction in seen:
                continue
            seen.add(direction)
            next_pos = current_pos.add(direction)
            if not self.in_bounds(next_pos):
                continue
            if self.try_move_into(c, next_pos, direction):
                return True

        for direction in ALL_DIRECTIONS:
            if direction in seen:
                continue
            next_pos = current_pos.add(direction)
            if not self.in_bounds(next_pos):
                continue
            if self.try_move_into(c, next_pos, direction):
                return True
        return False

    def closest_goal_position(self, goals: set[int], current_pos: Position) -> Position:
        best_idx = min(goals, key=lambda idx: chebyshev(current_pos, self.idx_to_pos(idx)))
        return self.idx_to_pos(best_idx)

    def update_stuck(self, c: Controller, took_action: bool) -> None:
        current_idx = self.pos_to_idx(c.get_position())
        if took_action or self.waiting_for_titanium:
            self.stuck_rounds = 0
        elif self.last_position_idx == current_idx and self.target_idx is not None:
            self.stuck_rounds += 1
        else:
            self.stuck_rounds = 0
        self.last_position_idx = current_idx

        if self.target_idx is not None and self.stuck_rounds >= TARGET_STUCK_LIMIT:
            self.mark_bad_target(self.target_kind, self.target_idx)
            self.reset_target()

    def reset_target(self) -> None:
        self.state = STATE_WANDER
        self.target_kind = None
        self.target_idx = None
        self.entry_idx = None
        self.stage_idx = None
        self.route_nodes = []
        self.route_edges = []
        self.route_build_index = 0
        self.route_ready = False
        self.pending_ore_sentinels = []
        self.pending_ore_outward_sentinel_idx = None
        self.pending_splitter_sentinels = []
        self.final_splitter_idx = None
        self.clear_route_preferences()
        self.clear_move_path()
        self.stuck_rounds = 0
        self.waiting_for_titanium = False
        if self.role == ROLE_ATTACKER:
            self.reset_attack_build_plan()
        if self.role == ROLE_CORE_SIEGE_ATTACKER:
            self.reset_attack_build_plan()

    def complete_active_route(self) -> None:
        if self.role == ROLE_ATTACKER and self.target_kind == TARGET_ATTACK_TITANIUM:
            self.state = STATE_ATTACK_SENTINEL
            self.clear_move_path()
            return
        if self.role == ROLE_AXONITE_HUNTER:
            if self.ax_state == AX_STATE_ROUTE_TITANIUM:
                self.ax_state = AX_STATE_BUILD_FOUNDRY
                self.state = STATE_WANDER
                self.clear_move_path()
                return
            elif self.ax_state == AX_STATE_ROUTE_CORE:
                self.reset_axonite_mission(revert_role=True)
                return
        self.reset_target()

    def mark_bad_target(self, target_kind: str | None, target_idx: int | None) -> None:
        if target_kind is None or target_idx is None:
            return
        self.bad_targets.add((target_kind, target_idx))
        self.last_failed_idx = target_idx

    def finish_splitter_sentinel(self) -> None:
        self.pending_splitter_sentinels.pop(0)
        if not self.pending_splitter_sentinels:
            if self.target_kind == TARGET_ORE and (
                self.pending_ore_sentinels or self.pending_ore_outward_sentinel_idx is not None
            ):
                self.state = STATE_BUILD_ROUTE
                return
            self.reset_target()

    def finish_ore_sentinel(self) -> None:
        self.pending_ore_sentinels.pop(0)
        if not self.pending_ore_sentinels:
            self.state = STATE_BUILD_ROUTE

    def get_titanium_cost(self, c: Controller, getter_name: str) -> int | None:
        getter = getattr(c, getter_name, None)
        if getter is None:
            return None
        cost = getter()
        if isinstance(cost, tuple):
            return cost[0]
        if isinstance(cost, list):
            return cost[0] if cost else None
        if isinstance(cost, int):
            return cost
        return None

    def wait_for_titanium_shortage(self, c: Controller, getter_name: str) -> bool:
        cost_ti = self.get_titanium_cost(c, getter_name)
        if cost_ti is None:
            return False
        return self.wait_for_titanium_amount(c, cost_ti)

    def wait_for_titanium_amount(self, c: Controller, cost_ti: int) -> bool:
        titanium, _ = c.get_global_resources()
        if titanium >= cost_ti:
            return False
        self.waiting_for_titanium = True
        return True

    def prepare_sentinel_site(self, c: Controller, sentinel_pos: Position) -> tuple[str, bool]:
        sentinel_idx = self.pos_to_idx(sentinel_pos)
        current_idx = self.pos_to_idx(c.get_position())
        builder_id = c.get_tile_builder_bot_id(sentinel_pos)
        if builder_id is not None and current_idx != sentinel_idx:
            return "wait", False

        building_id = c.get_tile_building_id(sentinel_pos)
        if building_id is None:
            env = c.get_tile_env(sentinel_pos)
            if env != Environment.WALL:
                return "ready", False
            return "blocked", False

        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)

        if building_type == EntityType.SENTINEL and building_team == self.my_team:
            return "done", False
        if building_type == EntityType.MARKER:
            return "ready", False
        if building_team == self.my_team and building_type in {EntityType.ROAD, EntityType.BARRIER}:
            if c.can_destroy(sentinel_pos):
                c.destroy(sentinel_pos)
                return "wait", True
            return "wait", False
        if building_team != self.my_team and (
            building_type == EntityType.ROAD or building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS
        ):
            if current_idx == sentinel_idx:
                if c.can_fire(c.get_position()):
                    if self.attack_break_target_is_healed(c, sentinel_pos):
                        return "blocked", False
                    c.fire(c.get_position())
                    return "wait", True
                self.wait_for_titanium_amount(c, 2)
                return "wait", False
            return "wait", self.move_toward_any(c, {sentinel_idx})
        return "blocked", False

    def role_debug_style(self) -> tuple[tuple[int, int, int] | None, Direction]:
        if self.role == ROLE_MINER:
            return COLOR_ROLE_MINER, Direction.NORTH
        if self.role == ROLE_GUARDIAN:
            return COLOR_ROLE_GUARDIAN, Direction.EAST
        if self.role == ROLE_ATTACKER:
            return COLOR_ROLE_ATTACKER, Direction.SOUTH
        if self.role == ROLE_CORE_SIEGE_ATTACKER:
            return COLOR_ROLE_CORE_SIEGE_ATTACKER, Direction.SOUTHEAST
        if self.role == ROLE_AXONITE_HUNTER:
            return COLOR_ROLE_AXONITE, Direction.NORTHEAST
        if self.role == ROLE_HUNTER:
            return COLOR_ROLE_HUNTER, Direction.WEST
        return None, Direction.CENTRE

    def debug_nearest_indices(
        self, origin: Position, indices: set[int], limit: int = 8, max_dist_sq: int = 400
    ) -> list[int]:
        best: list[tuple[tuple[int, int], int]] = []
        for idx in indices:
            pos = self.idx_to_pos(idx)
            dist_sq = pos_distance_sq(origin, pos)
            if dist_sq > max_dist_sq:
                continue
            score = (dist_sq, idx)
            if len(best) < limit:
                best.append((score, idx))
                continue
            worst_i = 0
            worst_score = best[0][0]
            for i in range(1, len(best)):
                if best[i][0] > worst_score:
                    worst_i = i
                    worst_score = best[i][0]
            if score < worst_score:
                best[worst_i] = (score, idx)
        best.sort()
        return [idx for _, idx in best]

    def draw_axonite_debug(self, c: Controller, my_pos: Position) -> None:
        for idx in self.debug_candidate_ores[:MAX_ORE_TARGET_ATTEMPTS]:
            c.draw_indicator_dot(self.idx_to_pos(idx), *COLOR_AXIONITE)
        for idx in self.debug_attempted_ores[:MAX_ORE_TARGET_ATTEMPTS]:
            c.draw_indicator_dot(self.idx_to_pos(idx), *COLOR_AXIONITE_ATTEMPT)
        for idx in self.debug_blocked_ores[:8]:
            c.draw_indicator_dot(self.idx_to_pos(idx), *COLOR_ORE_BLOCKED)

        unknown_conveyors = (
            self.seen_ally_conveyors
            - self.seen_ally_titanium_conveyors
            - self.seen_ally_axionite_conveyors
            - self.bad_axonite_foundry_sites
        )
        for idx in self.debug_nearest_indices(my_pos, unknown_conveyors, limit=6):
            c.draw_indicator_dot(self.idx_to_pos(idx), *COLOR_AXIONITE_UNKNOWN_CONVEYOR)
        for idx in self.debug_nearest_indices(my_pos, self.seen_ally_titanium_conveyors, limit=8):
            c.draw_indicator_dot(self.idx_to_pos(idx), *COLOR_AXIONITE_TITANIUM_CONVEYOR)
        for idx in self.debug_nearest_indices(my_pos, self.seen_ally_axionite_conveyors, limit=6):
            c.draw_indicator_dot(self.idx_to_pos(idx), *COLOR_AXIONITE_BAD_CONVEYOR)
        for idx in self.debug_nearest_indices(my_pos, self.bad_axonite_foundry_sites, limit=6):
            c.draw_indicator_dot(self.idx_to_pos(idx), *COLOR_FAILED)

        if self.axionite_harvester_idx is not None:
            source_pos = self.idx_to_pos(self.axionite_harvester_idx)
            c.draw_indicator_dot(source_pos, *COLOR_AXIONITE_SOURCE)
            c.draw_indicator_line(my_pos, source_pos, *COLOR_AXIONITE_SOURCE)

        if self.axionite_foundry_idx is not None:
            foundry_pos = self.idx_to_pos(self.axionite_foundry_idx)
            site_color = (
                COLOR_AXIONITE_READY_FOUNDRY
                if self.ax_state == AX_STATE_BUILD_FOUNDRY
                else COLOR_AXIONITE_FOUNDRY_SITE
            )
            c.draw_indicator_dot(foundry_pos, *site_color)
            c.draw_indicator_line(my_pos, foundry_pos, *site_color)
            if self.axionite_harvester_idx is not None:
                c.draw_indicator_line(self.idx_to_pos(self.axionite_harvester_idx), foundry_pos, *COLOR_AXIONITE_ROUTE_GOAL)
            progress_dirs = (
                Direction.NORTH,
                Direction.EAST,
                Direction.SOUTH,
                Direction.WEST,
                Direction.NORTHEAST,
            )
            progress = min(self.axionite_conveyor_validate_rounds, AXONITE_CONVEYOR_VALIDATE_ROUNDS)
            for i in range(progress):
                marker_pos = foundry_pos.add(progress_dirs[i])
                if self.in_bounds(marker_pos):
                    c.draw_indicator_dot(marker_pos, *COLOR_AXIONITE_VALIDATE)
            empty_dirs = (Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST)
            empty_marks = min(self.axionite_conveyor_empty_rounds, len(empty_dirs))
            for i in range(empty_marks):
                marker_pos = foundry_pos.add(empty_dirs[i])
                if self.in_bounds(marker_pos):
                    c.draw_indicator_dot(marker_pos, *COLOR_AXIONITE_EMPTY_WAIT)

        if self.target_idx is not None:
            target_pos = self.idx_to_pos(self.target_idx)
            target_color = COLOR_AXIONITE_SOURCE if self.target_kind == TARGET_AXIONITE_ORE else COLOR_AXIONITE_ROUTE_GOAL
            c.draw_indicator_dot(target_pos, *target_color)
            c.draw_indicator_line(my_pos, target_pos, *target_color)
        if self.entry_idx is not None:
            c.draw_indicator_dot(self.idx_to_pos(self.entry_idx), *COLOR_STAGE)
        if self.stage_idx is not None:
            c.draw_indicator_dot(self.idx_to_pos(self.stage_idx), *COLOR_STAGE)

        for goal_idx in self.route_goal_indices[:8]:
            c.draw_indicator_dot(self.idx_to_pos(goal_idx), *COLOR_AXIONITE_ROUTE_GOAL)

        if self.state == STATE_BUILD_ROUTE and self.route_build_index < len(self.route_nodes):
            next_build_pos = self.idx_to_pos(self.route_nodes[self.route_build_index])
            c.draw_indicator_line(my_pos, next_build_pos, *COLOR_ROUTE)
            c.draw_indicator_dot(next_build_pos, *COLOR_ROUTE)
            if self.route_build_index < len(self.route_edges) and self.route_edges[self.route_build_index] == EDGE_BRIDGE:
                bridge_target = self.idx_to_pos(self.route_nodes[self.route_build_index + 1])
                c.draw_indicator_line(next_build_pos, bridge_target, *COLOR_BRIDGE)

        if self.state == STATE_WANDER and self.primary_direction is not None:
            wander_pos = my_pos.add(self.primary_direction)
            if self.in_bounds(wander_pos):
                c.draw_indicator_line(my_pos, wander_pos, *COLOR_WANDER)

        if self.waiting_for_titanium:
            c.draw_indicator_dot(my_pos, *COLOR_WAIT)
        if self.stuck_rounds > 0:
            c.draw_indicator_dot(my_pos, *COLOR_STUCK)

    def draw_debug(self, c: Controller) -> None:
        my_pos = c.get_position()
        role_color, role_dir = self.role_debug_style()
        if role_color is not None:
            c.draw_indicator_dot(my_pos, *role_color)
            tip = my_pos.add(role_dir)
            if role_dir != Direction.CENTRE and self.in_bounds(tip):
                c.draw_indicator_line(my_pos, tip, *role_color)
        if self.role == ROLE_AXONITE_HUNTER:
            self.draw_axonite_debug(c, my_pos)
            return
        if self.role not in {ROLE_ATTACKER, ROLE_CORE_SIEGE_ATTACKER}:
            return

        enemy_core = self.current_enemy_core_guess()
        if enemy_core is not None:
            c.draw_indicator_line(my_pos, enemy_core, *COLOR_ENEMY)
            core_debug = self.attack_debug_core_tiles or [
                self.pos_to_idx(pos) for pos in self.get_core_footprint(enemy_core)
            ]
            for core_idx in core_debug[:9]:
                c.draw_indicator_dot(self.idx_to_pos(core_idx), *COLOR_CORE_THREAT)

        for ore_idx in self.debug_candidate_ores[:MAX_ORE_TARGET_ATTEMPTS]:
            c.draw_indicator_dot(self.idx_to_pos(ore_idx), *COLOR_ORE_CANDIDATE)
        for ore_idx in self.debug_attempted_ores[:MAX_ORE_TARGET_ATTEMPTS]:
            c.draw_indicator_dot(self.idx_to_pos(ore_idx), *COLOR_ORE_ATTEMPT)
        for ore_idx in self.debug_blocked_ores[:8]:
            c.draw_indicator_dot(self.idx_to_pos(ore_idx), *COLOR_ORE_BLOCKED)

        for sentinel_idx in self.attack_debug_sentinel_options[:8]:
            c.draw_indicator_dot(self.idx_to_pos(sentinel_idx), *COLOR_SENTINEL)

        if self.target_idx is not None:
            target_pos = self.idx_to_pos(self.target_idx)
            c.draw_indicator_line(my_pos, target_pos, *COLOR_ORE)
            c.draw_indicator_dot(target_pos, *COLOR_ORE)
        if self.entry_idx is not None:
            c.draw_indicator_dot(self.idx_to_pos(self.entry_idx), *COLOR_STAGE)
        if self.stage_idx is not None:
            c.draw_indicator_dot(self.idx_to_pos(self.stage_idx), *COLOR_STAGE)

        if self.attack_feeder_idx is not None:
            feeder_pos = self.idx_to_pos(self.attack_feeder_idx)
            c.draw_indicator_dot(feeder_pos, *COLOR_BRIDGE)
            if self.attack_sentinel_idx is not None:
                c.draw_indicator_line(feeder_pos, self.idx_to_pos(self.attack_sentinel_idx), *COLOR_BRIDGE)

        if self.attack_sentinel_idx is not None:
            sentinel_pos = self.idx_to_pos(self.attack_sentinel_idx)
            c.draw_indicator_dot(sentinel_pos, *COLOR_SENTINEL)
            if enemy_core is not None:
                c.draw_indicator_line(sentinel_pos, enemy_core, *COLOR_SENTINEL)
            if self.attack_sentinel_dir is not None:
                facing_tip = sentinel_pos.add(self.attack_sentinel_dir)
                if self.in_bounds(facing_tip):
                    c.draw_indicator_line(sentinel_pos, facing_tip, *COLOR_TURRET_TARGET)

        if self.state == STATE_BUILD_ROUTE and self.route_build_index < len(self.route_nodes):
            next_build_pos = self.idx_to_pos(self.route_nodes[self.route_build_index])
            c.draw_indicator_line(my_pos, next_build_pos, *COLOR_ROUTE)
            c.draw_indicator_dot(next_build_pos, *COLOR_ROUTE)
            if self.route_build_index < len(self.route_edges) and self.route_edges[self.route_build_index] == EDGE_BRIDGE:
                bridge_target = self.idx_to_pos(self.route_nodes[self.route_build_index + 1])
                c.draw_indicator_line(next_build_pos, bridge_target, *COLOR_BRIDGE)

        if self.state == STATE_WANDER and self.primary_direction is not None:
            wander_pos = my_pos.add(self.primary_direction)
            if self.in_bounds(wander_pos):
                c.draw_indicator_line(my_pos, wander_pos, *COLOR_WANDER)

        if self.waiting_for_titanium:
            c.draw_indicator_dot(my_pos, *COLOR_WAIT)
        if self.attack_stuck_rounds > 0:
            c.draw_indicator_dot(my_pos, *COLOR_STUCK)

    def find_allied_core(self, c: Controller) -> Position | None:
        for building_id in c.get_nearby_buildings():
            if c.get_entity_type(building_id) == EntityType.CORE and c.get_team(building_id) == self.my_team:
                return c.get_position(building_id)
        return None

    def infer_primary_direction(self, builder_pos: Position) -> Direction:
        dx = builder_pos.x - self.core_pos.x
        dy = builder_pos.y - self.core_pos.y
        if abs(dx) > abs(dy):
            return Direction.EAST if dx > 0 else Direction.WEST
        if dy != 0:
            return Direction.SOUTH if dy > 0 else Direction.NORTH
        return Direction.NORTH

    def octile_heuristic_to_goals(self, x: int, y: int, goal_points: tuple[tuple[int, int], ...]) -> int:
        best = 10**9
        for gx, gy in goal_points:
            dx = abs(x - gx)
            dy = abs(y - gy)
            heuristic = 10 * max(dx, dy) + 4 * min(dx, dy)
            if heuristic < best:
                best = heuristic
        return best

    def manhattan_heuristic_to_goals(self, x: int, y: int, goal_points: tuple[tuple[int, int], ...]) -> int:
        best = 10**9
        for gx, gy in goal_points:
            heuristic = 10 * (abs(x - gx) + abs(y - gy))
            if heuristic < best:
                best = heuristic
        return best

    def builder_path_extra_cost(self, idx: int, goal_set: set[int]) -> int | None:
        if self.known_builder_round[idx] == self.current_round and self.known_builder_present[idx]:
            if idx not in goal_set:
                return 50

        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        env = self.known_env[idx]

        if building_type is not None:
            if building_type == EntityType.MARKER:
                return 0 if env != Environment.WALL else None
            if building_type in WALKABLE_BUILDINGS:
                return 0
            if building_type == EntityType.CORE and building_mine:
                return 0
            return 0 if idx in goal_set else None

        if env == Environment.WALL:
            return None
        if env in ORE_ENVIRONMENTS and idx not in goal_set:
            return None
        return 0

    def route_path_extra_cost(self, idx: int, goal_set: set[int], x: int, y: int) -> int | None:
        if idx not in goal_set and self.core_pos is not None:
            if abs(x - self.core_pos.x) <= 1 and abs(y - self.core_pos.y) <= 1:
                return None
        if idx not in goal_set and self.role == ROLE_ATTACKER and self.target_kind == TARGET_ATTACK_TITANIUM:
            enemy_core = self.current_enemy_core_guess()
            if enemy_core is not None and abs(x - enemy_core.x) <= 1 and abs(y - enemy_core.y) <= 1:
                return None

        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        env = self.known_env[idx]

        if env in ORE_ENVIRONMENTS:
            return None
        if building_type is None:
            return 0 if env != Environment.WALL else None
        if building_type == EntityType.MARKER:
            return 0 if env != Environment.WALL else None
        if building_type == EntityType.ROAD:
            return 0
        if building_mine is False and building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
            return 8
        return None

    def find_builder_path(self, c: Controller, start_idx: int, goals: set[int]) -> list[int] | None:
        if not goals:
            return None
        astar_seen = self.astar_seen
        astar_closed = self.astar_closed
        astar_g = self.astar_g
        astar_parent = self.astar_parent
        known_builder_round = self.known_builder_round
        known_builder_present = self.known_builder_present
        known_building_type = self.known_building_type
        known_building_mine = self.known_building_mine
        known_env = self.known_env
        current_round = self.current_round
        width = self.width
        height = self.height
        _MARKER = EntityType.MARKER
        _WALL = Environment.WALL
        _ORE_TI = Environment.ORE_TITANIUM
        _ORE_AX = Environment.ORE_AXIONITE
        _CORE = EntityType.CORE
        goal_points = tuple((idx % width, idx // width) for idx in goals)
        self.astar_stamp += 1
        token = self.astar_stamp
        heap: list[tuple[int, int, int]] = []
        expansions = 0

        astar_seen[start_idx] = token
        astar_closed[start_idx] = 0
        astar_g[start_idx] = 0
        astar_parent[start_idx] = -1

        start_x = start_idx % width
        start_y = start_idx // width
        # inline octile heuristic for start
        best_h = 1000000000
        for gx, gy in goal_points:
            ddx = abs(start_x - gx); ddy = abs(start_y - gy)
            h = 10 * (ddx if ddx > ddy else ddy) + 4 * (ddy if ddx > ddy else ddx)
            if h < best_h: best_h = h
        heappush(heap, (best_h, 0, start_idx))

        search_start_time = time.perf_counter()
        while heap and expansions < BUILDER_PATH_MAX_NODES:
            if expansions % 100 == 0:
                if time.perf_counter() - search_start_time > 0.040:
                    break
            expansions += 1
            _, g_cost, current_idx = heappop(heap)
            if astar_closed[current_idx] == token:
                continue
            if current_idx in goals:
                return self.reconstruct_path(start_idx, current_idx)
            astar_closed[current_idx] = token
            current_x = current_idx % width
            current_y = current_idx // width

            for dx, dy, step_cost in BUILDER_PATH_OFFSETS:
                next_x = current_x + dx
                next_y = current_y + dy
                if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                    continue
                next_idx = next_y * width + next_x
                if astar_closed[next_idx] == token:
                    continue

                # inline builder_path_extra_cost
                extra = 0
                if known_builder_round[next_idx] == current_round and known_builder_present[next_idx]:
                    if next_idx not in goals:
                        extra = 50
                bt = known_building_type[next_idx]
                if bt is not None:
                    if bt == _MARKER:
                        if known_env[next_idx] == _WALL:
                            continue
                    elif bt not in WALKABLE_BUILDINGS:
                        if bt == _CORE and known_building_mine[next_idx]:
                            pass
                        elif next_idx not in goals:
                            continue
                else:
                    env = known_env[next_idx]
                    if env == _WALL:
                        continue
                    if (env == _ORE_TI or env == _ORE_AX) and next_idx not in goals:
                        continue

                next_g = g_cost + step_cost + extra
                if astar_seen[next_idx] != token or next_g < astar_g[next_idx]:
                    astar_seen[next_idx] = token
                    astar_g[next_idx] = next_g
                    astar_parent[next_idx] = current_idx
                    # inline octile heuristic
                    best_h = 1000000000
                    for gx, gy in goal_points:
                        ddx = abs(next_x - gx); ddy = abs(next_y - gy)
                        h = 10 * (ddx if ddx > ddy else ddy) + 4 * (ddy if ddx > ddy else ddx)
                        if h < best_h: best_h = h
                    heappush(heap, (next_g + best_h, next_g, next_idx))
        return None

    def find_route_path(self, c: Controller, start_idx: int) -> tuple[list[int], list[int]] | None:
        route_goals = self.current_route_goals()
        if not route_goals:
            return None
        astar_seen = self.astar_seen
        astar_closed = self.astar_closed
        astar_g = self.astar_g
        astar_parent = self.astar_parent
        astar_step = self.astar_step
        known_building_type = self.known_building_type
        known_building_mine = self.known_building_mine
        known_env = self.known_env
        width = self.width
        height = self.height
        core_pos = self.core_pos
        core_x = core_pos.x if core_pos is not None else -100
        core_y = core_pos.y if core_pos is not None else -100
        has_core = core_pos is not None
        attack_core = self.current_enemy_core_guess() if self.role == ROLE_ATTACKER and self.target_kind == TARGET_ATTACK_TITANIUM else None
        attack_core_x = attack_core.x if attack_core is not None else -100
        attack_core_y = attack_core.y if attack_core is not None else -100
        has_attack_core = attack_core is not None
        _MARKER = EntityType.MARKER
        _ROAD = EntityType.ROAD
        _WALL = Environment.WALL
        _ORE_TI = Environment.ORE_TITANIUM
        _ORE_AX = Environment.ORE_AXIONITE
        goal_set = set(route_goals)
        goal_points = tuple((idx % width, idx // width) for idx in route_goals)
        self.astar_stamp += 1
        token = self.astar_stamp
        heap: list[tuple[int, int, int]] = []
        expansions = 0

        astar_seen[start_idx] = token
        astar_closed[start_idx] = 0
        astar_g[start_idx] = 0
        astar_parent[start_idx] = -1
        astar_step[start_idx] = 0
        start_x = start_idx % width
        start_y = start_idx // width
        # inline manhattan heuristic for start
        best_h = 1000000000
        for gx, gy in goal_points:
            h = 10 * (abs(start_x - gx) + abs(start_y - gy))
            if h < best_h: best_h = h
        heappush(heap, (best_h, 0, start_idx))

        search_start_time = time.perf_counter()
        while heap and expansions < ROUTE_PATH_MAX_NODES:
            if expansions % 100 == 0:
                if time.perf_counter() - search_start_time > 0.040:
                    break
            expansions += 1
            _, g_cost, current_idx = heappop(heap)
            if astar_closed[current_idx] == token:
                continue
            if current_idx in goal_set:
                return self.reconstruct_route_path(start_idx, current_idx)
            astar_closed[current_idx] = token
            current_x = current_idx % width
            current_y = current_idx // width

            for dx, dy, step_cost in CARDINAL_PATH_OFFSETS:
                next_x = current_x + dx
                next_y = current_y + dy
                if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                    continue
                next_idx = next_y * width + next_x
                if astar_closed[next_idx] == token:
                    continue

                # inline route_path_extra_cost
                if next_idx not in goal_set and has_core:
                    if abs(next_x - core_x) <= 1 and abs(next_y - core_y) <= 1:
                        continue
                if next_idx not in goal_set and has_attack_core:
                    if abs(next_x - attack_core_x) <= 1 and abs(next_y - attack_core_y) <= 1:
                        continue
                bt = known_building_type[next_idx]
                extra = 0
                env = known_env[next_idx]
                if env == _ORE_TI or env == _ORE_AX:
                    continue
                if bt is None:
                    if env == _WALL:
                        continue
                elif bt == _MARKER:
                    if env == _WALL:
                        continue
                elif bt == _ROAD:
                    pass
                elif known_building_mine[next_idx] is False and bt in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
                    extra = 8
                else:
                    continue

                next_g = g_cost + step_cost + extra
                if astar_seen[next_idx] != token or next_g < astar_g[next_idx]:
                    astar_seen[next_idx] = token
                    astar_g[next_idx] = next_g
                    astar_parent[next_idx] = current_idx
                    astar_step[next_idx] = EDGE_CONVEYOR
                    # inline manhattan heuristic
                    best_h = 1000000000
                    for gx, gy in goal_points:
                        h = 10 * (abs(next_x - gx) + abs(next_y - gy))
                        if h < best_h: best_h = h
                    heappush(heap, (next_g + best_h, next_g, next_idx))

            for dx, dy in BRIDGE_DELTAS:
                next_x = current_x + dx
                next_y = current_y + dy
                if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                    continue
                next_idx = next_y * width + next_x
                if astar_closed[next_idx] == token:
                    continue

                # inline route_path_extra_cost
                if next_idx not in goal_set and has_core:
                    if abs(next_x - core_x) <= 1 and abs(next_y - core_y) <= 1:
                        continue
                if next_idx not in goal_set and has_attack_core:
                    if abs(next_x - attack_core_x) <= 1 and abs(next_y - attack_core_y) <= 1:
                        continue
                bt = known_building_type[next_idx]
                extra = 0
                env = known_env[next_idx]
                if env == _ORE_TI or env == _ORE_AX:
                    continue
                if bt is None:
                    if env == _WALL:
                        continue
                elif bt == _MARKER:
                    if env == _WALL:
                        continue
                elif bt == _ROAD:
                    pass
                elif known_building_mine[next_idx] is False and bt in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
                    extra = 8
                else:
                    continue

                next_g = g_cost + 32 + extra
                if astar_seen[next_idx] != token or next_g < astar_g[next_idx]:
                    astar_seen[next_idx] = token
                    astar_g[next_idx] = next_g
                    astar_parent[next_idx] = current_idx
                    astar_step[next_idx] = EDGE_BRIDGE
                    # inline manhattan heuristic
                    best_h = 1000000000
                    for gx, gy in goal_points:
                        h = 10 * (abs(next_x - gx) + abs(next_y - gy))
                        if h < best_h: best_h = h
                    heappush(heap, (next_g + best_h, next_g, next_idx))
        return None

    def reconstruct_path(self, start_idx: int, end_idx: int) -> list[int]:
        astar_parent = self.astar_parent
        path = [end_idx]
        current = end_idx
        while current != start_idx:
            current = astar_parent[current]
            path.append(current)
        path.reverse()
        return path

    def reconstruct_route_path(self, start_idx: int, end_idx: int) -> tuple[list[int], list[int]]:
        astar_parent = self.astar_parent
        astar_step = self.astar_step
        nodes = [end_idx]
        edges = []
        current = end_idx
        while current != start_idx:
            edges.append(astar_step[current])
            current = astar_parent[current]
            nodes.append(current)
        nodes.reverse()
        edges.reverse()
        return nodes, edges

    def build_vantage_goals(self, build_pos: Position) -> set[int]:
        goals: set[int] = set()
        bx = build_pos.x
        by = build_pos.y
        w = self.width
        h = self.height
        for dx, dy in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            nx = bx + dx
            ny = by + dy
            if 0 <= nx < w and 0 <= ny < h:
                goals.add(ny * w + nx)
        return goals

    def turret_probe_goals(self, c: Controller, turret_pos: Position) -> set[int]:
        goals = self.action_access_goals(c, turret_pos, allow_target_tile=False)
        if goals:
            return goals
        current_idx = self.pos_to_idx(c.get_position())
        return {
            idx
            for idx in self.build_vantage_goals(turret_pos)
            if idx != current_idx
        }

    def entry_tile_ok(self, c: Controller, pos: Position) -> bool:
        idx = self.pos_to_idx(pos)
        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        env = self.known_env[idx]
        if env in ORE_ENVIRONMENTS:
            return False
        if building_type is None:
            return env != Environment.WALL
        if building_type == EntityType.ROAD:
            return True
        if building_type == EntityType.MARKER:
            return env != Environment.WALL
        if building_mine is False and building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
            return True
        return False

    def builder_tile_ok(self, c: Controller, pos: Position) -> bool:
        if not self.in_bounds(pos):
            return False
        idx = self.pos_to_idx(pos)
        if self.known_builder_round[idx] == self.current_round and self.known_builder_present[idx]:
            return False
        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        env = self.known_env[idx]
        if building_type is not None:
            if building_type == EntityType.MARKER:
                return env != Environment.WALL
            if building_type in WALKABLE_BUILDINGS:
                return True
            if building_type == EntityType.CORE and building_mine:
                return True
            return False
        if env == Environment.WALL:
            return False
        if env is None:
            return True
        return env == Environment.EMPTY

    def route_tile_ok(self, c: Controller, pos: Position) -> bool:
        if not self.in_bounds(pos):
            return False
        if self.core_pos is not None:
            if abs(pos.x - self.core_pos.x) <= 1 and abs(pos.y - self.core_pos.y) <= 1:
                return False
        idx = self.pos_to_idx(pos)
        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        env = self.known_env[idx]
        if env in ORE_ENVIRONMENTS:
            return False
        if building_type is None:
            return env != Environment.WALL
        if building_type == EntityType.MARKER:
            return env != Environment.WALL
        if building_type == EntityType.ROAD:
            return True
        if building_mine is False and building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
            return True
        return False

    def is_titanium_occupied(self, c: Controller, ore_pos: Position) -> bool:
        if c.get_tile_env(ore_pos) != Environment.ORE_TITANIUM:
            return True
        if self.pos_to_idx(ore_pos) in self.occupied_titanium:
            return True
        return self.visible_titanium_is_occupied(c, ore_pos)

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def pos_to_idx(self, pos: Position) -> int:
        return pos.y * self.width + pos.x

    def idx_to_pos(self, idx: int) -> Position:
        return Position(idx % self.width, idx // self.width)

    def get_map_center(self) -> Position:
        return Position(self.width // 2, self.height // 2)
