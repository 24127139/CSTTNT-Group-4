from collections import deque
import heapq
import time
import tracemalloc
from game import FreeCell, GameState, Move, Suit, Rank


class SolverResult:
    """Stores solver results with metrics"""
    
    def __init__(self):
        self.solution = []  # List of Move objects
        self.search_time = 0.0
        self.memory_usage = 0  # Peak memory in bytes
        self.expanded_nodes = 0
        self.solution_length = 0
        self.found = False
        self.error_msg = ""


class BaseSolver:
    """Base class for all solvers"""
    
    def __init__(self, game):
        self.game = game
        self.expanded_nodes = 0
        self.visited = set()
    
    def reconstruct_path(self, current_state, parent_map):
        """Reconstruct solution path from parent map"""
        path = []
        current = current_state.to_hashable()
        
        while current in parent_map:
            move = parent_map[current]['move']
            path.append(move)
            current = parent_map[current]['state'].to_hashable()
        
        return path[::-1]  # Reverse to get correct order
    
    def solve(self, initial_state):
        """Solve should be implemented by subclasses"""
        raise NotImplementedError


class BFSSolver(BaseSolver):
    """Breadth-First Search Solver"""
    
    def solve(self, initial_state):
        """
        BFS explores all states at depth d before depth d+1.
        Guarantees shortest solution (minimum moves).
        """
        result = SolverResult()
        tracemalloc.start()
        start_time = time.perf_counter()
        
        try:
            queue = deque([initial_state])
            self.visited = {initial_state.to_hashable()}
            parent_map = {}
            
            while queue:
                current_state = queue.popleft()
                self.expanded_nodes += 1
                
                # Check if goal reached
                if current_state.is_goal():
                    result.solution = self.reconstruct_path(current_state, parent_map)
                    result.found = True
                    break
                
                # Generate next moves
                moves = self.game.get_possible_moves(current_state)
                
                for move in moves:
                    next_state = self.game.apply_move(current_state, move)
                    state_hash = next_state.to_hashable()
                    
                    if state_hash not in self.visited:
                        self.visited.add(state_hash)
                        parent_map[state_hash] = {
                            'move': move,
                            'state': current_state
                        }
                        queue.append(next_state)
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            result.search_time = time.perf_counter() - start_time
            result.memory_usage = peak
            result.expanded_nodes = self.expanded_nodes
            result.solution_length = len(result.solution)
            
        except Exception as e:
            result.error_msg = str(e)
            tracemalloc.stop()
        
        return result


class DFSSolver(BaseSolver):
    """Depth-First Search Solver (with depth limit to avoid infinite loops)"""
    
    def solve(self, initial_state, depth_limit=50):
        """
        DFS explores as far as possible along each branch before backtracking.
        Uses depth limit to prevent infinite exploration.
        """
        result = SolverResult()
        tracemalloc.start()
        start_time = time.perf_counter()
        
        try:
            stack = [(initial_state, [])]  # (state, path)
            self.visited = set()
            
            while stack:
                current_state, path = stack.pop()
                state_hash = current_state.to_hashable()
                
                # Avoid cycles
                if state_hash in self.visited:
                    continue
                
                self.visited.add(state_hash)
                self.expanded_nodes += 1
                
                # Check if goal reached
                if current_state.is_goal():
                    result.solution = path
                    result.found = True
                    break
                
                # Check depth limit
                if len(path) >= depth_limit:
                    continue
                
                # Generate next moves (in reverse for proper order)
                moves = self.game.get_possible_moves(current_state)
                
                for move in reversed(moves):
                    next_state = self.game.apply_move(current_state, move)
                    next_hash = next_state.to_hashable()
                    
                    if next_hash not in self.visited:
                        stack.append((next_state, path + [move]))
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            result.search_time = time.perf_counter() - start_time
            result.memory_usage = peak
            result.expanded_nodes = self.expanded_nodes
            result.solution_length = len(result.solution)
            
        except Exception as e:
            result.error_msg = str(e)
            tracemalloc.stop()
        
        return result


class UCSSolver(BaseSolver):
    """Uniform-Cost Search Solver"""
    
    @staticmethod
    def calculate_move_cost(move):
        """
        Cost function for UCS.
        
        Different moves have different costs:
        - Moving to foundation: cost 0.5 (very cheap - we want this!)
        - Moving to cascade: cost 1.0 (normal move)
        - Moving to free cell: cost 1.5 (more expensive - should avoid clogging free cells)
        """
        if move.dest_type == 'foundation':
            return 0.5
        elif move.dest_type == 'cascade':
            return 1.0
        elif move.dest_type == 'freecell':
            return 1.5
        return 1.0
    
    def solve(self, initial_state):
        """
        UCS explores states in order of cost from start.
        Guarantees minimum cost solution.
        """
        result = SolverResult()
        tracemalloc.start()
        start_time = time.perf_counter()
        
        try:
            # (cost, counter, state, path)
            heap = [(0, 0, initial_state, [])]
            counter = 1
            self.visited = {}  # state_hash -> best_cost
            
            while heap:
                cost, _, current_state, path = heapq.heappop(heap)
                state_hash = current_state.to_hashable()
                
                # Skip if we've seen this state with better cost
                if state_hash in self.visited and self.visited[state_hash] <= cost:
                    continue
                
                self.visited[state_hash] = cost
                self.expanded_nodes += 1
                
                # Check if goal reached
                if current_state.is_goal():
                    result.solution = path
                    result.found = True
                    break
                
                # Generate next moves
                moves = self.game.get_possible_moves(current_state)
                
                for move in moves:
                    next_state = self.game.apply_move(current_state, move)
                    next_hash = next_state.to_hashable()
                    move_cost = self.calculate_move_cost(move)
                    new_cost = cost + move_cost
                    
                    # Only add if we haven't seen it or found a better path
                    if next_hash not in self.visited or self.visited[next_hash] > new_cost:
                        heapq.heappush(heap, (new_cost, counter, next_state, path + [move]))
                        counter += 1
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            result.search_time = time.perf_counter() - start_time
            result.memory_usage = peak
            result.expanded_nodes = self.expanded_nodes
            result.solution_length = len(result.solution)
            
        except Exception as e:
            result.error_msg = str(e)
            tracemalloc.stop()
        
        return result


