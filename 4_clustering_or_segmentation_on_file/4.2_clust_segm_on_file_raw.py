from local_functions import *
import pandas as pd
from sklearn.metrics import normalized_mutual_info_score

# -------------------------------------
# --- Parameters
# -------------------------------------

# Input text file
input_text_file = "../corpora/manifesto_pp/61320_202011_pp_wostw.txt"
# Input group file
input_group_file = "../corpora/manifesto_pp/61320_202011_pp_wostw_groups.txt"
# Input vector model
home = os.path.expanduser("~")
vector_model_path = f"{home}/Documents/data/pretrained_word_vectors/en_fasttext.model"

#---

# Number of groups (if none, extracted from data)
n_groups = None

# Block size
block_size = None

# Strong pass
strong_pass = False

# Algo hyperparameters
dist_option = "max_minus"
exch_mat_opt = "u"
exch_range = 5
alpha = 2
beta = 5
kappa = 0.25
known_label_ratio = 0  # if > 0, semi-supervised model

# -------------------------------------
# --- Computations
# -------------------------------------

# Loading ground truth
with open(input_group_file) as ground_truth:
    real_group_vec = ground_truth.read()
    real_group_vec = np.array([int(element) for element in real_group_vec.split(",")])
if n_groups is None:
    n_groups = len(set(real_group_vec))

z_res, existing_token_list, existing_pos_list = \
    spatial_clustering_on_file(input_text_file, vector_model_path, dist_option,
                               exch_mat_opt, exch_range, n_groups, alpha, beta,
                               kappa, block_size=block_size, verbose=True, strong_pass=strong_pass)

write_groups_in_html_file("test.html", existing_token_list, z_res)

# Reshape groupe
real_group_vec = real_group_vec[existing_pos_list]

# Compute the aggregate labels
df_results = pd.DataFrame(z_res)
df_results["Token"] = existing_token_list
type_results = df_results.groupby("Token").mean()
type_list = list(type_results.index)
type_values = type_results.to_numpy()

write_membership_mat_in_csv_file("test.csv", type_list, type_values)

# Compute the groups
algo_group_vec = np.argmax(z_res, 1) + 1

# Compute nmi score
nmi = normalized_mutual_info_score(real_group_vec, algo_group_vec)

# Segmentation evaluation
pk_res, win_diff, pk_rdm, win_diff_rdm = seg_eval(algo_group_vec, real_group_vec)

print(f"nmi = {nmi}, pk={pk_res} (rdm={pk_rdm}), win_diff={win_diff} (rdm={win_diff_rdm})")
