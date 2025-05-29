import pandas as pd
import os

problem_period = pd.read_csv('/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Data/EPEX/Continuous_Orders-GB-20240126-20240127T044441000Z.csv', header = 1)
problem_period = problem_period[problem_period['Product'] == 'GB_Half_Hour_Power']
problem_period = problem_period[problem_period['DeliveryStart'] == '2024-01-26T08:30:00Z']
problem_period.to_csv('/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Data/EPEX/problem_period.csv', index=False)

os.system(f'open "/Users/josephcary/Library/CloudStorage/OneDrive-Nexus365/First Year/Data/EPEX/problem_period.csv"')
