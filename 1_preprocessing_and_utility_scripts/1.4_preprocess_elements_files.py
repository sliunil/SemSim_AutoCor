import os
import numpy as np
import string
import re
import nltk
from nltk.corpus import stopwords

# Setting the input file path
input_text_file = "corpora/elements/wikielements.text"
support_text_file = "corpora/elements/wikielements.segmenttitles"

# Setting the output files path
output_files_path = "corpora/elements_pp"

# Removing stopwords option
remove_stopwords = True

# Getting stopwords
stopwords = stopwords.words('english')

# Improved punctuation
improved_punctuation = string.punctuation + "”’—“–"

# Read sentences
with open(input_text_file) as text_file:
    sent_list = text_file.readlines()

# Get docs, and groups
with open(support_text_file) as sup_file:
    line_list = sup_file.readlines()
doc_list = []
group_list = []
for line in line_list:
    doc_list.append(int(line.split(",")[0]))
    group_list.append(line.split(",")[2])

# Loop on docs
for doc_id in set(doc_list):

    # Get sentences and groups from the doc
    doc_sent_vec = np.array(sent_list)[np.array(doc_list) == doc_id]
    doc_group_vec = np.array(group_list)[np.array(doc_list) == doc_id]

    # Translate group into num
    group_trad_dict = {g_name: (g_id + 1) for g_id, g_name in enumerate(set(doc_group_vec))}
    doc_group_id_vec = [group_trad_dict[group_name] for group_name in doc_group_vec]

    # Change the output name depending if stopwords are present
    if remove_stopwords:
        output_name = f"{doc_id}_pp_wostw"
    else:
        output_name = f"{doc_id}_pp"
    with open(f"{output_files_path}/e{output_name}.txt", "w") as text_file, \
            open(f"{output_files_path}/e{output_name}_groups.txt", "w") as groups_file:

        # Loop on sentences
        for i, sentence in enumerate(doc_sent_vec):

            # Lower cases
            sentence_pp = sentence.lower()
            # Remove numbers
            sentence_pp = re.sub(r"[0-9]", " ", sentence_pp)
            # Remove punctuation
            sentence_pp = sentence_pp.translate(str.maketrans(improved_punctuation, " " * len(improved_punctuation)))
            # Split by token
            token_list = nltk.word_tokenize(sentence_pp)

            # Removing stopwords if option is on
            if remove_stopwords:
                token_list = [token for token in token_list if token not in stopwords]

            # Write if sentence is not empty
            if len(token_list) > 0:
                # Write the sentence
                text_file.write(" ".join(token_list) + "\n")
                # Write the groups
                groups_file.write(",".join([str(doc_group_id_vec[i])] * len(token_list)) + ",")

    # Remove last char
    with open(f"{output_files_path}/e{output_name}.txt", "rb+") as text_file, \
            open(f"{output_files_path}/e{output_name}_groups.txt", "rb+") as groups_file:
        text_file.seek(-1, os.SEEK_END)
        text_file.truncate()
        groups_file.seek(-1, os.SEEK_END)
        groups_file.truncate()
