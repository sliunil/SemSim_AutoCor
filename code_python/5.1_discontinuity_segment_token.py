import numpy as np
import nltk
import pandas as pd
import os
import colorsys

# --- Parameters --- #

# Path of the text file with only nouns, verbs, adjectives or adverbs to compute autocorrelation
input_file = "The_WW_of_Oz_nouns.txt"

# Name of the tag for the similarity
sim_tag = "wesim"

# Autocorrelation windows size
segm_range = 20
# Number of groups
n_groups = 5
# Alpha parameter
alpha = 1
# Beta parameter
beta = 10
# kappa parameter
kappa = 1
# convergence threshold
conv_threshold = 1e-5

# --- Defining paths --- #

# Getting the base path (must run the script from a folder inside the "SemSim_Autocor" folder)
working_path = os.getcwd()
base_path = str.split(working_path, "SemSim_AutoCor")[0] + "SemSim_AutoCor/"

# Path of the text file
file_path = base_path + "corpora/" + input_file
# Path of the types and frequencies file
typefreq_file_path = base_path + "similarities_frequencies/" + input_file[:-4] + "_" + sim_tag + "_typefreq.txt"
# Path of the similarity matrix
similarities_file_path = base_path + "similarities_frequencies/" + input_file[:-4] + \
                         "_" + sim_tag + "_similarities.txt"
# Results html path file
results_html_file_path = base_path + "results/" + input_file[:-4] + "_" + sim_tag + "_discsegm.html"

# Results csv path file
results_csv_file_path = base_path + "results/" + input_file[:-4] + "_" + sim_tag + "_discsegm.csv"

# --- Load the data --- #

# Import the type freq file
type_freq_df = pd.read_csv(typefreq_file_path, sep=";", header=None)
type_list = list(type_freq_df[0])
freq_vec = np.array(type_freq_df[1])
freq_vec = freq_vec / sum(freq_vec)
n_type = len(type_list)  # The number of types

# Import the text file and remove non-existing token
with open(file_path, "r") as text_file:
    text_string = text_file.read()
raw_token_list = nltk.word_tokenize(text_string)
token_list = [token for token in raw_token_list if token in type_list]
n_token = len(token_list)  # The number of tokens

# Import the similarity matrix
sim_mat = np.loadtxt(similarities_file_path, delimiter=";")

# --- Computation before loop --- #

# Compute the exchange matrix and the markov chain transition matrix
exch_m = np.abs(np.add.outer(np.arange(n_token), -np.arange(n_token))) <= segm_range
np.fill_diagonal(exch_m, 0)
exch_m = exch_m / np.sum(exch_m)
f_vec = np.sum(exch_m, axis=0)
w_mat = (exch_m / f_vec).T

# Easy computation of dissimilarity matrix
d_mat = 1 - sim_mat

# Compute the n_type x n_token presence matrix
pres_mat = np.empty([0, n_token])
for type_i in type_list:
    pres_mat = np.append(pres_mat, [[token == type_i for token in token_list]], axis=0)

# Compute the extended distance matrix
d_ext_mat = pres_mat.T.dot(d_mat.dot(pres_mat))

# --- Loop --- #

# Initialization of Z
z_mat = np.random.random((n_token, n_groups))
z_mat = (z_mat.T / np.sum(z_mat, axis=1)).T

# Control of the loop
converge = False

# Loop
it = 0
print("Starting loop")
while not converge:

    # Computation of rho_g vector
    rho_vec = np.sum(z_mat.T * f_vec, axis=1)

    # Computation of f_i^g matrix
    fig_mat = ((z_mat / rho_vec).T * f_vec).T

    # Computation of D_i^g matrix
    dig_mat = fig_mat.T.dot(d_ext_mat).T
    delta_g_vec = 0.5 * np.diag(dig_mat.T.dot(fig_mat))
    dig_mat = dig_mat - delta_g_vec

    # Computation of the epsilon_g vector
    epsilon_g = np.sum(exch_m.dot(z_mat ** 2), axis=0) - np.diag(z_mat.T.dot(exch_m.dot(z_mat)))

    # Computation of H_ig
    hig_mat = beta * dig_mat + alpha * (rho_vec ** -kappa) * (z_mat - w_mat.dot(z_mat)) \
              - (0.5 * alpha * kappa * (rho_vec ** (-kappa - 1)) * epsilon_g)

    # Computation of the new z_mat
    z_new_mat = rho_vec * np.exp(hig_mat)
    z_new_mat = (z_new_mat.T / np.sum(z_new_mat, axis=1)).T

    # Print diff and it
    diff_pre_new = np.linalg.norm(z_mat - z_new_mat)
    it += 1
    print("Iteration {}: {}".format(it, diff_pre_new))

    # Verification of convergence
    if diff_pre_new < conv_threshold:
        converge = True

    # Saving the new z_mat
    z_mat = z_new_mat

# --- Saving results --- #

# Creating group colors
color_rgb_list = []
for i in range(n_groups):
    color_rgb_list.append(np.array(colorsys.hsv_to_rgb(i * 1 / n_groups, 1, 1)))
color_rgb_mat = np.array(color_rgb_list)

# Creating words color
token_color_mat = np.array(255 * z_mat.dot(color_rgb_mat), int)

# Creating html file
with open(results_html_file_path, 'w') as html_file:
    html_file.write("<html>\n<head></head>\n")
    html_file.write("<body><p>Input file: {} | Similarity tag: {} | Neighbourhood range: {} | Number of groups: {} | "
                    "Alpha: {} | Beta: {} | Kappa: {} | Convergence threshold: {}</p> <p>".format(input_file,
                                                                                                  sim_tag,
                                                                                                  segm_range,
                                                                                                  n_groups,
                                                                                                  alpha,
                                                                                                  beta,
                                                                                                  kappa,
                                                                                                  conv_threshold))
    for i in range(len(token_list)):
        html_file.write("<span style=\"background-color: rgb({},{},{})\">".format(token_color_mat[i, 0],
                                                                                  token_color_mat[i, 1],
                                                                                  token_color_mat[i, 2]))
        html_file.write(token_list[i] + " </span>")
    html_file.write("</p></body>\n</html>")

# Creating csv file
with open(results_csv_file_path, 'w') as text_file:
    text_file.write("Input file: {} | Similarity tag: {} | Neighbourhood range: {} | Number of groups: {} | "
                    "Alpha: {} | Beta: {} | Kappa: {} | Convergence threshold: {}\n".format(input_file,
                                                                                            sim_tag,
                                                                                            segm_range,
                                                                                            n_groups,
                                                                                            alpha,
                                                                                            beta,
                                                                                            kappa,
                                                                                            conv_threshold))
    text_file.write("group;token;id_token;percent\n")
    for i in range(n_groups):
        z_g_vec = z_mat[:, i]
        index_z_g = np.flip(np.argsort(z_g_vec))
        for j in range(n_token):
            id_token = index_z_g[j]
            text_file.write("{};{};{};{}\n".format(i + 1, token_list[id_token], id_token,
                                                   np.round(100 * z_g_vec[id_token], 2)))