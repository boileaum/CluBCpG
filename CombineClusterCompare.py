from sklearn.cluster import DBSCAN
from collections import Counter
import pandas as pd
import numpy as np
import sys
import logging
import os
from ParseBam import BamFileReadParser
import argparse


def filter_data_frame(matrix: pd.DataFrame, cluster_memeber_min):
    output = matrix.copy()
    for cluster in output['class'].unique():
        df = output[output['class'] == cluster]
        if len(df) < cluster_memeber_min
            indexes = df.index
            output.drop(indexes, inplace=True)

    return output



if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-a", "--input_bam_A",
                            help="First Input bam file, coordinate sorted with index present")
    arg_parser.add_argument("-b", "--input_bam_B",
                            help="Second Input bam file, coordinate sorted with index present")
    arg_parser.add_argument("-o", "--output_dir",
                            help="Output directory to save figures, defaults to bam file loaction")
    arg_parser.add_argument("-bins",
                            help="File with each line being one bin to extract and analyze, "
                                 "generated by CalculateCompleteBins")
    arg_parser.add_argument("-bin_size", help="Size of bins to extract and analyze, default=100", default=100)
    arg_parser.add_argument("-m", "--cluster_member_minimum",
                            help="Minimum number of members a cluster should have for it to be considered, default=4",
                            default=4)
    arg_parser.add_argument("-o", "--output_dir",
                            help="Output directory to write files, default=bam_A file locaiton")

    args = arg_parser.parse_args()

    input_bam_a = args.input_bam_A
    input_bam_b = args.input_bam_B
    bins_file = args.bins
    bin_size = args.bin_size
    cluster_min = args.cluster_member_minimum
    output_dir = args.output_dir

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.dirname(input_bam_a)

    # Check all inputs are supplied
    if not input_bam_a or not input_bam_b or not bins_file:
        raise FileNotFoundError("Please make sure all required input files are supplied")

    bam_parser_A = BamFileReadParser(input_bam_a, 20)
    bam_parser_B = BamFileReadParser(input_bam_b, 20)

    # Read in bins
    bins=[]
    with open(bins_file, 'r') as f:
        for line in f:
            data = line.strip().split(",")
            bins.append("_".join([data[0], data[2]]))

    # a list to hold the clusters we identify as interesting
    bins_with_unique_clusters = []

    # Open output file for writing all data and unique data
    output_all = open(os.path.join(output_dir, "CombineClusterCompare_output_all.csv", 'w'))
    output_unique = open(os.path.join(output_dir, "CombinedClusterCompare_outout_unique.csv"), 'w')

    # Go through and cluster reads from each bin
    for bin in bins:
        chromosome, bin_loc = bin.split("_")

        reads_A = bam_parser_A.parse_reads(chromosome, bin_loc-bin_size, bin_loc)
        reads_B = bam_parser_B.parse_reads(chromosome, bin_loc-bin_size, bin_loc)
        matrix_A = bam_parser_A.create_matrix(reads_A)
        matrix_B = bam_parser_B.create_matrix(reads_B)

        # drop reads without full coverage of CpGs
        matrix_A = matrix_A.dropna()
        matrix_B = matrix_B.dropna()

        # create labels and add to dataframe
        labels_A = ['A'] * len(matrix_A)
        labels_B = ['B'] * len(matrix_B)
        matrix_A['input'] = labels_A
        matrix_B['input'] = labels_B

        full_matrix = pd.concat([matrix_A, matrix_B])
        data_to_cluster = np.matrix(full_matrix)[:, :-1]

        # Create DBSCAN classifier and cluster add cluster classes to df
        clf = DBSCAN(min_samples=2)
        labels = clf.fit_predict(data_to_cluster)
        full_matrix['class'] = labels

        # Filter out any clusters with less than a minimum
        full_matrix = filter_data_frame(full_matrix, cluster_min)
        total_clusters = len(full_matrix['class'].unique()) # for output

        # Calculate clusters for A and B
        A_clusters = len(full_matrix[full_matrix['input'] == 'A']['class'].unique()) # for output
        B_clusters = len(full_matrix[full_matrix['input'] == 'B']['class'].unique()) # for output

        # Calculate how many clusters are unique to A or B
        num_unique_classes = 0 # for output
        for label in full_matrix['class'].unique():
            df = full_matrix[full_matrix['class'] == label]
            # This cluser is unique to only one input
            if len(df['input'].unique() == 1):
                num_unique_classes += 1

        # Write this data for an output
        output_line = ",".join([bin, str(total_clusters), str(A_clusters), str(B_clusters), str(num_unique_classes),'\n'])
        output_all.write(output_line)
        if num_unique_classes > 0:
            output_unique.write(output_line)

    output_all.close()
    output_unique.close()
    print("Done")