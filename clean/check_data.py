import pandas as pd

# 1. Load cleaned data
df = pd.read_csv("compact_cleaned.csv")

print("="*50)
print("✅ Preparation Before Data Analysis")
print("="*50)

# 2. Check data size (rows, columns)
print("\n[1] Data Scale")
print(f"Total Rows: {df.shape[0]}")
print(f"Total Columns: {df.shape[1]}")

# 3. Check column names and data types
print("\n[2] Column Name & Data Type of Each Column")
print(df.dtypes)

# 4. Check for missing values (most important!)
print("\n[3] Number of missing values")
print(df.isnull().sum())

# 5. Preview first 5 rows
print("\n[4] First 5 rows of data")
print(df.head())

# 6. Print description of all fields
print("\n" + "="*50)
print("📊 Description of All Fields")
print("="*50)

columns_info = """
country        
code          
continent      
date           
population     
total_cases    
new_cases      
new_cases_smoothed 
total_deaths   
new_deaths    
total_tests    
new_tests      
total_vaccinations 
new_vaccinations   
people_vaccinated  
people_fully_vaccinated 
stringency_index   
reproduction_rate  
"""

print(columns_info)
