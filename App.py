from collections import Counter
import random
import requests
import os
import socket
import json
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
    
    
class DogEntry(GridLayout):
    def __init__(self, **kwargs):
        super(DogEntry, self).__init__(**kwargs)
        self.cols = 6
        self.dog_name_entry = TextInput(hint_text="Dog Name", multiline=False)
        self.add_widget(self.dog_name_entry)
        self.average_speed_entry = TextInput(hint_text="Average Speed", multiline=False)
        self.add_widget(self.average_speed_entry)
        self.early_speed_spinner = Spinner(text="Early Speed", values=('Front Runner', 'Midfield', 'Backmarker'))
        self.add_widget(self.early_speed_spinner)
        self.days_since_entry = TextInput(hint_text="Days Since Last Raced", multiline=False)
        self.add_widget(self.days_since_entry)
        self.win_odds_entry = TextInput(hint_text="Win Odds", multiline=False)
        self.add_widget(self.win_odds_entry)
        self.place_odds_entry = TextInput(hint_text="Place Odds", multiline=False)
        self.add_widget(self.place_odds_entry)
    
def save_data_to_file():
    global entry_widgets, race_name_entry, race_distance_entry, track_type_combobox, track_state_combobox

    dog_data = []
    for widget in entry_widgets:
        dog_entry = {}
        for key, entry in widget.items():
            if isinstance(entry, ttk.Combobox):
                dog_entry[key] = entry.get()
            else:
                dog_entry[key] = entry.get()
        dog_data.append(dog_entry)

    race_data = {
        'race_name': race_name_entry.get(),
        'race_distance': race_distance_entry.get(),
        'track_type': track_type_combobox.get(),
        'track_state': track_state_combobox.get(),
        'dogs': dog_data
    }

    file_path = tk.filedialog.asksaveasfilename(title="Save Data", filetypes=[("JSON files", "*.json")], defaultextension=".json")
    if not file_path:
        return

    with open(file_path, 'w') as file:
        json.dump(race_data, file, indent=4)


def load_data_from_file():
    global entry_widgets, race_name_entry, race_distance_entry, track_type_combobox, track_state_combobox

    file_path = tk.filedialog.askopenfilename(title="Load Data", filetypes=[("JSON files", "*.json")])
    if not file_path:
        return

    with open(file_path, 'r') as file:
        race_data = json.load(file)

    race_name_entry.delete(0, tk.END)
    race_name_entry.insert(0, race_data['race_name'])
    
    race_distance_entry.delete(0, tk.END)
    race_distance_entry.insert(0, race_data['race_distance'])

    track_type_combobox.set(race_data['track_type'])
    track_state_combobox.set(race_data['track_state'])

    for i, dog_entry in enumerate(race_data['dogs']):
        for key, value in dog_entry.items():
            entry_widget = entry_widgets[i][key]
            if isinstance(entry_widget, ttk.Combobox):
                entry_widget.set(value)
            else:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, value)
            
            
            
def validate_inputs():
    global entry_widgets, race_name_entry, race_distance_entry, track_state_combobox

    # Check if race name, race distance, and track state are filled in
    if not race_name_entry.get().strip():
        return "Race Name is empty."
    if not race_distance_entry.get().strip():
        return "Race Distance is empty."
    if not track_state_combobox.get().strip():
        return "Track Weather State is not selected."

    # Check each dog row
    for i, widget in enumerate(entry_widgets):
        dog_name = widget['name'].get().strip()
        if dog_name:  # If dog name is filled out
            if not widget['average_speed'].get().strip():
                return f"Row {i+1}: Average Speed is empty for {dog_name}."
            if not widget['early_speed'].get().strip():
                return f"Row {i+1}: Early Speed is not selected for {dog_name}."
            if not widget['days_since_last_race'].get().strip():
                return f"Row {i+1}: Days Since Last Raced is empty for {dog_name}."
            if not widget['win_odds'].get().strip():
                return f"Row {i+1}: Win Odds is empty for {dog_name}."
            if not widget['place_odds'].get().strip():
                return f"Row {i+1}: Place Odds is empty for {dog_name}."

    return None  # If everything is filled out correctly
            



