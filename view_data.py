import os
import re
from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit

def int_from_str(text):
    try:
        return int(re.findall(r"\d+", text)[0])
    except:
        return 0

def is_valid_path(path_to_games, folder):
    joined = os.path.join(path_to_games, folder)
    return os.path.isdir(joined)

class TrainStep:
    def __init__(self, file_name):
        split_file = file_name.split("_")
        self.turn = int(split_file[0])
        self.train_step = int_from_str(split_file[-1])
        self.file = file_name

class DataManager:

    def __init__(self):
        self.path_to_games = "static/result" #input("Enter path to games: ")        
        self.create_game_folders()
        self.data = [self.game_data(x) for x in self.game_folders]

    def create_game_folders(self):
        self.ground_truth_folders = []
        self.game_folders = []
        all_folders = [x for x in os.listdir(self.path_to_games) if is_valid_path(self.path_to_games, x)]        
        all_folders = sorted(all_folders, key = lambda x : int_from_str(x))        
        for folder in all_folders:            
            if "_gt" in folder:
                self.ground_truth_folders.append(os.path.join(self.path_to_games, folder))
            else:
                self.game_folders.append(os.path.join(self.path_to_games, folder))

    def paths_for_game(self, folder_path):
        # Can we do it in one pass
        result = []
        all_files = sorted([x for x in os.listdir(folder_path) if '.png' in x or '.jpg' in x], key = lambda x : int_from_str(x))
        turn = 0
        highest_train_step = 0
        latest_file = 0

        for file in all_files:            
            train_step = TrainStep(file)  

            if train_step.turn == turn and train_step.train_step > highest_train_step:
                highest_train_step = train_step.train_step
                latest_file = file
            elif train_step.turn > turn:
                result.append(latest_file)
                turn = train_step.turn
                highest_train_step = train_step.train_step
                latest_file = train_step.file

        return [os.path.join(folder_path, x) for x in result if isinstance(x, str)]

    def game_data(self, folder_path):
        image_paths = self.paths_for_game(folder_path)
        utterances = [x.split('_')[1] for x in image_paths]
        result = {'images':image_paths, 'utterances':utterances}
        return result
        
# Init the server
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True)

# Get data
dm = DataManager()

@app.route('/')
def root():
    """ Send HTML from the server."""
    return render_template('index.html')

@socketio.on('request_data')   
def message_recieved(data):    
    emit('data', dm.data)

if __name__ == '__main__':
    """ Run the app. """    
    socketio.run(app, port=3000)