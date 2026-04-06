from cambc import *
from collections import deque
import sys
import random as rand

class Player:
    def __init__(self):
        self.core_pos: Position | None = None
        self.builder_bots_spawned: int = 0
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
        self.known_map: dict[Position, str] = {}
        self.opp_dir : Direction | None = None
        self.turn_one : bool = True
        self.last_conv_built : Position | None =None

    def run(self, ct: Controller) -> None:


        # Populate map dimensions on first run
        if self.map_width is None:
            self.map_width = ct.get_map_width()
            self.map_height = ct.get_map_height()

        entity_type = ct.get_entity_type()
        if entity_type == EntityType.CORE:
            self.run_core(ct)
        elif entity_type == EntityType.BUILDER_BOT:
            self.run_builder_bot(ct)
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

    def run_builder_bot(self, ct: Controller) -> None:
        self.update_known_map(ct) 

                                  
        self.curr_builder_bot_pos = ct.get_position()
        # Find our own core's position
        if self.core_pos is None:
            for entity_id in ct.get_nearby_entities(1):
                if ct.get_entity_type(entity_id) == EntityType.CORE:
                    self.core_pos = ct.get_position(entity_id)

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
                if ct.get_entity_type(building_id) == EntityType.MARKER and tile not in self.pos_markers_placed and ct.get_team(building_id)== Team.A:
                    claimed_pos = self.marker_position_decode(ct, tile)
                    if claimed_pos == self.titanium_currently_hunting_for:
                        ct.draw_indicator_dot(self.curr_builder_bot_pos,255,0,0)
                        self.titanium_currently_hunting_for = None
                        self.occupied_titanium.append(claimed_pos)

                        
                    if claimed_pos not in self.occupied_titanium:
                        self.occupied_titanium.append(claimed_pos)


        if self.titanium_currently_hunting_for is not None:    

            for tile in self.nearby_tiles:
                if ct.get_tile_env(tile) == Environment.ORE_TITANIUM and ct.get_entity_type(ct.get_tile_building_id(tile))==EntityType.HARVESTER and ct.get_team(ct.get_tile_building_id(tile))==Team.A:
                    self.occupied_titanium.append(tile)
                    continue

            if ct.get_position().distance_squared(self.titanium_currently_hunting_for)<=2:
                if self.marker_placed_for_current_target == False:
                    self.Place_marker(ct,self.titanium_currently_hunting_for)
                    self.marker_placed_for_current_target = True
                    #for next search set back to false
                if ct.can_build_harvester(self.titanium_currently_hunting_for):
                    ct.build_harvester(self.titanium_currently_hunting_for)
                    self.occupied_titanium.append(self.titanium_currently_hunting_for)
                    self.current_harvestor_position = self.titanium_currently_hunting_for
                    self.current_build_pos = self.current_harvestor_position
                    self.titanium_currently_hunting_for=None
                    self.building_conveyor = True
            else:
                self.move(ct,self.titanium_currently_hunting_for)
                    


        # Find a new titanium ore to hunt if not already hunting
        if self.titanium_currently_hunting_for is None:
            for tile in self.nearby_tiles:
                if ct.get_tile_env(tile) == Environment.ORE_TITANIUM and ct.get_entity_type(ct.get_tile_building_id(tile))==EntityType.HARVESTER and ct.get_team(ct.get_tile_building_id(tile))==Team.A:
                    self.occupied_titanium.append(tile)
                    continue

                if ct.get_tile_env(tile) == Environment.ORE_TITANIUM and tile not in self.occupied_titanium:
                    
                    self.titanium_currently_hunting_for = tile
                    self.move(ct, tile)
                    break
                
            if self.titanium_currently_hunting_for is None:
                if ct.is_tile_passable(self.curr_builder_bot_pos.add(self.builder_bot_direction)):
                    if ct.can_move(self.builder_bot_direction) and ct.get_move_cooldown()==0:
                        ct.move(self.builder_bot_direction)
                    
                
                elif ct.can_build_road(self.curr_builder_bot_pos.add(self.builder_bot_direction)) and ct.get_action_cooldown()==0:
                    ct.build_road(self.curr_builder_bot_pos.add(self.builder_bot_direction))

                elif self.curr_builder_bot_pos.x==0 or self.curr_builder_bot_pos.x==(self.map_width-1) or self.curr_builder_bot_pos.y==0 or self.curr_builder_bot_pos.y==(self.map_height-1) :
                    self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                    self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                    self.run_builder_bot(ct)
                
                elif not ct.is_tile_empty(self.curr_builder_bot_pos.add(self.builder_bot_direction)):
                    self.builder_bot_direction=self.builder_bot_direction.rotate_left()
                    self.run_builder_bot(ct)                   


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
        for tile in ct.get_nearby_tiles():
            try:
                env = ct.get_tile_env(tile)
                if env == Environment.WALL:
                    self.known_map[tile] = 'wall'
                    continue
                building_id = ct.get_tile_building_id(tile)
                if building_id is not None:
                    entity_type = ct.get_entity_type(building_id)
                    if entity_type not in (EntityType.CORE, EntityType.CONVEYOR,
                                        EntityType.ARMOURED_CONVEYOR, EntityType.ROAD):
                        self.known_map[tile] = 'building'
                    else:
                        self.known_map[tile] = 'passable'
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
                if tile_state == 'wall' or tile_state == 'building':
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
                if tile_state == 'wall' or tile_state == 'building':
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
            if ct.is_tile_passable(next_step):
                if ct.can_move(direction_to_move):
                    ct.move(direction_to_move)
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

            if target is None or start is None:
                return

            ct.draw_indicator_line(bot_pos, target, 0, 0, 255)

            # Stop condition
            # if self.last_conv_built is not None and self.last_conv_built.distance_squared(target) <8:
            #     self.building_conveyor = False
            #     self.last_conv_built = None
            #     ct.draw_indicator_dot(bot_pos,0,0,0)
            #     #self.marker_placed_for_current_target = False
            #     return

            self.update_known_map(ct)
            path = self.astar_cardinal(start, target)

            if len(path) <= 2:
                ct.draw_indicator_dot(bot_pos, 255, 0, 255)
                self.building_conveyor = False
                return

            # Initialize a memory set to prevent entity-masking oscillation
            if not hasattr(self, 'known_conveyors'):
                self.known_conveyors = set()

            # 1. Find the first unbuilt tile in the path.
            first_unbuilt_idx = -1
            for i in range(1, len(path) - 1):
                tile = path[i]
                
                # If we previously verified a conveyor is here, skip it!
                if tile in self.known_conveyors:
                    continue
                    
                try:
                    building_id = ct.get_tile_building_id(tile)
                    if building_id is not None:
                        ent_type = ct.get_entity_type(building_id)
                        
                        # If we clearly see a conveyor right now, commit it to memory
                        if ent_type in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
                            self.known_conveyors.add(tile)
                            continue
                            
                    # If we made it here, the tile is either empty, or occupied by a bot/item
                    # Since we haven't memorized it as built, we must treat it as unbuilt.
                    first_unbuilt_idx = i
                    break
                except Exception:
                    first_unbuilt_idx = i
                    break

            # If no unbuilt tiles remain, route is finished
            if first_unbuilt_idx == -1:
                self.building_conveyor = False
                ct.draw_indicator_dot(bot_pos,0,0,0)
                #self.marker_placed_for_current_target = False
                return

            target_build_tile = path[first_unbuilt_idx]
            build_facing = target_build_tile.direction_to(path[first_unbuilt_idx + 1])

            # 2. If the bot is standing ON the tile it needs to build on, move away!
            if bot_pos == target_build_tile:
                if ct.get_move_cooldown() == 0:
                    for d in self.directions:
                        adj = bot_pos.add(d)
                        if ct.is_tile_passable(adj) and ct.can_move(d):
                            ct.move(d)
                            break
                return 

            # 3. If the bot is adjacent, build the conveyor
            if bot_pos.distance_squared(target_build_tile) <= 2:
                if ct.get_action_cooldown() == 0:
                    try:
                        ti, ax = ct.get_global_resources()
                        conveyor_cost = ct.get_conveyor_cost()
                        cost_ti = conveyor_cost[0] if isinstance(conveyor_cost, tuple) else conveyor_cost

                        if ti < cost_ti:
                            ct.draw_indicator_dot(bot_pos, 255, 105, 180)  # pink = broke
                        else:
                            existing = ct.get_tile_building_id(target_build_tile)
                            if existing is not None and ct.get_entity_type(existing) == EntityType.ROAD:
                                if ct.can_destroy(target_build_tile):
                                    ct.destroy(target_build_tile)
                            
                            if ct.can_build_conveyor(target_build_tile, build_facing):
                                ct.build_conveyor(target_build_tile, build_facing)
                                self.last_conv_built = target_build_tile
                                # Immediately add to memory so we don't try to build here again
                                self.known_conveyors.add(target_build_tile) 
                                ct.draw_indicator_dot(target_build_tile, 255, 165, 0)
                            else:
                                ct.draw_indicator_dot(target_build_tile, 255, 0, 0) 
                    except Exception:
                        ct.draw_indicator_dot(bot_pos, 255, 0, 255) 
            
            # 4. If the bot is not adjacent, move towards the target tile
            else:
                self.move(ct, target_build_tile)
