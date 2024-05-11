This directory contains the scripts used to evaluate the performance of the [DA-Bench](https://github.com/InfiAgent/InfiAgent/tree/main/examples/DA-Agent) benchmark.

# How to?
1. Clone the [DA-Bench](https://github.com/InfiAgent/InfiAgent.git) repository.
2. Run the `prepare_cases.py` script to generate the test cases.
   ```bash
   cd auto_eval/dabench_scripts 
   python prepare_cases.py <path_to_the_jsonl_questions_file> <path_to_thejsonl_label_file> <path_to_the_data_folder> <output_directory>
   ```
    Each test case contain the `case.yaml` file and optionally the required data files.
3. Once the test cases are generated, follow the instructions in `auto_eval/README.md` to evaluate the performance of the benchmark.

An example of the test case prompt is shown below:
```markdown
# Task
Load the file test_ave.csv and answer the following questions.

# Question
Calculate the mean fare paid by the passengers.

   
# Constraints
Calculate the mean fare using Python's built-in statistics
module or appropriate statistical method in pandas. Rounding off the answer to
two decimal places.

# Format
@mean_fare[mean_fare_value] where "mean_fare_value" is a floating-point number rounded to two decimal places.
```

