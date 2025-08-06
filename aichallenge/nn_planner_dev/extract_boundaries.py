import argparse
import numpy as np
import lanelet2
import rosbag2_py
from pathlib import Path
from tqdm import tqdm

# We need to borrow some functions from post_process
from post_process import get_rosbag_options, deserialize_message

# ======================================================================================
# Constants
# ======================================================================================
MAP_TOPIC = "/map/vector_map"

# ======================================================================================
# Main Logic
# ======================================================================================

def load_map_data(bag_path: Path):
    """
    Loads the binary map data from the first HADMapBin message in a rosbag.
    """
    print(f"Loading map data from rosbag: {bag_path}")
    options, converter_options = get_rosbag_options(str(bag_path))
    reader = rosbag2_py.SequentialReader()
    reader.open(options, converter_options)

    topic_types = reader.get_all_topics_and_types()
    type_map = {topic.name: topic.type for topic in topic_types}
    map_msg_type = type_map.get(MAP_TOPIC)

    if not map_msg_type:
        raise RuntimeError(f"Topic '{MAP_TOPIC}' not found in the bag file.")

    while reader.has_next():
        (topic, data, t) = reader.read_next()
        if topic == MAP_TOPIC:
            print("  + Found map message. Deserializing...")
            msg = deserialize_message(data, map_msg_type)
            # The actual map is in the 'data' field as a binary blob
            return msg.data

    raise RuntimeError(f"No message found for topic '{MAP_TOPIC}' in the bag file.")

def main(bag_path: Path, output_dir: Path):
    """
    Main function to load map, parse it, extract boundaries, and save them.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load the binary map data from the rosbag
    map_binary_data = load_map_data(bag_path)

    # Step 2: Use lanelet2 to load the map from the binary data
    # We need to load it into a LaneletMap object. The lanelet2 library can
    # load from a file, so we'll write the binary data to a temporary file.
    tmp_map_path = output_dir / "temp_map.osm"
    with open(tmp_map_path, "wb") as f:
        f.write(map_binary_data)
    
    print(f"  + Wrote binary map data to temporary file: {tmp_map_path}")

    # Define the projector to convert lat/lon to local x/y.
    # We assume the map is in a UTM projection, which is common.
    # We need to find the origin from the map data itself if possible,
    # but for now, we can use a default or assume it's already in a local frame.
    # The provided data seems to be in a local metric frame already, so we use a basic projector.
    projector = lanelet2.projection.UtmProjector(lanelet2.io.Origin(0, 0))
    
    print("  + Loading map with lanelet2 library...")
    try:
        loaded_map = lanelet2.io.load(str(tmp_map_path), projector)
        print("  + Map loaded successfully.")
    except Exception as e:
        print(f"Error loading map with lanelet2: {e}")
        # Clean up the temporary file
        tmp_map_path.unlink()
        return

    # Step 3: Extract the physical road boundaries
    # We iterate through all lanelets and find those that are on the edge of the road.
    # A boundary is an edge if it's not shared between two lanelets.
    print("  + Extracting physical boundaries...")
    
    all_linestrings = loaded_map.lineStringLayer
    boundary_linestrings = []

    for ls in tqdm(all_linestrings):
        # In lanelet2, if a linestring is a boundary, it usually has a "type" tag.
        # We are looking for "road_border".
        if ls.attributes.get("type") == "road_border":
            boundary_linestrings.append(ls)

    if not boundary_linestrings:
        print("Warning: No linestrings with 'type'='road_border' found. Trying another method.")
        # Fallback method: find all lanelet bounds that are not used by other lanelets.
        # This is more complex. For now, we will assume the 'road_border' tag exists.
        # If this fails, we will need to implement the more complex graph traversal.
        print("Please inspect your map file in a tool like JOSM to check boundary tags.")

    # For simplicity, we can't easily distinguish left/right without more context.
    # We will save all boundary points into one file. The RL environment can
    # then just check the distance to the nearest point in this set.
    all_boundary_points = []
    for ls in boundary_linestrings:
        for pt in ls:
            all_boundary_points.append([pt.x, pt.y])

    all_boundary_points = np.array(all_boundary_points)

    if all_boundary_points.size == 0:
        print("Error: Could not extract any boundary points. Aborting.")
        # Clean up the temporary file
        tmp_map_path.unlink()
        return

    # Step 4: Save the extracted boundary points
    boundaries_path = output_dir / "road_boundaries.npy"
    np.save(boundaries_path, all_boundary_points)
    
    print(f"\n  + Successfully extracted {len(all_boundary_points)} boundary points.")
    print(f"  + Saved to: {boundaries_path}")
    print("\nExtraction complete. This file can now be used for robust collision detection.")

    # Clean up the temporary file
    tmp_map_path.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Extract physical road boundaries from a rosbag's HADMapBin message."
    )
    parser.add_argument(
        "bag_path", 
        type=str, 
        help="Path to the rosbag directory containing the map."
    )
    parser.add_argument(
        "--output_dir", 
        type=str, 
        default="processed_data/boundaries", 
        help="Directory to save the processed boundary .npy file."
    )
    
    args = parser.parse_args()
    
    main(Path(args.bag_path), Path(args.output_dir)) 