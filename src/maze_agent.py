import time
import random
import math
from queue import Queue
from constants import *
from maze_clause import *
from maze_knowledge_base import *

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
        
        # [!] TODO: Initialize any other knowledge-related attributes for
        # agent here, or any other record-keeping attributes you'd like
        
        
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
        explored = self.env.get_explored_locs()
        playable = self.env.get_playable_locs()


        #part 1
        frontier.remove(loc)
        self.safe_tiles.update(loc)
        explored.update(loc)
        #tileType = perception[tile]
        
        #part 2
        #add truth of current tile being safe, then simplify
        #self.kb.tell(loc)
        #self.kb.simplify_from_known_locs(self.kb.clauses, self.safe_tiles, self.pit_tiles)
        # if tileType != ".":
        #     for card in self.env.get_cardinal_locs(loc, 1):
        #         self.possible_pits.add(card)
        
        #part 3
        #Check if any possible pits are now definitely safe or not
        for loc in self.possible_pits:
            if not self.is_safe_tile(loc):
                self.possible_pits.remove(loc)
                self.pit_tiles.update(loc)

        #finish sorting
        #Priority for sorting: 
        #1.Number of warning tiles
        #2.Distance from goal
        self.possible_pits = sorted(self.possible_pits, key=lambda item: item[1])

        
        return random.choice(list(frontier))
        
    def is_safe_tile (self, loc: tuple[int, int]) -> Optional[bool]:
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
        
        pit_location = self.kb.ask(MazeClause([((loc, "P"),True)]))
        not_pit_location = self.kb.ask(MazeClause([((loc, "P"),False)]))

        if pit_location: 
            return False
        elif not_pit_location:
            return True
        else:   
            return None

# Declared here to avoid circular dependency
from environment import Environment