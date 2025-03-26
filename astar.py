Class PathNode:
    def __init__(self, x, y, parent=None):
        self.x = x
        self.y = y
        self.parent = parent
        self.g = 0  # Cost from start to this node
        self.h = 0  # Heuristic (estimated cost to goal)
        self.f = 0  # Total cost (g + h)
    
    def __lt__(self, other):
        # Comparison for priority queue
        return self.f < other.f
    
    def __eq__(self, other):
        # Check if two nodes are the same position
        return self.x == other.x and self.y == other.y

# Implement A* pathfinding algorithm
def a_star_pathfinding(start_x, start_y, goal_x, goal_y, max_iterations=1000):
    # Convert to grid coordinates
    start_grid_x, start_grid_y = int(start_x / TILE_SIZE), int(start_y / TILE_SIZE)
    goal_grid_x, goal_grid_y = int(goal_x / TILE_SIZE), int(goal_y / TILE_SIZE)
    
    # Check if start or goal is in a wall
    if MAP[start_grid_y][start_grid_x] != 0 or MAP[goal_grid_y][goal_grid_x] != 0:
        return []  # No valid path possible
    
    # Define movement directions (including diagonals)
    directions = [
        (0, -1),   # up
        (1, -1),   # up-right
        (1, 0),    # right
        (1, 1),    # down-right
        (0, 1),    # down
        (-1, 1),   # down-left
        (-1, 0),   # left
        (-1, -1),  # up-left
    ]
    
    # Initialize open and closed lists
    open_list = []
    closed_set = set()
    
    # Create start and end nodes
    start_node = PathNode(start_grid_x, start_grid_y)
    goal_node = PathNode(goal_grid_x, goal_grid_y)
    
    # Calculate heuristic for start node
    start_node.h = abs(start_node.x - goal_node.x) + abs(start_node.y - goal_node.y)
    start_node.f = start_node.h
    
    # Add start node to open list
    heapq.heappush(open_list, start_node)
    
    iterations = 0
    
    # Main loop
    while open_list and iterations < max_iterations:
        iterations += 1
        
        # Get node with lowest f score from open list
        current_node = heapq.heappop(open_list)
        
        # Check if reached goal
        if current_node.x == goal_node.x and current_node.y == goal_node.y:
            # Reconstruct path
            path = []
            while current_node:
                # Convert back to world coordinates (center of tile)
                path.append((current_node.x * TILE_SIZE + TILE_SIZE/2, 
                             current_node.y * TILE_SIZE + TILE_SIZE/2))
                current_node = current_node.parent
            return path[::-1]  # Return reversed path (start to goal)
        
        # Add current node to closed set
        closed_set.add((current_node.x, current_node.y))
        
        # Check all adjacent nodes
        for dx, dy in directions:
            # Calculate new position
            new_x, new_y = current_node.x + dx, current_node.y + dy
            
            # Check if valid position (within map bounds and not a wall)
            if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and 
                MAP[new_y][new_x] == 0 and (new_x, new_y) not in closed_set):
                
                # Create neighbor node
                neighbor = PathNode(new_x, new_y, current_node)
                
                # Calculate g score (cost from start to this node)
                # Diagonal movement costs more
                if dx != 0 and dy != 0:
                    # Check if diagonal path is blocked by walls (to prevent cutting corners)
                    if MAP[current_node.y][new_x] != 0 or MAP[new_y][current_node.x] != 0:
                        continue
                    neighbor.g = current_node.g + 1.414  # √2 for diagonal movement
                else:
                    neighbor.g = current_node.g + 1
                
                # Calculate h score (heuristic - estimated cost to goal)
                # Using Manhattan distance (abs(x1-x2) + abs(y1-y2))
                neighbor.h = abs(neighbor.x - goal_node.x) + abs(neighbor.y - goal_node.y)
                
                # Calculate f score (total cost)
                neighbor.f = neighbor.g + neighbor.h
                
                # Check if node is already in open list with better score
                better_node_exists = False
                for idx, open_node in enumerate(open_list):
                    if open_node == neighbor and open_node.g <= neighbor.g:
                        better_node_exists = True
                        break
                
                if not better_node_exists:
                    heapq.heappush(open_list, neighbor)
    
    # No path found
    return []

# Fast bulk texture rendering for walls
def render_textured_column(color_array, texture_column, tex_step, tex_start_pos, height, shade):
    """Fill a color array with texture data in one operation"""
    # Early exit for invalid heights
    if height <= 0:
        return