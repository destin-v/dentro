import networkx as nx
import numpy as np
import ray


@ray.remote
def rollout(G: nx.Graph, source: str = "root") -> list[tuple]:
    """Perform a rollout of the game using the probability distributions available in the tree.

    Args:
        G (nx.Graph): Networkx graph.
        source (str): The starting point of the game.  Usually "root" but can be defined by the user.

    Returns:
        list[tuple]: A list of decision points (edges) that represent the actions the and events that occurred during a rollout.  Each trajectory is a full play through from beginning to end of the game.
    """

    # Internal recursive function definition
    def recursive_rollout(G: nx.Graph, source: str, trajectory: list):
        edges = list(nx.dfs_edges(G, source, depth_limit=1))

        # Exit if no more edges are found
        if len(edges) == 0:
            return

        decisions = []
        distribution = []
        for u, v, d in G.edges(source, data=True):
            decisions.append((u, v))
            distribution.append(d["s"]["m"] / d["s"]["n"])

        # Add the selected decision to rollout
        index = np.random.choice(len(edges), p=distribution)
        trajectory.append(decisions[index])

        recursive_rollout(G, decisions[index][1], trajectory)

        return trajectory

    # Calling internal function
    trajectory: list = []
    recursive_rollout(G, source, trajectory)

    return trajectory


def load_aliases(G: nx.Graph) -> dict[str, dict]:
    """Each data dictionary of an edge has a `s` variable that represents the stats.  Within the `s` variable there is a unique Id.  In order to load aliasing we need to perform the following:

    * Identify all the unique Ids of aliased nodes/edges.
    * Load the Networkx graph so that each node/edge is pointing to the same data object stats `s`.

    Since saved files do not have any object linking, the loading process has to reconstruct the object pointer to point to the same data object when loading.  This process is simple conceptually but somewhat tricky to implement.

    Args:
        G (nx.Graph): Networkx graph.

    Returns:
        dict[str, dict]: A dictionary of a unique Id mapped to a dictionary representing the stats data `s` for that particular edge.
    """
    alias_edges = {}

    # Retrieve the aliases edges
    for u, v, data in G.edges(data=True):
        if data["s"].get("alias", False):
            uuid = data["s"]["id"]
            alias_edges[uuid] = data["s"]

    # Assign alias edges back into the graph tree
    for uuid, link in alias_edges.items():
        for u, v, data in G.edges(data=True):
            # Link the data only if a matching uuid is found
            check1 = data["s"].get("alias", False)
            check2 = data["s"].get("id", 0) == uuid
            if check1 and check2:
                data["s"] = link

    return alias_edges
