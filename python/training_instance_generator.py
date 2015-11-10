import sys
import os

from talk_parser import TalkParser
import sliding_window
from word2vec_file import Word2VecFile
from level_db_creator import LevelDBCreator
from sets import set


WORD_VECTOR_FILE = "/home/fb10dl01/workspace/ms-2015-t3/GoogleNews-vectors-negative300.bin"
#WORD_VECTOR_FILE = "/home/ms2015t3/vectors.bin"
LEVEL_DB_DIR = "/home/ms2015t3/sentence-boundary-detection-nn/leveldbs/"


class TrainingInstanceGenerator():
    """reads the original data, process them and writes them to a level-db"""

    def __init__(self):
        self.word2vec = Word2VecFile(WORD_VECTOR_FILE)
        self.test_talks = Set()

    def generate(self, training_data, database, test):
        level_db = LevelDBCreator(LEVEL_DB_DIR + database)
        window_slider = sliding_window.SlidingWindow()

        count = len(training_data)

        nr_instances = 0

        for i, training_paths in enumerate(training_data):
            progress = int(i * 100.0 / count)
            sys.stdout.write(str(progress) + "% ")
            sys.stdout.flush()

            talk_parser = TalkParser(training_paths[0], training_paths[1])
            talks = talk_parser.list_talks()

            for talk in talks:
                if test:
                    self.test_talks.add(talk.id)
                if not test and talk.id in self.test_talks:
                    print("Skip talk %s for training! Talk is already in test set." % talk.id)
                    continue

                for sentence in talk.sentences:
                    # get the word vectors for all token in the sentence
                    for token in sentence.gold_tokens:
                        if not token.is_punctuation():
                            token.word_vec = self.word2vec.get_vector(token.word.lower())

                    # get the training instances
                    training_instances = window_slider.list_windows(sentence)

                    # write training instances to level db
                    for training_instance in training_instances:
                        nr_instances += 1
                        level_db.write_training_instance(training_instance)

                    # print (training_instances)

        print("Created " + str(nr_instances) + " instances.")

    def get_not_covered_words(self):
        return self.word2vec.not_covered_words


if __name__ == '__main__':

    argc = len(sys.argv)
    if argc != 2:
        print("Usage: " + sys.argv[0] + " [data_folder]")
        sys.exit(1)

    data_folder = sys.argv[1]
    sentence_home = os.environ['SENTENCE_HOME']

    print("Deleting " + sentence_home + "/leveldbs/" + data_folder + ". Y/n?")
    s = raw_input()
    if s != "Y":
        print("Not deleting. Exiting ..")
        sys.exit(2)

    database = sentence_home + "/leveldbs/" + data_folder
    if os.path.isdir(database):
        import shutil
        shutil.rmtree(database)
    os.mkdir(database)

    training_data = [
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/dev2010-w/IWSLT15.TED.dev2010.en-zh.en.xml",
         "/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/dev2010-w/word-level transcript/dev2010.en.talkid<id>_sorted.txt"),
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/tst2010-w/IWSLT15.TED.tst2010.en-zh.en.xml",
         None),
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/tst2012-w/IWSLT12.TED.MT.tst2012.en-fr.en.xml",
         None),
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/tst2013-w/IWSLT15.TED.tst2013.en-zh.en.xml",
         None)
    ]
    test_data = [
        ("/home/fb10dl01/workspace/ms-2015-t3/Data/Dataset/tst2013-w/IWSLT15.TED.tst2013.en-zh.en.xml",
         None)
    ]

    generator = TrainingInstanceGenerator()
    print("Generating test data .. ")
    generator.generate(test_data, data_folder + "/test", True)
    print("Done.")
    print("Generating training data .. ")
    generator.generate(training_data, data_folder + "/train", False)
    print("Done.")
    print("")
    print(generator.get_not_covered_words())
