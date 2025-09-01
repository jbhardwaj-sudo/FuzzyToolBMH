import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from typing import Dict, Any
import os
import json

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
        self.comparison_tab = self.create_comparison_tab()
        
        # Add tabs to notebook
        self.notebook.add(self.config_tab, text="Configuration")
        self.notebook.add(self.matching_tab, text="Matching")
        self.notebook.add(self.comparison_tab, text="List Comparison")
        
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
    def create_config_tab(self):
        """Create the configuration tab."""
        tab = ttk.Frame(self.notebook)
        
        # Algorithm selection
        algo_frame = ttk.LabelFrame(tab, text="Matching Algorithm & Weights", padding=10)
        algo_frame.pack(fill='x', padx=5, pady=5)

        # Core algorithms with descriptions
        core_algorithms = [
            ('Levenshtein Distance', 'levenshtein', 'Best for typos and spelling mistakes'),
            ('Jaro-Winkler', 'jaro_winkler', 'Best for person names and brands'),
            ('Jaccard Similarity', 'jaccard', 'Best for addresses and word overlap'),
            ('Cosine Similarity', 'cosine', 'Best for long text and context'),
            ('Soundex', 'soundex', 'Best for phonetic/sound-alike matches')
        ]

        # Create weight sliders for each algorithm
        self.weight_vars = {}
        
        for name, algo_id, desc in core_algorithms:
            # Create frame for each algorithm
            frame = ttk.Frame(algo_frame)
            frame.pack(fill='x', pady=2)
            
            # Algorithm name and description
            label_frame = ttk.Frame(frame)
            label_frame.pack(side='left', padx=5)
            
            ttk.Label(label_frame, text=name, font=('', 9, 'bold')).pack(anchor='w')
            ttk.Label(label_frame, text=desc, font=('', 8)).pack(anchor='w')
            
            # Weight slider
            weight_frame = ttk.Frame(frame)
            weight_frame.pack(side='right', padx=5, fill='x', expand=True)
            
            ttk.Label(weight_frame, text="Weight:").pack(side='left')
            
            var = tk.DoubleVar(value=1.0)
            self.weight_vars[algo_id] = var
            
            scale = ttk.Scale(
                weight_frame,
                from_=0,
                to=5,
                variable=var,
                orient='horizontal'
            )
            scale.pack(side='left', fill='x', expand=True, padx=5)
            
            # Weight value label
            ttk.Label(weight_frame, textvariable=var, width=4).pack(side='left')
            
            ttk.Separator(algo_frame, orient='horizontal').pack(fill='x', pady=5)

        # Info label for weights
        ttk.Label(
            algo_frame,
            text="Adjust weights to control how each algorithm influences matching:\n"
                 "0 = not used, 1 = normal weight, >1 = increased importance",
            wraplength=500,
            font=('', 8)
        ).pack(pady=5)
            
        # Threshold setting
        thresh_frame = ttk.LabelFrame(tab, text="Matching Threshold", padding=10)
        thresh_frame.pack(fill='x', padx=5, pady=5)
        
        self.threshold_var = tk.DoubleVar(value=80)
        threshold_scale = ttk.Scale(
            thresh_frame,
            from_=0,
            to=100,
            variable=self.threshold_var,
            orient='horizontal'
        )
        threshold_scale.pack(fill='x')
        
        # Max matches setting
        matches_frame = ttk.LabelFrame(tab, text="Maximum Matches", padding=10)
        matches_frame.pack(fill='x', padx=5, pady=5)
        
        self.max_matches_var = tk.IntVar(value=5)
        max_matches_entry = ttk.Entry(
            matches_frame,
            textvariable=self.max_matches_var
        )
        max_matches_entry.pack(fill='x')
        
        # Save configuration button
        save_btn = ctk.CTkButton(
            tab,
            text="Save Configuration",
            command=self.save_configuration
        )
        save_btn.pack(pady=10)
        
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
            command=lambda: self.browse_file(self.source_path_var)
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
            command=lambda: self.browse_file(self.ref_path_var)
        ).grid(row=1, column=2)
        
        file_frame.columnconfigure(1, weight=1)
        
        # Column weights
        weights_frame = ttk.LabelFrame(tab, text="Column Weights", padding=10)
        weights_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Add weight controls
        weight_controls = ttk.Frame(weights_frame)
        weight_controls.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(weight_controls, text="Column:").grid(row=0, column=0, padx=5)
        self.column_var = tk.StringVar()
        self.column_combo = ttk.Combobox(weight_controls, textvariable=self.column_var)
        self.column_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(weight_controls, text="Weight:").grid(row=0, column=2, padx=5)
        self.weight_var = tk.StringVar(value="1.0")
        weight_entry = ttk.Entry(weight_controls, textvariable=self.weight_var, width=10)
        weight_entry.grid(row=0, column=3, padx=5)
        
        add_btn = ctk.CTkButton(
            weight_controls,
            text="Add Weight",
            command=self.add_weight
        )
        add_btn.grid(row=0, column=4, padx=5)
        
        remove_btn = ctk.CTkButton(
            weight_controls,
            text="Remove Selected",
            command=self.remove_weight
        )
        remove_btn.grid(row=0, column=5, padx=5)
        
        # Weight list
        self.weights_tree = ttk.Treeview(
            weights_frame,
            columns=('Column', 'Weight'),
            show='headings',
            height=6
        )
        self.weights_tree.heading('Column', text='Column')
        self.weights_tree.heading('Weight', text='Weight')
        self.weights_tree.pack(fill='both', expand=True, pady=5)
        
        # Run matching button
        run_btn = ctk.CTkButton(
            tab,
            text="Run Matching",
            command=self.run_matching
        )
        run_btn.pack(pady=10)
        
        return tab
        
    def create_comparison_tab(self):
        """Create the list comparison tab."""
        tab = ttk.Frame(self.notebook)
        
        # File selection
        file_frame = ttk.LabelFrame(tab, text="Input File", padding=10)
        file_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky='w')
        self.comp_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.comp_file_var).grid(
            row=0, column=1, padx=5, sticky='ew'
        )
        ctk.CTkButton(
            file_frame,
            text="Browse",
            command=lambda: self.browse_file(self.comp_file_var)
        ).grid(row=0, column=2)
        
        file_frame.columnconfigure(1, weight=1)
        
        # Column selection
        cols_frame = ttk.LabelFrame(tab, text="Column Selection", padding=10)
        cols_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(cols_frame, text="List 1 Column:").grid(row=0, column=0, sticky='w')
        self.list1_col_var = tk.StringVar()
        self.list1_combo = ttk.Combobox(cols_frame, textvariable=self.list1_col_var)
        self.list1_combo.grid(row=0, column=1, padx=5, sticky='ew')
        
        ttk.Label(cols_frame, text="List 2 Column:").grid(row=1, column=0, sticky='w')
        self.list2_col_var = tk.StringVar()
        self.list2_combo = ttk.Combobox(cols_frame, textvariable=self.list2_col_var)
        self.list2_combo.grid(row=1, column=1, padx=5, sticky='ew')
        
        cols_frame.columnconfigure(1, weight=1)
        
        # Results display
        results_frame = ttk.LabelFrame(tab, text="Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=('String1', 'String2', 'Score'),
            show='headings'
        )
        self.results_tree.heading('String1', text='String 1')
        self.results_tree.heading('String2', text='String 2')
        self.results_tree.heading('Score', text='Score')
        self.results_tree.pack(fill='both', expand=True)
        
        # Compare button
        compare_btn = ctk.CTkButton(
            tab,
            text="Compare Lists",
            command=self.compare_lists
        )
        compare_btn.pack(pady=10)
        
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
            
            # If this is the comparison tab file, update column combos
            if string_var == self.comp_file_var:
                self.update_column_combos()
            # If this is source or reference file, update matching columns
            elif string_var in (self.source_path_var, self.ref_path_var):
                self.update_matching_columns()

    def update_matching_columns(self):
        """Update available columns for matching when files are loaded."""
        try:
            columns = set()
            
            # Get columns from source file
            if self.source_path_var.get():
                source_df = FileHandler.read_file(self.source_path_var.get())
                columns.update(source_df.columns)
            
            # Get columns from reference file
            if self.ref_path_var.get():
                ref_df = FileHandler.read_file(self.ref_path_var.get())
                columns.update(ref_df.columns)
            
            # Update column combo
            if columns:
                self.column_combo['values'] = sorted(list(columns))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading columns: {str(e)}")
            
    def add_weight(self):
        """Add a column weight to the weights tree."""
        try:
            column = self.column_var.get()
            weight = float(self.weight_var.get())
            
            if not column:
                raise ValueError("Please select a column")
            
            if weight <= 0:
                raise ValueError("Weight must be greater than 0")
            
            # Check if column already has a weight
            for item in self.weights_tree.get_children():
                if self.weights_tree.item(item)['values'][0] == column:
                    self.weights_tree.delete(item)
                    break
            
            # Add new weight
            self.weights_tree.insert('', 'end', values=(column, weight))
            
            # Clear entry
            self.weight_var.set("1.0")
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            
    def remove_weight(self):
        """Remove selected weight from the weights tree."""
        selected = self.weights_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a weight to remove")
            return
            
        for item in selected:
            self.weights_tree.delete(item)
    
    def update_column_combos(self):
        """Update column selection combos in comparison tab."""
        try:
            df = FileHandler.read_file(self.comp_file_var.get())
            columns = df.columns.tolist()
            
            self.list1_combo['values'] = columns
            self.list2_combo['values'] = columns
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
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
            
            # Get weights from treeview
            weights = {}
            for item in self.weights_tree.get_children():
                values = self.weights_tree.item(item)['values']
                weights[values[0]] = float(values[1])
            
            if not weights:
                raise ValueError("Please set column weights")
            
            # Initialize matcher with algorithm weights
            self.matcher = FuzzyMatcher(
                algorithm=self.algorithm_var.get(),
                threshold=self.threshold_var.get(),
                max_matches=self.max_matches_var.get()
            )
            
            # Get algorithm weights if using weighted approach
            if self.algorithm_var.get() == 'weighted':
                algorithm_weights = self.get_algorithm_weights()
            
            # Process data
            preprocessor = DataPreprocessor()
            self.source_df = preprocessor.prepare_dataframe(
                self.source_df,
                list(weights.keys())
            )
            self.reference_df = preprocessor.prepare_dataframe(
                self.reference_df,
                list(weights.keys())
            )
            
            # Run matching
            results_df = self.matcher.find_matches(
                self.source_df,
                self.reference_df,
                weights
            )
            
            # Save results
            output_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("CSV files", "*.csv")
                ]
            )
            
            if output_path:
                FileHandler.save_results(
                    results_df,
                    output_path,
                    include_scores=True
                )
                messagebox.showinfo("Success", "Matching completed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def compare_lists(self):
        """Execute the list comparison process."""
        try:
            # Validate inputs
            if not self.comp_file_var.get():
                raise ValueError("Please select input file")
            
            if not self.list1_col_var.get() or not self.list2_col_var.get():
                raise ValueError("Please select both columns")
            
            # Read lists
            list1, list2 = FileHandler.read_lists(
                self.comp_file_var.get(),
                self.list1_col_var.get(),
                self.list2_col_var.get()
            )
            
            # Initialize matcher
            matcher = FuzzyMatcher(
                algorithm=self.algorithm_var.get(),
                threshold=0  # No threshold for direct comparison
            )
            
            # Compare lists
            results_df = matcher.compare_lists(list1, list2)
            
            # Update results display
            self.results_tree.delete(*self.results_tree.get_children())
            for _, row in results_df.iterrows():
                self.results_tree.insert('', 'end', values=(
                    row['string1'],
                    row['string2'],
                    f"{row['score']:.2f}"
                ))
            
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
        from ..core.algorithm_weights import AlgorithmWeights
        
        tab = ttk.Frame(self.notebook)
        self.algorithm_weights = AlgorithmWeights()
        
        # Description frame
        desc_frame = ttk.LabelFrame(tab, text="Algorithm Descriptions", padding=10)
        desc_frame.pack(fill='x', padx=5, pady=5)
        
        for algo, desc in self.algorithm_weights.descriptions.items():
            ttk.Label(
                desc_frame,
                text=f"{algo.title()}: {desc}",
                wraplength=600
            ).pack(anchor='w', pady=2)
        
        # Weights frame
        weights_frame = ttk.LabelFrame(tab, text="Algorithm Weights", padding=10)
        weights_frame.pack(fill='x', padx=5, pady=5)
        
        self.weight_vars = {}
        
        for algo in self.algorithm_weights.algorithms:
            frame = ttk.Frame(weights_frame)
            frame.pack(fill='x', pady=2)
            
            ttk.Label(frame, text=algo.title() + ":", width=15).pack(side='left')
            
            var = tk.DoubleVar(value=1.0)
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
            for algo in self.algorithm_weights.algorithms
        }

    def run(self):
        """Start the application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = FuzzyMatchApp()
    app.run()
