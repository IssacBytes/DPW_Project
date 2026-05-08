import pandas as pd

# 1. 读取已经清洗好的数据
df = pd.read_csv("compact_cleaned.csv")

print("="*50)
print("✅ Preparation Before Data Analysis")
print("="*50)

# 2. 查看数据大小（行、列）
print("\n【1】Data Scale")
print(f"Total Rows：{df.shape[0]}")
print(f"Total Columns：{df.shape[1]}")

# 3. 查看每一列的名字和类型
print("\n【2】Column Name & Data Type of Each Column")
print(df.dtypes)

# 4. 检查缺失值（最重要！）
print("\n【3】Number of missing values")
print(df.isnull().sum())

# 5. 查看前5行数据样子
print("\n【4】First 5 rows of data")
print(df.head())

# 6. 输出所有列的中文说明（给队友看）
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