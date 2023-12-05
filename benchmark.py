import time
import sys
import os
import csv
from ford_fulkerson import FordFulkerson
from scaling_ford_fulkerson import ScalingFordFulkerson
from preflow_push import PreflowPushSolver, file_to_adjmat

def run_ff(filename, delimiter=" "):
	ff = FordFulkerson(filename, delimiter)
	ff_start = time.time()
	computed_flow_val = ff.ford_fulkerson()
	ff_end = time.time()
	time_taken = ff_end - ff_start

	return (time_taken, computed_flow_val)

def run_sff(filename, delimiter=" "):
	sff = ScalingFordFulkerson(filename, delimiter)
	sff_start = time.time()
	computed_flow_val = sff.scaling_ff()
	sff_end = time.time()
	time_taken = sff_end - sff_start

	return (time_taken, computed_flow_val)

def run_pfp(filename, delimiter=" "):
	(src, sink, adjmat) = file_to_adjmat(filename, delimiter)
	pfp = PreflowPushSolver(adjmat, src, sink)
	pfp_start = time.time()
	computed_flow_val = pfp.solve_max_flow()
	pfp_end = time.time()
	time_taken = pfp_end - pfp_start

	return (time_taken, computed_flow_val)

def test_all_algos(filename, delimiter=" "):
	print(f"Testing on {filename}")
	pfp_res = run_pfp(filename, delimiter)
	ff_res = run_ff(filename, delimiter)
	sff_res = run_sff(filename, delimiter)

	# Sanity check.
	if not (ff_res[1] == sff_res[1] == pfp_res[1]):
		print(f"ERROR: Algorithms calculate different flow vals on graph {filename}")
		print(f"ERROR: FF gives flow val of {ff_res[1]}")
		print(f"ERROR: SFF gives flow val of {sff_res[1]}")
		print(f"ERROR: PFP gives flow val of {pfp_res[1]}")
		print("PANICKING.")
		exit(1)

	print(f"Successfully executed all algos on {filename}, w/ max flow {ff_res[1]}")
	return (ff_res, sff_res, pfp_res)

if __name__ == "__main__":
	bipartite_dir = os.path.join("data_test", "bipartite_examples")
	fixeddegree_dir = os.path.join("data_test", "fixeddegree_examples")  
	mesh_dir = os.path.join("data_test", "mesh_examples")  
	random_dir = os.path.join("data_test", "random_examples")

	sys.setrecursionlimit(10000)
	
	
	with open("bipartite_benchmark.csv", "w+") as csvfile:
		csv_writer = csv.writer(csvfile)
		# Each filename has form "$output_bipartite_${nodes_source}_${nodes_sink}_${maxProbability}.txt"
		for f_name in os.listdir(bipartite_dir):
			full_name = os.path.join(bipartite_dir, f_name)
			if os.path.isfile(full_name):
				stem = os.path.splitext(f_name)[0]
				params = stem.split("_")[2:]
				nodes_source = int(params[0])
				nodes_sink = int(params[1])
				max_prob = float(params[2])
	
				# For some reason, bipartite graphs use tabs instead of spaces between fields.
				(ff_res, sff_res, pfp_res) = test_all_algos(full_name, "\t")
				csv_writer.writerow([nodes_source, nodes_sink, max_prob, 
									ff_res[0], ff_res[1], 
									sff_res[0], sff_res[1],
									pfp_res[0], pfp_res[1]])
				
	
			
	with open("fixeddegree_benchmark.csv", "w+") as csvfile:
		csv_writer = csv.writer(csvfile)
		# Each filename has form "$output_dir/output_fixeddegree_${nodes_source}_${edges}_${minCapacity}_${maxCapacity}.txt"
		for f_name in os.listdir(fixeddegree_dir):
			full_name = os.path.join(fixeddegree_dir, f_name)
			if os.path.isfile(full_name):
				stem = os.path.splitext(f_name)[0]
				params = stem.split("_")[2:]
				nodes_source = int(params[0])
				edges = int(params[1])
				min_cap = int(params[2])
				max_cap = int(params[3])
	
				(ff_res, sff_res, pfp_res) = test_all_algos(full_name)
				csv_writer.writerow([nodes_source, edges, min_cap, max_cap,
									ff_res[0], ff_res[1], 
									sff_res[0], sff_res[1],
									pfp_res[0], pfp_res[1]])
	
	with open("mesh_benchmark.csv", "w+") as csvfile:
		csv_writer = csv.writer(csvfile)
		# Each filename has form "output_dir/output_mesh_${rows}_${columns}.txt"
		for f_name in os.listdir(mesh_dir):
			full_name = os.path.join(mesh_dir, f_name)
			if os.path.isfile(full_name):
				stem = os.path.splitext(f_name)[0]
				params = stem.split("_")[2:]
				rows = int(params[0])
				cols = int(params[1])
	
				(ff_res, sff_res, pfp_res) = test_all_algos(full_name)
				csv_writer.writerow([rows, cols,
									ff_res[0], ff_res[1], 
									sff_res[0], sff_res[1],
									pfp_res[0], pfp_res[1]])
	
	with open("random_benchmark.csv", "w+") as csvfile:
		csv_writer = csv.writer(csvfile)
		# Each filename has form "output_random_${nodes_source}_${dense}_${minCapacity}_${maxCapacity}.txt"
		for f_name in os.listdir(random_dir):
			full_name = os.path.join(mesh_dir, f_name)
			if os.path.isfile(full_name):
				stem = os.path.splitext(f_name)[0]
				params = stem.split("_")[2:]
				nodes_source = int(params[0])
				dense = int(params[1])
				min_cap = int(params[2])
	
				(ff_res, sff_res, pfp_res) = test_all_algos(full_name)
				csv_writer.writerow([nodes_source, dense, min_cap,
									ff_res[0], ff_res[1], 
									sff_res[0], sff_res[1],
									pfp_res[0], pfp_res[1]])
	