def show_average_speed_info():
    messagebox.showinfo("Info", "Use GPT to calculate the average speed of dogs past races (paste the form guide into GPT)" + "\n" + "\n" + "Dogs Names Must Have Box Number too E.G Springview Hero (1)" + "\n" + "\n" + "Use SP Odds")
   
def box_effect(box_number, early_speed_type):
    front_runner_chances = {
        1: 0.15, 2: 0.18, 3: 0.20, 4: 0.22, 5: 0.25,
        6: 0.10, 7: 0.12, 8: 0.15, 9: 0.17, 10: 0.20
    }
    backmarker_chances = {
        1: 0.10, 2: 0.12, 3: 0.14, 4: 0.16, 5: 0.18,
        6: 0.10, 7: 0.12, 8: 0.14, 9: 0.16, 10: 0.18
    }
    midfield_chances = {
        1: 0.20, 2: 0.22, 3: 0.24, 4: 0.26, 5: 0.28,
        6: 0.15, 7: 0.17, 8: 0.19, 9: 0.21, 10: 0.23
    }
    if early_speed_type == 'Front Runner':
        return 1 - front_runner_chances.get(box_number, 1.0)
    elif early_speed_type == 'Backmarker':
        return 1 - backmarker_chances.get(box_number, 1.0)
    elif early_speed_type == 'Midfield':
        return 1 - midfield_chances.get(box_number, 1.0)
    else:
        return 1.0

def days_since_last_race_effect(days_since):
    if days_since <= 7:
        return 0.9
    elif 7 < days_since <= 14:
        return 1.0
    else:
        return 0.95

def calculate_race_score_adjusted(dog, attributes, distance, form_factor=1, prev_wins_factor=1):
    # Average Speed as base
    race_score = attributes['average_speed']
    
    # Early Speed adjustment
    early_speed_scores = {'Front Runner': 1.1, 'Midfield': 1.0, 'Backmarker': 0.9}
    early_speed_score = early_speed_scores.get(attributes['early_speed'], 1.0)
    race_score *= early_speed_score
    
    # Days Since Last Raced adjustment
    days_since_last_race = attributes.get('days_since_last_race', 3)
    days_multiplier = 1 / days_since_last_race
    race_score *= days_multiplier
    
    # Endurance Factor
    endurance_factor = attributes.get('endurance_factor', 1)
    race_score *= endurance_factor
    
    # Speed Decay based on distance
    speed_decay = attributes.get('speed_decay', 0)
    race_score -= (speed_decay * distance)
    
    # Box Effect
    box_num = int(dog.split('(')[-1].split(')')[0])
    race_score *= box_effect(box_num, attributes['early_speed'])
    
    # Win Odds and Place Odds
    win_odds = attributes.get('win_odds', 1.0)
    MIN_MULTIPLIER = 0.2
    MAX_MULTIPLIER = 0.3
    win_odds_multiplier = 1 / win_odds
    win_odds_multiplier = max(MIN_MULTIPLIER, min(win_odds_multiplier, MAX_MULTIPLIER))
    race_score *= win_odds_multiplier
    
    place_odds = attributes.get('place_odds', 1.0)
    place_odds_multiplier = 1 / place_odds
    place_odds_multiplier = max(MIN_MULTIPLIER, min(place_odds_multiplier, MAX_MULTIPLIER))
    race_score *= place_odds_multiplier
    
    # Form Factor
    form_factor = 1
    race_score *= form_factor
    
    # Previous Wins Factor
    prev_wins_factor = 1
    race_score *= prev_wins_factor
    
    return race_score