class AStarSolver(BaseSolver):
    """A* Search Solver with heuristic"""
    
    @staticmethod
    def heuristic(state):
        """
        Heuristic for A* - estimates remaining cost to goal.
        
        Components:
        1. Cards not in foundation (each needs at least 1 move)
        2. Penalty for cards buried deep (especially low ranks)
        3. Bonus for empty free cells/cascades (more flexibility)
        
        Admissible: Never overestimates actual remaining cost.
        """
        h = 0
        
        # 1. Count cards not in foundation
        cards_in_foundation = sum(state.foundations[suit] for suit in Suit)
        cards_not_placed = 52 - cards_in_foundation
        h += cards_not_placed
        
        # 2. Penalty for low-rank cards buried in cascades
        # Low rank cards (A, 2, 3, etc.) should go to foundation first
        for col_idx, cascade in enumerate(state.cascades):
            for card_idx, card in enumerate(cascade):
                depth_from_top = len(cascade) - card_idx - 1
                
                # Low rank cards (A=1, 2=2, 3=3) are important
                if card.rank.numeric_value <= 3:
                    h += depth_from_top * 0.5  # Penalty for being buried
        
        # 3. Bonus for empty free cells (more flexibility = closer to goal)
        empty_free_cells = state.get_empty_free_cells()
        h -= empty_free_cells * 0.5
        
        # 4. Bonus for empty cascades (more flexibility)
        empty_cascades = state.get_empty_cascades()
        h -= empty_cascades * 0.3
        
        return max(1, h)  # At least 1
    
    def solve(self, initial_state):
        """
        A* combines BFS (explores systematically) with heuristic.
        Explores states with lowest f(n) = g(n) + h(n) first.
        """
        result = SolverResult()
        tracemalloc.start()
        start_time = time.perf_counter()
        
        try:
            # (f_score, counter, state, path, g_score)
            h_initial = self.heuristic(initial_state)
            heap = [(h_initial, 0, initial_state, [], 0)]
            counter = 1
            self.visited = {}  # state_hash -> best_g_score
            
            while heap:
                f_score, _, current_state, path, g_score = heapq.heappop(heap)
                state_hash = current_state.to_hashable()
                
                # Skip if we've seen this state with lower g_score
                if state_hash in self.visited and self.visited[state_hash] <= g_score:
                    continue
                
                self.visited[state_hash] = g_score
                self.expanded_nodes += 1
                
                # Check if goal reached
                if current_state.is_goal():
                    result.solution = path
                    result.found = True
                    break
                
                # Generate next moves
                moves = self.game.get_possible_moves(current_state)
                
                for move in moves:
                    next_state = self.game.apply_move(current_state, move)
                    next_hash = next_state.to_hashable()
                    new_g_score = g_score + 1  # Each move costs 1 (for solution length)
                    h_next = self.heuristic(next_state)
                    new_f_score = new_g_score + h_next
                    
                    # Only add if we haven't seen it or found a better path
                    if next_hash not in self.visited or self.visited[next_hash] > new_g_score:
                        heapq.heappush(heap, (new_f_score, counter, next_state, path + [move], new_g_score))
                        counter += 1
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            result.search_time = time.perf_counter() - start_time
            result.memory_usage = peak
            result.expanded_nodes = self.expanded_nodes
            result.solution_length = len(result.solution)
            
        except Exception as e:
            result.error_msg = str(e)
            tracemalloc.stop()
        
        return result


# Test the solvers
if __name__ == "__main__":
    from pysol_cards.deal_game import Game
    from pysol_cards.random_base import RandomBase
    from pysol_cards.cards import CardRenderer
    import random
    
    # Generate a board
    layout = Game(
        game_id="freecell",
        game_num=1,
        which_deals=RandomBase.DEALS_MS,
        max_rank=13
    ).calc_layout_string(CardRenderer(print_ts=True))
    
    board = []
    for line in layout.split("\n"):
        cards = line.split()
        board.append(cards)
    
    # Create game and load board
    game = FreeCell()
    game.load_from_board(board)
    
    print("Testing BFS...")
    bfs_solver = BFSSolver(game)
    bfs_result = bfs_solver.solve(game.state)
    print(f"  Found: {bfs_result.found}")
    print(f"  Solution length: {bfs_result.solution_length}")
    print(f"  Expanded nodes: {bfs_result.expanded_nodes}")
    print(f"  Time: {bfs_result.search_time:.3f}s")
    print(f"  Memory: {bfs_result.memory_usage / 1024:.1f} KB")