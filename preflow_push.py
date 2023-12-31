import sys
import heapq
import time
import pprint
import collections
import time

# Delimiter is space in all file types except bipartite, where it is tab.
def file_to_adjmat(fname, delimiter=' '):
	with open(fname, "r") as f:
		line = f.readline()
		node_to_index = {}
		edges = {}
		index = 0

		# This accounts for weird case where last line of mesh graph files
		# as generated by Java code is "Done Mesh\n".
		while line and line != "Done Mesh\n":
			fields = list(filter(None, line.split(delimiter)))
			if fields[0] not in node_to_index:
				node_to_index[fields[0]] = index
				edges[index] = {}
				index += 1
			if fields[1] not in node_to_index:
				node_to_index[fields[1]] = index
				edges[index] = {}
				index += 1

			src_ind = node_to_index[fields[0]]
			dst_ind = node_to_index[fields[1]]
			edges[src_ind][dst_ind] = int(fields[2])
			line = f.readline()

		adj_mat = [[0 for i in range(index)] for i in range(index)]
		for (src, dst_dict) in edges.items():
			for (dst, cap) in dst_dict.items():
				adj_mat[src][dst] = cap

		src = node_to_index['s']
		sink = node_to_index['t']
		return (src, sink, adj_mat)

class PreflowPushSolver:
	def __init__(self, adj_mat, source, sink, debug=False):
		self.source = source
		self.sink = sink
		self.caps = adj_mat
		self.debug = debug
		self.vertices = [i for i in range(len(adj_mat))]

		# self.flow[u][v] defines the current flow over edge [u][v]
		self.flow = collections.defaultdict(dict)
		# self.excess[u] defines the current excess flow at node u.
		# I.e. the difference between inflow and outflow at node u.
		self.excess = collections.defaultdict(int)
		# self.neighbors[u] gives a list of all neighbors of node u,
		# i.e. all nodes v s.t. (u, v) or (v, u) is an edge.
		self.neighbors = collections.defaultdict(list)
		
		# As described in textbook, it is preferable that, when we 
		# repeatedly push excess from a node v, we push it from the
		# same neighbor. self.current_neighbor[u] gives the last
		# neighbor of u to which u pushed excess.
		self.current_neighbor = collections.defaultdict(int)
		# self.height[u] stores the current height of a node u.
		self.height = {}
		# self.nodes_with_excess[h] contains a doubly-linked list of
		# all nodes which currently have positive excess and a height
		# of h.
		self.nodes_with_excess = []
		# self.current_max_height is the maximum height of any node in
		# the graph at any given time.
		self.current_max_height = 0
		self.pp = pprint.PrettyPrinter(indent=4)

		for src in self.vertices:
			self.flow[src] = {}
			self.height[src] = len(self.vertices) if src == source else 0

			for (dst, capacity) in enumerate(self.caps[src]):
				if self.caps[src][dst] != 0:
					self.flow[src][dst] = capacity if src == source else 0
					self.neighbors[src].append(dst)
					self.neighbors[dst].append(src)
					self.excess[src] -= self.flow[src][dst]
					self.excess[dst] += self.flow[src][dst]


		# NOTE: height is upper bounded by 2n, as described in textbook.
		for i in range(2*len(self.vertices)):
			self.nodes_with_excess.append(collections.deque())
		
		for vertex in self.vertices:
			if self.excess[vertex] > 0 and vertex != self.sink:
				v_height = self.height[vertex]
				self.nodes_with_excess[v_height].append(vertex)
	
	# Print a string if solver is in debug mode.
	def print_if_debugging(self, string):
		if self.debug:
			print(string)
	
	# Ensures that currnet flow does not violate capacity or balance conditions.
	def sanity_check_flow(self):
		inflow = {}
		outflow = {}
		error = False
		for (v, outflows) in self.flow.items():
			if v not in outflow:
				outflow[v] = 0
			for (dst, val) in outflows.items():
				if val > self.caps[v][dst]:
					print(f"ERROR: Edge ({v}, {dst}) violates capacity.")
					print(f"Capacity is self.caps[v][dst]. Flow is {val}.")
					error = True
				if dst not in inflow:
					inflow[dst] = 0
				inflow[dst] += val
				outflow[v] += val
			
		for v in self.flow.keys():
			if v not in [self.source, self.sink] and inflow[v] != outflow[v]:
				print(f"ERROR: Node {v} violates balance.")
				print(f"Inflow is {inflow[v]}. Outflow is {outflow[v]}.")
				error = True

		if outflow[self.source] != inflow[self.sink]:
			print(f"ERROR: Source has outflow of {outflow[self.source]}. "
					"Sink has inflow of {inflow[self.sink]}")
			error = True

		if error:
			print("Error detected. Exiting.")
			exit(1)
	
	# Determine value of self.flow (i.e. outflow from source).
	def get_flow_val(self):
		val = 0
		for node in self.neighbors[self.source]:
			val += self.flow[self.source][node]
		return val
	
	# Calculate remaining capacity over edge (v, w).
	def remaining_cap(self, v, w):
		return self.caps[v][w] - self.flow[v][w]

	# Push as much flow as possible along some edge (v, w) in the residual
	# graph. v is assumed to be a node with height of self.current_max_height,
	# as selected by `find_pushable_node' function. w is assumed to be a neighbor
	# of v. direction is "FW" is (v, w) is forward edge in residual graph,
	# "BW" if it is backwards edge.
	def push(self, v, w, direction):
		delta = None
		saturating = None
		# If (v,w) is forward edge in G_f.
		if direction == "FW":
			delta = min(self.excess[v], self.caps[v][w] - self.flow[v][w])
			saturating = (delta == self.caps[v][w] - self.flow[v][w])
			self.flow[v][w] += delta

		# If (v,w) is backwards edge in G_f.
		elif direction == "BW":
			# There is edge from (w, v) with flow flow[w][v]
			delta = min(self.excess[v], self.flow[w][v])
			saturating = (delta == self.flow[w][v])
			self.flow[w][v] -= delta
		
		self.print_if_debugging(f"Pushing {delta} from {v} to {w}")

		# Note that, regardless of whether edge is backwards or forwards,
		# the excess decreases at v and increases at w.
		old_excess_w = self.excess[w]
		self.excess[v] -= delta
		self.excess[w] += delta

		if old_excess_w == 0 and w != self.sink:
			w_height = self.height[w]
			self.nodes_with_excess[w_height].append(w)

		# If v no longer has excess, then remove it from `nodes_with_excess' list.
		# We know v is first element in  self.nodes_with_excess[self.current_max_height], 		 # because it is chosen this way by `find_pushable_node' function as invoked in
		# the `solve_max_flow' function.
		if self.excess[v] == 0:
			self.nodes_with_excess[self.current_max_height].popleft()

		if saturating:
			self.current_neighbor[v] += 1

	# Increase height of node v, which is assumed to be the first element with
	# excess at height self.current_max_height in self.nodes_with_excess, as
	# selected by `find_pushable_node'
	def relabel(self, v):
		self.print_if_debugging(f"Relabeling {v} to height {self.height[v] + 1}")
		self.height[v] += 1
		self.nodes_with_excess[self.current_max_height].popleft()
		self.current_max_height += 1
		self.nodes_with_excess[self.current_max_height].append(v)
		self.current_neighbor[v] = 0

	# Find a node of maximum height from self.nodes_with_excess[self.current_max_height].
	# If one does not exist, decrement current max height until one is found. (Though,
	# if such a node exists, we will only need to decrement once, as proven in textbook.)
	def find_pushable_node(self):
		while self.current_max_height >= 0:
			if len(self.nodes_with_excess[self.current_max_height]) > 0:
				return self.nodes_with_excess[self.current_max_height][0]
			self.current_max_height -= 1
		return None

	# Find a neighbor of v using current neighbor pointer.
	# For neighbor w, return ("FW", w) if (v, w) is selected edge in graph
	# and ("BW", v) if (w, v) is selected edge in graph.
	def find_neighbor_for_push(self, v):
		# 0 is minimum height, so if v has height 0, it can have no
		# neighbors with lower heights.
		if self.height[v] == 0:
			return None

		current = self.current_neighbor[v]
		for i in range(current, len(self.neighbors[v])):
			w = self.neighbors[v][i]
			if self.caps[v][w] > 0:
				if self.height[w] < self.height[v] and self.remaining_cap(v, w) > 0:
					return ("FW", w)
			
			if self.caps[w][v] > 0:
				if self.height[w] < self.height[v] and self.flow[w][v] > 0:
					return ("BW", w)
				
			self.current_neighbor[v] += 1

		return None
	
	# Calculate the max flow and return its value.
	def solve_max_flow(self):
		v = self.find_pushable_node()
		while v is not None:
			dir_w_tuple = self.find_neighbor_for_push(v)
			if dir_w_tuple is None:
				self.relabel(v)
			else:
				(direction, w) = dir_w_tuple
				self.push(v, w, direction)
			
			v = self.find_pushable_node()

		if self.debug:
			self.sanity_check_flow()
		return self.get_flow_val()

if __name__ == "__main__":
	(src, sink, adjmat) = file_to_adjmat(sys.argv[1])
	debug = len(sys.argv) > 2 and sys.argv[2] == "--debug"
	start_time = time.time()
	solver = PreflowPushSolver(adjmat, src, sink, debug)
	end_time = time.time()
	print(f"Max flow is: {solver.solve_max_flow()}")
	print(f"Elapsed time: {end_time - start_time}")

	
		



