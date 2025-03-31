# Excel Analyzer  
This project uses **Owl** for data analysis and visualization.

## Features

- Provides both English and Chinese versions of the raw data and prompts
- Utilizes **CodeExecutionToolkit**, **ExcelToolkit**, and **FileWriteToolkit** to complete related tasks  
- Implements **ExcelRolePlaying** based on **OwlRolePlaying**, which overrides the `system_prompt` with a cleaner, more focused version tailored for data analysis scenarios  

## How to Use  
1. Set up the environment according to Owl's official instructions
2. Run the following commands:  
    ```bash
    cd community_usecase/excel_analyzer

    # Chinese version
    python data_insights_deepseek_zh.py

    # English version
    python data_insights_gpt4o_zh.py
    ```
3. The analysis results will be saved in the current directory

## Demo Video

