import sys
import os
import numpy as np


def init_d(capacities: np.ndarray, source: int) -> int:
	s_max = np.max(capacities[source])

	# Assuming integer weights
	d = 1
	while d * 2 <= s_max:
		d = d * 2

	return d


class ScalingFordFulkerson:
	def __init__(self, graph_file, file_delim=" "):
		self.graph, self.node_mapping = self.read_graph(graph_file, file_delim)
		self.num_nodes = len(self.node_mapping)
		self.source = self.node_mapping['s']
		self.sink = self.node_mapping['t']

	def augment(self, path: list, residual_graph: np.ndarray) -> int:
		min_capacity = min(residual_graph[u][v] for u, v in path)
		for u, v in path:
			residual_graph[u][v] -= min_capacity
			residual_graph[v][u] += min_capacity

		return min_capacity

	def dfs(self, start: int, end: int, path: list, residual_graph: np.ndarray, visited: list, d: int) -> list:
		visited[start] = True
		path.append(start)

		if start == end:
			return path

		for next_node, capacity in enumerate(residual_graph[start]):
			if not visited[next_node] and (capacity) >= d:
				result = self.dfs(next_node, end, path, residual_graph, visited, d)
				if result:
					return result

		path.pop()
		return None

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

	def init_residual_graph(self, residual_graph: np.ndarray, d: int):
		new_residual_graph = np.copy(residual_graph)

		for i in range(new_residual_graph.shape[0]):
			for j in range(new_residual_graph.shape[1]):
				if new_residual_graph[i, j] < d:
					new_residual_graph[i, j] = 0

		return new_residual_graph

	def scaling_ff(self) -> int:
		residual_graph: np.ndarray = np.copy(self.graph)
		d: int = init_d(self.graph, self.source)
		flow: int = 0

		while d >= 1:
			P = self.dfs(self.source, self.sink, [], residual_graph, [False] * self.num_nodes, d)
			while P:
				b = self.augment([(P[i], P[i + 1]) for i in range(len(P) - 1)], residual_graph)
				flow += b
				P = self.dfs(self.source, self.sink, [], residual_graph, [False] * self.num_nodes, d)
			d = d / 2

		return flow

	def scaling_ford_fulkerson(self):
		max_flow = 0
		residual_graph = self.graph.copy()

		while True:
			path = self.dfs(self.source, self.sink, [], residual_graph, [False] * self.num_nodes)

			if not path:
				break

			flow = self.augment([(path[i], path[i + 1]) for i in range(len(path) - 1)], residual_graph)
			max_flow += flow

		return max_flow

if __name__ == "__main__":	
	ford_fulkerson = ScalingFordFulkerson(sys.argv[1])
	result_sff = ford_fulkerson.scaling_ff()
	print("Flow SFF:", result_sff)
