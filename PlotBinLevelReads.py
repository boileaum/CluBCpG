from ParseBam import BamFileReadParser
import  matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.cm as cm
import argparse
import logging
import sys
import os
from multiprocessing import Pool

sns.set_context("talk")
sns.set_style("darkgrid")



def plot_complete_bin_reads(bin):
    # Take a martix of CpG status and plot
    # Visualze the reads from the bam file, 1=methylated, 0=unmethylated
    bin_chr = bin.split("_")
    chromosome = bin_chr[0]
    stop_pos = int(bin_chr[1])
    start_pos = stop_pos - 100

    # Create bam file parser object
    bam_parser = BamFileReadParser(args.input_bam, 20)


    reads = bam_parser.parse_reads(chromosome, stop_pos - 100, stop_pos)
    matrix = bam_parser.create_matrix(reads)
    if drop_na:
        matrix = matrix.dropna()

    fig = plt.figure(figsize=(10, 6))
    if cluster:
        g = sns.clustermap(matrix, vmax=1, vmin=0, cmap='coolwarm', linewidths=0.1, col_cluster=False)
        ax = g.ax_heatmap
        ax.set_title("{}: {}-{}".format(chromosome, start_pos, stop_pos))
        ax.set_ylabel("reads")
        ax.set_xlabel("CpG site")

    else:
        g = sns.heatmap(matrix, vmax=1, vmin=0, cmap='coolwarm', linewidths=0.1)
        g.set_title("{}: {}-{}".format(chromosome, start_pos, stop_pos))
        g.set_ylabel("reads")
        g.set_xlabel("CpG site")


    file_name = "{}_{}.png".format(chromosome, str(stop_pos))
    output_file = os.path.join(file_spec_path, file_name)
    plt.savefig(output_file)
    plt.close(fig)


if __name__ == "__main__":
    # Get arguments from the command line
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("bins_to_plot",
                            help="File with each line being one bin to extract and plot, "
                                 "bins should be in format: chr19:3333333")
    arg_parser.add_argument("input_bam",
                            help="Input bam file, coordinate sorted with index present")
    arg_parser.add_argument("-o", "--output_dir",
                            help="Output directory to save figures, defaults to bam file loaction",)
    arg_parser.add_argument("-c", "--cluster", help="produce clustermaps instead of heatmaps", action="store_true")
    arg_parser.add_argument("-n", "--number_of_processors",
                            help="Number of processors to use, default=1", default=1)
    arg_parser.add_argument("-na", "--drop_na",
                            help="Drop reads which do not span all CpGs from the clustering, default=False", default=False)


    args = arg_parser.parse_args()

    # Set output directory to user input or default
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.dirname(args.input_bam)

    print("Output directory set to {}".format(output_dir))
    file_spec_path = os.path.join(output_dir, "plots_{}".format(os.path.basename(os.path.splitext(args.input_bam)[0])))

    # Create subdirectory for plots
    if not os.path.exists(file_spec_path):
        print("Creating file specific plots folder in output directory")
        os.makedirs(file_spec_path)
    else:
        print("plots folder already exists, saving there...")

    # write out inputs for reference
    print("Input bam file is: {}".format(args.input_bam))
    print("List of bins is: {}".format(args.bins_to_plot))
    print("Plots being saved to {}".format(file_spec_path))
    sys.stdout.flush()

    # Load bins into memory
    bins = []
    with open(args.bins_to_plot, 'r') as f:
        for line in f:
            bins.append(line.strip())

    # Get cluster arg for plotting
    cluster = args.cluster
    num_processors = int(args.number_of_processors)
    drop_na = args.drop_na



    # Start multiprocessing
    pool = Pool(processes=num_processors)
    print("Starting plotting using {} processors".format(num_processors))
    sys.stdout.flush()
    pool.map(plot_complete_bin_reads, bins)
    print("Done")





