import common.sbd_config as sbd
import json, caffe, argparse
from classification import Classifier
from flask import Flask, render_template, request
from os import walk, listdir
from preprocessing.word2vec_file import Word2VecFile
from tools.netconfig import NetConfig
from preprocessing.nlp_pipeline import PosTag

app = Flask(__name__)

route_folder = ''
config_file = None
caffeeproto_name = ''
caffemodel_file = None
folder = ''
config_options = []

DEBUG = True

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/classify", methods = ['POST'])
def classify():
    assert request.method == 'POST'
    text = request.form['text']
    data = classifier.predict_text(text)
    return json.dumps(data)

@app.route("/settings", methods = ['GET'])
def getSettingOptions():
    assert request.method == 'GET'
    result = []
    for (dirpath, dirnames, filenames) in walk(route_folder):
        result.extend(dirnames)
        break
    response = {"selected": folder, "options": result}
    return json.dumps(response)

@app.route("/settings", methods = ['POST'])
def changeSettings():
    global classifier
    assert request.method == 'POST'
    classifier = settings(str(request.form['folder']), vector)
    return ('', 200)


def settings(folder, vector):
    print 'Loading config folder: ' + folder

    config_file, caffemodel_file, net_proto = get_filenames(route_folder + folder)

    config_file = sbd.SbdConfig(config_file)
    WINDOW_SIZE = sbd.config.getint('windowing', 'window_size')
    POS_TAGGING = sbd.config.getboolean('features', 'pos_tagging')
    FEATURE_LENGTH = 300 if not POS_TAGGING else 300 + len(PosTag)

    with file(net_proto, "r") as input_:
        nc = NetConfig(input_)
    nc.transform_deploy([1, 1, WINDOW_SIZE, FEATURE_LENGTH])
    temp_proto = "%s/%s/temp_deploy.prototxt" % (route_folder, folder)
    with file(temp_proto, "w") as output:
        nc.write_to(output)

    net = caffe.Net(temp_proto, caffemodel_file, caffe.TEST)

    if vector:
        classifier = Classifier(net, vector, False)
    else:
        classifier = Classifier(net, vector, True)

    return classifier

def get_filenames(folder):
    config_file = ""
    caffemodel_file = ""
    net_proto = ""
    for file_ in listdir(folder):
        if file_.endswith(".ini"):
            config_file = folder + "/" + file_
        elif file_.endswith(".caffemodel"):
            caffemodel_file = folder + "/" + file_
        elif file_ == "net.prototxt":
            net_proto = folder + "/" + file_
    return config_file, caffemodel_file, net_proto

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='run the web demo')
    parser.add_argument('-r', '--rootfolder', help='the main directory containing all possible configurations', default='models/', nargs='?')
    parser.add_argument('-s', '--standard_model', help='the subdirectory of routes folder containing the default model', default="20160108-025006_google_ted_wiki_window-5-4_pos-false_qm-false_balanced-false_nr-rep-true_word-this", nargs='?')
    parser.add_argument('-v', '--vectorfile', help='the google news word vector', default='models/GoogleNews-vectors-negative300.bin', nargs='?')
    parser.add_argument('-nd','--no-debug', help='do not use debug mode, google vector is read', action='store_false', dest='debug', default=DEBUG)
    args = parser.parse_args()

    route_folder = args.rootfolder
    folder = args.standard_model

    config_options = []
    for (dirpath, dirnames, filenames) in walk(route_folder):
        config_options.extend(dirnames)
        break
    if not folder in config_options:
        folder = config_options[0]

    config_file, caffemodel_file, net_proto = get_filenames(route_folder + folder)
    config_file = sbd.SbdConfig(config_file)

    if not args.debug:
        vector = Word2VecFile(args.vectorfile)
        classifier = settings(folder, vector)
        app.run(debug = True, use_reloader = False)
    else:
        vector = None
        classifier = settings(folder, vector)
        app.run(debug = True)
