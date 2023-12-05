import sys
import os
import numpy as np

class FordFulkerson:
	def __init__(self, graph_file, file_delim=" "):
		self.graph, self.node_mapping = self.read_graph(graph_file, file_delim)
		self.num_nodes = len(self.node_mapping)
		self.source = self.node_mapping['s']
		self.sink = self.node_mapping['t']

	def read_graph(self, graph_file, delimiter=" "):
		with open(graph_file, 'r') as file:
			lines = file.readlines()

		graph = []
		node_mapping = {}
		node_count = 0

		for line in lines:
			# Bizzarely, this is last line of mesh graph files.
			if line == "Done Mesh\n":
				continue

			u, v, capacity = filter(None, line.split(delimiter))
			if u not in node_mapping:
				node_mapping[u] = node_count
				node_count += 1
			if v not in node_mapping:
				node_mapping[v] = node_count
				node_count += 1

			u, v, capacity = node_mapping[u], node_mapping[v], int(capacity)
			graph.append((u, v, capacity))

		adjacency_matrix = np.zeros((node_count, node_count), dtype=int)

		for u, v, capacity in graph:
			adjacency_matrix[u][v] = capacity

		return adjacency_matrix, node_mapping

	def augment(self, path, residual_graph):
		# Find the minimum capacity along the path and update the residual graph
		min_capacity = min(residual_graph[u][v] for u, v in path)
		for u, v in path:
			residual_graph[u][v] -= min_capacity
			residual_graph[v][u] += min_capacity

		return min_capacity

	def dfs(self, start, end, path, residual_graph, visited):
		visited[start] = True
		path.append(start)

		if start == end:
			return path

		for next_node, capacity in enumerate(residual_graph[start]):
			if not visited[next_node] and capacity > 0:
				result = self.dfs(next_node, end, path, residual_graph, visited)
				if result:
					return result

		path.pop()  # Revert changes to the path
		return None

	def ford_fulkerson(self):
		max_flow = 0
		residual_graph = self.graph.copy()

		while True:
			# Find an augmenting path using DFS
			path = self.dfs(self.source, self.sink, [], residual_graph, [False] * self.num_nodes)

			if not path:
				break  # No more augmenting paths

			# Augment the flow along the path
			flow = self.augment([(path[i], path[i + 1]) for i in range(len(path) - 1)], residual_graph)
			max_flow += flow

		return max_flow




if __name__ == "__main__":
	ford_fulkerson = FordFulkerson(sys.argv[1])
	result = ford_fulkerson.ford_fulkerson()
	print("Max Flow:", result)

