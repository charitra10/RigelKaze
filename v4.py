from cambc import *
from collections import deque
import sys
import random as rand

class Player:
    def __init__(self):
        self.core_pos: Position | None = None
        self.builder_bots_spawned: int = 0
        self.raider_bots_spawned: int = 0
        self.raider_spawn_dirs_used: set[Direction] = set()
        self.nearby_tiles: list[Position] | None = None
        self.map_width: int | None = None
        self.map_height: int | None = None
        self.occupied_titanium: list[Position] = []
        self.pos_markers_placed: list[Position] = []
        self.directions = [
            Direction.SOUTHEAST,
            Direction.SOUTHWEST,
            Direction.NORTHEAST,
            Direction.NORTHWEST,
            Direction.SOUTH,
            Direction.WEST,
            Direction.NORTH,
            Direction.EAST,
        ]
        self.cardinal_directions = [
            Direction.NORTH,
            Direction.EAST,
            Direction.SOUTH,
            Direction.WEST
        ]
        self.diagnol_direction = [
            Direction.SOUTHEAST,
            Direction.SOUTHWEST,
            Direction.NORTHWEST,
            Direction.NORTHEAST
        ]
        self.titanium_currently_hunting_for: Position | None = None
        self.builder_bot_direction: Direction | None = None
        self.curr_builder_bot_pos: Position | None= None
        self.marker_placed_for_current_target : bool = False
        self.building_conveyor: bool = False
        self.current_harvestor_position : Position | None = None
        self.current_build_pos: Position | None = None
        self.conveyor_path: list[Position] | None = None
        self.known_map: dict[Position, str] = {}
        self.opp_dir : Direction | None = None
        self.turn_one : bool = True
        self.last_conv_built : Position | None =None
        self.role: str | None = None
        self.spawn_direction: Direction | None = None
        self.symmetry_candidates: set[str] = {"rotational", "reflect_x", "reflect_y"}
        self.observed_env: dict[Position, Environment] = {}
        self.detected_symmetry: str | None = None
        self.enemy_core_pos: Position | None = None
        self.center_target: Position | None = None
        self.raider_roam_target: Position | None = None
        self.enemy_siege_active: bool = False
        self.enemy_siege_source: Position | None = None
        self.enemy_siege_path: list[Position] | None = None

    def run(self, ct: Controller) -> None:


        # Populate map dimensions on first run
        if self.map_width is None:
            self.map_width = ct.get_map_width()
            self.map_height = ct.get_map_height()

        entity_type = ct.get_entity_type()
        if entity_type == EntityType.CORE:
            self.run_core(ct)
        elif entity_type == EntityType.BUILDER_BOT:
            self.route_builder_bot(ct)
        elif entity_type == EntityType.GUNNER:
            self.run_gunner(ct)
        elif entity_type == EntityType.LAUNCHER:
            self.run_launcher(ct)
        elif entity_type == EntityType.SENTINEL:
            self.run_sentinel(ct)
        elif entity_type == EntityType.BREACH:
            self.run_breach(ct)

    def run_core(self, ct: Controller) -> None:
        if self.core_pos is None:
            self.core_pos = ct.get_position()

        # Opening Phase: spawn 4 builder bots around the core
        if self.builder_bots_spawned == 0:
            pos = Position(self.core_pos.x, self.core_pos.y + 1)
            if ct.can_spawn(pos):
                ct.spawn_builder(pos)
                self.builder_bots_spawned += 1

        elif self.builder_bots_spawned == 1 and ct.get_action_cooldown()==0:
            pos = Position(self.core_pos.x + 1, self.core_pos.y)
            if ct.can_spawn(pos):
                ct.spawn_builder(pos)
                self.builder_bots_spawned += 1

        elif self.builder_bots_spawned == 2 and ct.get_action_cooldown()==0:
            pos = Position(self.core_pos.x - 1, self.core_pos.y)
            if ct.can_spawn(pos):
                ct.spawn_builder(pos)
                self.builder_bots_spawned += 1

        elif self.builder_bots_spawned == 3 and ct.get_action_cooldown()==0:
            pos = Position(self.core_pos.x, self.core_pos.y - 1)
            if ct.can_spawn(pos):
                ct.spawn_builder(pos)
                self.builder_bots_spawned += 1

        elif (
            self.builder_bots_spawned >= 4
            and ct.get_current_round() > 30
            and self.raider_bots_spawned < 3
            and ct.get_action_cooldown() == 0
        ):
            raider_spawn_dirs = [
                Direction.SOUTHEAST,
                Direction.SOUTHWEST,
                Direction.NORTHEAST,
                Direction.NORTHWEST,
            ]
            for direction in raider_spawn_dirs:
                if direction in self.raider_spawn_dirs_used:
                    continue

                pos = self.core_pos.add(direction)
                if ct.can_spawn(pos):
                    ct.spawn_builder(pos)
                    self.raider_spawn_dirs_used.add(direction)
                    self.raider_bots_spawned += 1
                    break

    def route_builder_bot(self, ct: Controller) -> None:
        if self.role is None:
            self.initialize_builder_role(ct)

        if self.core_pos is not None:
            self.observe_symmetry(ct)

        if self.role == "raider":
            self.run_raider_bot(ct)
            return

        self.run_builder_bot(ct)

    def initialize_builder_role(self, ct: Controller) -> None:
        if self.core_pos is None:
            for entity_id in ct.get_nearby_entities(1):
                if ct.get_entity_type(entity_id) == EntityType.CORE:
                    self.core_pos = ct.get_position(entity_id)
                    break

        self.role = "miner"
        if self.core_pos is not None and ct.get_position().distance_squared(self.core_pos) <= 2:
            self.spawn_direction = self.core_pos.direction_to(ct.get_position())
            if ct.get_current_round() > 30 and self.spawn_direction in self.diagnol_direction:
                self.role = "raider"
                self.center_target = self.get_center_target_for_direction(self.spawn_direction)

    def run_raider_bot(self, ct: Controller) -> None:
        self.update_known_map(ct)

        if self.core_pos is None:
            for entity_id in ct.get_nearby_entities(1):
                if ct.get_entity_type(entity_id) == EntityType.CORE:
                    self.core_pos = ct.get_position(entity_id)
                    break

        if self.enemy_core_pos is None:
            self.move_to_center_and_scout(ct)
            return

        self.raid_enemy_core(ct)

    def observe_symmetry(self, ct: Controller) -> None:
        enemy_team = self.get_enemy_team(ct)

        for tile in ct.get_nearby_tiles():
            try:
                env = ct.get_tile_env(tile)
                self.observed_env[tile] = env

                for candidate in tuple(self.symmetry_candidates):
                    mirrored = self.transform_position(tile, candidate)
                    mirrored_env = self.observed_env.get(mirrored)
                    if mirrored_env is not None and mirrored_env != env:
                        self.symmetry_candidates.discard(candidate)

                building_id = ct.get_tile_building_id(tile)
                if (
                    building_id is not None
                    and ct.get_entity_type(building_id) == EntityType.CORE
                    and ct.get_team(building_id) == enemy_team
                ):
                    self.enemy_core_pos = tile
            except Exception:
                pass

        if self.enemy_core_pos is None and len(self.symmetry_candidates) == 1 and self.core_pos is not None:
            symmetry = next(iter(self.symmetry_candidates))
            self.detected_symmetry = "rotational" if symmetry == "rotational" else "reflective"
            self.enemy_core_pos = self.transform_position(self.core_pos, symmetry)

    def move_to_center_and_scout(self, ct: Controller) -> None:
        bot_pos = ct.get_position()

        if self.center_target is None or self.is_bad_roam_target(self.center_target):
            self.center_target = self.pick_random_target_near(self.get_map_center(), 8)

        if self.center_target is None:
            return

        if bot_pos.distance_squared(self.center_target) <= 2:
            self.center_target = self.pick_random_target_near(self.get_map_center(), 8)
            if self.center_target is None:
                return

        self.move(ct, self.center_target)

    def raid_enemy_core(self, ct: Controller) -> None:
        bot_pos = ct.get_position()
        enemy_conveyor = self.find_visible_enemy_conveyor(ct)

        if enemy_conveyor is not None:
            if bot_pos == enemy_conveyor:
                if ct.get_action_cooldown() == 0:
                    titanium, _ = ct.get_global_resources()
                    if titanium >= 2 and ct.can_fire(bot_pos):
                        ct.fire(bot_pos)
                return

            self.move(ct, enemy_conveyor)
            return

        if self.raider_roam_target is None or self.is_bad_roam_target(self.raider_roam_target):
            self.raider_roam_target = self.pick_random_target_near(self.enemy_core_pos, 12)
        elif bot_pos.distance_squared(self.raider_roam_target) <= 2:
            self.raider_roam_target = self.pick_random_target_near(self.enemy_core_pos, 12)

        if self.raider_roam_target is not None:
            self.move(ct, self.raider_roam_target)

    def find_visible_enemy_conveyor(self, ct: Controller) -> Position | None:
        enemy_team = self.get_enemy_team(ct)
        bot_pos = ct.get_position()
        best_tile: Position | None = None
        best_dist = 10**9

        for tile in ct.get_nearby_tiles():
            try:
                building_id = ct.get_tile_building_id(tile)
                if building_id is None or ct.get_team(building_id) != enemy_team:
                    continue

                entity_type = ct.get_entity_type(building_id)
                if entity_type not in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                    continue

                occupant = ct.get_tile_builder_bot_id(tile)
                if occupant is not None and tile != bot_pos:
                    continue

                dist = bot_pos.distance_squared(tile)
                if dist < best_dist:
                    best_tile = tile
                    best_dist = dist
            except Exception:
                pass

        return best_tile

    def get_center_target_for_direction(self, direction: Direction | None) -> Position:
        center = self.get_map_center()
        offsets = {
            Direction.SOUTHEAST: (1, 1),
            Direction.SOUTHWEST: (-1, 1),
            Direction.NORTHEAST: (1, -1),
            Direction.NORTHWEST: (-1, -1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0),
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
        }
        dx, dy = offsets.get(direction, (0, 0))
        return self.clamp_position(center.x + dx, center.y + dy)

    def get_map_center(self) -> Position:
        return Position(self.map_width // 2, self.map_height // 2)

    def clamp_position(self, x: int, y: int) -> Position:
        return Position(
            max(0, min(self.map_width - 1, x)),
            max(0, min(self.map_height - 1, y)),
        )

    def is_in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.x < self.map_width and 0 <= pos.y < self.map_height

    def transform_position(self, pos: Position, symmetry: str) -> Position:
        if symmetry == "rotational":
            return Position(self.map_width - 1 - pos.x, self.map_height - 1 - pos.y)
        if symmetry == "reflect_x":
            return Position(self.map_width - 1 - pos.x, pos.y)
        return Position(pos.x, self.map_height - 1 - pos.y)

    def pick_random_target_near(self, centre: Position, radius_sq: int) -> Position | None:
        candidates: list[Position] = []

        radius = 0
        while (radius + 1) * (radius + 1) <= radius_sq:
            radius += 1

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                target = Position(centre.x + dx, centre.y + dy)
                if not self.is_in_bounds(target):
                    continue
                if target == self.enemy_core_pos:
                    continue
                if centre.distance_squared(target) > radius_sq:
                    continue
                if self.observed_env.get(target) == Environment.WALL:
                    continue
                if self.known_map.get(target) in ('building', 'enemy_core','builder_bot'):
                    continue
                candidates.append(target)

        if not candidates:
            return None

        return rand.choice(candidates)

    def is_bad_roam_target(self, target: Position | None) -> bool:
        if target is None:
            return True
        if not self.is_in_bounds(target):
            return True
        if self.observed_env.get(target) == Environment.WALL:
            return True
        if self.known_map.get(target) in ('building', 'enemy_core','builder_bot'):
            return True
        if self.enemy_core_pos is not None and target != self.enemy_core_pos:
            return self.enemy_core_pos.distance_squared(target) > 12
        return False

    def get_ally_team(self, ct: Controller) -> Team:
        return ct.get_team()

    def get_enemy_team(self, ct: Controller) -> Team:
        return Team.B if self.get_ally_team(ct) == Team.A else Team.A

    def is_enemy_side_titanium(self, tile: Position) -> bool:
        if self.core_pos is None or self.enemy_core_pos is None:
            return False
        return tile.distance_squared(self.enemy_core_pos) < tile.distance_squared(self.core_pos)

    def start_enemy_siege(self, source: Position) -> None:
        self.enemy_siege_active = True
        self.enemy_siege_source = source
        self.enemy_siege_path = None
        self.bridge_build_task = None
        self.enemy_road_destroy_task = None
        self.building_conveyor = False
        self.conveyor_path = None
        self.current_harvestor_position = source
        self.titanium_currently_hunting_for = None

    def reset_enemy_siege(self) -> None:
        self.enemy_siege_active = False
        self.enemy_siege_source = None
        self.enemy_siege_path = None
        self.bridge_build_task = None
        self.enemy_road_destroy_task = None

    def get_enemy_siege_path(self, start: Position, target: Position) -> list[Position]:
        raw_path = self.astar_cardinal(start, target)
        if len(raw_path) < 3:
            return []

        valid_path: list[Position] = []
        sentinel_idx: int | None = None
        for idx, tile in enumerate(raw_path):
            valid_path.append(tile)
            if idx >= 2 and tile.distance_squared(target) <= 32:
                sentinel_idx = idx
                break

        if sentinel_idx is None:
            return raw_path if len(raw_path) >= 3 else []

        return valid_path

    def run_builder_bot(self, ct: Controller) -> None:
        self.update_known_map(ct) 
        ally_team = self.get_ally_team(ct)
        enemy_team = self.get_enemy_team(ct)

                                
        self.curr_builder_bot_pos = ct.get_position()
        # Find our own core's position
        if self.core_pos is None:
            for entity_id in ct.get_nearby_entities(1):
                if ct.get_entity_type(entity_id) == EntityType.CORE:
                    self.core_pos = ct.get_position(entity_id)

        if self.enemy_siege_active:
            self.build_enemy_siege_route(ct)
            return

        if self.building_conveyor == True:
            ct.draw_indicator_dot(self.curr_builder_bot_pos,0,255,0)
            self.build_conveyor_route(ct)
            return

        if self.builder_bot_direction is None:
            self.builder_bot_direction = self.core_pos.direction_to(self.curr_builder_bot_pos)


        # If we've reached the titanium we're hunting, place a marker


        # Scan nearby tiles for markers (already-claimed titanium)
        self.nearby_tiles = ct.get_nearby_tiles()
        for tile in self.nearby_tiles:
            building_id = ct.get_tile_building_id(tile)
            if building_id is not None:
                if ct.get_entity_type(building_id) == EntityType.MARKER and tile not in self.pos_markers_placed and ct.get_team(building_id) == ally_team:
                    claimed_pos = self.marker_position_decode(ct, tile)
                    if claimed_pos == self.titanium_currently_hunting_for:
                        self.titanium_currently_hunting_for = None
                        self.occupied_titanium.append(claimed_pos)

                        
                    if claimed_pos not in self.occupied_titanium:
                        self.occupied_titanium.append(claimed_pos)


        if self.titanium_currently_hunting_for is not None:    

            for tile in self.nearby_tiles:
                if ct.get_tile_env(tile) == Environment.ORE_TITANIUM and ct.get_entity_type(ct.get_tile_building_id(tile))==EntityType.HARVESTER and ct.get_team(ct.get_tile_building_id(tile)) == ally_team:
                    self.occupied_titanium.append(tile)
                    continue

# NEW — only checks tile when it's in vision, guards None, and returns after recursion
        if self.titanium_currently_hunting_for in self.nearby_tiles:
            try:
                building_id_target = ct.get_tile_building_id(self.titanium_currently_hunting_for)
                if (ct.get_tile_env(self.titanium_currently_hunting_for) == Environment.ORE_TITANIUM
                        and building_id_target is not None
                        and ct.get_entity_type(building_id_target) == EntityType.HARVESTER
                        and ct.get_team(building_id_target) == enemy_team):
                    
                    has_allied_conveyor = False
                    for d in self.cardinal_directions:
                        adj = self.titanium_currently_hunting_for.add(d)
                        adj_id = ct.get_tile_building_id(adj)
                        if adj_id is not None:
                            ent_type = ct.get_entity_type(adj_id)
                            ent_team = ct.get_team(adj_id)
                            if ent_team == ally_team and ent_type in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                                has_allied_conveyor = True
                                break
                    
                    if has_allied_conveyor:
                        self.occupied_titanium.append(self.titanium_currently_hunting_for)
                        self.titanium_currently_hunting_for = None
                    else:
                        self.occupied_titanium.append(self.titanium_currently_hunting_for)
                        if self.is_enemy_side_titanium(self.titanium_currently_hunting_for):
                            self.start_enemy_siege(self.titanium_currently_hunting_for)
                        else:
                            self.current_harvestor_position = self.titanium_currently_hunting_for
                            self.current_build_pos = self.current_harvestor_position
                            self.titanium_currently_hunting_for = None
                            self.building_conveyor = True
                            self.conveyor_path = None
                        self.run_builder_bot(ct)
                        return  # ← critical: stop execution after recursion
            except Exception:
                pass

        if self.titanium_currently_hunting_for is not None:
            if ct.get_position().distance_squared(self.titanium_currently_hunting_for)<=2:
                if self.marker_placed_for_current_target == False:
                    self.Place_marker(ct,self.titanium_currently_hunting_for)
                    self.marker_placed_for_current_target = True
                    #for next search set back to false
                if ct.can_build_harvester(self.titanium_currently_hunting_for):
                    ct.build_harvester(self.titanium_currently_hunting_for)
                    self.occupied_titanium.append(self.titanium_currently_hunting_for)
                    if self.is_enemy_side_titanium(self.titanium_currently_hunting_for):
                        self.start_enemy_siege(self.titanium_currently_hunting_for)
                    else:
                        self.current_harvestor_position = self.titanium_currently_hunting_for
                        self.current_build_pos = self.current_harvestor_position
                        self.titanium_currently_hunting_for=None
                        self.building_conveyor = True
                        self.conveyor_path = None
                    return
            else:
                self.move(ct,self.titanium_currently_hunting_for)
                    


        # Find a new titanium ore to hunt if not already hunting
        if self.titanium_currently_hunting_for is None:
            priority_target: Position | None = None
            fallback_target: Position | None = None
            for tile in self.nearby_tiles:
                if ct.get_tile_env(tile) != Environment.ORE_TITANIUM:
                    continue

                building_id = ct.get_tile_building_id(tile)
                if building_id is not None and ct.get_entity_type(building_id)==EntityType.HARVESTER:
                    if ct.get_team(building_id) == ally_team:
                        self.occupied_titanium.append(tile)
                        continue
                    if ct.get_team(building_id) == enemy_team and self.is_enemy_side_titanium(tile):
                        priority_target = tile
                        break

                if tile in self.occupied_titanium:
                    continue

                if self.is_enemy_side_titanium(tile):
                    priority_target = tile
                    break

                if fallback_target is None:
                    fallback_target = tile

            chosen_target = priority_target if priority_target is not None else fallback_target
            if chosen_target is not None:
                self.titanium_currently_hunting_for = chosen_target
                self.move(ct, chosen_target)
                
            if self.titanium_currently_hunting_for is None:
                if ct.is_tile_passable(self.curr_builder_bot_pos.add(self.builder_bot_direction)):
                    if ct.can_move(self.builder_bot_direction) and ct.get_move_cooldown()==0:
                        ct.move(self.builder_bot_direction)
                    
                
                elif ct.can_build_road(self.curr_builder_bot_pos.add(self.builder_bot_direction)) and ct.get_action_cooldown()==0:
                    ct.build_road(self.curr_builder_bot_pos.add(self.builder_bot_direction))

                elif self.curr_builder_bot_pos.x==0 or self.curr_builder_bot_pos.x==(self.map_width-1) or self.curr_builder_bot_pos.y==0 or self.curr_builder_bot_pos.y==(self.map_height-1) :
                    rand1=rand.randint(0,3)
                    if(rand1==0):
                        self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                        self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                    elif(rand1==1):
                        self.builder_bot_direction=self.builder_bot_direction.rotate_right()
                        self.builder_bot_direction=self.builder_bot_direction.rotate_right()
                    elif(rand1==2):
                        self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                        self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                        self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                    else:
                        self.builder_bot_direction=self.builder_bot_direction.rotate_right()
                        self.builder_bot_direction=self.builder_bot_direction.rotate_right()
                        self.builder_bot_direction=self.builder_bot_direction.rotate_right()
                        
                    self.run_builder_bot(ct)
                
                elif (not ct.is_tile_empty(self.curr_builder_bot_pos.add(self.builder_bot_direction))) or (ct.get_tile_builder_bot_id(self.curr_builder_bot_pos.add(self.builder_bot_direction)) is not None):
                    rand2=rand.randint(0,1)
                    if(rand2==0):
                        self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                    else:
                        self.builder_bot_direction=self.builder_bot_direction.rotate_right()
                    self.run_builder_bot(ct)                   

    def build_enemy_siege_route(self, ct: Controller) -> None:
        source = self.enemy_siege_source
        bot_pos = ct.get_position()
        target = self.enemy_core_pos
        ally_team = self.get_ally_team(ct)
        enemy_team = self.get_enemy_team(ct)

        if source is None or target is None:
            self.reset_enemy_siege()
            return

        ct.draw_indicator_line(bot_pos, target, 255, 0, 0)
        self.update_known_map(ct)

        if getattr(self, 'bridge_build_task', None) is not None:
            b_pos, b_target = self.bridge_build_task
            if bot_pos.distance_squared(b_pos) <= 2:
                if ct.get_action_cooldown() == 0:
                    try:
                        ti, ax = ct.get_global_resources()
                        cost_ti = ct.get_bridge_cost()[0] if isinstance(ct.get_bridge_cost(), tuple) else ct.get_bridge_cost()
                        if ti < cost_ti:
                            ct.draw_indicator_dot(bot_pos, 255, 105, 180)
                            return

                        existing = ct.get_tile_building_id(b_pos)
                        if existing is not None:
                            e_type = ct.get_entity_type(existing)
                            if e_type != getattr(EntityType, 'BRIDGE', None):
                                if ct.get_team(existing) == ally_team and ct.can_destroy(b_pos):
                                    ct.destroy(b_pos)
                                return
                            self.bridge_build_task = None
                            if not hasattr(self, 'known_bridges'):
                                self.known_bridges = set()
                            self.known_bridges.add(b_pos)
                            return
                        else:
                            if ct.can_build_bridge(b_pos, b_target):
                                ct.build_bridge(b_pos, b_target)
                                self.bridge_build_task = None
                                if not hasattr(self, 'known_bridges'):
                                    self.known_bridges = set()
                                self.known_bridges.add(b_pos)
                    except Exception:
                        pass
            else:
                self.move(ct, b_pos)
            return

        if getattr(self, 'enemy_road_destroy_task', None) is not None:
            e_pos = self.enemy_road_destroy_task
            try:
                existing = ct.get_tile_building_id(e_pos)
                if existing is None or ct.get_entity_type(existing) != EntityType.ROAD or ct.get_team(existing) != enemy_team:
                    self.enemy_road_destroy_task = None
                else:
                    if bot_pos == e_pos:
                        if ct.get_action_cooldown() == 0:
                            ti, ax = ct.get_global_resources()
                            if ti >= 2 and ct.can_fire(bot_pos):
                                ct.fire(bot_pos)
                            elif ti < 2:
                                ct.draw_indicator_dot(bot_pos, 255, 105, 180)
                    else:
                        self.move(ct, e_pos)
                    return
            except Exception:
                self.enemy_road_destroy_task = None

        if self.enemy_siege_path is None:
            self.enemy_siege_path = self.get_enemy_siege_path(source, target)

        path = self.enemy_siege_path
        if not path or len(path) <= 2:
            self.reset_enemy_siege()
            return

        if not hasattr(self, 'known_conveyors'):
            self.known_conveyors = set()

        sentinel_tile = path[-1]
        first_unbuilt_idx = -1
        for i in range(1, len(path) - 1):
            tile = path[i]
            expected_facing = tile.direction_to(path[i + 1])

            try:
                building_id = ct.get_tile_building_id(tile)
                if building_id is not None:
                    ent_type = ct.get_entity_type(building_id)
                    if ent_type in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                        facing = ct.get_direction(building_id)
                        if facing == expected_facing:
                            self.known_conveyors.add(tile)
                            continue
                        if tile in self.known_conveyors:
                            self.known_conveyors.remove(tile)
                        first_unbuilt_idx = i
                        break
                    elif getattr(EntityType, 'BRIDGE', None) and ent_type == getattr(EntityType, 'BRIDGE', None):
                        if not hasattr(self, 'known_bridges'):
                            self.known_bridges = set()
                        self.known_bridges.add(tile)
                        continue

                first_unbuilt_idx = i
                break
            except Exception:
                if tile in self.known_conveyors or tile in getattr(self, 'known_bridges', set()):
                    continue
                first_unbuilt_idx = i
                break

        if first_unbuilt_idx == -1:
            if bot_pos == sentinel_tile:
                if ct.get_move_cooldown() == 0:
                    for d in self.directions:
                        adj = bot_pos.add(d)
                        if ct.is_tile_passable(adj) and ct.can_move(d):
                            ct.move(d)
                            break
                return

            if bot_pos.distance_squared(sentinel_tile) <= 2:
                if ct.get_action_cooldown() == 0:
                    try:
                        existing = ct.get_tile_building_id(sentinel_tile)
                        if existing is not None:
                            e_type = ct.get_entity_type(existing)
                            if ct.get_team(existing) == ally_team:
                                if e_type == EntityType.SENTINEL:
                                    self.reset_enemy_siege()
                                    return
                                if e_type in (EntityType.ROAD, EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                                    if ct.can_destroy(sentinel_tile):
                                        ct.destroy(sentinel_tile)
                                    return
                            elif e_type == EntityType.ROAD:
                                self.enemy_road_destroy_task = sentinel_tile
                                return
                            else:
                                self.enemy_siege_path = None
                                return

                        facing = sentinel_tile.direction_to(target)
                        if ct.can_build_sentinel(sentinel_tile, facing):
                            ct.build_sentinel(sentinel_tile, facing)
                            self.reset_enemy_siege()
                    except Exception:
                        pass
            else:
                self.move(ct, sentinel_tile)
            return

        target_build_tile = path[first_unbuilt_idx]
        build_facing = target_build_tile.direction_to(path[first_unbuilt_idx + 1])

        if bot_pos == target_build_tile:
            if ct.get_move_cooldown() == 0:
                for d in self.directions:
                    adj = bot_pos.add(d)
                    if ct.is_tile_passable(adj) and ct.can_move(d):
                        ct.move(d)
                        break
            return

        if bot_pos.distance_squared(target_build_tile) <= 2:
            if ct.get_action_cooldown() == 0:
                try:
                    ti, ax = ct.get_global_resources()
                    conveyor_cost = ct.get_conveyor_cost()
                    cost_ti = conveyor_cost[0] if isinstance(conveyor_cost, tuple) else conveyor_cost

                    if ti < cost_ti:
                        ct.draw_indicator_dot(bot_pos, 255, 105, 180)
                    else:
                        existing = ct.get_tile_building_id(target_build_tile)

                        if existing is not None and ct.get_entity_type(existing) == EntityType.ROAD and ct.get_team(existing) == enemy_team:
                            self.enemy_road_destroy_task = target_build_tile
                            return

                        if existing is not None and ct.get_team(existing) == ally_team:
                            e_type = ct.get_entity_type(existing)
                            if e_type in (EntityType.ROAD, EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                                if ct.can_destroy(target_build_tile):
                                    ct.destroy(target_build_tile)
                                return

                        if ct.can_build_conveyor(target_build_tile, build_facing):
                            ct.build_conveyor(target_build_tile, build_facing)
                            self.last_conv_built = target_build_tile
                            self.known_conveyors.add(target_build_tile)
                            ct.draw_indicator_dot(target_build_tile, 255, 165, 0)
                        else:
                            if ct.get_tile_env(target_build_tile) == Environment.WALL:
                                if first_unbuilt_idx > 1:
                                    prev_tile = path[first_unbuilt_idx - 1]
                                    bridge_target = None
                                    for j in range(first_unbuilt_idx, len(path)):
                                        if ct.get_tile_env(path[j]) != Environment.WALL:
                                            bridge_target = path[j]
                                            break

                                    if bridge_target is not None and prev_tile.distance_squared(bridge_target) <= 9:
                                        self.bridge_build_task = (prev_tile, bridge_target)
                                        idx = path.index(bridge_target)
                                        self.enemy_siege_path = path[:first_unbuilt_idx] + path[idx:]
                                        if prev_tile in self.known_conveyors:
                                            self.known_conveyors.remove(prev_tile)
                                        return
                                    self.enemy_siege_path = None
                            else:
                                if existing is not None and ct.get_entity_type(existing) not in (EntityType.ROAD, EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                                    self.enemy_siege_path = None
                            ct.draw_indicator_dot(target_build_tile, 255, 0, 0)
                except Exception:
                    ct.draw_indicator_dot(bot_pos, 255, 0, 255)
        else:
            self.move(ct, target_build_tile)


    def marker_position_decode(self, ct: Controller, i: Position) -> Position:
        building_id = ct.get_tile_building_id(i)
        val = ct.get_marker_value(building_id)
        y = val // self.map_width
        x = val % self.map_width
        return Position(x, y)

    def Place_marker(self, ct: Controller, i: Position) -> None:
        marker_val = (i.x) + (i.y) * self.map_width
        for d in self.directions:
            neighbour = i.add(d)
            if ct.is_tile_empty(neighbour) and ct.get_tile_env(neighbour)!=Environment.ORE_TITANIUM:
                if ct.can_place_marker(neighbour):
                    ct.place_marker(neighbour, marker_val)
                    self.pos_markers_placed.append(neighbour)
                    break

    def update_known_map(self, ct: Controller) -> None:
        self.known_map={k:v for k, v in self.known_map.items() if v != 'builder_bot'}
        for tile in ct.get_nearby_tiles():
            try:
                env = ct.get_tile_env(tile)
                if env == Environment.WALL:
                    self.known_map[tile] = 'wall'
                    continue
                building_id = ct.get_tile_building_id(tile)
                builder_bot_id=ct.get_tile_builder_bot_id(tile)
                if building_id is not None:
                    entity_type = ct.get_entity_type(building_id)
                    if entity_type == EntityType.CORE:
                        if ct.get_team(building_id) == self.get_ally_team(ct):
                            self.known_map[tile] = 'allied_core'
                        else:
                            self.known_map[tile] = 'enemy_core'
                    elif entity_type not in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR, EntityType.ROAD):
                        self.known_map[tile] = 'building'
                    else:
                        self.known_map[tile] = 'passable'
                elif builder_bot_id is not None:
                    self.known_map[tile]='builder_bot'
                else:
                    self.known_map[tile] = 'passable'
            except Exception:
                pass

    def heuristic(self, a: Position, b: Position) -> int:
        # Chebyshev distance — accurate for 8-directional movement
        return max(abs(a.x - b.x), abs(a.y - b.y))

    def astar(self, start: Position, target: Position) -> list[Position]:
        # f_score = g_score + heuristic
        # open_set entries: (f_score, g_score, position)
        open_set = []
        import heapq
        heapq.heappush(open_set, (0, 0, start))
        came_from: dict[Position, Position | None] = {start: None}
        g_score: dict[Position, int] = {start: 0}

        while open_set:
            _, g, curr = heapq.heappop(open_set)

            if curr == target:
                # Reconstruct path
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                return path

            # Skip if we've already found a better path to curr
            if g > g_score.get(curr, float('inf')):
                continue

            for d in self.directions:
                nxt = curr.add(d)

                # Boundary check
                if nxt.x < 0 or nxt.x >= self.map_width or nxt.y < 0 or nxt.y >= self.map_height:
                    continue

                # Check known map — unknown tiles are treated as passable
                tile_state = self.known_map.get(nxt)
                if tile_state in ('wall', 'building', 'enemy_core','builder_bot'):
                    if nxt != target:  # always allow stepping onto target
                        continue

                # Diagonal moves cost 14 (approx sqrt(2)*10), cardinal cost 10
                dx = abs(nxt.x - curr.x)
                dy = abs(nxt.y - curr.y)
                step_cost = 14 if dx + dy == 2 else 10

                tentative_g = g_score[curr] + step_cost

                if tentative_g < g_score.get(nxt, float('inf')):
                    g_score[nxt] = tentative_g
                    f = tentative_g + self.heuristic(nxt, target) * 10
                    came_from[nxt] = curr
                    heapq.heappush(open_set, (f, tentative_g, nxt))

        return []  # No path found
    
    def astar_cardinal(self, start: Position, target: Position) -> list[Position]:
        cardinal_directions = [
            Direction.NORTH,
            Direction.SOUTH,
            Direction.EAST,
            Direction.WEST
        ]
        import heapq
        open_set = []
        heapq.heappush(open_set, (0, 0, start))
        came_from: dict[Position, Position | None] = {start: None}
        g_score: dict[Position, int] = {start: 0}

        while open_set:
            _, g, curr = heapq.heappop(open_set)

            if curr == target:
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                return path

            if g > g_score.get(curr, float('inf')):
                continue

            for d in cardinal_directions:
                nxt = curr.add(d)

                if nxt.x < 0 or nxt.x >= self.map_width or nxt.y < 0 or nxt.y >= self.map_height:
                    continue

                tile_state = self.known_map.get(nxt)
                if tile_state in ('wall', 'building', 'enemy_core','builder_bot'):
                    if nxt != target:
                        continue

                tentative_g = g_score[curr] + 10  # all cardinal steps cost 10

                if tentative_g < g_score.get(nxt, float('inf')):
                    g_score[nxt] = tentative_g
                    f = tentative_g + self.heuristic(nxt, target) * 10
                    came_from[nxt] = curr
                    heapq.heappush(open_set, (f, tentative_g, nxt))

        return []

    def move(self, ct: Controller, target: Position) -> None:
        start = ct.get_position()
        if start == target:
            return

        # Always update our terrain knowledge first
        self.update_known_map(ct)

        if ct.get_move_cooldown() > 0:
            return

        path = self.astar(start, target)

        if len(path) < 2:
            # No path found at all — fallback to greedy direction
            direction_to_move = start.direction_to(target)
            if ct.can_move(direction_to_move):
                ct.move(direction_to_move)
            return

        next_step = path[1]
        direction_to_move = start.direction_to(next_step)

        try:
            if ct.is_tile_passable(next_step): #and ct.get_tile_builder_bot_id(next_step) is None:
                if ct.can_move(direction_to_move):
                    ct.move(direction_to_move)
            #elif ct.get_tile_builder_bot_id(next_step) is not None:

            else:
                # Tile exists but isn't passable yet — build a road on it
                if ct.get_action_cooldown() == 0 and ct.can_build_road(next_step):
                    ct.build_road(next_step)
        except Exception:
            pass

    def build_conveyor_route(self, ct: Controller) -> None:
        start = self.current_harvestor_position
        bot_pos = ct.get_position()
        target = self.core_pos
        ally_team = self.get_ally_team(ct)
        enemy_team = self.get_enemy_team(ct)

        if target is None or start is None:
            return

        ct.draw_indicator_line(bot_pos, target, 0, 0, 255)

        self.update_known_map(ct)

        if getattr(self, 'bridge_build_task', None) is not None:
            b_pos, b_target = self.bridge_build_task
            if bot_pos.distance_squared(b_pos) <= 2:
                if ct.get_action_cooldown() == 0:
                    try:
                        ti, ax = ct.get_global_resources()
                        cost_ti = ct.get_bridge_cost()[0] if isinstance(ct.get_bridge_cost(), tuple) else ct.get_bridge_cost()
                        if ti < cost_ti:
                            ct.draw_indicator_dot(bot_pos, 255, 105, 180)
                            return

                        existing = ct.get_tile_building_id(b_pos)
                        if existing is not None:
                            e_type = ct.get_entity_type(existing)
                            if e_type != getattr(EntityType, 'BRIDGE', None):
                                if ct.get_team(existing) == ally_team and ct.can_destroy(b_pos):
                                    ct.destroy(b_pos)
                                return
                            else:
                                self.bridge_build_task = None
                                if not hasattr(self, 'known_bridges'):
                                    self.known_bridges = set()
                                self.known_bridges.add(b_pos)
                                return
                        else:
                            if ct.can_build_bridge(b_pos, b_target):
                                ct.build_bridge(b_pos, b_target)
                                self.bridge_build_task = None
                                if not hasattr(self, 'known_bridges'):
                                    self.known_bridges = set()
                                self.known_bridges.add(b_pos)
                    except Exception:
                        pass
            else:
                self.move(ct, b_pos)
            return

        if getattr(self, 'enemy_road_destroy_task', None) is not None:
            e_pos = self.enemy_road_destroy_task
            try:
                existing = ct.get_tile_building_id(e_pos)
                if existing is None or ct.get_entity_type(existing) != EntityType.ROAD or ct.get_team(existing) != enemy_team:
                    self.enemy_road_destroy_task = None
                else:
                    if bot_pos == e_pos:
                        if ct.get_action_cooldown() == 0:
                            ti, ax = ct.get_global_resources()
                            if ti >= 2:
                                if ct.can_fire(bot_pos):
                                    ct.fire(bot_pos)
                            else:
                                ct.draw_indicator_dot(bot_pos, 255, 105, 180)
                    else:
                        self.move(ct, e_pos)
                    return
            except Exception:
                self.enemy_road_destroy_task = None

        if getattr(self, 'conveyor_path', None) is None:
            raw_path = self.astar_cardinal(start, target)
            valid_path = []
            for p in raw_path:
                valid_path.append(p)
                if getattr(self, 'known_map', {}).get(p) == 'allied_core':
                    break
            self.conveyor_path = valid_path

        path = self.conveyor_path

        if not path or len(path) <= 2:
            ct.draw_indicator_dot(bot_pos, 255, 0, 255)
            self.building_conveyor = False
            self.conveyor_path = None
            return

        if not hasattr(self, 'known_conveyors'):
            self.known_conveyors = set()

        first_unbuilt_idx = -1
        for i in range(1, len(path) - 1):
            tile = path[i]
            expected_facing = tile.direction_to(path[i + 1])

            try:
                building_id = ct.get_tile_building_id(tile)
                if building_id is not None:
                    ent_type = ct.get_entity_type(building_id)
                    if ent_type in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                        facing = ct.get_direction(building_id)
                        if facing == expected_facing:
                            self.known_conveyors.add(tile)
                            continue
                        else:
                            if tile in self.known_conveyors:
                                self.known_conveyors.remove(tile)
                            first_unbuilt_idx = i
                            break
                    elif getattr(EntityType, 'BRIDGE', None) and ent_type == getattr(EntityType, 'BRIDGE', None):
                        if not hasattr(self, 'known_bridges'):
                            self.known_bridges = set()
                        self.known_bridges.add(tile)
                        continue

                first_unbuilt_idx = i
                break
            except Exception:
                if tile in self.known_conveyors or tile in getattr(self, 'known_bridges', set()):
                    continue
                first_unbuilt_idx = i
                break

        if first_unbuilt_idx == -1:
            self.building_conveyor = False
            self.conveyor_path = None
            ct.draw_indicator_dot(bot_pos, 0, 0, 0)
            return

        target_build_tile = path[first_unbuilt_idx]
        build_facing = target_build_tile.direction_to(path[first_unbuilt_idx + 1])

        if bot_pos == target_build_tile:
            if ct.get_move_cooldown() == 0:
                for d in self.directions:
                    adj = bot_pos.add(d)
                    if ct.is_tile_passable(adj) and ct.can_move(d):
                        ct.move(d)
                        break
            return

        if bot_pos.distance_squared(target_build_tile) <= 2:
            if ct.get_action_cooldown() == 0:
                try:
                    ti, ax = ct.get_global_resources()
                    conveyor_cost = ct.get_conveyor_cost()
                    cost_ti = conveyor_cost[0] if isinstance(conveyor_cost, tuple) else conveyor_cost

                    if ti < cost_ti:
                        ct.draw_indicator_dot(bot_pos, 255, 105, 180)
                    else:
                        existing = ct.get_tile_building_id(target_build_tile)

                        if existing is not None and ct.get_entity_type(existing) == EntityType.ROAD and ct.get_team(existing) == enemy_team:
                            self.enemy_road_destroy_task = target_build_tile
                            return

                        if existing is not None and ct.get_team(existing) == ally_team:
                            e_type = ct.get_entity_type(existing)
                            if e_type in (EntityType.ROAD, EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                                if ct.can_destroy(target_build_tile):
                                    ct.destroy(target_build_tile)
                                return

                        if ct.can_build_conveyor(target_build_tile, build_facing):
                            ct.build_conveyor(target_build_tile, build_facing)
                            self.last_conv_built = target_build_tile
                            self.known_conveyors.add(target_build_tile)
                            ct.draw_indicator_dot(target_build_tile, 255, 165, 0)
                        else:
                            if ct.get_tile_env(target_build_tile) == Environment.WALL:
                                if first_unbuilt_idx > 1:
                                    prev_tile = path[first_unbuilt_idx - 1]
                                    bridge_target = None
                                    for j in range(first_unbuilt_idx, len(path)):
                                        if ct.get_tile_env(path[j]) != Environment.WALL:
                                            bridge_target = path[j]
                                            break

                                    if bridge_target is not None and prev_tile.distance_squared(bridge_target) <= 9:
                                        self.bridge_build_task = (prev_tile, bridge_target)
                                        idx = path.index(bridge_target)
                                        self.conveyor_path = path[:first_unbuilt_idx] + path[idx:]
                                        if prev_tile in self.known_conveyors:
                                            self.known_conveyors.remove(prev_tile)
                                        return
                                    else:
                                        self.conveyor_path = None
                            else:
                                if existing is not None and ct.get_entity_type(existing) not in (EntityType.ROAD, EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                                    self.conveyor_path = None
                            ct.draw_indicator_dot(target_build_tile, 255, 0, 0)
                except Exception:
                    ct.draw_indicator_dot(bot_pos, 255, 0, 255)
        else:
            self.move(ct, target_build_tile)

    def run_gunner(self, ct: Controller) -> None:
        return

    def run_launcher(self, ct: Controller) -> None:
        return

    def run_sentinel(self, ct: Controller) -> None:
        if ct.get_action_cooldown() != 0:
            return

        enemy_team = self.get_enemy_team(ct)
        fallback_target: Position | None = None

        try:
            for tile in ct.get_attackable_tiles():
                building_id = ct.get_tile_building_id(tile)
                if building_id is not None and ct.get_team(building_id) == enemy_team:
                    if ct.get_entity_type(building_id) == EntityType.CORE:
                        if ct.can_fire(tile):
                            ct.fire(tile)
                            return
                    elif fallback_target is None:
                        fallback_target = tile

                unit_id = ct.get_tile_builder_bot_id(tile)
                if unit_id is not None and ct.get_team(unit_id) == enemy_team and fallback_target is None:
                    fallback_target = tile

            if fallback_target is not None and ct.can_fire(fallback_target):
                ct.fire(fallback_target)
        except Exception:
            pass

    def run_breach(self, ct: Controller) -> None:
        return
