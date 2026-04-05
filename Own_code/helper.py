from cambc import *

class Player:
    def __init__(self):
        self.core_pos: Position | None = None
        self.builder_bots_spawned : int | None=None
        self.nearby_tiles: list[Position]|None = None
        self.map_width: int | None=None
        self.map_height: int |None=None
        self.occupied_titanium: list[Position]|None=None



    def run(self,ct:contoller)->None:
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
    
    def run_core(self,ct:Controller)->None:
        if self.core_pos == None:
            self.core_pos = ct.get_position()
        
        #Opening Phase Code
        if self.builder_bots_spawned == 0:
            if ct.can_spawn(Position(self.core_pos.x,(self.core_pos.y)+1)):
                ct.spawn_builder(Position(self.core_pos.x,(self.core_pos.y)+1))
                self.builder_bots_spawned+=1
        if self.builder_bots_spawned == 1:
            if ct.can_spawn(Position((self.core_pos.x)+1,(self.core_pos.y))):
                ct.spawn_builder((Position(self.core_pos.x)+1,(self.core_pos.y)))
                self.builder_bots_spawned+=1
        if self.builder_bots_spawned == 2:
            if ct.can_spawn(Position((self.core_pos.x)-1,(self.core_pos.y))):
                ct.spawn_builder((Position(self.core_pos.x)-1,(self.core_pos.y)))
                self.builder_bots_spawned+=1
        if self.builder_bots_spawned == 3:
            if ct.can_spawn(Position((self.core_pos.x),(self.core_pos.y)-1)):
                ct.spawn_builder((Position(self.core_pos.x),(self.core_pos.y)-1))
                self.builder_bots_spawned+=1      
        
        #Mid Phase Code
    def run_builder_bot(self,ct:controller)->None:
        if self.core_pos == None:
            for entity_id in ct.get_nearby_entities(1):
                if ct.get_entity_type(entity_id) == EntityType.CORE:
                   self.core_pos = ct.get_position(entity_id)
        
        self.nearby_tiles = ct.get_nearby_tiles()
        for i in self.nearby_tiles:
            if ct.get_entity_type(ct.get_tile_building_id(i))==EntityType.MARKER:
                self.marker_position_decode(i)
                #only for titanium as of now
            elif ct.get_tile_env(i)==Environement.ORE_TITANIUM:
                self.move(i)
            
    #Gives the coordinate of the position on the marker
    def marker_position_decode(self,ct:controller)->Position:
        self.val=ct.get_marker_value(ct.get_tile_building_id(i))
        self.y=(val/self.map_width)
        self.x=(val%(self.map_width))
        return Position(self.x,self.y)





        




