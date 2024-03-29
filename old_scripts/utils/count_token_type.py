import os
import nltk

# Corpus name
corpus_name_list = ["Civil_Disobedience_pp.txt",
                    "Flowers_of_the_Farm_pp.txt",
                    "Sidelights_on_relativity_pp.txt",
                    "Prehistoric_Textile_pp.txt",
                    "mix_word1.txt",
                    "mix_word5.txt",
                    "mix_sent1.txt",
                    "mix_sent5.txt",
                    "61320_199211_pp.txt",
                    "61320_200411_pp.txt",
                    "61320_201211_pp.txt",
                    "61320_201611_pp.txt",
                    "61620_200411_pp.txt",
                    "61620_200811_pp.txt",
                    "61620_201211_pp.txt",
                    "61620_201611_pp.txt"]

for corpus_name in corpus_name_list:
    # Getting the base path (must run the script from a folder inside the "SemSim_Autocor" folder)
    working_path = os.getcwd()
    base_path = str.split(working_path, "SemSim_AutoCor")[0] + "SemSim_AutoCor/"
    # Path of the raw text file
    text_file_path = f"{base_path}corpora/{corpus_name}"

    # Import the text file and remove non-existing token
    with open(text_file_path, "r") as text_file:
        text_string = text_file.read()
    token_list = nltk.word_tokenize(text_string)
    type_list = set(token_list)

    # Print result
    print(f"File {corpus_name} has {len(token_list)} tokens and {len(type_list)} types")
