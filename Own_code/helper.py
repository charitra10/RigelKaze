from cambc import *

#to do-
#make fucntion for placing marker when unoccupied titatnium is found
#make function for movement of builder bot towards titanium
#create a case where where we found a marker for titanium later and we have to restart search
class Player:
    def __init__(self):
        self.core_pos: Position | None = None
        self.builder_bots_spawned : int | None=None
        self.nearby_tiles: list[Position]|None = None
        self.map_width: int | None=None
        self.map_height: int |None=None
        self.occupied_titanium: list[Position]|None=None
        self.pos_markers_placed: list[Position] | None = None
        self.directions = [
            ct.Direction.SOUTHEAST
            ct.DIrection.SOUTHWEST,
            ct.Direction.NORTHEAST,
            ct.Direction.NORTHWEST,
            ct.Direction.SOUTH,
            ct.Direction.WEST,
            ct.Direction.NORTH,
            ct.Direction.EAST,

        ]
        self.titanium_currently_hunting_for: Position | None = None



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
        #mid phase shenanigans

    def run_builder_bot(self,ct:controller)->None:

        # Just finds our own cores position
        if self.core_pos == None:
            for entity_id in ct.get_nearby_entities(1):
                if ct.get_entity_type(entity_id) == EntityType.CORE:
                   self.core_pos = ct.get_position(entity_id)

        # function call to place marker after reaching the titanium ore
        if self.titanium_currently_hunting_for == ct.get_position():
            self.place_marker(self.titanium_currently_hunting_for)
        
        # if we are currently hunting for an ore then to first move towards it 
        if self.titanium_currently_hunting_for != None:
            self.move(self.titanium_currently_hunting_for)
        
        # code to find titanium ores already being hunted for
        self.nearby_tiles = ct.get_nearby_tiles()
        for i in self.nearby_tiles:
            if ct.get_entity_type(ct.get_tile_building_id(i))==EntityType.MARKER and i not in self.pos_markers_placed:
                if(self.marker_position_decode(ct,i)==self.titanium_currently_hunting_for):
                    self.titanium_currently_hunting_for= None
                self.occupied_titanium.append(self.marker_position_decode(ct,i))

                #only for titanium as of now

        #finding titanium ore if not hunting for one currently
        if self.titanium_currently_hunting_for==None:
            for i in self.nearby_tiles:       
                if ct.get_tile_env(i)==Environement.ORE_TITANIUM and i not in self.occupied_titanium:
                    self.titanium_currently_hunting_for=i
                    self.move(i)
                    break
            
    #Gives the coordinate of the position on the marker
    def marker_position_decode(self,ct:controller,i:Position)->Position:
        self.val=ct.get_marker_value(ct.get_tile_building_id(i))
        self.y=(val/self.map_width)
        self.x=(val%(self.map_width))
        return Position(self.x,self.y)

    #code to place marker 
    def place_marker(self,curr_pos:Position,i:Position,ct:controller)->None:
        self.marker_val = curr_pos.x + curr_pos.y*self.map_width
        for d in self.directions:
            if ct.is_tile_empty(i.add(d)):
                if ct.can_place_marker(i.add(d)):
                    ct.place_marker(i.add(d),self.marker_val)
                    self.pos_markers_placed.append(i.add(d))
                    break

    




        




