from __future__ import annotations

import heapq

from cambc import Controller, Direction, EntityType, Environment, Position


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

WALKABLE_BUILDINGS = {
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE,
    EntityType.ROAD,
}
ENEMY_REPLACEABLE_ROUTE_BUILDINGS = {
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.ROAD,
}
ALLY_REPLACEABLE_ROUTE_BUILDINGS = {
    EntityType.ROAD,
    EntityType.MARKER,
}
ORE_OCCUPYING_BUILDINGS = {
    EntityType.HARVESTER,
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH,
    EntityType.LAUNCHER,
    EntityType.BARRIER,
    EntityType.FOUNDRY,
    EntityType.CORE,
}

STATE_WANDER = "wander"
STATE_TRAVEL = "travel"
STATE_PREP = "prep"
STATE_BUILD_ROUTE = "build_route"
STATE_SPLITTER_SENTINELS = "splitter_sentinels"

ROLE_MINER = "miner"
ROLE_GUARDIAN = "guardian"

GUARD_IDLE = "guard_idle"
GUARD_CORE_RESPONSE = "guard_core_response"
GUARD_RETURN_HEAL = "guard_return_heal"
GUARD_REPAIR = "guard_repair"

# ── Raider phases ──────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────


TARGET_ORE = "ore"
TARGET_ENEMY_HARVESTER = "enemy_harvester"

GUARD_TARGET_DESTROY_ALLY = "destroy_ally_supply"
GUARD_TARGET_DESTROY_ALLY_HARVESTER = "destroy_ally_harvester"
GUARD_TARGET_FIRE_ENEMY = "fire_enemy_supply"

EDGE_CONVEYOR = 1
EDGE_BRIDGE = 2
BRIDGE_EDGE_COST = 8

TARGET_STUCK_LIMIT = 10
MAX_ENTRY_ATTEMPTS = 4
MAX_ORE_TARGET_ATTEMPTS = 5
MAX_ENEMY_TARGET_ATTEMPTS = 2
BUILDER_PATH_MAX_NODES = 2200
ROUTE_PATH_MAX_NODES = 1800
GUARDIAN_IDLE_CAP = 4
GUARDIAN_REPAIR_COUNT = 2
GUARDIAN_SEARCH_STEP_LIMIT = 18
NEAR_CORE_REPAIR_DIST_SQ = 10
NEAR_CORE_DEFENDER_DIST_SQ = 25
OFFSCREEN_SCOUT_COUNT = 2
INITIAL_MINER_COUNT = 4
INITIAL_DEFENDER_COUNT = 1

