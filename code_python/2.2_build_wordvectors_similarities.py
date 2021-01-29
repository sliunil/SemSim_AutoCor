import nltk
from gensim.models import KeyedVectors
from tqdm import tqdm
from code_python.local_functions import get_all_paths

# -------------------------------------
# --- Parameters
# -------------------------------------

# List of paths for text files to compute similarity
input_file_list = ["Civil_Disobedience_pp.txt",
                   "Flowers_of_the_Farm_pp.txt",
                   "Sidelights_on_relativity_pp.txt",
                   "Prehistoric_Textile_pp.txt"]

# List of tags to enumerate similarity to compute
sim_tag_list = ["glv", "w2v"]

# -------------------------------------
# --- Computations
# -------------------------------------

# Loading wordvector models
w2v_model = KeyedVectors.load("/home/gguex/Documents/data/pretrained_word_vectors/enwiki.model")
glv_model = KeyedVectors.load("/home/gguex/Documents/data/pretrained_word_vectors/glove42B300d.model")

# Loop on files and tags
for input_file in input_file_list:
    for sim_tag in sim_tag_list:

        # Print which is computed
        print(f"Computing similarity {sim_tag} for corpus {input_file}")

        # Getting all paths
        file_path, type_freq_file_path, sim_matrix_file_path, _ = get_all_paths(input_file, sim_tag, warn=False)

        # Opening the file
        with open(file_path, "r") as text_file:
            text_string = text_file.read()

        # Split by tokens
        token_list = nltk.word_tokenize(text_string)

        # Get type list and frequencies
        type_freq_dict = nltk.FreqDist(token_list)
        vocab_text = set(type_freq_dict.keys())

        # select gensim model
        if sim_tag == "w2v":
            wv_model = w2v_model
        else:
            wv_model = glv_model

        # build vocabulary
        vocab_wv = set(wv_model.vocab.keys())

        # Find the common vocabulary
        vocab_common = list(vocab_wv & vocab_text)

        # Write the two files
        with open(type_freq_file_path, "w") as type_freq_file, open(sim_matrix_file_path, "w") as sim_matrix_file:
            for type_1 in tqdm(vocab_common):
                type_freq_file.write(type_1 + ";" + str(type_freq_dict[type_1]) + "\n")
                for type_2 in vocab_common:
                    sim_matrix_file.write(str(wv_model.similarity(type_1, type_2)))
                    if type_2 != vocab_common[len(vocab_common) - 1]:
                        sim_matrix_file.write(";")
                    else:
                        sim_matrix_file.write("\n")