def collision_chance(box_number, early_speed_type):
    front_runner_chances = {
        1: 0.15, 2: 0.18, 3: 0.20, 4: 0.22, 5: 0.25,
        6: 0.10, 7: 0.12, 8: 0.15, 9: 0.17, 10: 0.20
    }
    backmarker_chances = {
        1: 0.10, 2: 0.12, 3: 0.14, 4: 0.16, 5: 0.18,
        6: 0.10, 7: 0.12, 8: 0.14, 9: 0.16, 10: 0.18
    }
    midfield_chances = {
        1: 0.20, 2: 0.22, 3: 0.24, 4: 0.26, 5: 0.28,
        6: 0.15, 7: 0.17, 8: 0.19, 9: 0.21, 10: 0.23
    }
    if early_speed_type == 'Front Runner':
        return front_runner_chances.get(box_number, 0)
    elif early_speed_type == 'Backmarker':
        return backmarker_chances.get(box_number, 0)
    elif early_speed_type == 'Midfield':
        return midfield_chances.get(box_number, 0)
    else:
        return 0.0 
        
        
def get_starting_positions(dogs):
    """Return a sorted list of dogs based on their box numbers."""
    return sorted(dogs.keys(), key=lambda x: int(x.split('(')[-1].split(')')[0]))

def dynamic_collision_chance(dog1_name, dog2_name, evaluated_positions):
    """Calculate the chance of collision between two dogs based on their evaluated positions."""
    pos_difference = abs(evaluated_positions[dog1_name] - evaluated_positions[dog2_name])
    if pos_difference <= 1:
        # More likely to collide if they're adjacent
        return 0.02
    elif pos_difference == 2:
        return 0.01
    else:
        return 0.05

def evaluate_positions(starting_positions, dogs):
    """Evaluate the position of each dog during the race based on its early speed."""
    early_speed_rank = {'Front Runner': 3, 'Midfield': 2, 'Backmarker': 1}
    return {dog: early_speed_rank[dogs[dog]['early_speed']] for dog in starting_positions}

def get_huddle_mates(dog, evaluated_positions):
    """Get the dogs that are in close proximity (huddle) with the given dog."""
    dog_position = evaluated_positions[dog['name']]
    return [name for name, position in evaluated_positions.items() if abs(position - dog_position) <= 1 and name != dog['name']]

def handle_collision(dog1, dog2):
    """Handle the effect of a collision between two dogs."""
    # For this example, we just reduce the speed of both dogs by 10%.
    # This can be made more sophisticated based on the nature and impact of collisions.
    dog1_speed = dog1.get('average_speed', 0)
    dog2_speed = dog2.get('average_speed', 0)
    dog1['average_speed'] = dog1_speed * 0.9
    dog2['average_speed'] = dog2_speed * 0.9        

def simulate_dog_race_probabilistic_adjusted_with_collision(dogs, distance, race_name, num_simulations=100000):
    race_scores = {}
    for dog, attributes in dogs.items():
        race_scores[dog] = calculate_race_score_adjusted(dog, attributes, distance)

        
    total_score = sum(race_scores.values())
    race_probabilities = {dog: score / total_score for dog, score in race_scores.items()}
    for dog, attributes in dogs.items():
        win_odds = attributes.get('win_odds', 1.0)
        race_probabilities[dog] *= 1 / win_odds
    total_probability = sum(race_probabilities.values())
    race_probabilities = {dog: prob / total_probability for dog, prob in race_probabilities.items()}

    # Enhanced collision handling
    starting_positions = get_starting_positions(dogs)
    evaluated_positions = evaluate_positions(starting_positions, dogs)

    simulation_results = []
    for _ in range(num_simulations):
        selected_dog = random.choices(list(race_probabilities.keys()), weights=list(race_probabilities.values()), k=1)[0]
        
        # Handle dynamic collisions based on positions and early speed types
        huddle_mates = get_huddle_mates({'name': selected_dog, **dogs[selected_dog]}, evaluated_positions)
        for mate_name in huddle_mates:
            if random.random() <= dynamic_collision_chance(selected_dog, mate_name, evaluated_positions):
                race_scores[selected_dog] *= 0.9

        simulation_results.append(selected_dog)

    outcome_counts = Counter(simulation_results)
    sorted_outcomes = sorted(outcome_counts.items(), key=lambda x: x[1], reverse=True)
    print("Most Likely Race Winner (Based on Simulations with Collision Chances):")
    outcome_message = f"{race_name}\n Most Likely Race Winner (Based on Simulations with Collision Chances):\n"
    for i, (dog, count) in enumerate(sorted_outcomes):
        outcome_message += f"{i+1}. {dog} - Probability: {count / num_simulations:.2%}\n"
        print(f"{i+1}. {dog} - Probability: {count / num_simulations:.2%}")
    safe_bet_dogs = [dog for dog, _ in sorted_outcomes[:2]]
    risky_bet_dogs_top3 = [dog for dog, _ in sorted_outcomes[:1]]
    risky_bet_dogs_top4 = [dog for dog, _ in sorted_outcomes[1:3]]
    safe_bet_message = f"\nSAFE BET: Top 4 " + " and ".join(safe_bet_dogs) + "\n"
    risky_bet_message = f"RISKY BET: Top 3 {risky_bet_dogs_top3[0]} Top 4 " + " and ".join(risky_bet_dogs_top4) + "\n"
    print(safe_bet_message)
    print(risky_bet_message)
    outcome_message += safe_bet_message + risky_bet_message
    return outcome_message, sorted_outcomes

