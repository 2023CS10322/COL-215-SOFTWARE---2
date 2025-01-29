
class Gate:
    def __init__(self, name, width, height, pins):
        self.name = name
        self.width = width
        self.height = height
        self.pins = pins  # List of pin coordinates (x, y) relative to the gate's position
        self.position = (0, 0)  # Default bottom-left position of the gate (to be calculated later)

    def __repr__(self):
        return f"Gate({self.name}, {self.width}x{self.height}, Pins: {self.pins}, Position: {self.position})"

class Wire:
    def __init__(self, pin1, pin2):
        self.pin1 = pin1  # (gate_name, pin_number)
        self.pin2 = pin2  # (gate_name, pin_number)

    def __repr__(self):
        return f"Wire({self.pin1} -> {self.pin2})"

class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.occupied = set()
    def is_empty(self, x, y, w, h):#check
        """Check if the space is available for a gate with width w and height h starting at (x, y)."""
        if x + w > self.width or y + h > self.height:
            return False
        for i in range(x, x + w):
            if (i,y) in self.occupied:
                return False
            if (i,y+h-1) in self.occupied:
                return False
        for i in range(y,y+h):
            if (x,i) in self.occupied:
                return False
            if (x+w-1,i) in self.occupied:
                return False
        return True
    def mark_occupied(self, location, w, h):
        """Mark the grid cells occupied by a gate starting at location (x, y) and spanning w x h."""
        x, y = location
        for i in range(x, x + w):
            for j in range(y, y + h):
                self.occupied.add((i, j))
    def place_gate(self, gate, position):
        """Place the gate at a specified position (x, y) on the grid."""
        x, y = position
        if self.is_empty(x, y, gate.width, gate.height):
            gate.position = (x, y)  # Set the gate's position
            self.mark_occupied((x, y), gate.width, gate.height)  # Mark grid as occupied
            return position  # Return the position where the gate was placed
        else:
            print(f"Cannot place gate at {position}; it is occupied.")
            return None  # Return None if the position is not valid

def calculate_bounding_box(positions):
    """Calculate the bounding box of a set of gate positions."""
    min_x = min(pos[0] for pos in positions)
    max_x = max(pos[0] for pos in positions)
    min_y = min(pos[1] for pos in positions)
    max_y = max(pos[1] for pos in positions)
    width = max_x - min_x
    height = max_y - min_y
    return width, height
def calculate_semi_perimeter(positions):
    """Calculate the semi-perimeter of the bounding box for a set of gate positions."""
    width, height = calculate_bounding_box(positions)
    return width + height
def parse_input(file_path):
    """Parse the input file to extract gates and wires information."""
    try:
        gates = {}
        wires = []
        
        with open(file_path, 'r') as file:
            lines = file.readlines()
            current_gate = None
            
            for line in lines:
                tokens = line.split()
                if len(tokens) == 0:
                    continue  # Skip empty lines
                if tokens[0][0] == 'g':  # Gate definition, e.g. "g1 3 3"
                    gate_name = tokens[0]
                    width = int(tokens[1])
                    height = int(tokens[2])
                    gates[gate_name] = Gate(gate_name, width, height, [])
                    current_gate = gates[gate_name]
                elif tokens[0] == 'pins' and current_gate:  # Pin coordinates, e.g. "pins g1 0 1 0 2"
                    for i in range(2, len(tokens), 2):
                        pin_x = int(tokens[i])
                        pin_y = int(tokens[i+1])
                        current_gate.pins.append((pin_x, pin_y))
                elif tokens[0] == 'wire':  # Wire definition, e.g. "wire g3.p2 g7.p1"
                    wire1 = tokens[1].split('.')
                    wire2 = tokens[2].split('.')
                    gate1 = wire1[0]
                    pin1 = int(wire1[1][1:])  # Remove the 'p' from the pin number
                    gate2 = wire2[0]
                    pin2 = int(wire2[1][1:])  # Remove the 'p' from the pin number
                    wire = Wire(f"{gate1}.p{pin1}", f"{gate2}.p{pin2}")
                    wires.append(wire)
        
        return gates, wires
    except FileNotFoundError:
        print("File not found")
        return None, None
    except Exception as e:
        print("Error parsing input file: ", str(e))
        return None, None
