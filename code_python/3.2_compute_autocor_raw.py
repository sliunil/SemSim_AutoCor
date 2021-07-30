from local_functions import get_all_paths, similarity_to_dissimilarity, exchange_and_transition_matrices, \
    autocorrelation_index
import os
import numpy as np
import multiprocessing as mp
from miniutils import parallel_progbar
from os.path import expanduser
import nltk
from gensim.models import KeyedVectors
import re

# -------------------------------------
# --- Parameters
# -------------------------------------

# Similarity tag list
sim_tag_list = ["w2v"]
# Input files list
input_file_list = ["gutenberg/Carroll,Lewis_Alice'sAdventuresinWonderla.txt"]
# Distance option
dist_option = "max_minus"
# Exchange matrix option ("s" = standard, "u" = uniform, "d" = diffusive, "r" = ring)
exch_mat_opt = "u"
# Exchange matrix max range
exch_max_range = 50
# Number of cpus to use
n_cpu = mp.cpu_count()

# -------------------------------------
# --- Computations
# -------------------------------------

# Working path
working_path = os.getcwd()
# Getting the SemSim_AutoCor folder, if above
base_path = str.split(working_path, "SemSim_AutoCor")[0] + "SemSim_AutoCor"
# Save the windows for autocorrelation range
exch_range_window = list(range(1, exch_max_range + 1))

# Getting home path
home = expanduser("~")

for sim_tag in sim_tag_list:

    # Get the wv path
    if sim_tag == "w2v":
        word_vector_path = f"{home}/Documents/data/pretrained_word_vectors/enwiki.model"
    elif sim_tag == "glv":
        word_vector_path = f"{home}/Documents/data/pretrained_word_vectors/glove42B300d.model"
    else:
        word_vector_path = f"{home}/Documents/data/pretrained_word_vectors/en_fasttext.model"

    # Loading wordvector models
    wv_model = KeyedVectors.load(word_vector_path)
    # Vocabulary of word vectors
    vocab_wv = set(wv_model.vocab.keys())

    # Output file name
    output_file_name = f"{base_path}/results/3.2_autocor{exch_max_range}_{sim_tag}.csv"
    # Write header
    with open(output_file_name, "w") as output_file:
        output_file.write("csv_file_name, " + f"{list(range(1, 1 + exch_max_range))}"[1:-1] + "\n")

    for input_file in input_file_list:

        # Write file name
        with open(output_file_name, "a") as output_file:
            output_file.write(input_file[:-7])
        # Print
        print(f"Autocorrelation for {input_file} with similarity {sim_tag}")

        # Get the file paths
        text_file_path, _, _, _ = get_all_paths(input_file, sim_tag)

        # Opening the file
        with open(text_file_path, "r") as text_file:
            text_string = text_file.read()
            text_string = re.sub(r'[^a-zA-Z ]', '', text_string).lower()
        # Split by tokens
        token_list = nltk.word_tokenize(text_string)
        # Vocabulary of text
        vocab_text = set(token_list)

        # The common vocabulary
        vocab_common = list(vocab_wv & vocab_text)
        # Number of type
        n_type = len(vocab_common)

        # Reducing token_list to existing one
        existing_pos_list = [token in vocab_common for token in token_list]
        existing_token_list = np.array(token_list)[existing_pos_list]
        # Number of token
        n_token = len(existing_token_list)

        # Build sim matrix
        sim_mat = np.eye(n_token) / 2
        for ind_token_1 in range(n_token):
            for ind_token_2 in range(ind_token_1 + 1, n_token):
                sim_mat[ind_token_1, ind_token_2] = \
                    wv_model.similarity(existing_token_list[ind_token_1], existing_token_list[ind_token_2])
        sim_mat = sim_mat + sim_mat.T

        # Compute the dissimilarity matrix from similarity
        d_mat = similarity_to_dissimilarity(sim_mat,
                                            dist_option=dist_option)

        # the z_autocor function
        def z_autocor(exch_range):
            # Compute the exchange and transition matrices
            exch_mat, w_mat = exchange_and_transition_matrices(len(existing_token_list),
                                                               exch_mat_opt=exch_mat_opt,
                                                               exch_range=exch_range)
            # Compute the autocorrelation index
            autocor_index, theoretical_mean, theoretical_var = autocorrelation_index(d_mat, exch_mat, w_mat)

            # Z score for autocor
            z_ac = (autocor_index - theoretical_mean) / np.sqrt(theoretical_var)

            # Return
            return z_ac

        # Run on multiprocess
        z_autocor_vec = parallel_progbar(z_autocor, exch_range_window, nprocs=n_cpu)

        with open(output_file_name, "a") as output_file:
            for z_val in z_autocor_vec:
                output_file.write(f", {z_val}")
            output_file.write("\n")