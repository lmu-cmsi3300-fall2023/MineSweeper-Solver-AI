import time
import random
import math
from queue import Queue
from constants import *
from maze_clause import *
from maze_knowledge_base import *
from itertools import combinations

class MazeAgent:
    '''
    BlindBot MazeAgent meant to employ Propositional Logic,
    Planning, and Active Learning to navigate the Pitsweeper
    Problem. Have fun!
    '''
    
    def __init__ (self, env: "Environment", perception: dict) -> None:
        """
        Initializes the MazeAgent with any attributes it will need to
        navigate the maze.
        [!] Add as many attributes as you see fit!
        
        Parameters:
            env (Environment):
                The Environment in which the agent is operating; make sure
                to see the spec / Environment class for public methods that
                your agent will use to solve the maze!
            perception (dict):
                The starting perception of the agent, which is a
                small dictionary with keys:
                  - loc:  the location of the agent as a (c,r) tuple
                  - tile: the type of tile the agent is currently standing upon
        """
        self.env: "Environment" = env
        self.goal: tuple[int, int] = env.get_goal_loc()
        
        
        # The agent's maze can be manipulated as a tracking mechanic
        # for what it has learned; changes to this maze will be drawn
        # by the environment and is simply for visuals / debugging
        # [!] Feel free to change self.maze at will
        self.maze: list = env.get_agent_maze()
        # Standard set of attributes you'll want to maintain
        self.kb: "MazeKnowledgeBase" = MazeKnowledgeBase()
        self.possible_pits: set[tuple[int, int]] = set()
        self.safe_tiles: set[tuple[int, int]] = set()
        self.pit_tiles: set[tuple[int, int]] = set()
        initial_loc: tuple[int, int] = env.get_player_loc()
        
        # [!] TODO: Initialize any other knowledge-related attributes for
        # agent here, or any other record-keeping attributes you'd like
        self.moveOrder: list[tuple[tuple[int, int], int]] = list()
        self.startLoc = self.env._initial_loc  
        
        #add goal to safetiles
        self.kb.tell(MazeClause([((Constants.PIT_BLOCK, self.goal),False)]))
        self.safe_tiles.add(self.goal)
        
        #add initial location to safetiles
        self.kb.tell(MazeClause([((Constants.PIT_BLOCK, self.startLoc),False)]))
        self.safe_tiles.add(self.env._initial_loc)
        
        #goal can not have 4 pits around it
        self.kb.tell(MazeClause([((Constants.WRN_FOUR_BLOCK, self.goal),False)]))
        self.kb.tell(MazeClause([(("P", tile), False) for tile in self.env.get_cardinal_locs(self.goal, 1)]))

        #Use this to keep track of the agent's current location
        self.think(perception)
        
    ##################################################################
    # Methods
    ##################################################################
    
    def think(self, perception: dict) -> tuple[int, int]:
        """
        The main workhorse method of how your agent will process new information
        and use that to make deductions and decisions. In gist, it should follow
        this outline of steps:
        1. Process the given perception, i.e., the new location it is in and the
           type of tile on which it's currently standing (e.g., a safe tile, or
           warning tile like "1" or "2")
        2. Update the knowledge base and record-keeping of where known pits and
           safe tiles are located, as well as locations of possible pits.
        3. Query the knowledge base to see if any locations that possibly contain
           pits can be deduced as safe or not.
        4. Use all of the above to prioritize the next location along the frontier
           to move to next.
        
        Parameters:
            perception (dict):
                A dictionary providing the agent's current location
                and current tile type being stood upon, of the format:
                {"loc": (x, y), "tile": tile_type}
        
        Returns:
            tuple[int, int]:
                The maze location along the frontier that your agent will try to
                move into next.
        """
        frontier = self.env.get_frontier_locs()
        # [!] TODO! Agent is currently just making a random choice from the
        # frontier -- use logic and your own strategy to improve this!
        loc = self.env.get_player_loc()
        
        #part 1
        #Check if goal, start, and cardinals are in safetiles. 
        #if not, add them to safetiles and update kb to reflect
        tileType = perception["tile"]
        
        #part 2
        #add truth of current tile
        pit = False if tileType == "P" else True
        self.kb.tell(MazeClause([(("P", tileType),pit)]))

        pit_locations = self.env.get_cardinal_locs(loc, 1) - self.safe_tiles
        comb = combinations(pit_locations, 2)

        match tileType:

            case ".":
                self.kb.tell(MazeClause([(("P", loc),False)]))
                self.safe_tiles.add(loc)

                for cardinal in self.env.get_cardinal_locs(loc,1):
                    self.kb.tell(MazeClause([(("P", cardinal),False)]))
                    self.safe_tiles.add(cardinal)
            case "4":
                self.safe_tiles.add(loc)
                self.kb.tell(MazeClause([(("P", loc),False)]))

                for cardinal in self.env.get_cardinal_locs(loc,1):
                    self.kb.tell(MazeClause([(("P", cardinal),True)]))
            case "3":
                self.safe_tiles.add(loc)
                self.kb.tell(MazeClause([(("P", loc),False)]))

                for l in pit_locations:
                    self.kb.tell(MazeClause([(("P", l), True)]))
            case "2":
                self.safe_tiles.add(loc)
                self.kb.tell(MazeClause([(("P", loc),False)]))

                for prop in comb:
                    self.kb.tell(MazeClause([
                        (("P", prop[0]),True),
                        (("P", prop[1]),True)]))
                
                self.kb.tell(MazeClause([(("P", l),False) for l in pit_locations]))
            case "1":
                self.safe_tiles.add(loc)
                self.kb.tell(MazeClause([(("P", loc),False)]))

                for prop in comb:
                    self.kb.tell(MazeClause([
                        (("P", prop[0]),False),
                        (("P", prop[1]),False)]))
                
                self.kb.tell(MazeClause([(("P", l),True) for l in pit_locations]))
            case "P":
                self.pit_tiles.add(loc)
                self.kb.tell(MazeClause([(("P", loc), True)]))
            
        self.kb.simplify_from_known_locs(self.kb.clauses, self.safe_tiles, self.pit_tiles)
        # self.kb.simplify_self(self.pit_tiles, self.safe_tiles)
        #part 3
        #Check if any possible pits are now definitely safe or not
        self.scanKB(loc)

        #Priority for sorting: 
        #1.Number of warning tiles
        #2.Distance from goal
        #3.Tile included in most number of props?

        # Initialize priority outside the loop
        best_tile = (0,0)
        best_distance = 1000
        weight:float = 1   

        for tile in frontier:
            # Update priority based on the current tileType
            if tile in self.pit_tiles:
                continue

            distance = 0

            if float(abs(tile[0] - loc[0]) - abs(tile[1] - loc[1])) > 1:
                distance += (abs(tile[0] - loc[0]) + abs(tile[1] - loc[1]))

            # match tileType:
            #     case ".": #if current tile is safe move straight to goal
            #         if tile not in self.safe_tiles:
            #             weight = 0
            #         else:
            #             weight = 2
            #     case "3": #if 3, 3/4 + surrounding save tiles probibility of being pit
            #         weight = 1.75 + (len(self.env.get_cardinal_locs(tile, 1) & self.safe_tiles))/4
            #     case "2": #if 2, 2/4 + surrounding save tiles probibility of being pit
            #         weight = 1.5 + (len(self.env.get_cardinal_locs(tile, 1) & self.safe_tiles))/4
            #     case "1": #if 1, 1/4 + surrounding save tiles probibility of being pit
            #         weight = 1.25 + (len(self.env.get_cardinal_locs(tile, 1) & self.safe_tiles))/4
            #     case "P": #if P move towards goal
            #         weight = 1

            # Manhattan Distance for priority
            if tile in self.safe_tiles or tile not in self.pit_tiles:
                player_loc = self.env.get_player_loc()
                mDist = int(abs(tile[0] - self.goal[0]) + abs(tile[1] - self.goal[1]))
                new_distance = mDist + int(abs(tile[0] - player_loc[0]) + abs(tile[1] - player_loc[1]))
                with_weight = new_distance * weight
                if with_weight < best_distance:
                    best_distance = with_weight
                    best_tile = tile
                    print("tile: " ,new_distance)

        # Sort based on priority and Manhattan Distance
        if best_tile == (0,0):
            best_tile = min(
                frontier - self.pit_tiles,
                key = lambda tile: abs(tile[0] - self.goal[0]) + abs(tile[1] - self.goal[1]*weight)
            )

        print("best: ", best_distance)
        return best_tile
        
    def is_safe_tile (self, loc: tuple[int, int ]) -> Optional[bool]:
        """
        Determines whether or not the given maze location can be concluded as
        safe (i.e., not containing a pit), following the steps:
        1. Check to see if the location is already a known pit or safe tile,
           responding accordingly
        2. If not, performs the necessary queries on the knowledge base in an
           attempt to deduce its safety
        
        Parameters:
            loc (tuple[int, int]):
                The maze location in question
        
        Returns:
            One of three return values:
            1. True if the location is certainly safe (i.e., not pit)
            2. False if the location is certainly dangerous (i.e., pit)
            3. None if the safety of the location cannot be currently determined
        """
        # [!] TODO! Agent is currently dumb; this method should perform queries
        # on the agent's knowledge base from its gathered perceptions
        if loc in self.safe_tiles:
            return True
        elif loc in self.pit_tiles:
            return False 

        if self.kb.ask(MazeClause([(("P", loc),True)])):
            return False
        elif self.kb.ask(MazeClause([(("P", loc),False)])):
            return True
        else:   
            return None
        
    def scanKB (self, loc: tuple[int, int]) -> None:
        """
        Determines whether any new information passed into KB
        entails that any tile is now definitely safe, a pit,
        or neither

        Returns:
            None:
                Simply updating the kb and the number of 
                possible pits, nothing else
        """

        copySet: set[tuple[int, int]] = set()

        for l in self.possible_pits:
            confirmed = False
            if not self.is_safe_tile(l):
                self.kb.tell(MazeClause([(("P", loc),False)]))
                self.pit_tiles.add(l)
                confirmed = True
            elif self.is_safe_tile(l):
                self.kb.tell(MazeClause([(("P", loc),True)]))
                self.safe_tiles.add(l)
                confirmed = True
            elif not confirmed:
                copySet.add(l)
        
        self.possible_pits = copySet

# Declared here to avoid circular dependency
from environment import Environment