class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, x):
        """Find the representative of the set that contains x."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x, y):
        """Merge the sets that contain x and y, ensuring they are from different gates."""
        rootX = self.find(x)
        rootY = self.find(y)

        if rootX != rootY:
            # Union by rank
            if self.rank[rootX] > self.rank[rootY]:
                self.parent[rootY] = rootX
            elif self.rank[rootX] < self.rank[rootY]:
                self.parent[rootX] = rootY
            else:
                self.parent[rootY] = rootX
                self.rank[rootX] += 1

    def add(self, x):
        """Add a new element with itself as the parent."""
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def get_clusters(self):
        """Return the clusters of connected pins."""
        clusters = {}
        for pin in self.parent:
            root = self.find(pin)
            if root not in clusters:
                clusters[root] = set()
            clusters[root].add(pin)
        return list(clusters.values())

def form_clusters(gates, wires):
    uf = UnionFind()

    # Add all pins to the union-find structure
    for gate in gates.values():
        for i, pin in enumerate(gate.pins):
            pin_identifier = f"{gate.name}.p{i+1}"
            uf.add(pin_identifier)

    # Union the pins that are connected by wires, but only if they belong to different gates
    for wire in wires:
        gate1_name, pin1 = wire.pin1.split('.')
        gate2_name, pin2 = wire.pin2.split('.')

        if gate1_name != gate2_name:  # Ensure pins belong to different gates
            uf.union(wire.pin1, wire.pin2)

    # Get and return the clusters of connected pins
    return uf.get_clusters()
def generate_perimeter_positions(gate_name, gate_position, gates, perimeter_positions):
    x, y = gate_position  # Unpack the gate's position
    gate = gates[gate_name]

    # Add positions adjacent to the gate's entire boundary based on its width and height
    for i in range(gate.width):
        # Top and bottom perimeter (above and below the gate)
        perimeter_positions.add((x + i, y,"bottom"))  # Above (top side)
        perimeter_positions.add((x + i, y + gate.height,"top"))  # Below (bottom side)

    for j in range(gate.height):
        # Left and right perimeter (beside the gate)
        perimeter_positions.add((x, y + j,"left"))  # Left side
        perimeter_positions.add((x + gate.width, y + j,"right"))  # Right side

    return perimeter_positions  # Return the updated perimeter positions
 # Return the updated perimeter positions
 # Return a list of unique perimeter positions

            
def place_gates(grid, gates, clusters):
    placed_gates = set()
    placed_gates_position = set()
    total_wire_length = 0  # Initialize total wire length

    # Sort clusters by the number of pins (largest to smallest)
    sorted_clusters = sorted(clusters, key=lambda cluster: len(cluster), reverse=True)
    
    # Debugging: Print sorted clusters
    print(f"Sorted Clusters (by size): {sorted_clusters}")
    candidate_positions = set()
    
    for cluster in sorted_clusters:
        cluster=list(cluster)
        cluster.sort()
        
        gates_placed_in_this_cluster=set()
        print(len(candidate_positions))
        cluster_positions = []
        initial_semi_perimeter=0
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        for pin in cluster:
            gate_name, pin_number = pin.split('.')
            gate = gates[gate_name]
            
            if gate_name in placed_gates:
                relative_pin_coordinates = gate.pins[int(pin_number[1]) - 1]
                cluster_positions.append((gate.position[0] + relative_pin_coordinates[0], gate.position[1] + relative_pin_coordinates[1]))
                min_x = min(min_x, gate.position[0] + relative_pin_coordinates[0])
                max_x = max(max_x, gate.position[0] + relative_pin_coordinates[0])
                min_y = min(min_y, gate.position[1] + relative_pin_coordinates[1])
                max_y = max(max_y, gate.position[1] + relative_pin_coordinates[1])
                initial_semi_perimeter=max_x-min_x+max_y-min_y

        print(f"\nPlacing cluster: {cluster}", cluster_positions)  # Debugging: Start placing a new cluster

        positions_to_remove = []  # Keep track of positions to be removed safely

        for pin in cluster:
            gate_name, pin_number = pin.split('.')
            gate = gates[gate_name]
            if gate_name not in placed_gates:
                # Try to place the gate on the grid
                best_position = None                
                best_semi_perimeter = float('inf')
                best_gate_position = None

                if placed_gates_position:
                    pass
                    print("Generating candidate positions")
                    # Generate candidate positions based on already placed gates
                    # candidate_positions = generate_perimeter_positions(placed_gates_position, gates)
                else:
                    grid.place_gate(gate, (0, 0))
                    placed_gates_position.add((gate_name, (0, 0)))  # Place the gate at the optimal position
                    placed_gates.add(gate_name)
                    relative_pin_coordinates = gate.pins[int(pin_number[1]) - 1]
                    temp_position = (relative_pin_coordinates[0], relative_pin_coordinates[1])
                    cluster_positions.append(temp_position)
                    min_x = min(min_x, relative_pin_coordinates[0])
                    max_x = max(max_x, relative_pin_coordinates[0])
                    min_y = min(min_y, relative_pin_coordinates[1])
                    max_y = max(max_y, relative_pin_coordinates[1])
                    candidate_positions = generate_perimeter_positions(gate_name, (0, 0), gates, candidate_positions)
                    # for i in range(0,gate.width):
                    #     if i in height:
                    #         height[i]+=gate.height
                    #     else:
                    #         height[i]=gate.height
                    continue

                # Iterate through candidate positions and find the best placement
                for x, y, z in candidate_positions:
                    if z == "bottom":
                        y = y - gate.height
                    if z == "left":
                        x = x - gate.width
                    if grid.is_empty(x, y, gate.width, gate.height):
                        relative_pin_coordinates = gate.pins[int(pin_number[1]) - 1]
                        temp_position = (x + relative_pin_coordinates[0], y + relative_pin_coordinates[1])
                        cluster_positions.append(temp_position)
                        new_min_x = min(min_x, temp_position[0])
                        new_max_x = max(max_x, temp_position[0])
                        new_min_y = min(min_y, temp_position[1])
                        new_max_y = max(max_y, temp_position[1])
                        semi_perimeter= (new_max_x - new_min_x) + (new_max_y - new_min_y)
                        # semi_perimeter = calculate_semi_perimeter(cluster_positions)

                        if semi_perimeter < best_semi_perimeter:
                            best_semi_perimeter = semi_perimeter
                            best_position = temp_position
                            best_gate_position = (x, y)

                        # Remove the temporary position after checking
                        cluster_positions.pop()
                    else:
                        if z == "bottom":
                            y = y + gate.height

                        elif z == "left":
                            x = x + gate.width
                        else:
                            positions_to_remove.append((x, y, z))
                            continue

                # After iterating through candidate positions, remove the positions that should no longer be considered
                for position in positions_to_remove:
                    candidate_positions.discard(position)

                if best_position:
                    grid.place_gate(gate, best_gate_position)
                    placed_gates_position.add((gate_name, best_gate_position))  # Place the gate at the optimal position
                    placed_gates.add(gate_name)
                    gates_placed_in_this_cluster.add(gate_name)
                    cluster_positions.append(best_position)
                    candidate_positions = generate_perimeter_positions(gate_name, best_gate_position, gates, candidate_positions)
                    min_x = min(min_x, best_position[0])
                    max_x = max(max_x, best_position[0])
                    min_y = min(min_y, best_position[1])
                    max_y = max(max_y, best_position[1])
                    # for i in range(best_gate_position[0],best_gate_position[0]+gate.width):
                    #     if i in height:
                    #         height[i]+=gate.height
                    #     else:
                    #         height[i]=gate.height
                    initial_semi_perimeter = (max_x - min_x) + (max_y - min_y)
            elif gate_name in gates_placed_in_this_cluster:
                relative_pin_coordinates = gate.pins[int(pin_number[1]) - 1]
                temp_position = (gate.position[0] + relative_pin_coordinates[0], gate.position[1] + relative_pin_coordinates[1])
                min_x = min(min_x, gate.position[0] + relative_pin_coordinates[0])
                max_x = max(max_x, gate.position[0] + relative_pin_coordinates[0])
                min_y = min(min_y, gate.position[1] + relative_pin_coordinates[1])
                max_y = max(max_y, gate.position[1] + relative_pin_coordinates[1])
                initial_semi_perimeter = (max_x - min_x) + (max_y - min_y)
        if cluster_positions:
            total_wire_length += initial_semi_perimeter 
            # cluster_semi_perimeter = calculate_semi_perimeter(cluster_positions)
            # total_wire_length += cluster_semi_perimeter  # Add the semi-perimeter to the total wire length

    return placed_gates, total_wire_length


def write_gate_dimensions_file(gates, output_file):
    """
    Write the gate dimensions to an output file in the format:
    gate_name width height
    """
    with open(output_file, 'w') as f:
        for gate_name, gate in gates.items():
            f.write(f"{gate_name} {gate.width} {gate.height}\n")
    print(f"Gate dimensions written to {output_file}")
def write_output(file_path, gates,total_wire_length):
    # Calculate the overall bounding box for the placed gates
    placed_positions = [gate.position for gate in gates.values()]
    width, height = calculate_bounding_box(placed_positions)

    with open(file_path, 'w') as file:
        # Write the bounding box dimensions
        file.write(f"bounding_box {width} {height}\n")

        # Write the position of each gate
        for gate in gates.values():
            x, y = gate.position
            file.write(f"{gate.name} {x} {y}\n")
        file.write(f"wirelength {total_wire_length}\n")
    print(f"Output written to {file_path}")
def adjust_coordinates(gates):
    """Adjust the gate positions and pins to make all coordinates positive."""
    # Get all gate positions
    positions = [gate.position for gate in gates.values()]
    min_x = min(pos[0] for pos in positions)
    min_y = min(pos[1] for pos in positions)

    # Adjust all gate positions and pins to be positive
    offset_x = -min_x if min_x < 0 else 0
    offset_y = -min_y if min_y < 0 else 0

    for gate in gates.values():
        # Adjust gate position
        gate.position = (gate.position[0] + offset_x, gate.position[1] + offset_y)
        # Adjust pin coordinates
        gate.pins = [(pin[0] + offset_x, pin[1] + offset_y) for pin in gate.pins]

# Example usage


# Example usage with the parsed gates and wires
# clusters = form_clusters(gates.value, wires)

# # Print the clusters
# print("Connected Pin Clusters:")
# for cluster in clusters:
#     print(cluster)

# gates, wires = parse_input('testnew.txt')
# grid = Grid(500000,500000)
# clusters=form_clusters(gates,wires)

            

# placed_gates, total_wire_length = place_gates(grid, gates, clusters)
# adjust_coordinates(gates)
# write_output("new_output.txt",gates,total_wire_length)
# print(total_wire_length)

def main(input_file, output_file):
    gates, wires = parse_input(input_file)
    if gates is None or wires is None:
        print("Failed to parse input file.")
        return

    grid = Grid(1000000, 1000000)
    clusters = form_clusters(gates, wires)

    placed_gates, total_wire_length = place_gates(grid, gates, clusters)
    adjust_coordinates(gates)
    write_output(output_file, gates, total_wire_length)
    print(f"Total wire length: {total_wire_length}")

if __name__ == "__main__":
    input_file = input("Please enter the input file name: ")  # Prompt user for input file name
    output_file = input("Please enter the desired output file name: ")  # Prompt user for output file name
    main(input_file, output_file)
# Print parsed gates and wires for verification
# if gates and wires:
#     print("Parsed Gates:")
#     for gate in gates.values():
#         print(gate)

#     print("\nParsed Wires:")
#     for wire in wires:
#         print(wire)

#     # Create a grid and place gates
