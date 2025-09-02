import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from typing import Dict, Any
import os
import json
import pandas as pd  # Explicitly import pandas
from fuzzywuzzy import fuzz  # Explicitly import fuzz
from geopy.geocoders import Nominatim
import openrouteservice
import re
from math import radians, sin, cos, sqrt, atan2
import usaddress
from ..core.matcher import FuzzyMatcher
from ..core.preprocessor import DataPreprocessor
from ..utils.config import Config
from ..utils.file_handler import FileHandler

class FuzzyMatchApp:
    def __init__(self):
        """Initialize the main application window."""
        self.root = ctk.CTk()
        self.root.title("Fuzzy Match Tool")
        self.root.geometry("800x600")
        
        # Initialize configuration
        self.config = Config()
        
        # Initialize algorithm weights
        self.algorithm_weights = {
            'levenshtein': 1.0,
            'jaro_winkler': 1.0,
            'jaccard': 1.0,
            'cosine': 1.0,
            'soundex': 1.0
        }
        
        # Create main components
        self.create_notebook()
        self.create_menu()
        
        # Initialize data containers
        self.source_df = None
        self.reference_df = None
        self.matcher = None
        
    def create_notebook(self):
        """Create the main notebook with tabs."""
        self.notebook = ttk.Notebook(self.root)
        
        # Create tabs
        self.config_tab = self.create_config_tab()
        self.matching_tab = self.create_matching_tab()
        self.geo_tab = self.create_geo_tab()
        
        # Add tabs to notebook
        self.notebook.add(self.config_tab, text="Configuration")
        self.notebook.add(self.matching_tab, text="Matching")
        self.notebook.add(self.geo_tab, text="Geo Level Refinement")
        
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Initialize geo services
        self.initialize_geo_services()
        
    def initialize_geo_services(self):
        """Initialize geolocation services."""
        self.geolocator = Nominatim(user_agent="fuzzy_match_tool")
        self.ors_client = openrouteservice.Client(
            key="eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjZlMzdlMzdlYTc4NTQ0YWRiODk2MzllNTYwMjNkMTlhIiwiaCI6Im11cm11cjY0In0="
        )

    def clean_address(self, addr: str) -> str:
        """Clean and format address string."""
        if not addr:
            return ""
        s = str(addr).strip()
        s = re.sub(r"\.0\b", "", s)
        s = re.sub(r"(\b)(\d{4})(\b)$", r"\g<1>0\2", s)
        s = re.sub(r"\s{2,}", " ", s)
        return s

    def haversine_miles(self, lat1, lon1, lat2, lon2):
        """Calculate haversine distance in miles."""
        R = 3959.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
        return 2 * R * atan2(sqrt(a), sqrt(1 - a))

    def get_coords_dynamic(self, address):
        """Get coordinates for an address using ORS or Nominatim."""
        address = self.clean_address(address)
        try:
            res = self.ors_client.pelias_search(text=address)
            feats = res.get("features", []) if isinstance(res, dict) else []
            if feats:
                coords = feats[0]["geometry"]["coordinates"]
                return (coords[0], coords[1])
        except Exception:
            pass
            
        try:
            loc = self.geolocator.geocode(address, country_codes="us", timeout=10)
            if loc:
                return (loc.longitude, loc.latitude)
        except Exception:
            pass
        return None

    def get_travel_info(self, origin_address, destination_address, same_point_radius_meters=50):
        """Calculate travel distance and time between two addresses."""
        origin = self.get_coords_dynamic(origin_address)
        destination = self.get_coords_dynamic(destination_address)
        
        if not origin or not destination:
            return {"error": "Could not geocode one or both addresses."}
            
        o_lon, o_lat = origin
        d_lon, d_lat = destination
        crow_miles = round(self.haversine_miles(o_lat, o_lon, d_lat, d_lon), 3)
        
        if crow_miles <= (same_point_radius_meters * 0.000621371):
            return {
                "straight_line_miles": crow_miles,
                "driving_distance_miles": 0.0,
            }
            
        try:
            route = self.ors_client.directions([origin, destination], profile="driving-car")
            routes = route.get("routes", []) if isinstance(route, dict) else []
            if not routes:
                return {
                    "error": "No valid route found.",
                    "straight_line_miles": crow_miles
                }
                
            summary = routes[0].get("summary", {})
            if "distance" not in summary:
                return {
                    "error": "ORS routing did not return distance.",
                    "straight_line_miles": crow_miles
                }
                
            distance_miles = round(summary["distance"] / 1609.34, 2)
            return {
                "straight_line_miles": crow_miles,
                "driving_distance_miles": distance_miles,
            }
        except Exception as e:
            return {
                "error": f"Routing failed: {e}",
                "straight_line_miles": crow_miles
            }

    def create_config_tab(self):
        """Create the configuration tab."""
        tab = ttk.Frame(self.notebook)
        tab.grid_columnconfigure(0, weight=1)  # Make tab expand horizontally
        
        # Create main configuration frame
        main_frame = ttk.Frame(tab)
        main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)

        # Algorithm selection frame
        algo_select_frame = ttk.LabelFrame(main_frame, text="Primary Matching Algorithm", padding=(10, 5))
        algo_select_frame.grid(row=0, column=0, sticky='ew', pady=5)
        algo_select_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(algo_select_frame, text="Select Algorithm:").grid(row=0, column=0, padx=5, pady=2)
        self.algorithm_var = tk.StringVar(value='weighted')
        algorithm_combo = ttk.Combobox(
            algo_select_frame, 
            textvariable=self.algorithm_var,
            values=['weighted', 'levenshtein', 'jaro_winkler', 'jaccard', 'cosine', 'soundex'],
            state='readonly',
            width=30
        )
        algorithm_combo.grid(row=0, column=1, padx=5, sticky='w')
        
        # Weight configuration frame
        weight_frame = ttk.LabelFrame(main_frame, text="Algorithm Weights", padding=(10, 5))
        weight_frame.grid(row=1, column=0, sticky='ew', pady=5)
        weight_frame.grid_columnconfigure(0, weight=1)
        
        # Style configuration for the entire application
        style = ttk.Style()
        style.configure("Compact.Horizontal.TScale", sliderlength=15)
        
        # Configure consistent fonts for all widgets
        style.configure("TLabel", font=("", 11))
        style.configure("TLabelframe.Label", font=("", 12, "bold"))
        style.configure("TButton", font=("", 11))
        style.configure("TEntry", font=("", 11))
        style.configure("TCombobox", font=("", 11))
        style.configure("Treeview", font=("", 11))
        style.configure("Treeview.Heading", font=("", 11, "bold"))
        # Configure tab font size
        style.configure("TNotebook.Tab", font=("", 10))  # Set smaller font size for tabs without bold
        
        # Core algorithms with descriptions
        core_algorithms = [
            ('Levenshtein', 'levenshtein', 'Best for typos and spelling mistakes'),
            ('Jaro-Winkler', 'jaro_winkler', 'Best for person names and brands'),
            ('Jaccard', 'jaccard', 'Best for addresses and word overlap'),
            ('Cosine', 'cosine', 'Best for long text and context'),
            ('Soundex', 'soundex', 'Best for phonetic matching')
        ]

        # Create weight sliders
        self.weight_vars = {}
        self.weight_labels = {}  # Store labels for updating
        
        for idx, (name, algo_id, desc) in enumerate(core_algorithms):
            # Algorithm container
            algo_container = ttk.Frame(weight_frame)
            algo_container.grid(row=idx, column=0, sticky='ew', pady=2)
            algo_container.grid_columnconfigure(1, weight=1)
            
            # Algorithm name and description with number
            name_frame = ttk.Frame(algo_container)
            name_frame.grid(row=0, column=0, padx=5)
            
            ttk.Label(name_frame, text=f"{idx+1}. {name}").grid(row=0, column=0, sticky='w')
            ttk.Label(name_frame, text=desc).grid(row=1, column=0, sticky='w')
            
            # Slider container
            slider_container = ttk.Frame(algo_container)
            slider_container.grid(row=0, column=1, sticky='ew', padx=10)
            slider_container.grid_columnconfigure(0, weight=1)
            
            # Create IntVar for the slider
            var = tk.IntVar(value=1)
            self.weight_vars[algo_id] = var
            
            # Create slider
            scale = ttk.Scale(
                slider_container,
                from_=0,
                to=5,
                variable=var,
                orient='horizontal',
                style="Compact.Horizontal.TScale"
            )
            scale.grid(row=0, column=0, sticky='ew')
            
            # Create value label
            value_label = ttk.Label(
                slider_container,
                text="1",
                width=2,
                font=('', 11, 'bold'),
                anchor='e'
            )
            value_label.grid(row=0, column=1, padx=(5, 10))
            
            # Create update function specific to this slider
            def make_update_func(v, lbl):
                def update(*args):
                    try:
                        value = int(v.get())
                        lbl.configure(text=str(value))
                    except:
                        lbl.configure(text="1")
                return update
            
            # Bind the update function
            update_func = make_update_func(var, value_label)
            var.trace_add("write", update_func)

        # Info label for weights
        ttk.Label(
            weight_frame,
            text="Adjust weights to control how each algorithm influences matching. 0 = not used, 1 = normal weight, >1 = increased importance",
            wraplength=500
        ).grid(row=len(core_algorithms), column=0, pady=(5,0), sticky='w')
            
        # Threshold frame
        thresh_frame = ttk.LabelFrame(main_frame, text="Matching Configuration", padding=(10, 5))
        thresh_frame.grid(row=2, column=0, sticky='ew', pady=5)
        thresh_frame.grid_columnconfigure(1, weight=1)
        
        # Threshold setting
        ttk.Label(thresh_frame, text="Match Threshold:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        threshold_container = ttk.Frame(thresh_frame)
        threshold_container.grid(row=0, column=1, sticky='ew', padx=5)
        threshold_container.grid_columnconfigure(0, weight=1)
        
        self.threshold_var = tk.DoubleVar(value=80)
        threshold_scale = ttk.Scale(
            threshold_container,
            from_=0,
            to=100,
            variable=self.threshold_var,
            orient='horizontal',
            style="Compact.Horizontal.TScale"
        )
        threshold_scale.grid(row=0, column=0, sticky='ew')
        
        # Create StringVar for formatted threshold display
        self.threshold_display_var = tk.StringVar()
        def update_threshold_display(*args):
            value = int(self.threshold_var.get())
            self.threshold_display_var.set(str(value))
        self.threshold_var.trace_add("write", update_threshold_display)
        update_threshold_display()  # Initial update
        
        # Threshold value label
        ttk.Label(threshold_container, textvariable=self.threshold_display_var, font=('', 11, 'bold'), width=3, anchor='e').grid(row=0, column=1, padx=(5, 10), sticky='e')
        
        # Remove threshold numbers to keep the UI clean
        
        # Max matches setting
        ttk.Label(thresh_frame, text="Maximum Matches:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        self.max_matches_var = tk.IntVar(value=5)
        max_matches_entry = ttk.Entry(
            thresh_frame,
            textvariable=self.max_matches_var,
            width=10
        )
        max_matches_entry.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        # Save configuration button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Configuration",
            command=self.save_configuration,
            height=25,  # Reduced button height
            font=("", 10)  # Reduced font size
        )
        save_btn.pack()
        
        return tab
        
    def create_matching_tab(self):
        """Create the matching tab."""
        tab = ttk.Frame(self.notebook)
        
        # File selection
        file_frame = ttk.LabelFrame(tab, text="Input Files", padding=10)
        file_frame.pack(fill='x', padx=5, pady=5)
        
        # Source file
        ttk.Label(file_frame, text="Source File:").grid(row=0, column=0, sticky='w')
        self.source_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.source_path_var).grid(
            row=0, column=1, padx=5, sticky='ew'
        )
        ctk.CTkButton(
            file_frame,
            text="Browse",
            command=lambda: self.browse_file(self.source_path_var),
            height=25,
            font=("", 10)
        ).grid(row=0, column=2)
        
        # Reference file
        ttk.Label(file_frame, text="Reference File:").grid(row=1, column=0, sticky='w')
        self.ref_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.ref_path_var).grid(
            row=1, column=1, padx=5, sticky='ew'
        )
        ctk.CTkButton(
            file_frame,
            text="Browse",
            command=lambda: self.browse_file(self.ref_path_var),
            height=25,
            font=("", 10)
        ).grid(row=1, column=2)
        
        file_frame.columnconfigure(1, weight=1)
        
        # Column selection frame
        column_frame = ttk.LabelFrame(tab, text="Column Matching", padding=10)
        column_frame.pack(fill='x', padx=5, pady=5)
        
        # Column pairs list
        self.column_pairs_tree = ttk.Treeview(
            column_frame,
            columns=('Source', 'Reference', 'Weight', 'Threshold'),
            show='headings',
            height=6
        )
        self.column_pairs_tree.heading('Source', text='Source Column')
        self.column_pairs_tree.heading('Reference', text='Reference Column')
        self.column_pairs_tree.heading('Weight', text='Weight')
        self.column_pairs_tree.heading('Threshold', text='Threshold %')
        
        # Set column widths
        self.column_pairs_tree.column('Source', width=150)
        self.column_pairs_tree.column('Reference', width=150)
        self.column_pairs_tree.column('Weight', width=70)
        self.column_pairs_tree.column('Threshold', width=90)
        
        self.column_pairs_tree.pack(fill='both', expand=True, pady=5)
        
        # Column selection controls
        controls_frame = ttk.Frame(column_frame)
        controls_frame.pack(fill='x', pady=5)
        
        # Source column selection
        ttk.Label(controls_frame, text="Source:").grid(row=0, column=0, padx=5)
        self.source_column_var = tk.StringVar()
        self.source_column_combo = ttk.Combobox(controls_frame, textvariable=self.source_column_var)
        self.source_column_combo.grid(row=0, column=1, padx=5)
        
        # Reference column selection
        ttk.Label(controls_frame, text="Reference:").grid(row=0, column=2, padx=5)
        self.ref_column_var = tk.StringVar()
        self.ref_column_combo = ttk.Combobox(controls_frame, textvariable=self.ref_column_var)
        self.ref_column_combo.grid(row=0, column=3, padx=5)
        
        # Weight entry
        ttk.Label(controls_frame, text="Weight:").grid(row=0, column=4, padx=(15,5))
        self.column_weight_var = tk.StringVar(value="1.0")
        weight_entry = ttk.Entry(controls_frame, textvariable=self.column_weight_var, width=8)
        weight_entry.grid(row=0, column=5, padx=5)
        
        # Threshold entry
        ttk.Label(controls_frame, text="Threshold %:").grid(row=0, column=6, padx=(15,5))
        self.column_threshold_var = tk.StringVar(value="80")
        threshold_entry = ttk.Entry(controls_frame, textvariable=self.column_threshold_var, width=8)
        threshold_entry.grid(row=0, column=7, padx=5)
        
        # Add/Remove buttons
        add_pair_btn = ctk.CTkButton(
            controls_frame,
            text="Add Column Pair",
            command=self.add_column_pair,
            height=25,
            font=("", 10)
        )
        add_pair_btn.grid(row=0, column=8, padx=5)
        
        remove_pair_btn = ctk.CTkButton(
            controls_frame,
            text="Remove Selected",
            command=self.remove_column_pair,
            height=25,
            font=("", 10)
        )
        remove_pair_btn.grid(row=0, column=9, padx=5)
        
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(3, weight=1)
        
        # Run matching button
        run_btn = ctk.CTkButton(
            tab,
            text="Run Matching",
            command=self.run_matching,
            height=25,
            font=("", 10)
        )
        run_btn.pack(pady=10)
        
        return tab
        

    
    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Configuration", command=self.load_configuration)
        file_menu.add_command(label="Save Configuration", command=self.save_configuration)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def browse_file(self, string_var):
        """Open file browser dialog and update path variable."""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            string_var.set(file_path)
            
            # Update matching columns if source or reference file changed
            if string_var in (self.source_path_var, self.ref_path_var):
                self.update_matching_columns()

    def update_matching_columns(self):
        """Update available columns for matching when files are loaded."""
        try:
            # Get columns from source file
            if self.source_path_var.get():
                source_df = FileHandler.read_file(self.source_path_var.get())
                source_columns = sorted(source_df.columns.tolist())
                self.source_column_combo['values'] = source_columns
            
            # Get columns from reference file
            if self.ref_path_var.get():
                ref_df = FileHandler.read_file(self.ref_path_var.get())
                ref_columns = sorted(ref_df.columns.tolist())
                self.ref_column_combo['values'] = ref_columns
        except Exception as e:
            messagebox.showerror("Error", f"Error loading columns: {str(e)}")
            
    def add_column_pair(self):
        """Add a column pair to the matching columns tree."""
        try:
            source_col = self.source_column_var.get()
            ref_col = self.ref_column_var.get()
            if not source_col or not ref_col:
                raise ValueError("Please select both source and reference columns")
            
            # Get the weight value
            weight = float(self.column_weight_var.get())
            if weight <= 0:
                raise ValueError("Weight must be greater than 0")
                
            # Get the threshold value
            threshold = float(self.column_threshold_var.get())
            if threshold < 0 or threshold > 100:
                raise ValueError("Threshold must be between 0 and 100")

            # Check if either column is already paired
            for item in self.column_pairs_tree.get_children():
                values = self.column_pairs_tree.item(item)['values']
                if values[0] == source_col or values[1] == ref_col:
                    self.column_pairs_tree.delete(item)
                    break
            
            # Add new pair with the specified weight and threshold
            self.column_pairs_tree.insert('', 'end', values=(source_col, ref_col, weight, threshold))
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def remove_column_pair(self):
        """Remove selected column pair from the tree."""
        selected = self.column_pairs_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a column pair to remove")
            return
            
        for item in selected:
            self.column_pairs_tree.delete(item)
    
    def save_configuration(self):
        """Save current configuration to file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                config_data = {
                    'matching': {
                        'algorithm': self.algorithm_var.get(),
                        'threshold': self.threshold_var.get(),
                        'max_matches': self.max_matches_var.get()
                    }
                }
                self.config.update_config(config_data)
                self.config.save_config(file_path)
                messagebox.showinfo("Success", "Configuration saved successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_configuration(self):
        """Load configuration from file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            try:
                self.config.load_config(file_path)
                config_data = self.config.get_matching_config()
                
                self.algorithm_var.set(config_data['algorithm'])
                self.threshold_var.set(config_data['threshold'])
                self.max_matches_var.set(config_data['max_matches'])
                
                messagebox.showinfo("Success", "Configuration loaded successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def run_matching(self):
        """Execute the fuzzy matching process."""
        try:
            # Validate inputs
            if not self.source_path_var.get() or not self.ref_path_var.get():
                raise ValueError("Please select both source and reference files")
            
            # Read input files
            self.source_df = FileHandler.read_file(self.source_path_var.get())
            self.reference_df = FileHandler.read_file(self.ref_path_var.get())
            
            # Get column pairs for matching
            column_pairs = []
            source_columns = []
            ref_columns = []
            pair_thresholds = {}  # Dictionary to store thresholds for each column pair
            
            for item in self.column_pairs_tree.get_children():
                values = self.column_pairs_tree.item(item)['values']
                source_col = values[0]
                ref_col = values[1]
                weight = float(values[2])
                threshold = float(values[3])
                column_pairs.append((source_col, ref_col, weight))
                source_columns.append(source_col)
                ref_columns.append(ref_col)
                pair_thresholds[(source_col, ref_col)] = threshold
            
            if not column_pairs:
                raise ValueError("Please add at least one column pair for matching")
            
            # Initialize matcher
            self.matcher = FuzzyMatcher(
                algorithm=self.algorithm_var.get(),
                threshold=self.threshold_var.get(),
                max_matches=self.max_matches_var.get()
            )
            
            # If using weighted algorithm, set the weights
            if self.algorithm_var.get() == 'weighted':
                self.matcher.algorithm_weights = {
                    algo: self.weight_vars[algo].get()
                    for algo in ['levenshtein', 'jaro_winkler', 'jaccard', 'cosine', 'soundex']
                    if algo in self.weight_vars
                }

            # Create temporary copies of dataframes
            source_df_temp = self.source_df.copy()
            ref_df_temp = self.reference_df.copy()
            
            # Process data
            preprocessor = DataPreprocessor()
            source_df_temp = preprocessor.prepare_dataframe(source_df_temp, source_columns)
            ref_df_temp = preprocessor.prepare_dataframe(ref_df_temp, ref_columns)
            
            # Run matching
            results = []
            
            # Get global threshold
            global_threshold = self.threshold_var.get()
            
            # Create source record lookup for faster access
            source_records = source_df_temp.to_dict('index')
            ref_records = ref_df_temp.to_dict('index')
            
            # Perform matching
            for idx in source_records:
                source_record = source_records[idx]
                record_matches = []
                
                for ref_idx in ref_records:
                    ref_record = ref_records[ref_idx]
                    total_score = 0
                    total_weight = 0
                    
                    # Calculate weighted score for each column pair
                    pair_scores = {}
                    total_weighted_threshold = 0
                    
                    for source_col, ref_col, weight in column_pairs:
                        source_val = str(source_record[source_col])
                        ref_val = str(ref_record[ref_col])
                        
                        # Calculate similarity for this column pair
                        pair_score = self.matcher._calculate_similarity(source_val, ref_val)
                        pair_scores[(source_col, ref_col)] = pair_score
                        
                        # Each pair must meet its own exact threshold
                        pair_threshold = pair_thresholds[(source_col, ref_col)]
                        if pair_score >= pair_threshold:  # Exact threshold match required
                            total_score += pair_score * weight
                            total_weight += weight
                    
                    # All pairs must meet their individual thresholds
                    all_thresholds_met = True
                    for (source_col, ref_col) in pair_scores:
                        if pair_scores[(source_col, ref_col)] < pair_thresholds[(source_col, ref_col)]:
                            all_thresholds_met = False
                            break

                    # Calculate final score only if all thresholds are met
                    if total_weight > 0 and all_thresholds_met:
                        final_score = total_score / total_weight
                        # Store the match with individual scores
                        record_matches.append({
                            'ref_idx': ref_idx,
                            'final_score': final_score,
                            'pair_scores': pair_scores
                        })
                
                # Sort matches by score and take top N
                record_matches.sort(key=lambda x: x['final_score'], reverse=True)
                top_matches = record_matches[:self.max_matches_var.get()]
                
                # Add matches to results
                for match in top_matches:
                    # Start with match metadata and pair-specific scores
                    ref_idx = match['ref_idx']
                    match_data = {
                        'Overall_Match_Score': match['final_score'],
                        'Source_Row': idx,
                        'Reference_Row': ref_idx
                    }
                    
                    # Add individual column pair scores
                    for source_col, ref_col, weight in column_pairs:
                        source_val = str(source_records[idx][source_col])
                        ref_val = str(ref_records[ref_idx][ref_col])
                        pair_score = self.matcher._calculate_similarity(source_val, ref_val)
                        match_data[f'Score_{source_col}_vs_{ref_col}'] = pair_score
                    
                    # Add all source columns with their original values
                    original_source = self.source_df.iloc[idx]
                    for col in self.source_df.columns:
                        match_data[f'Source_{col}'] = original_source[col]
                    
                    # Add all reference columns with their original values
                    original_ref = self.reference_df.iloc[ref_idx]
                    for col in self.reference_df.columns:
                        match_data[f'Reference_{col}'] = original_ref[col]
                    
                    results.append(match_data)
            
            # Create DataFrame with all results
            if not results:
                messagebox.showinfo("No Matches", "No matches found that meet all threshold criteria.")
                return
                
            results_df = pd.DataFrame(results)
            
            # Reorder columns for better readability
            metadata_cols = ['Overall_Match_Score', 'Source_Row', 'Reference_Row']
            score_cols = [col for col in results_df.columns if col.startswith('Score_')]
            source_cols = [col for col in results_df.columns if col.startswith('Source_')]
            ref_cols = [col for col in results_df.columns if col.startswith('Reference_')]
            
            results_df = results_df[metadata_cols + score_cols + source_cols + ref_cols]
            
            # Store results for geo refinement
            self.last_results_df = results_df
            
            # Update geo tab columns
            self.source_addr_combo['values'] = [col.replace('Source_', '') for col in source_cols]
            self.ref_addr_combo['values'] = [col.replace('Reference_', '') for col in ref_cols]
            
            # Save results
            output_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("CSV files", "*.csv")
                ]
            )
            
            if output_path:
                # Sort by overall match score in descending order
                results_df = results_df.sort_values('Overall_Match_Score', ascending=False)
                
                # Save to Excel with proper formatting
                if output_path.endswith('.xlsx'):
                    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                        results_df.to_excel(writer, index=False, sheet_name='Matches')
                        # Auto-adjust columns width
                        worksheet = writer.sheets['Matches']
                        for idx, col in enumerate(results_df.columns):
                            max_length = max(
                                results_df[col].astype(str).apply(len).max(),
                                len(col)
                            ) + 2
                            worksheet.column_dimensions[chr(65 + idx)].width = max_length
                else:
                    results_df.to_csv(output_path, index=False)
                
                messagebox.showinfo("Success", 
                    f"Matching completed successfully.\n\n"
                    f"Total matches found: {len(results_df)}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def create_geo_tab(self):
        """Create the geo level refinement tab."""
        tab = ttk.Frame(self.notebook)
        
        # Column selection frame
        cols_frame = ttk.LabelFrame(tab, text="Address Column Selection", padding=10)
        cols_frame.pack(fill='x', padx=5, pady=5)
        
        # Source address column
        ttk.Label(cols_frame, text="Source Address Column:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.source_addr_var = tk.StringVar()
        self.source_addr_combo = ttk.Combobox(cols_frame, textvariable=self.source_addr_var)
        self.source_addr_combo.grid(row=0, column=1, sticky='ew', padx=5)
        
        # Reference address column
        ttk.Label(cols_frame, text="Reference Address Column:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.ref_addr_var = tk.StringVar()
        self.ref_addr_combo = ttk.Combobox(cols_frame, textvariable=self.ref_addr_var)
        self.ref_addr_combo.grid(row=1, column=1, sticky='ew', padx=5)
        
        # Distance threshold
        ttk.Label(cols_frame, text="Maximum Distance (miles):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.distance_threshold_var = tk.StringVar(value="10")
        distance_entry = ttk.Entry(cols_frame, textvariable=self.distance_threshold_var, width=10)
        distance_entry.grid(row=2, column=1, sticky='w', padx=5)
        
        cols_frame.columnconfigure(1, weight=1)
        
        # Info label
        ttk.Label(
            tab, 
            text="Note: This will filter the fuzzy matching results based on the driving distance\n"
                 "between locations. Only matches within the specified distance will be kept.",
            wraplength=600
        ).pack(pady=10)
        
        # Process button
        process_btn = ctk.CTkButton(
            tab,
            text="Apply Geo Refinement",
            command=self.process_geo_refinement,
            height=25,
            font=("", 10)
        )
        process_btn.pack(pady=10)
        
        return tab
        
    def process_geo_refinement(self):
        """Process the fuzzy matches with geo distance refinement."""
        try:
            # Get the last fuzzy matching results
            if not hasattr(self, 'last_results_df'):
                raise ValueError("Please run fuzzy matching first before applying geo refinement.")
                
            source_col = self.source_addr_var.get()
            ref_col = self.ref_addr_var.get()
            max_distance = float(self.distance_threshold_var.get())
            
            if not source_col or not ref_col:
                raise ValueError("Please select both source and reference address columns.")
                
            # Add distance calculations
            results = []
            total_rows = len(self.last_results_df)
            
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Calculating Distances")
            progress_window.geometry("300x150")
            
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(
                progress_window, 
                variable=progress_var, 
                maximum=total_rows
            )
            progress_bar.pack(padx=10, pady=20, fill='x')
            
            status_label = ttk.Label(progress_window, text="Processing...")
            status_label.pack(pady=10)
            
            for idx, row in self.last_results_df.iterrows():
                source_addr = str(row[f"Source_{source_col}"])
                ref_addr = str(row[f"Reference_{ref_col}"])
                
                # Calculate distance
                travel_info = self.get_travel_info(source_addr, ref_addr)
                
                # Update progress
                progress_var.set(idx + 1)
                status_label.config(text=f"Processing row {idx + 1} of {total_rows}")
                progress_window.update()
                
                # Add distance info to results
                row_dict = row.to_dict()
                row_dict['Driving_Distance_Miles'] = travel_info.get('driving_distance_miles', None)
                row_dict['Straight_Line_Miles'] = travel_info.get('straight_line_miles', None)
                row_dict['Distance_Error'] = travel_info.get('error', None)
                
                # Only include rows within distance threshold
                if (travel_info.get('driving_distance_miles') is not None and 
                    travel_info['driving_distance_miles'] <= max_distance):
                    results.append(row_dict)
                
            progress_window.destroy()
            
            if not results:
                messagebox.showinfo("No Results", 
                    "No matches found within the specified distance threshold.")
                return
                
            # Create new DataFrame with distance information
            results_df = pd.DataFrame(results)
            
            # Save results
            output_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("CSV files", "*.csv")
                ]
            )
            
            if output_path:
                if output_path.endswith('.xlsx'):
                    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                        results_df.to_excel(writer, index=False, sheet_name='Matches')
                        worksheet = writer.sheets['Matches']
                        for idx, col in enumerate(results_df.columns):
                            max_length = max(
                                results_df[col].astype(str).apply(len).max(),
                                len(col)
                            ) + 2
                            worksheet.column_dimensions[chr(65 + idx)].width = max_length
                else:
                    results_df.to_csv(output_path, index=False)
                
                messagebox.showinfo("Success", 
                    f"Geo refinement completed successfully.\n\n"
                    f"Total matches within {max_distance} miles: {len(results_df)}")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Fuzzy Match Tool\n\n"
            "A configurable tool for fuzzy matching across datasets.\n\n"
            "Version 1.0"
        )
    
    def create_algorithm_weights_tab(self):
        """Create the algorithm weights configuration tab."""
        tab = ttk.Frame(self.notebook)
        
        # Description frame
        desc_frame = ttk.LabelFrame(tab, text="Algorithm Descriptions", padding=10)
        desc_frame.pack(fill='x', padx=5, pady=5)
        
        descriptions = {
            'levenshtein': 'Best for comparing strings with typos and spelling mistakes',
            'jaro_winkler': 'Best for comparing person names and short strings',
            'jaccard': 'Best for comparing strings where word order doesn\'t matter',
            'cosine': 'Best for comparing longer text strings',
            'soundex': 'Best for matching strings that sound similar'
        }
        
        for algo, desc in descriptions.items():
            ttk.Label(
                desc_frame,
                text=f"{algo.title()}: {desc}",
                wraplength=600
            ).pack(anchor='w', pady=2)
        
        # Weights frame
        weights_frame = ttk.LabelFrame(tab, text="Algorithm Weights", padding=10)
        weights_frame.pack(fill='x', padx=5, pady=5)
        
        self.weight_vars = {}
        
        for algo in self.algorithm_weights.keys():
            frame = ttk.Frame(weights_frame)
            frame.pack(fill='x', pady=2)
            
            ttk.Label(frame, text=algo.title() + ":", width=15).pack(side='left')
            
            var = tk.DoubleVar(value=self.algorithm_weights[algo])
            self.weight_vars[algo] = var
            
            scale = ttk.Scale(
                frame,
                from_=0,
                to=5,
                variable=var,
                orient='horizontal'
            )
            scale.pack(side='left', fill='x', expand=True, padx=5)
            
            ttk.Label(frame, textvariable=var, width=5).pack(side='left')
        
        # Info label
        ttk.Label(
            tab,
            text="Adjust the weights to control how much each algorithm influences the final similarity score.\n"
                 "0 = algorithm not used, 1 = normal weight, >1 = increased importance",
            wraplength=600
        ).pack(pady=10)
        
        return tab

    def get_algorithm_weights(self) -> Dict[str, float]:
        """Get the current algorithm weights from the UI."""
        return {
            algo: self.weight_vars[algo].get()
            for algo in self.algorithm_weights.keys()
            if algo in self.weight_vars
        }

    def run(self):
        """Start the application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = FuzzyMatchApp()
    app.run()