TURRET_TYPES = {
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH,
}
DIRECT_SUPPLY_BUILDINGS = {
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.ARMOURED_CONVEYOR,
}
THREAT_FEED_BUILDINGS = {
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.HARVESTER,
    EntityType.FOUNDRY,
}
REPAIRABLE_NEAR_CORE_BUILDINGS = {
    EntityType.CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
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
        self.pending_splitter_sentinels: list[int] = []
        self.final_splitter_idx: int | None = None
        self.occupied_titanium: set[int] = set()
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
            self.known_env[idx] = c.get_tile_env(pos)
            building_id = c.get_tile_building_id(pos)
            if building_id is None:
                self.known_building_type[idx] = None
                self.known_building_mine[idx] = None
            else:
                self.known_building_type[idx] = c.get_entity_type(building_id)
                self.known_building_mine[idx] = c.get_team(building_id) == self.my_team
            self.known_builder_present[idx] = c.get_tile_builder_bot_id(pos) is not None
            self.known_builder_round[idx] = self.current_round

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

        attackers, neutralized_attackers = self.classify_enemy_turrets_attacking_core(c, core_pos)
        attacker = attackers[0] if attackers else None
        if attacker is not None:
            self.place_core_threat_marker(c, attacker[1])
        elif core_damaged and core_took_damage:
            self.place_offscreen_scout_marker(c)

        for _, turret_pos in attackers[:4]:
            c.draw_indicator_line(core_pos, turret_pos, *COLOR_CORE_THREAT)
            c.draw_indicator_dot(turret_pos, *COLOR_CORE_THREAT)
        for _, turret_pos in neutralized_attackers[:4]:
            c.draw_indicator_line(core_pos, turret_pos, *COLOR_NEUTRALIZED_THREAT)
            c.draw_indicator_dot(turret_pos, *COLOR_NEUTRALIZED_THREAT)

        damaged_near_core = self.find_damaged_near_core_buildings(c)
        for pos in damaged_near_core[:3]:
            c.draw_indicator_dot(pos, *COLOR_REPAIR)
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
            for direction in self.pick_guardian_spawn_directions(core_damaged, damaged_near_core):
                spawn_pos = core_pos.add(direction)
                if c.can_spawn(spawn_pos):
                    c.spawn_builder(spawn_pos)
                    return

        if self.spawn_initial_defender(c):
            return
        if self.spawn_initial_miners(c):
            return
        self.spawn_regular_builder(c)

    def run_builder(self, c: Controller) -> None:
        if self.core_pos is None:
            self.core_pos = self.find_allied_core(c)
            if self.core_pos is not None:
                self.ensure_core_goals()
        if self.role is None:
            self.initialize_builder_role(c)
        if self.role == ROLE_MINER:
            self.try_promote_miner_to_emergency_guardian(c)
        if self.role == ROLE_GUARDIAN:
            self.run_guardian(c)
            self.draw_debug(c)
            return
        if self.primary_direction is None and self.core_pos is not None:
            self.primary_direction = self.infer_primary_direction(c.get_position())
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

    def initialize_builder_role(self, c: Controller) -> None:
        if self.core_pos is None:
            self.role = ROLE_MINER
            return
        pos = c.get_position()
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
        scout_dir = self.select_offscreen_scout_direction()
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

        turret_pos = self.read_latest_core_threat_marker(c)
        if turret_pos is not None and self.is_selected_guardian_for(c, turret_pos, 1):
            self.begin_guardian_core_response(turret_pos, self.core_pos.direction_to(turret_pos))
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
        turret_pos = self.emergency_guardian_target(c)
        if turret_pos is None:
            return False
        self.activate_emergency_guardian(c, turret_pos)
        return True

    def emergency_guardian_target(self, c: Controller) -> Position | None:
        if self.core_pos is None or self.temporary_guardian:
            return None
        if not self.is_core_damaged(c):
            return None
        if pos_distance_sq(c.get_position(), self.core_pos) > NEAR_CORE_DEFENDER_DIST_SQ:
            return None
        visible_turrets = self.find_visible_turrets_attacking_core_from_guardian(c)
        if not visible_turrets:
            return None
        limit = min(len(visible_turrets), 2)
        for turret_pos in visible_turrets:
            if self.is_selected_emergency_guardian(c, turret_pos, limit):
                return turret_pos
        return None

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

    def activate_emergency_guardian(self, c: Controller, turret_pos: Position) -> None:
        self.reset_target()
        self.role = ROLE_GUARDIAN
        self.temporary_guardian = True
        self.home_wait_idx = self.pos_to_idx(c.get_position())
        self.begin_guardian_core_response(turret_pos, self.core_pos.direction_to(turret_pos))

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
        ordered = self.guardian_slot_order()
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
        self, core_damaged: bool, damaged_near_core: list[Position]
    ) -> list[Direction]:
        slots = self.guardian_slot_order()
        if core_damaged:
            return [self.core_pos.direction_to(pos) for pos in slots]
        if damaged_near_core:
            slots.sort(
                key=lambda pos: min(pos_distance_sq(pos, target) for target in damaged_near_core)
            )
        return [self.core_pos.direction_to(pos) for pos in slots]

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
        if slot_rank >= len(directions):
            return None
        return directions[slot_rank]

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
        best_target: Position | None = None
        blocked_target: Position | None = None
        for _, target_pos in self.collect_all_enemy_targets(c):
            if c.can_fire(target_pos):
                best_target = target_pos
                break
            if blocked_target is None:
                blocked_target = target_pos
        self.draw_turret_debug(c, best_target, blocked_target)
        if best_target is not None and c.can_fire(best_target):
            c.fire(best_target)

    def run_gunner(self, c: Controller) -> None:
        current_dir = c.get_direction()
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

    def collect_all_enemy_targets(
        self, c: Controller
    ) -> list[tuple[tuple[int, ...], Position]]:
        seen: dict[tuple[int, int], tuple[tuple[int, ...], Position]] = {}
        for entity_id in c.get_nearby_entities():
            if c.get_team(entity_id) == self.my_team:
                continue
            entity_type = c.get_entity_type(entity_id)
            if entity_type == EntityType.MARKER:
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
        my_pos = c.get_position()
        if facing_dir is None and c.get_entity_type() != EntityType.CORE:
            try:
                facing_dir = c.get_direction()
            except Exception:
                facing_dir = None
        if facing_dir is not None and facing_dir != Direction.CENTRE:
            facing_pos = my_pos.add(facing_dir)
            if self.in_bounds(facing_pos):
                c.draw_indicator_line(my_pos, facing_pos, *COLOR_WANDER)
        if target_pos is not None:
            c.draw_indicator_line(my_pos, target_pos, *COLOR_TURRET_TARGET)
            c.draw_indicator_dot(target_pos, *COLOR_TURRET_TARGET)
        if blocked_pos is not None:
            c.draw_indicator_line(my_pos, blocked_pos, *COLOR_TURRET_BLOCKED)
            c.draw_indicator_dot(blocked_pos, *COLOR_TURRET_BLOCKED)

    def get_attack_target_priority(self, entity_type: EntityType) -> int:
        if entity_type == EntityType.BUILDER_BOT:
            return 0
        if entity_type in TURRET_TYPES:
            return 1
        if entity_type == EntityType.CORE:
            return 2
        priorities = {
            EntityType.HARVESTER: 3,
            EntityType.FOUNDRY: 4,
            EntityType.CONVEYOR: 5,
            EntityType.SPLITTER: 6,
            EntityType.BRIDGE: 7,
            EntityType.ARMOURED_CONVEYOR: 8,
            EntityType.ROAD: 9,
            EntityType.BARRIER: 10,
        }
        return priorities.get(entity_type, 11)

    def acquire_target(self, c: Controller) -> bool:
        self.debug_candidate_ores = []
        self.debug_blocked_ores = []
        self.debug_attempted_ores = []

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
            if idx in self.occupied_titanium:
                continue
            if (TARGET_ENEMY_HARVESTER, idx) in self.bad_targets:
                continue
            score = chebyshev(c.get_position(), pos)
            enemy_candidates.append((score, manhattan(c.get_position(), pos), pos))
        enemy_candidates.sort()
        for _, _, harvester_pos in enemy_candidates[:MAX_ENEMY_TARGET_ATTEMPTS]:
            if self.plan_target(c, TARGET_ENEMY_HARVESTER, harvester_pos):
                return True

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
        self.pending_splitter_sentinels = []
        self.final_splitter_idx = None
        self.route_ready = False
        self.state = STATE_TRAVEL
        self.move_path = path
        self.move_goal_signature = tuple(sorted(goals))
        return True

    def choose_entry_stage(self, c: Controller, target_pos: Position) -> tuple[int, int] | None:
        ring_positions = []
        for direction in CARDINAL_DIRECTIONS:
            pos = target_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            ring_positions.append(pos)

        ring_positions.sort(
            key=lambda pos: (
                0 if self.entry_tile_ok(c, pos) else 1,
                manhattan(pos, self.core_pos) if self.core_pos is not None else 0,
                chebyshev(pos, c.get_position()),
            )
        )

        for entry_pos in ring_positions:
            if not self.entry_tile_ok(c, entry_pos):
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
        return True

    def choose_route_plan(
        self, c: Controller, target_pos: Position
    ) -> tuple[int, int, list[int], list[int]] | None:
        if self.core_pos is None:
            return None

        ring_positions = []
        for direction in CARDINAL_DIRECTIONS:
            pos = target_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            ring_positions.append(pos)

        ring_positions.sort(
            key=lambda pos: (manhattan(pos, self.core_pos), chebyshev(pos, c.get_position()))
        )

        attempts = 0
        for entry_pos in ring_positions:
            if not self.route_tile_ok(c, entry_pos):
                continue
            attempts += 1
            if attempts > MAX_ENTRY_ATTEMPTS:
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
        if self.target_kind == TARGET_ORE:
            return self.prepare_ore_target(c)
        return self.prepare_enemy_harvester(c)

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
            if self.core_pos is not None and pos_distance_sq(self.core_pos, ore_pos) <= 250:
                self.pending_ore_sentinels = self.compute_ore_sentinel_plan(ore_pos)
            self.state = STATE_BUILD_ROUTE
            return True

        if c.get_tile_building_id(ore_pos) is not None:
            return False

        self.mark_bad_target(TARGET_ORE, ore_idx)
        self.reset_target()
        return False

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
            if adj_type not in {
                EntityType.CONVEYOR,
                EntityType.SPLITTER,
                EntityType.BRIDGE,
            }:
                continue
            if c.get_team(adj_building_id) == self.my_team:
                continue
            adj_idx = self.pos_to_idx(adj)
            if self.pos_to_idx(c.get_position()) == adj_idx:
                if c.can_fire(c.get_position()):
                    c.fire(c.get_position())
                    return True
                return False
            return self.move_toward_any(c, {adj_idx})

        if self.pos_to_idx(c.get_position()) != self.stage_idx:
            return self.move_toward_any(c, {self.stage_idx})

        if not self.ensure_route_plan(c):
            return False

        self.state = STATE_BUILD_ROUTE
        return False

    def handle_build_route(self, c: Controller) -> bool:
        if self.target_idx is None or self.entry_idx is None:
            self.reset_target()
            return False

        if not self.ensure_route_plan(c):
            return False

        if self.target_kind == TARGET_ORE and self.pending_ore_sentinels:
            built = self.place_next_ore_sentinel(c)
            if self.pending_ore_sentinels:
                return built
            return built

        if self.route_build_index >= len(self.route_nodes):
            if self.pending_splitter_sentinels:
                self.state = STATE_SPLITTER_SENTINELS
                return False
            self.reset_target()
            return False

        build_idx = self.route_nodes[self.route_build_index]
        build_pos = self.idx_to_pos(build_idx)
        current_idx = self.pos_to_idx(c.get_position())

        if current_idx == build_idx:
            build_tile_id = c.get_tile_building_id(build_pos)
            if build_tile_id is not None:
                build_tile_type = c.get_entity_type(build_tile_id)
                if c.get_team(build_tile_id) != self.my_team and build_tile_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS:
                    if c.can_fire(c.get_position()):
                        c.fire(c.get_position())
                        return True
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
                else:
                    self.reset_target()
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

        core_dir = self.core_goal_dir.get(self.route_nodes[-1])
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
        if len(self.route_nodes) < 2:
            return False
        final_idx = self.route_nodes[-1]
        core_dir = self.core_goal_dir.get(final_idx)
        if core_dir is None or self.route_edges[-1] != EDGE_CONVEYOR:
            return False
        final_pos = self.idx_to_pos(final_idx)
        previous_pos = self.idx_to_pos(self.route_nodes[-2])
        return previous_pos == final_pos.add(opposite(core_dir))

    def compute_ore_sentinel_plan(self, ore_pos: Position) -> list[int]:
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
        ordered = [idx for _, idx in candidates]
        return ordered[:2]

    def choose_ore_sentinel_facing(self, ore_pos: Position, sentinel_pos: Position) -> Direction:
        outward = ore_pos.direction_to(sentinel_pos)
        if outward not in CARDINAL_DIRECTIONS:
            return outward

        if self.core_pos is None:
            base_dir = outward
        elif pos_distance_sq(ore_pos, self.core_pos) <= 50:
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
                    c.fire(c.get_position())
                    return False
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

        attempts = [0, 1, -1, 2, -2, 3, -3, 4]
        current_pos = c.get_position()
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
            self.move_path.pop(0)
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
        self.pending_splitter_sentinels = []
        self.final_splitter_idx = None
        self.clear_move_path()
        self.stuck_rounds = 0
        self.waiting_for_titanium = False

    def mark_bad_target(self, target_kind: str | None, target_idx: int | None) -> None:
        if target_kind is None or target_idx is None:
            return
        self.bad_targets.add((target_kind, target_idx))
        if target_kind == TARGET_ENEMY_HARVESTER and self.known_env[target_idx] == Environment.ORE_TITANIUM:
            self.occupied_titanium.add(target_idx)
        self.last_failed_idx = target_idx

    def finish_splitter_sentinel(self) -> None:
        self.pending_splitter_sentinels.pop(0)
        if not self.pending_splitter_sentinels:
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
        c.draw_indicator_dot(c.get_position(), *COLOR_WAIT)
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
            if env == Environment.EMPTY:
                return "ready", False
            return "blocked", False

        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)

        if building_type == EntityType.SENTINEL and building_team == self.my_team:
            return "done", False
        if building_type == EntityType.MARKER:
            return "ready", False
        if building_team == self.my_team and building_type == EntityType.ROAD:
            if c.can_destroy(sentinel_pos):
                c.destroy(sentinel_pos)
                return "wait", True
            return "wait", False
        if building_team != self.my_team and (
            building_type == EntityType.ROAD or building_type in ENEMY_REPLACEABLE_ROUTE_BUILDINGS
        ):
            if current_idx == sentinel_idx:
                if c.can_fire(c.get_position()):
                    c.fire(c.get_position())
                    return "wait", True
                return "wait", False
            return "wait", self.move_toward_any(c, {sentinel_idx})
        return "blocked", False

    def draw_debug(self, c: Controller) -> None:
        my_pos = c.get_position()
        if self.role == ROLE_GUARDIAN:
            if self.home_wait_idx is not None:
                c.draw_indicator_dot(self.idx_to_pos(self.home_wait_idx), *COLOR_STAGE)
            if self.temporary_guardian:
                c.draw_indicator_dot(my_pos, *COLOR_TEMP_GUARDIAN)
            if self.guard_turret_idx is not None:
                turret_pos = self.idx_to_pos(self.guard_turret_idx)
                c.draw_indicator_line(my_pos, turret_pos, *COLOR_ENEMY)
                c.draw_indicator_dot(turret_pos, *COLOR_ENEMY)
            if self.guard_target_idx is not None:
                c.draw_indicator_dot(self.idx_to_pos(self.guard_target_idx), *COLOR_ROUTE)
            if self.guard_build_idx is not None:
                c.draw_indicator_dot(self.idx_to_pos(self.guard_build_idx), *COLOR_SENTINEL)
            if self.guard_search_dir is not None:
                preview = my_pos.add(self.guard_search_dir)
                if self.in_bounds(preview):
                    c.draw_indicator_line(my_pos, preview, *COLOR_WANDER)
            if self.guard_mode == GUARD_RETURN_HEAL and self.core_pos is not None:
                c.draw_indicator_line(my_pos, self.core_pos, *COLOR_REPAIR)

        if self.target_idx is not None:
            target_pos = self.idx_to_pos(self.target_idx)
            if self.target_kind == TARGET_ORE:
                c.draw_indicator_line(my_pos, target_pos, *COLOR_ORE)
                c.draw_indicator_dot(target_pos, *COLOR_ORE)
            else:
                c.draw_indicator_line(my_pos, target_pos, *COLOR_ENEMY)
                c.draw_indicator_dot(target_pos, *COLOR_ENEMY)

        if self.stage_idx is not None:
            c.draw_indicator_dot(self.idx_to_pos(self.stage_idx), *COLOR_STAGE)
        if self.entry_idx is not None:
            c.draw_indicator_dot(self.idx_to_pos(self.entry_idx), *COLOR_STAGE)

        if self.state == STATE_BUILD_ROUTE and self.route_build_index < len(self.route_nodes):
            next_build_pos = self.idx_to_pos(self.route_nodes[self.route_build_index])
            c.draw_indicator_line(my_pos, next_build_pos, *COLOR_ROUTE)
            c.draw_indicator_dot(next_build_pos, *COLOR_ROUTE)
            if self.route_build_index < len(self.route_edges) and self.route_edges[self.route_build_index] == EDGE_BRIDGE:
                bridge_target = self.idx_to_pos(self.route_nodes[self.route_build_index + 1])
                c.draw_indicator_line(next_build_pos, bridge_target, *COLOR_BRIDGE)

        for sentinel_idx in self.pending_ore_sentinels[:2]:
            c.draw_indicator_dot(self.idx_to_pos(sentinel_idx), *COLOR_SENTINEL)
        for sentinel_idx in self.pending_splitter_sentinels[:2]:
            c.draw_indicator_dot(self.idx_to_pos(sentinel_idx), *COLOR_SENTINEL)

        if self.state == STATE_WANDER and self.primary_direction is not None:
            wander_pos = my_pos.add(self.primary_direction)
            if self.in_bounds(wander_pos):
                c.draw_indicator_line(my_pos, wander_pos, *COLOR_WANDER)

        for ore_idx in self.debug_blocked_ores[:10]:
            c.draw_indicator_dot(self.idx_to_pos(ore_idx), *COLOR_ORE_BLOCKED)
        for ore_idx in self.debug_candidate_ores[:MAX_ORE_TARGET_ATTEMPTS]:
            c.draw_indicator_dot(self.idx_to_pos(ore_idx), *COLOR_ORE_CANDIDATE)
        for ore_idx in self.debug_attempted_ores[:MAX_ORE_TARGET_ATTEMPTS]:
            c.draw_indicator_dot(self.idx_to_pos(ore_idx), *COLOR_ORE_ATTEMPT)

        if self.last_failed_idx is not None:
            failed_pos = self.idx_to_pos(self.last_failed_idx)
            c.draw_indicator_dot(failed_pos, *COLOR_FAILED)

        if self.stuck_rounds > 0:
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
        if env == Environment.ORE_TITANIUM and idx not in goal_set:
            return None
        return 0

    def route_path_extra_cost(self, idx: int, goal_set: set[int], x: int, y: int) -> int | None:
        if idx not in goal_set and self.core_pos is not None:
            if abs(x - self.core_pos.x) <= 1 and abs(y - self.core_pos.y) <= 1:
                return None

        building_type = self.known_building_type[idx]
        building_mine = self.known_building_mine[idx]
        env = self.known_env[idx]

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
        width = self.width
        height = self.height
        goal_points = tuple((idx % width, idx // width) for idx in goals)
        self.astar_stamp += 1
        token = self.astar_stamp
        heap: list[tuple[int, int, int]] = []
        expansions = 0

        self.astar_seen[start_idx] = token
        self.astar_closed[start_idx] = 0
        self.astar_g[start_idx] = 0
        self.astar_parent[start_idx] = -1
        self.astar_step[start_idx] = 0

        start_x = start_idx % width
        start_y = start_idx // width
        heapq.heappush(
            heap,
            (self.octile_heuristic_to_goals(start_x, start_y, goal_points), 0, start_idx),
        )

        while heap and expansions < BUILDER_PATH_MAX_NODES:
            expansions += 1
            _, g_cost, current_idx = heapq.heappop(heap)
            if self.astar_closed[current_idx] == token:
                continue
            if current_idx in goals:
                return self.reconstruct_path(start_idx, current_idx)
            self.astar_closed[current_idx] = token
            current_x = current_idx % width
            current_y = current_idx // width

            for dx, dy, step_cost in BUILDER_PATH_OFFSETS:
                next_x = current_x + dx
                next_y = current_y + dy
                if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                    continue
                next_idx = next_y * width + next_x
                if self.astar_closed[next_idx] == token:
                    continue
                extra_cost = self.builder_path_extra_cost(next_idx, goals)
                if extra_cost is None:
                    continue
                next_g = g_cost + step_cost + extra_cost
                if self.astar_seen[next_idx] != token or next_g < self.astar_g[next_idx]:
                    self.astar_seen[next_idx] = token
                    self.astar_g[next_idx] = next_g
                    self.astar_parent[next_idx] = current_idx
                    heuristic = self.octile_heuristic_to_goals(next_x, next_y, goal_points)
                    heapq.heappush(heap, (next_g + heuristic, next_g, next_idx))
        return None

    def find_route_path(self, c: Controller, start_idx: int) -> tuple[list[int], list[int]] | None:
        if not self.core_goals:
            return None
        width = self.width
        height = self.height
        goal_set = set(self.core_goals)
        goal_points = tuple((idx % width, idx // width) for idx in self.core_goals)
        self.astar_stamp += 1
        token = self.astar_stamp
        heap: list[tuple[int, int, int]] = []
        expansions = 0

        self.astar_seen[start_idx] = token
        self.astar_closed[start_idx] = 0
        self.astar_g[start_idx] = 0
        self.astar_parent[start_idx] = -1
        self.astar_step[start_idx] = 0
        start_x = start_idx % width
        start_y = start_idx // width
        heapq.heappush(
            heap,
            (self.manhattan_heuristic_to_goals(start_x, start_y, goal_points), 0, start_idx),
        )

        while heap and expansions < ROUTE_PATH_MAX_NODES:
            expansions += 1
            _, g_cost, current_idx = heapq.heappop(heap)
            if self.astar_closed[current_idx] == token:
                continue
            if current_idx in goal_set:
                return self.reconstruct_route_path(start_idx, current_idx)
            self.astar_closed[current_idx] = token
            current_x = current_idx % width
            current_y = current_idx // width

            for dx, dy, step_cost in CARDINAL_PATH_OFFSETS:
                next_x = current_x + dx
                next_y = current_y + dy
                if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                    continue
                next_idx = next_y * width + next_x
                if self.astar_closed[next_idx] == token:
                    continue
                extra_cost = self.route_path_extra_cost(next_idx, goal_set, next_x, next_y)
                if extra_cost is None:
                    continue
                next_g = g_cost + step_cost + extra_cost
                if self.astar_seen[next_idx] != token or next_g < self.astar_g[next_idx]:
                    self.astar_seen[next_idx] = token
                    self.astar_g[next_idx] = next_g
                    self.astar_parent[next_idx] = current_idx
                    self.astar_step[next_idx] = EDGE_CONVEYOR
                    heuristic = self.manhattan_heuristic_to_goals(next_x, next_y, goal_points)
                    heapq.heappush(heap, (next_g + heuristic, next_g, next_idx))

            for dx, dy in BRIDGE_DELTAS:
                next_x = current_x + dx
                next_y = current_y + dy
                if next_x < 0 or next_x >= width or next_y < 0 or next_y >= height:
                    continue
                next_idx = next_y * width + next_x
                if self.astar_closed[next_idx] == token:
                    continue
                extra_cost = self.route_path_extra_cost(next_idx, goal_set, next_x, next_y)
                if extra_cost is None:
                    continue
                next_g = g_cost + 32 + extra_cost
                if self.astar_seen[next_idx] != token or next_g < self.astar_g[next_idx]:
                    self.astar_seen[next_idx] = token
                    self.astar_g[next_idx] = next_g
                    self.astar_parent[next_idx] = current_idx
                    self.astar_step[next_idx] = EDGE_BRIDGE
                    heuristic = self.manhattan_heuristic_to_goals(next_x, next_y, goal_points)
                    heapq.heappush(
                        heap,
                        (next_g + heuristic, next_g, next_idx),
                    )
        return None

    def reconstruct_path(self, start_idx: int, end_idx: int) -> list[int]:
        path = [end_idx]
        current = end_idx
        while current != start_idx:
            current = self.astar_parent[current]
            path.append(current)
        path.reverse()
        return path

    def reconstruct_route_path(self, start_idx: int, end_idx: int) -> tuple[list[int], list[int]]:
        nodes = [end_idx]
        edges = []
        current = end_idx
        while current != start_idx:
            edges.append(self.astar_step[current])
            current = self.astar_parent[current]
            nodes.append(current)
        nodes.reverse()
        edges.reverse()
        return nodes, edges

    def build_vantage_goals(self, build_pos: Position) -> set[int]:
        goals: set[int] = set()
        for direction in ALL_DIRECTIONS:
            pos = build_pos.add(direction)
            if not self.in_bounds(pos):
                continue
            goals.add(self.pos_to_idx(pos))
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

        if c.get_tile_builder_bot_id(ore_pos) is not None:
            return True

        building_id = c.get_tile_building_id(ore_pos)
        if building_id is None:
            return False

        building_type = c.get_entity_type(building_id)
        building_team = c.get_team(building_id)

        if building_type == EntityType.MARKER:
            return False
        if building_type == EntityType.ROAD:
            return False
        if building_type == EntityType.HARVESTER:
            return True
        if building_type == EntityType.ARMOURED_CONVEYOR:
            return True
        if building_type in ORE_OCCUPYING_BUILDINGS:
            return True
        if building_team == self.my_team and building_type in {
            EntityType.CONVEYOR,
            EntityType.SPLITTER,
            EntityType.BRIDGE,
        }:
            return True
        return False

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def pos_to_idx(self, pos: Position) -> int:
        return pos.y * self.width + pos.x

    def idx_to_pos(self, idx: int) -> Position:
        return Position(idx % self.width, idx // self.width)

    def get_map_center(self) -> Position:
        return Position(self.width // 2, self.height // 2)
