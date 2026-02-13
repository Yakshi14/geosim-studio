import networkx as nx
import os

def build_navigation_network():
    print("module 23:initializing navigation graph engine...")
    
    data_path="data/phase1_output/output_files"
    G=nx.Graph()
    
    # check if the path exists and is actually a directory
    if os.path.exists(data_path) and os.path.isdir(data_path):
        files=os.listdir(data_path)
        if not files:
            print("folder is empty.creating simulation node.")
            G.add_node("Sim_Origin")
        else:
            print(f"found {len(files)}files.Building graph...")
    else:
        print(f"Error:{data_path} is missing or is not a directory.")
        
        G.add_node("Safe_Start")

    print(f"graph status:{G.number_of_nodes()} intersections mapped.")
    return G

if __name__ == "__main__":
    build_navigation_network()