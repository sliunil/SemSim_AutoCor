import os
import string
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.corpus import wordnet
import contractions
from tqdm import tqdm

# -------------------------------------
# --- Parameters
# -------------------------------------

# Corpus name list
# corpus_name_list = ["Civil_Disobedience.txt",
#                     "Flowers_of_the_Farm.txt",
#                     "Sidelights_on_relativity.txt",
#                     "Prehistoric_Textile.txt"]
corpus_name_list = ["gutenberg/CarrollLewis_AliceAdventures.txt",
                    "gutenberg/CarrollLewis_SylvieandBruno.txt",
                    "gutenberg/CarrollLewis_TheHuntingoftheSnark.txt",
                    "gutenberg/CarrollLewis_ThroughtheLookingGlass.txt",
                    "gutenberg/ShakespeareWilliam_Hamlet.txt",
                    "gutenberg/ShakespeareWilliam_Macbeth.txt",
                    "gutenberg/ShakespeareWilliam_Othello.txt",
                    "gutenberg/ShakespeareWilliam_RomeoandJuliet.txt",
                    "gutenberg/WellsHG_DoctorMoreau.txt",
                    "gutenberg/WellsHG_TheFirstMenintheMoon.txt",
                    "gutenberg/WellsHG_TheInvisibleMan.txt",
                    "gutenberg/WellsHG_TheTimeMachine.txt",
                    "gutenberg/WildeOscar_AnIdealHusband.txt",
                    "gutenberg/WildeOscar_TheCantervilleGhost.txt",
                    "gutenberg/WildeOscar_TheImportanceofBeingEarnes.txt",
                    "gutenberg/WildeOscar_ThePictureofDorianGray.txt"]

# -------------------------------------
# --- Computations
# -------------------------------------

# Getting the base path (must run the script from a folder inside the "SemSim_Autocor" folder)
working_path = os.getcwd()
base_path = str.split(working_path, "SemSim_AutoCor")[0] + "/SemSim_AutoCor/"

# Stopwords
stop_words = stopwords.words('english')
# Lemmatizer
lemmatizer = WordNetLemmatizer()

# Loop on coprora
for corpus_name in tqdm(corpus_name_list):

    # Path of the raw text file
    text_file_path = f"{base_path}corpora/{corpus_name}"
    # Path of the outputted preprocessed text file
    pp_output_path = f"{base_path}corpora/{corpus_name[:-4]}_pp.txt"

    # --- Loading and Preprocessing --- #

    # Opening the file
    with open(text_file_path, "r") as text_file:
        text_string = text_file.read()

    # To lower case
    text_string_pp = text_string.lower()

    # Remove contractions
    text_string_pp = contractions.fix(text_string_pp)

    # Split by sentence
    sentence_list = nltk.sent_tokenize(text_string_pp)

    # Loop on sentences
    with open(pp_output_path, "w") as output_file:
        for sentence in sentence_list:

            # Remove punctuation
            sentence_pp = "".join([char for char in sentence if char in string.ascii_letters + " \n"])

            # Split by token
            token_list = nltk.word_tokenize(sentence_pp)

            # Remove stopwords
            token_list = [token for token in token_list if token not in stop_words]

            # POS tag
            tagged_token_list = nltk.pos_tag(token_list)

            # Changing POS tag to wordnet tag
            wn_tagged_token_list = []
            for tagged_token in tagged_token_list:
                if tagged_token[1].startswith('J'):
                    wn_tagged_token_list.append((tagged_token[0], wordnet.ADJ))
                elif tagged_token[1].startswith('V'):
                    wn_tagged_token_list.append((tagged_token[0], wordnet.VERB))
                elif tagged_token[1].startswith('N'):
                    wn_tagged_token_list.append((tagged_token[0], wordnet.NOUN))
                elif tagged_token[1].startswith('R'):
                    wn_tagged_token_list.append((tagged_token[0], wordnet.ADV))
                else:
                    wn_tagged_token_list.append([tagged_token[0]])

            # Lemmatization
            token_list_pp = [lemmatizer.lemmatize(*tagged_token) for tagged_token in wn_tagged_token_list]

            # --- SAVING FILE --- #

            # Saving the file with all tokens and tags
            for token in token_list_pp:
                output_file.write(f"{token} ")

            # End of line
            output_file.write("\n")
