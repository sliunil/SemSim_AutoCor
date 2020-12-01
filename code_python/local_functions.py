import nltk
import pandas as pd
import os
import errno
import colorsys
from scipy.linalg import expm
import warnings
import numpy as np


def sim_to_dissim(input_file, sim_tag, dist_option="minus_log", working_path=os.getcwd()):
    """
    Compute the token dissimilarity matrix from a file and a similarity tag.
    Also give the list of tokens where a similarity was present

    :param input_file: name of the text input file
    :type input_file: str
    :param sim_tag: similarity tag
    :type sim_tag: str
    :param dist_option: transformation parameter from similarity to dissimilarity, eigther "minus_log" or "1_minus"
    :type dist_option: str
    :param working_path: a path to the SemSim_AutoCor folder or above (default = os.getcwd())
    :type working_path: str
    :return: the n_token x n_token dissimilarity matrix between text tokens and the list of tokens used
    :rtype: (numpy.ndarray, list[str])
    """

    # --- Defining paths --- #

    # Getting the SemSim_AutoCor folder, if above
    base_path = str.split(working_path, "SemSim_AutoCor")[0] + "SemSim_AutoCor/"

    # Path of the text file
    file_path = base_path + "corpora/" + input_file
    # Path of the types and frequencies file
    typefreq_file_path = base_path + "similarities_frequencies/" + input_file[:-4] + "_" + sim_tag + "_typefreq.txt"

    # Path of the similarity matrix
    similarities_file_path = base_path + "similarities_frequencies/" + input_file[:-4] \
        + "_" + sim_tag + "_similarities.txt"

    # Raise errors if files not found
    if not os.path.exists(file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)
    if not os.path.exists(typefreq_file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), typefreq_file_path)
    if not os.path.exists(similarities_file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), typefreq_file_path)

    # --- Load the data --- #

    # Import the type freq file
    type_freq_df = pd.read_csv(typefreq_file_path, sep=";", header=None)
    type_list = list(type_freq_df[0])

    # Import the text file and remove non-existing token
    with open(file_path, "r") as text_file:
        text_string = text_file.read()
    raw_token_list = nltk.word_tokenize(text_string)
    token_list = [token for token in raw_token_list if token in type_list]
    n_token = len(token_list)  # The number of tokens

    # Import the similarity matrix
    sim_mat = np.loadtxt(similarities_file_path, delimiter=";")

    # Computation of dissimilarity matrix with option
    if dist_option == "minus_log":
        d_mat = - np.log(sim_mat - np.min(sim_mat) + 1e-30)
    elif dist_option == "1_minus":
        d_mat = 1 - sim_mat
    else:
        warnings.warn("The parameter 'dist_option' is not recognise, setting it to 'minus_log'")
        d_mat = - np.log(sim_mat + 1e-30)

    # Compute the n_type x n_token presence matrix
    pres_mat = np.empty([0, n_token])
    for type_i in type_list:
        pres_mat = np.append(pres_mat, [[token == type_i for token in token_list]], axis=0)

    # Compute the extended distance matrix
    d_ext_mat = pres_mat.T.dot(d_mat.dot(pres_mat))

    # Return the distance_matrix
    return d_ext_mat, token_list


def exchange_and_transition_matrices(n_token, exch_mat_opt, exch_range):
    """
    Compute the exchange matrix and the Markov chain transition matrix from given number of tokens

    :param n_token: the number of tokens
    :type n_token: int
    :param exch_mat_opt: option for the exchange matrix, "s" = standard, "u" = uniform, "d" = diffusive
    :type exch_mat_opt: str
    :param exch_range: range of the exchange matrix
    :type exch_range: int
    :return: the n_token x n_token exchange matrix and the n_token x n_token markov transition matrix
    :rtype: (numpy.ndarray, numpy.ndarray)
    """

    # To manage other options
    if exch_mat_opt not in ["s", "u", "d"]:
        warnings.warn("Exchange matrix option ('exch_mat_opt') not recognized, setting it to 's'")
        exch_mat_opt = "s"

    # Computation regarding options
    if exch_mat_opt == "s":
        exch_mat = np.abs(np.add.outer(np.arange(n_token), -np.arange(n_token))) <= exch_range
        np.fill_diagonal(exch_mat, 0)
        exch_mat = exch_mat / np.sum(exch_mat)
    elif exch_mat_opt == "u":
        f_vec = np.ones(n_token) / n_token
        adj_mat = np.abs(np.add.outer(np.arange(n_token), -np.arange(n_token))) <= exch_range
        np.fill_diagonal(adj_mat, 0)
        g_vec = np.sum(adj_mat, axis=1) / np.sum(adj_mat)
        k_vec = f_vec / g_vec
        b_mat = np.array([[min(v1, v2) for v2 in k_vec] for v1 in k_vec]) * adj_mat / np.sum(adj_mat)
        exch_mat = np.diag(f_vec) - np.diag(np.sum(b_mat, axis=1)) + b_mat
    else:
        f_vec = np.ones(n_token) / n_token
        adj_mat = np.abs(np.add.outer(np.arange(n_token), -np.arange(n_token))) <= 1
        np.fill_diagonal(adj_mat, 0)
        l_adj_mat = np.diag(np.sum(adj_mat, axis=1)) - adj_mat
        pi_outer_mat = np.outer(np.sqrt(f_vec), np.sqrt(f_vec))
        phi_mat = (l_adj_mat / pi_outer_mat) / np.trace(l_adj_mat)
        exch_mat = expm(- exch_range * phi_mat) * pi_outer_mat

    w_mat = (exch_mat / np.sum(exch_mat, axis=1)).T

    # Return the transition matrix
    return exch_mat, w_mat


