import pandas as pd
import numpy as np

# Create source data
source_data = {
    'company_name': [
        'Microsoft Corporation',
        'Apple Inc',
        'Google LLC',
        'Amazon.com Inc',
        'Meta Platforms Inc'
    ],
    'address': [
        'One Microsoft Way, Redmond, WA',
        '1 Apple Park Way, Cupertino, CA',
        '1600 Amphitheatre Parkway, Mountain View, CA',
        '410 Terry Ave N, Seattle, WA',
        '1 Hacker Way, Menlo Park, CA'
    ],
    'contact_person': [
        'John Smith',
        'Sarah Johnson',
        'Mike Williams',
        'Emily Brown',
        'David Wilson'
    ]
}

# Create reference data with slight variations
reference_data = {
    'company_name': [
        'Microsoft Corp.',
        'Apple Corporation',
        'Google Limited',
        'Amazon Inc.',
        'Meta Platforms',
        'Tesla Motors',
        'IBM Corporation'
    ],
    'address': [
        'One Microsoft Way Redmond Washington',
        '1 Apple Park Way Cupertino California',
        '1600 Amphitheatre Pkwy Mountain View CA',
        '410 Terry Avenue North Seattle WA',
        '1 Hacker Way Menlo Park California',
        '3500 Deer Creek Rd, Palo Alto, CA',
        '1 New Orchard Road, Armonk, NY'
    ],
    'contact_person': [
        'Jonathan Smith',
        'Sara Johnson',
        'Michael Williams',
        'Emma Brown',
        'Dave Wilson',
        'Elon Musk',
        'John Doe'
    ]
}

# Create DataFrames
source_df = pd.DataFrame(source_data)
reference_df = pd.DataFrame(reference_data)

# Save to Excel files
source_df.to_excel('data/sample_data/source_companies.xlsx', index=False)
reference_df.to_excel('data/sample_data/reference_companies.xlsx', index=False)

print("Sample data files created successfully!")