def recommend_MBO_for_second(dogs_with_attributes, sorted_outcomes):
    if len(sorted_outcomes) < 2:
        print("Not enough data for MBO recommendation.")
        return "Not enough data for MBO recommendation."
        
    second_place_dog = sorted_outcomes[1][0]
    mbo_message = f"MBO for 3rd: {second_place_dog}" + "\n"
    mbo_message2 = f"MBO for 3rd: {second_place_dog}" + "\n"    
    print(mbo_message)   
    return mbo_message

class GreyhoundSimulatorApp(App):
    def build(self):
        main_layout = BoxLayout(orientation="vertical")
        
        # Race Info
        race_info = GridLayout(cols=6, size_hint_y=None, height=44)
        race_info.add_widget(Label(text="Race Name:"))
        self.race_name_entry = TextInput(multiline=False)
        race_info.add_widget(self.race_name_entry)
        race_info.add_widget(Label(text="Race Distance:"))
        self.race_distance_entry = TextInput(multiline=False)
        race_info.add_widget(self.race_distance_entry)
        race_info.add_widget(Label(text="Track Type:"))
        self.track_type_spinner = Spinner(text="Curved", values=("Curved", "Straight"))
        race_info.add_widget(self.track_type_spinner)
        main_layout.add_widget(race_info)
        
        # Dog Entries
        self.dog_entries_layout = GridLayout(cols=1, size_hint_y=None)
        self.dog_entries_layout.bind(minimum_height=self.dog_entries_layout.setter('height'))
        for _ in range(10):  # For 10 dogs
            dog_entry = DogEntry(size_hint_y=None, height=44)
            self.dog_entries_layout.add_widget(dog_entry)
        
        scroll_view = ScrollView(do_scroll_x=False)
        scroll_view.add_widget(self.dog_entries_layout)
        main_layout.add_widget(scroll_view)
        
        # Result Display
        self.result_label = Label(text="Results will be displayed here...", size_hint_y=None, height=200)
        main_layout.add_widget(self.result_label)
        
        # Buttons
        button_layout = BoxLayout(size_hint_y=None, height=50)
        simulate_button = Button(text="Start Simulation")
        # You'd typically bind the simulate button's 'on_press' event to the function that handles the simulation.
        # For this example, I haven't implemented that logic.
        button_layout.add_widget(simulate_button)
        clear_button = Button(text="Reset", on_press=self.clear_entries)
        button_layout.add_widget(clear_button)
        main_layout.add_widget(button_layout)
        
        return main_layout

    def clear_entries(self, instance):
        self.race_name_entry.text = ""
        self.race_distance_entry.text = ""
        self.track_type_spinner.text = "Curved"
        for dog_entry in self.dog_entries_layout.children:
            dog_entry.dog_name_entry.text = ""
            dog_entry.average_speed_entry.text = ""
            dog_entry.early_speed_spinner.text = "Early Speed"
            dog_entry.days_since_entry.text = ""
            dog_entry.win_odds_entry.text = ""
            dog_entry.place_odds_entry.text = ""
        self.result_label.text = "Results will be displayed here..."

if __name__ == '__main__':
    GreyhoundSimulatorApp().run()