def discontinuity_segmentation(d_ext_mat, exch_mat, w_mat, n_groups, alpha, beta, kappa,
                               conv_threshold=1e-5, max_it=100, init_labels=None):
    """
    Cluster tokens with discontinuity segmentation from a dissimilarity matrix, exchange matrix and transition matrix.
    Semi-supervised option available if init_labels is given.

    :param d_ext_mat: the n_token x n_token distance matrix
    :type d_ext_mat: numpy.ndarray
    :param exch_mat: the n_token x n_token exchange matrix
    :type exch_mat: numpy.ndarray
    :param w_mat: the n_token x n_token Markov chain transition matrix
    :type w_mat: numpy.ndarray
    :param n_groups: the number of groups
    :type n_groups: int
    :param alpha: alpha parameter
    :type alpha: float
    :param beta: beta parameter
    :type beta: float
    :param kappa: kappa parameter
    :type kappa: float
    :param conv_threshold: convergence threshold (default = 1e-5)
    :type conv_threshold: float
    :param max_it: maximum iterations (default = 100)
    :type max_it: int
    :param init_labels: a vector containing initial labels. 0 = unknown class. (default = None)
    :type init_labels: numpy.ndarray
    :return: the n_tokens x n_groups membership matrix for each token
    :rtype: numpy.ndarray
    """

    # Getting the number of token
    n_token, _ = d_ext_mat.shape

    # Compute the weights of token
    f_vec = np.sum(exch_mat, 0)

    # Initialization of Z
    z_mat = np.random.random((n_token, n_groups))
    z_mat = (z_mat.T / np.sum(z_mat, axis=1)).T

    # Set true labels
    # If init_labels is not None, set known to value
    if init_labels is not None:
        for i, label in enumerate(init_labels):
            if label != 0:
                z_mat[i, :] = 0
                z_mat[i, label - 1] = 1

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
        epsilon_g = np.sum(exch_mat.dot(z_mat ** 2), axis=0) - np.diag(z_mat.T.dot(exch_mat.dot(z_mat)))

        # Computation of H_ig
        hig_mat = beta * dig_mat + alpha * (rho_vec ** -kappa) * (z_mat - w_mat.dot(z_mat)) \
            - (0.5 * alpha * kappa * (rho_vec ** (-kappa - 1)) * epsilon_g)

        # Computation of the new z_mat
        if np.sum(-hig_mat > 690) > 0:
            warnings.warn("Overflow of exp(-hig_mat)")
            hig_mat[-hig_mat > 690] = -690
        z_new_mat = rho_vec * np.exp(-hig_mat)
        z_new_mat = (z_new_mat.T / np.sum(z_new_mat, axis=1)).T

        # If init_labels is not None, set known to value
        if init_labels is not None:
            for i, label in enumerate(init_labels):
                if label != 0:
                    z_new_mat[i, :] = 0
                    z_new_mat[i, label - 1] = 1

        # Print diff and it
        diff_pre_new = np.linalg.norm(z_mat - z_new_mat)
        it += 1
        print(f"Iteration {it}: {diff_pre_new}")

        # Verification of convergence
        if diff_pre_new < conv_threshold:
            converge = True
        if it > max_it:
            converge = True

        # Saving the new z_mat
        z_mat = z_new_mat

    # Return the result
    return z_mat


