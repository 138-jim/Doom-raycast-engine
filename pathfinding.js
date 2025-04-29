// Pathfinding.js - A* pathfinding implementation for enemy AI

class Pathfinding {
    constructor() {
        // Pre-calculate directions including diagonals
        this.directions = [
            [0, -1],  // up
            [1, -1],  // up-right
            [1, 0],   // right
            [1, 1],   // down-right
            [0, 1],   // down
            [-1, 1],  // down-left
            [-1, 0],  // left
            [-1, -1]  // up-left
        ];
    }
    
    // Find a path from (startX, startY) to (goalX, goalY)
    findPath(startX, startY, goalX, goalY, maxIterations = 1000) {
        // Convert to grid coordinates
        const startGridX = Math.floor(startX / TILE_SIZE);
        const startGridY = Math.floor(startY / TILE_SIZE);
        const goalGridX = Math.floor(goalX / TILE_SIZE);
        const goalGridY = Math.floor(goalY / TILE_SIZE);
        
        // Check if start or goal is in a wall
        if (startGridX < 0 || startGridX >= MAP_WIDTH || startGridY < 0 || startGridY >= MAP_HEIGHT ||
            goalGridX < 0 || goalGridX >= MAP_WIDTH || goalGridY < 0 || goalGridY >= MAP_HEIGHT ||
            MAP[startGridY][startGridX] !== 0 || MAP[goalGridY][goalGridX] !== 0) {
            return []; // No valid path possible
        }
        
        // Initialize open list (priority queue) and closed set
        const openList = [];
        const closedSet = new Set();
        
        // Create start and end nodes
        const startNode = {
            x: startGridX,
            y: startGridY,
            g: 0,
            h: this.manhattan(startGridX, startGridY, goalGridX, goalGridY),
            f: 0,
            parent: null
        };
        
        startNode.f = startNode.h;
        
        // Add start node to open list (min-heap priority queue)
        openList.push(startNode);
        
        let iterations = 0;
        
        // Main A* loop
        while (openList.length > 0 && iterations < maxIterations) {
            iterations++;
            
            // Sort by f-score and get node with lowest value
            openList.sort((a, b) => a.f - b.f);
            const currentNode = openList.shift();
            
            // Check if reached goal
            if (currentNode.x === goalGridX && currentNode.y === goalGridY) {
                // Reconstruct path
                const path = [];
                let node = currentNode;
                
                while (node) {
                    // Convert back to world coordinates (center of tile)
                    path.push([
                        node.x * TILE_SIZE + TILE_SIZE/2,
                        node.y * TILE_SIZE + TILE_SIZE/2
                    ]);
                    node = node.parent;
                }
                
                return path.reverse(); // Return path from start to goal
            }
            
            // Add current node to closed set
            closedSet.add(`${currentNode.x},${currentNode.y}`);
            
            // Check all adjacent nodes
            for (const [dx, dy] of this.directions) {
                // Calculate new position
                const newX = currentNode.x + dx;
                const newY = currentNode.y + dy;
                
                // Check if valid position (within map bounds and not a wall)
                if (newX >= 0 && newX < MAP_WIDTH && newY >= 0 && newY < MAP_HEIGHT &&
                    MAP[newY][newX] === 0 && !closedSet.has(`${newX},${newY}`)) {
                    
                    // Check if diagonal path is blocked by walls (to prevent cutting corners)
                    if (dx !== 0 && dy !== 0) {
                        if (MAP[currentNode.y][newX] !== 0 || MAP[newY][currentNode.x] !== 0) {
                            continue;
                        }
                    }
                    
                    // Calculate g score (cost from start to this node)
                    let gScore;
                    if (dx !== 0 && dy !== 0) {
                        gScore = currentNode.g + 1.414; // √2 for diagonal movement
                    } else {
                        gScore = currentNode.g + 1;
                    }
                    
                    // Create neighbor node
                    const neighbor = {
                        x: newX,
                        y: newY,
                        g: gScore,
                        h: this.manhattan(newX, newY, goalGridX, goalGridY),
                        parent: currentNode
                    };
                    
                    neighbor.f = neighbor.g + neighbor.h;
                    
                    // Check if node is already in open list with better score
                    const existingNode = openList.find(node => node.x === newX && node.y === newY);
                    
                    if (existingNode) {
                        if (existingNode.g <= neighbor.g) {
                            continue; // Skip this neighbor as existing path is better
                        }
                        // Otherwise, update existing node values
                        existingNode.g = neighbor.g;
                        existingNode.f = neighbor.f;
                        existingNode.parent = currentNode;
                    } else {
                        // Add new node to open list
                        openList.push(neighbor);
                    }
                }
            }
        }
        
        return []; // No path found
    }
    
    // Calculate Manhattan distance heuristic
    manhattan(x1, y1, x2, y2) {
        return Math.abs(x1 - x2) + Math.abs(y1 - y2);
    }
}