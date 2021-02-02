import os
import numpy as np
import segeval

ground_truth_file_list = ["mix_word1_groups.txt",
                          "mix_word5_groups.txt",
                          "mix_sent1_groups.txt",
                          "mix_sent5_groups.txt"]


for ground_truth_file in ground_truth_file_list:
    # Getting the base path (must run the script from a folder inside the "SemSim_Autocor" folder)
    working_path = os.getcwd()
    base_path = str.split(working_path, "SemSim_AutoCor")[0] + "SemSim_AutoCor/"
    # Path of the raw text file
    ground_truth_path = f"{base_path}corpora/{ground_truth_file}"

    # Loading ground truth
    with open(ground_truth_path) as ground_truth:
        real_group_vec = ground_truth.read()
        real_group_vec = np.array([int(element) for element in real_group_vec.split(",")])

    real_segm_vec = segeval.convert_positions_to_masses(real_group_vec)
    print(f"Groupfile {ground_truth_file} has a mean segment length of {np.mean(real_segm_vec)}")
