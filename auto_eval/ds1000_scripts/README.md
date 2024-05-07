This directory contains the scripts used to evaluate the performance of the [DS-1000](https://ds1000-code-gen.github.io/) benchmark.

# How to?

1. Clone the [DS-1000](https://github.com/xlang-ai/DS-1000/tree/main) repository.
2. Extract the `ds1000.jsonl` file from the `ds1000.jsonl.gz` file in the `data` directory.
3. Run the `prepare_cases.py` script to generate the test cases.
   ```bash
   cd auto_eval/ds1000_scripts 
   python prepare_cases.py <path_to_the_jsonl_file> <output_directory>
   ```
    Each test case contains 5 files:
   - case.yaml: the test case file.
   - code_context.py: the evaluation code.
   - metadata.json: the metadata of the test case.
   - prompt.txt: the composed prompt of the test case.
   - reference_code.py: the ground truth code.
4. Copy the example files from `ds1000_scritps/planner_examples` to `project/planner_examples` directory; 
   and the example files from `ds1000_scritps/codeinterpreter_examples` to `project/codeinterpreter_examples` directory.
   Disable (or discard) the original example files from the project directory. See the notes below for understanding why.
5. Once the test cases are generated, follow the instructions in `auto_eval/README.md` to evaluate the performance of the benchmark.

An example of the test case prompt is shown below:
```markdown
The task is to complete the sample code described in the <TASK DESCRIPTION> block below.
Complete the code, run it successfully, and finally present the code back. 
Please "copy and paste" the following task description in your request to ensure 
that the task description is correct and complete.

<TASK DESCRIPTION>
# Problem
I have the following DataFrame:
    Col1  Col2  Col3  Type
0      1     2     3     1
1      4     5     6     1
2      7     8     9     2
3    10    11    12     2
4    13    14    15     3
5    16    17    18     3


The DataFrame is read from a CSV file. All rows which have Type 1 are on top, followed by the rows with Type 2, followed by the rows with Type 3, etc.
I would like to shuffle the order of the DataFrame's rows according to a list. \
For example, give a list [2, 4, 0, 3, 1, 5] and desired result should be:
    Col1  Col2  Col3  Type
2      7     8     9     2
4     13    14    15     3
0     1     2     3     1
3    10    11    12     2
1     4     5     6     1
5    16    17    18     3
...


How can I achieve this?


# Solution
The following is the solution code to the problem statement provided above.
You must complete the code by filling in the missing parts between `### SOLUTION START` and `### SOLUTION END`.
You must keep any code outside of `### SOLUTION START` and `### SOLUTION END` untouched.
Once you have completed the code, run it to check if your solution is correct.
Make sure you keep `### SOLUTION START` and `### SOLUTION END` along with your solution code.


import pandas as pd
import numpy as np


df = pd.DataFrame({'Col1': [1, 4, 7, 10, 13, 16],
                   'Col2': [2, 5, 8, 11, 14, 17],
                   'Col3': [3, 6, 9, 12, 15, 18],
                   'Type': [1, 1, 2, 2, 3, 3]})
List = np.random.permutation(len(df))
### SOLUTION START
result = ... # put solution in this variable
### SOLUTION END

</TASK DESCRIPTION>
```

# Notes

The original DS-1000 benchmark is designed for evaluating the performance of code generation capabilities of a LLM. 
There are 2 types of test cases in the original benchmark: `insertion` and `completion`.
The `insertion` test cases are designed to evaluate the performance of the model in inserting code snippets at specific locations in the code.
The `completion` test cases are designed to evaluate the performance of the model in completing the code snippets.

To make it easier to evaluate the performance of an agent, instead of the LLM model itself, we have transformed the test cases.
First of all, we have transformed all the test cases into `insertion` test cases.
Secondly, we have changed the task to be filling the blanks in the code snippets, running the code, and report the completed code back.
Because we need to run the code, we have filtered out a subset of tests cases where the given sample code is not able to run.
Specifically, we ignore all the test cases with `problem_id` greater than 817, because most cases in this subset 
contain code snippets that are not able to run. The remaining 816 test cases are used to evaluate the performance of the agent.

The transformation actually makes it more challenging, especially for the `completion` cases.
Relatively small LLM models may not follow the instructions correctly, leading to issues such as changing the given sample code. 
That is why we have added examples for both the planner and codeinterpreter tasks as described in step 4 above.
The main reason is to teach the agent on how to format the output code correctly, in order for extracting
the solution code from the output code to be easier. 

During the evaluation, we are aware that some test cases may not be perfect for evaluating the performance of an agent, 
especially if the output is a DataFrame. This is because comparing the equality of two DataFrames is a bit tricky, although the test cases use the `assert_frame_equal` function from the `pandas.testing` module, and the authors 
had been very careful in designing the test cases. 
For example, the output DataFrame of the agent may have different index (due to an optional `reset_index` operation) or column data types than the expected DataFrame.
When you consider solving a real problem, these flaws may not be a big issue, because you can always convert the output DataFrame 
to the expected DataFrame format. However, for a test case, we only have binary results: pass or fail.

We have noticed that some test cases need manual intervention to continue running the batch evaluation.
The main reason is that the evaluation code contains plotting functions, which block the execution of the code.
