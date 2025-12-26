"""
Test nawigacji między heksami - sprawdzenie poprawności współrzędnych
"""

# Kierunki dla pointy-top hex w układzie axial (q, r)
neighbor_dirs = [
    (1, 0),   # E (prawo)
    (1, -1),  # NE (prawo-góra)
    (0, -1),  # NW (lewo-góra)
    (-1, 0),  # W (lewo)
    (-1, 1),  # SW (lewo-dół)
    (0, 1),   # SE (prawo-dół)
]

def get_neighbors(hex_id: str) -> dict:
    """Zwraca współrzędne sąsiadów dla danego heksa"""
    q, r = map(int, hex_id.split(","))
    neighbors = {}
    labels = ["E", "NE", "NW", "W", "SW", "SE"]
    
    for label, (dq, dr) in zip(labels, neighbor_dirs):
        neighbor_id = f"{q + dq},{r + dr}"
        neighbors[label] = neighbor_id
    
    return neighbors

def test_navigation():
    """Test przechodzenia po skosie w dół"""
    print("Test nawigacji heksagonalnej\n")
    print("=" * 50)
    
    # Startujemy z heksa 10,10
    current = "10,10"
    print(f"START: {current}")
    print(f"Sąsiedzi: {get_neighbors(current)}")
    print()
    
    # Klikamy SE (skos w dół na prawo)
    neighbors = get_neighbors(current)
    next_hex = neighbors["SE"]
    print(f"Klikam SE → przechodzę do: {next_hex}")
    
    # Sprawdzamy sąsiadów nowego heksa
    new_neighbors = get_neighbors(next_hex)
    print(f"Nowi sąsiedzi: {new_neighbors}")
    print()
    
    # Sprawdzamy czy pierwszy sąsiad z powrotem wskazuje na start
    print(f"Sprawdzenie: NW sąsiada {next_hex} = {new_neighbors['NW']}")
    print(f"Czy wraca do startu? {new_neighbors['NW'] == current}")
    print()
    
    # Test sekwencji
    print("=" * 50)
    print("Test sekwencji SE → SE → SE:")
    current = "10,10"
    path = [current]
    
    for i in range(3):
        neighbors = get_neighbors(current)
        current = neighbors["SE"]
        path.append(current)
        print(f"Krok {i+1}: {current}")
    
    print(f"\nŚcieżka: {' → '.join(path)}")
    print()
    
    # Test powrotu
    print("=" * 50)
    print("Test powrotu NW → NW → NW:")
    current = path[-1]
    return_path = [current]
    
    for i in range(3):
        neighbors = get_neighbors(current)
        current = neighbors["NW"]
        return_path.append(current)
        print(f"Krok {i+1}: {current}")
    
    print(f"\nŚcieżka powrotu: {' → '.join(return_path)}")
    print(f"Czy wróciliśmy do startu? {return_path[-1] == path[0]}")
    print()
    
    # Test wszystkich kierunków
    print("=" * 50)
    print("Test wszystkich kierunków z 10,10:")
    start = "10,10"
    neighbors = get_neighbors(start)
    
    for direction, neighbor_id in neighbors.items():
        # Sprawdź przeciwny kierunek
        opposite = {
            "E": "W", "W": "E",
            "NE": "SW", "SW": "NE",
            "NW": "SE", "SE": "NW"
        }
        
        back_neighbors = get_neighbors(neighbor_id)
        back_id = back_neighbors[opposite[direction]]
        matches = back_id == start
        
        print(f"{direction:3} → {neighbor_id:8} | Powrót {opposite[direction]:3}: {back_id:8} {'✓' if matches else '✗ BŁĄD'}")

if __name__ == "__main__":
    test_navigation()
