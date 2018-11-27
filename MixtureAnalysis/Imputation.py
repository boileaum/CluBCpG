import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import os
from multiprocessing import Pool
from MixtureAnalysis.ConnectToCpGNet import TrainWithCpGNet
from MixtureAnalysis.ParseBam import BamFileReadParser
from CpGNet import CpGNet
from keras.models import load_model
import keras.backend as K


class Imputation:

    def __init__(self, cpg_density: int, bam_file: str, mbias_read1_5=None, 
        mbias_read1_3=None, mbias_read2_5= None, mbias_read2_3=None, processes=-1):
        self.cpg_density = cpg_density
        self.bam_file = bam_file
        self.mbias_read1_5 = mbias_read1_5
        self.mbias_read1_3 = mbias_read1_3
        self.mbias_read2_5 = mbias_read2_5
        self.mbias_read2_3 = mbias_read2_3
        self.processes = processes



    def extract_matrices(self, coverage_data_frame: pd.DataFrame, return_bins=False):

        def track_progress(job, update_interval=30):
            while job._number_left > 0:
                print("Tasks remaining = {0}".format(job._number_left * job._chunksize), flush=True)
                time.sleep(update_interval)

        subset = coverage_data_frame[coverage_data_frame['cpgs'] == self.cpg_density]
        bins_of_interest = subset['bin'].unique()

        pool = Pool(processes=self.processes)
        matrices = pool.map_async(self._multiprocess_extract, bins_of_interest)

        track_progress(matrices)
        matrices = matrices.get()

        bins, matrices =zip(*matrices)

        # Remove any potential bad data
        clean_matrices = []
        for matrix in matrices:
            if matrix.shape[1] == self.cpg_density:
                clean_matrices.append(matrix)

        if return_bins:
            return bins, np.array(clean_matrices)
        else:
            return np.array(clean_matrices)


    def _multiprocess_extract(self, one_bin: str):
        read_parser = BamFileReadParser(self.bam_file, 20, read1_5=self.mbias_read1_5, read1_3=self.mbias_read1_3, read2_5=self.mbias_read2_5, read2_3=self.mbias_read2_3)
        chrom, loc = one_bin.split("_")
        loc = int(loc)
        reads = read_parser.parse_reads(chrom, loc-100, loc) # TODO unhardcode bin size
        matrix = read_parser.create_matrix(reads)
        matrix = matrix.dropna(how="all")
        matrix = matrix.fillna(-1)
        matrix = np.array(matrix)
        matrix = matrix.astype('uint16')

        return (one_bin, matrix)


    def train_model(self, output_folder: str, matrices: iter):
        train_net = TrainWithCpGNet(cpg_density=self.cpg_density, save_path=output_folder)
        model = train_net.train_model(matrices)

        return model

    @staticmethod
    def postprocess_predictions(predicted_matrix):
        """Takes array with predicted values and rounds them to 0 or 1 if threshold is exceeded
        
        Arguments:
            predicted_matrix {[type]} -- matrix generated by imputation
        
        Returns:
            [type] -- predicted matrix predictions as 1, 0, or NaN
        """

        processed_array = []
        for array in predicted_matrix:
            new_array = []
            for item in array:
                if item != 1 and item != 0:
                    if item <= 0.2: #TODO un-hardcode this
                        new_array.append(0.0)
                    elif item >= 0.8: #TODO un-hardcode this
                        new_array.append(1.0)
                    else:
                        new_array.append(np.nan)
                else:
                    new_array.append(item)

            processed_array.append(new_array)

        return np.array(processed_array)



    def impute_from_model(self, models_folder: str, matrices: iter, postprocess=True):
        """Generator to provide imputed matrices on-the-fly
        
        Arguments:
            models_folder {str} -- Path to directory containing trained CpGNet models
            matrices {iter} -- An iterable containging n x m matrices with n=cpgs and m=reads
        
        Keyword Arguments:
            postprocess {bool} -- Round imputed values to 1s and 0s  (default: {True})
        """

        model_path = os.path.join(models_folder, "saved_model_{}_cpgs.h5".format(self.cpg_density))
        trained_model = CpGNet(cpgDensity=self.cpg_density)
        trained_model.model = load_model(model_path)

        for m in matrices:
            # only impute if there is an unknown
            if -1 in m:
                pm = trained_model.impute(m)
                if postprocess:
                    pm = self.postprocess_predictions(pm)
            # Nothing to impute, passback original matrix to keep list in order
            else:
                pm = m.copy()
            # predicted_matrices.append(pm)
            yield pm        