def cut_segmentation(d_ext_mat, exch_mat, w_mat, n_groups, gamma, beta, kappa,
                     conv_threshold=1e-5, max_it=100, init_labels=None):
    """
    Cluster tokens with cut segmentation from a dissimilarity matrix, exchange matrix and transition matrix.
    Semi-supervised option available if init_labels is given.

    :param d_ext_mat: the n_token x n_token distance matrix
    :type d_ext_mat: numpy.ndarray
    :param exch_mat: the n_token x n_token exchange matrix
    :type exch_mat: numpy.ndarray
    :param w_mat: the n_token x n_token Markov chain transition matrix
    :type w_mat: numpy.ndarray
    :param n_groups: the number of groups
    :type n_groups: int
    :param gamma: gamma parameter
    :type gamma: float
    :param beta: beta parameter
    :type beta: float
    :param kappa: kappa parameter
    :type kappa: float
    :param conv_threshold: convergence threshold (default = 1e-5)
    :type conv_threshold: float
    :param max_it: maximum iterations (default = 100)
    :type max_it: int
    :param init_labels: a vector containing initial labels. 0 = unknown class. (default = None)
    :type init_labels: numpy.ndarray
    :return: the n_tokens x n_groups membership matrix for each token
    :rtype: numpy.ndarray
    """

    # Getting the number of token
    n_token, _ = d_ext_mat.shape

    # Compute the weights of token
    f_vec = np.sum(exch_mat, 0)

    # Initialization of Z
    z_mat = np.random.random((n_token, n_groups))
    z_mat = (z_mat.T / np.sum(z_mat, axis=1)).T

    # Set true labels
    # If init_labels is not None, set known to value
    if init_labels is not None:
        for i, label in enumerate(init_labels):
            if label != 0:
                z_mat[i, :] = 0
                z_mat[i, label - 1] = 1

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

        # Computation of the e_gg vector
        e_gg = np.diag(z_mat.T.dot(exch_mat.dot(z_mat)))

        # Computation of H_ig
        hig_mat = beta * dig_mat + gamma * (rho_vec ** -kappa) * (rho_vec - w_mat.dot(z_mat)) \
            - (0.5 * gamma * kappa * (rho_vec ** (-kappa - 1)) * (rho_vec ** 2 - e_gg))

        # Computation of the new z_mat
        if np.sum(-hig_mat > 690) > 0:
            warnings.warn("Overflow of exp(-hig_mat)")
            hig_mat[-hig_mat > 690] = -690
        z_new_mat = rho_vec * np.exp(-hig_mat)
        z_new_mat = (z_new_mat.T / np.sum(z_new_mat, axis=1)).T

        # Print diff and it
        diff_pre_new = np.linalg.norm(z_mat - z_new_mat)
        it += 1
        print(f"Iteration {it}: {diff_pre_new}")

        # Verification of convergence
        if diff_pre_new < conv_threshold:
            converge = True
        if it > max_it:
            converge = True

        # Saving the new z_mat
        z_mat = z_new_mat

    # Return the result
    return z_mat


def write_groups_in_html_file(output_file, z_token_list, z_mat, comment_line=None):
    """
    Write the html group color file from an input file and a membership matrix Z.

    :param output_file: the name of the html outputted file
    :type output_file: str
    :param z_token_list: the list of tokens which define z_mat rows
    :type z_token_list: list[string]
    :param z_mat: the fuzzy membership matrix Z
    :type z_mat: numpy.ndarray
    :param comment_line: an optional comment line to start the file (default=None)
    :type comment_line: str
    """

    # Getting the number of groups
    _, n_groups = z_mat.shape

    # Creating group colors
    color_rgb_list = []
    for i in range(n_groups):
        color_rgb_list.append(np.array(colorsys.hsv_to_rgb(i * 1 / n_groups, 1, 1)))
    color_rgb_mat = np.array(color_rgb_list)

    # Creating tokens color
    token_color_mat = np.array(255 * z_mat.dot(color_rgb_mat), int)

    # Creating html file
    with open(output_file, 'w') as html_file:

        html_file.write("<html>\n<head></head>\n")

        # Writing comment is present
        if comment_line is None:
            html_file.write("<body><p>")
        else:
            html_file.write(f"<body><p>{comment_line}</p> <p>")

        # Writing tokens with colors
        for i in range(len(z_token_list)):
            html_file.write(f"<span style=\"background-color: "
                            f"rgb({token_color_mat[i, 0]},{token_color_mat[i, 1]},{token_color_mat[i, 2]})\">")
            html_file.write(z_token_list[i] + " </span>")

        html_file.write("</p></body>\n</html>")

    # Return 0 is all went well
    return 0


def write_membership_mat_in_csv_file(output_file, z_token_list, z_mat, comment_line=None):
    """
    Write the csv file containing the membership matrix and token list

    :param output_file: the name of the csv outputted file
    :type output_file: str
    :param z_token_list: the list of tokens which define z_mat rows
    :type z_token_list: list[string]
    :param z_mat: the fuzzy membership matrix Z
    :type z_mat: numpy.ndarray
    :param comment_line: an optional comment line to start the file (default=None)
    :type comment_line: str
    """

    # Getting the number of groups
    _, n_groups = z_mat.shape

    # Creating csv file
    with open(output_file, 'w') as text_file:

        # Write comment_line if exists
        if comment_line is not None:
            text_file.write(comment_line + "," * (n_groups + 1) + "\n")

        # Write head
        text_file.write("token,id")
        for i in range(n_groups):
            text_file.write(f",G{i + 1}")
        text_file.write("\n")

        # Write matrix
        for i, token in enumerate(z_token_list):
            text_file.write(f"{token},{i + 1}")
            for j in range(n_groups):
                text_file.write(f",{z_mat[i, j]}")
            text_file.write("\n")

    # Return 0 is all went well
    return 0