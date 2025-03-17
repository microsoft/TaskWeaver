"use strict";(self.webpackChunkwebsite=self.webpackChunkwebsite||[]).push([[5312],{5774:(e,t,n)=>{n.r(t),n.d(t,{assets:()=>l,contentTitle:()=>s,default:()=>h,frontMatter:()=>a,metadata:()=>i,toc:()=>c});var o=n(4848),r=n(8453);const a={title:"What makes a good agent reasoning framework?",authors:"liqli",date:new Date("2025-01-20T00:00:00.000Z")},s=void 0,i={permalink:"/TaskWeaver/blog/reasoning",editUrl:"https://github.com/microsoft/TaskWeaver/tree/main/website/blog/reasoning.md",source:"@site/blog/reasoning.md",title:"What makes a good agent reasoning framework?",description:"An agent can listen to the user's request, understand the context, make plans, take actions, observe the results, and respond to the user. Its behavior is driven by the reasoning process, which is the core of the agent's intelligence.",date:"2025-01-20T00:00:00.000Z",tags:[],readingTime:20.54,hasTruncateMarker:!0,authors:[{name:"Liqun Li",url:"https://liqul.github.io",title:"Principal Researcher",imageURL:"https://liqul.github.io/assets/logo_small_bw.png",key:"liqli",page:null}],frontMatter:{title:"What makes a good agent reasoning framework?",authors:"liqli",date:"2025-01-20T00:00:00.000Z"},unlisted:!1,prevItem:{title:"Vision input for the Planner",permalink:"/TaskWeaver/blog/vision"},nextItem:{title:"Experience Selection in TaskWeaver",permalink:"/TaskWeaver/blog/experience"}},l={authorsImageUrls:[void 0]},c=[];function d(e){const t={code:"code",p:"p",pre:"pre",strong:"strong",...(0,r.R)(),...e.components};return(0,o.jsxs)(o.Fragment,{children:[(0,o.jsx)(t.p,{children:"An agent can listen to the user's request, understand the context, make plans, take actions, observe the results, and respond to the user. Its behavior is driven by the reasoning process, which is the core of the agent's intelligence."}),"\n",(0,o.jsx)(t.p,{children:"There are many techniques developed to build an agent reasoning framework. For example, Chain-of-Thought (CoT) is one of the most popular reasoning approaches that uses a chain of thought to generate next-step actions. Another technique is ReAct, where the agent reflect on its action results to adjust its future actions. In TaskWeaver, one of the key reasoning technique is task decomposition and tracking, where the agent breaks down a task into subtasks and keeps track of the progress of each subtask. The following snippet shows an example of task decomposition and tracking in TaskWeaver:"}),"\n",(0,o.jsx)(t.pre,{children:(0,o.jsx)(t.code,{className:"language-commandline",children:"\u251c\u2500\u25ba [init_plan]\n\u2502   1. Request historical stock price data for MSFT from the user\n\u2502   2. Request the forecasting model or method to be used for prediction <interactively depends on 1>\n\u2502   3. Perform the prediction using the provided data and model <interactively depends on 2>\n\u2502   4. Report the prediction results to the user <interactively depends on 3>\n\u251c\u2500\u25ba [plan]\n\u2502   1. Request historical stock price data for MSFT from the user\n\u2502   2. Request the forecasting model or method to be used for prediction\n\u2502   3. Perform the prediction using the provided data and model\n\u2502   4. Report the prediction results to the user\n\u251c\u2500\u25ba [current_plan_step] 1. Request historical stock price data for MSFT from the user\n"})}),"\n",(0,o.jsx)(t.p,{children:"The agent lists the steps of the plan and the current step it is working on. While the agent is working on the task, it keeps track of the current step. This is useful especially when the task is complex and requires multiple steps to complete. The agent can refer to the current step to know what to do next. Without task decomposition and tracking, the agent may lose track of the task and fail to complete it."}),"\n",(0,o.jsx)(t.p,{children:"TaskWeaver also support ReAct-like reasoning. This is done by introducing multiple roles in the problem-solving process, especially the Planner and CodeInterpreter roles. The Planner role is responsible for planning the steps of the task, while the CodeInterpreter role is responsible for interpreting the code generated by the Planner. The Planner can reflect on the results of the CodeInterpreter and adjust the plan accordingly. In one round, the Planner and Code Interpreter can work together to complete a subtask with multiple interactions."}),"\n",(0,o.jsx)(t.p,{children:"However, there are still situations where the agent reasoning framework can be improved. If you have read the discussion above, you may have noticed that CoT is not implemented in TaskWeaver."}),"\n",(0,o.jsx)(t.p,{children:(0,o.jsx)(t.strong,{children:"Why?"})}),"\n",(0,o.jsx)(t.p,{children:"In this article, we are focused on the reasoning in the Planner. In fact, the Code Interpreter has CoT implemented as shown in the following snippet:"}),"\n",(0,o.jsx)(t.pre,{children:(0,o.jsx)(t.code,{className:"language-commandline",children:"\u251c\u2500\u25ba [thought] To fetch historical stock price data for MSFT using yfinance, I will first try to import yfinance and download the data. If yfinance is not installed, I will provide instructions to install it.\n\u251c\u2500\u25ba [reply_type] python\n\u251c\u2500\u25ba [reply_content]\n\u2502   import yfinance as yf\n\u2502\n\u2502   # Fetch historical stock price data for MSFT\n\u2502   ticker = 'MSFT'\n\u2502   msft_data = yf.download(ticker, start='2020-01-01', end='2025-01-01')\n\u2502\n\u2502   msft_data\n"})}),"\n",(0,o.jsxs)(t.p,{children:["For the Planner, there are actually two places in the response schema where CoT can be implemented: before generating the ",(0,o.jsx)(t.code,{children:"init_plan"})," and after the ",(0,o.jsx)(t.code,{children:"current_plan_step"}),", as shown in the previous snippet. The former is to generate the initial plan, while the latter is to use Planner's reasoning capabilities to solve the current subtask."]}),"\n",(0,o.jsxs)(t.p,{children:["The former was not implemented in TaskWeaver for two reasons: (1) to simplify the schema and save the reasoning time/prompt size; (2) the existing ",(0,o.jsx)(t.code,{children:"init_plan"})," and ",(0,o.jsx)(t.code,{children:"plan"})," already represent a thought process, and adding CoT may not bring significant benefits. But as the LLM becomes faster and cheaper, it is possible to add CoT to the Planner to improve the planning quality."]}),"\n",(0,o.jsx)(t.p,{children:"With reasoning for planning, the output of the Planner looks like this:"}),"\n",(0,o.jsx)(t.pre,{children:(0,o.jsx)(t.code,{className:"language-commandline",children:" Human   \u25b6  predict msft's stock price in the next 7 days\n \u256d\u2500\u2500\u2500< Planner >\n \u251c\u2500\u25ba [plan_reasoning] The user wants to predict Microsoft's stock price for the next 7 days. This task involves time series forecasting, which requires historical stock price data and a forecasting model. However, the user hasn't provided any data or specified a model to use. I need to ask the user for more information.\n \u251c\u2500\u25ba [init_plan]\n \u2502   1. Request historical stock price data from the user\n \u2502   2. Ask the user to specify a forecasting model or confirm if a default model should be used\n \u2502   3. Load the historical stock price data <interactively depends on 1>\n \u2502   4. Train the forecasting model using the historical data <interactively depends on 2 and 3>\n \u2502   5. Predict the stock price for the next 7 days <sequentially depends on 4>\n \u2502   6. Report the prediction results to the user <interactively depends on 5>\n"})}),"\n",(0,o.jsx)(t.p,{children:"It looks good, but it is not the most important part of this article. The latter is more interesting and also more challenging to implement than it looks."}),"\n",(0,o.jsx)(t.p,{children:"Let's use an example to motivate the necessity and explain the challenges. The task is described as follows and all the data in it are fake:"}),"\n",(0,o.jsx)(t.pre,{children:(0,o.jsx)(t.code,{className:"language-markdown",children:"# Task Instructions  \n## Step 1: Extract Employee Data  \nExtract the following information from the employee summary:  \n- `Employee ID`  \n- `Department`  \n- `Project Code`  \n- `Role`  \n- `Manager`  \n- `Location`  \n\n### Employee Summary  \nOn April 10, 2025, a review was conducted for an employee with ID `E12345`. \nThe employee is part of the `Development` department and is currently assigned to project code `\"X987\"`. \nThe role held is `\"Software Engineer\"` under the supervision of manager `\"J. Doe.\"` \nThe primary work location is `\"Remote.\"`  \n\n## Step 2: Validate the Role  \n- Confirm if the role is recognized among the following: Software Engineer, Data Analyst, Project Manager, DevOps Specialist, QA Tester.  \n- Check if the role is one of the recognized roles.  \n\n## Step 3: Construct SQL Query  \nPrepare and print the SQL query using the extracted details:  \n===\nSELECT EmployeeID, Department, ProjectCode, Role, Manager, Location  \nFROM EmployeeRecords  \nWHERE EmployeeID = '{EmployeeID}'  \nAND Department = '{Department}'  \nAND ProjectCode = '{ProjectCode}'  \nAND Role = '{Role}'  \nAND Manager = '{Manager}'  \nAND Location = '{Location}'  \nORDER BY EmployeeID;  \n=== \n"})}),"\n",(0,o.jsx)(t.p,{children:"The task has 3 steps: extract employee data, validate the role, and construct an SQL query. This would not be a hard problem for any ReAct based agents. Actually, for all the 3 steps, there is no need to call Code Interpreter. The Planner can reason through the task and generate the code directly. However, let's run it in TaskWeaver:"}),"\n",(0,o.jsx)(t.pre,{children:(0,o.jsx)(t.code,{className:"language-commandline",children:" \u256d\u2500\u2500\u2500< Planner >\n \u251c\u2500\u25ba [plan_reasoning] The user has provided a task with specific instructions to be followed step by step. The task involves extracting employee data, validating the role, and constructing an SQL query. Each step is dependent on\n \u2502    the completion of the previous one, so they must be executed in sequence.\n \u251c\u2500\u25ba [init_plan]\n \u2502   1. Extract the specified employee data from the summary provided.\n \u2502   2. Validate the role against the recognized roles list <sequentially depends on 1>\n \u2502   3. Construct the SQL query using the extracted details <sequentially depends on 2>\n \u2502   4. Report the constructed SQL query to the user <interactively depends on 3>\n \u251c\u2500\u25ba [plan]\n \u2502   1. Extract the specified employee data from the summary provided.\n \u2502   2. Validate the role against the recognized roles list.\n \u2502   3. Construct the SQL query using the extracted details.\n \u2502   4. Report the constructed SQL query to the user.\n \u251c\u2500\u25ba [current_plan_step] 1. Extract the specified employee data from the summary provided.\n \u251c\u2500\u25ba [stop] InProcess\n \u251c\u2500\u2500\u25cf Please extract the following information from the employee summary: Employee ID, Department, Project Code, Role, Manager, and Location. The summary is: On April 10, 2025, a review was conducted for an employee with ID     \n \u2502   `E12345`. The employee is part of the `Development` department and is currently assigned to project code `\"X987\"`. The role held is `\"Software Engineer\"` under the supervision of manager `\"J. Doe.\"` The primary work        \n \u2502   location is `\"Remote.\"`\n \u251c\u2500\u25ba [shared_memory_entry] Add the plan to the shared memory\n \u2570\u2500\u2500\u25cf sending message to CodeInterpreter\n \u256d\u2500\u2500\u2500< CodeInterpreter >\n \u251c\u2500\u25ba [thought] I will extract the required information from the given employee summary using string manipulation techniques.\n \u251c\u2500\u25ba [reply_type] python\n \u251c\u2500\u25ba [reply_content]\n \u2502   employee_summary = \"On April 10, 2025, a review was conducted for an employee with ID `E12345`. The employee is part of the `Development` department and is currently assigned to project code \\\"X987\\\". The role held is      \n \u2502   \\\"Software Engineer\\\" under the supervision of manager \\\"J. Doe.\\\" The primary work location is \\\"Remote.\\\"\"\n \u2502\n \u2502   # Extracting information\n \u2502   employee_id = employee_summary.split('ID `')[1].split('`')[0]\n \u2502   department = employee_summary.split('`')[3]\n \u2502   project_code = employee_summary.split('project code \\\"')[1].split('\\\"')[0]\n \u2502   role = employee_summary.split('role held is \\\"')[1].split('\\\"')[0]\n \u2502   manager = employee_summary.split('manager \\\"')[1].split('\\\"')[0]\n \u2502   location = employee_summary.split('location is \\\"')[1].split('\\\"')[0]\n \u2502\n \u2502   employee_id, department, project_code, role, manager, location\n \u251c\u2500\u25ba [verification] NONE\n \u251c\u2500\u25ba [code_error] No code verification is performed.\n \u251c\u2500\u25ba [execution_status] SUCCESS\n \u251c\u2500\u25ba [execution_result]\n \u2502   The execution of the generated python code above has succeeded\n \u2502\n \u2502   The result of above Python code after execution is:\n \u2502   ('E12345', 'Development', 'X987', 'Software Engineer', 'J. Doe.', 'Remote.')\n \u251c\u2500\u25ba [artifact_paths] []\n \u251c\u2500\u2500\u25cf The following python code has been executed:\n \u2502   ```python\n \u2502   employee_summary = \"On April 10, 2025, a review was conducted for an employee with ID `E12345`. The employee is part of the `Development` department and is currently assigned to project code \\\"X987\\\". The role held is      \n \u2502   \\\"Software Engineer\\\" under the supervision of manager \\\"J. Doe.\\\" The primary work location is \\\"Remote.\\\"\"\n \u2502\n \u2502   # Extracting information\n \u2502   employee_id = employee_summary.split('ID `')[1].split('`')[0]\n \u2502   department = employee_summary.split('`')[3]\n \u2502   project_code = employee_summary.split('project code \\\"')[1].split('\\\"')[0]\n \u2502   role = employee_summary.split('role held is \\\"')[1].split('\\\"')[0]\n \u2502   manager = employee_summary.split('manager \\\"')[1].split('\\\"')[0]\n \u2502   location = employee_summary.split('location is \\\"')[1].split('\\\"')[0]\n \u2502\n \u2502   employee_id, department, project_code, role, manager, location\n \u2502   ```\n \u2502\n \u2502\n \u2502   The execution of the generated python code above has succeeded\n \u2502\n \u2502   The result of above Python code after execution is:\n \u2502   ('E12345', 'Development', 'X987', 'Software Engineer', 'J. Doe.', 'Remote.')\n \u2570\u2500\u2500\u25cf sending message to Planner\n \u256d\u2500\u2500\u2500< Planner >\n \u251c\u2500\u25ba [plan_reasoning] The employee data has been successfully extracted from the summary. The next step is to validate the role against the list of recognized roles.\n \u251c\u2500\u25ba [init_plan]\n \u2502   1. Extract the specified employee data from the summary provided.\n \u2502   2. Validate the role against the recognized roles list <sequentially depends on 1>\n \u2502   3. Construct the SQL query using the extracted details <sequentially depends on 2>\n \u2502   4. Report the constructed SQL query to the user <interactively depends on 3>\n \u251c\u2500\u25ba [plan]\n \u2502   1. Extract the specified employee data from the summary provided.\n \u2502   2. Validate the role against the recognized roles list.\n \u2502   3. Construct the SQL query using the extracted details.\n \u2502   4. Report the constructed SQL query to the user.\n \u251c\u2500\u25ba [current_plan_step] 2. Validate the role against the recognized roles list.\n \u251c\u2500\u25ba [stop] InProcess\n \u251c\u2500\u2500\u25cf Please validate if the role 'Software Engineer' is recognized among the following roles: Software Engineer, Data Analyst, Project Manager, DevOps Specialist, QA Tester.\n \u251c\u2500\u25ba [shared_memory_entry] Add the plan to the shared memory\n \u2570\u2500\u2500\u25cf sending message to CodeInterpreter\n \u256d\u2500\u2500\u2500< CodeInterpreter >\n \u251c\u2500\u25ba [thought] I will validate if the role 'Software Engineer' is recognized among the given list of roles.\n \u251c\u2500\u25ba [reply_type] python\n \u251c\u2500\u25ba [reply_content]\n \u2502   # Step 2: Validate the Role\n \u2502   recognized_roles = [\"Software Engineer\", \"Data Analyst\", \"Project Manager\", \"DevOps Specialist\", \"QA Tester\"]\n \u2502   role = \"Software Engineer\"\n \u2502\n \u2502   is_role_recognized = role in recognized_roles\n \u2502   is_role_recognized\n \u251c\u2500\u25ba [verification] NONE\n \u251c\u2500\u25ba [code_error] No code verification is performed.\n \u251c\u2500\u25ba [execution_status] SUCCESS\n \u251c\u2500\u25ba [execution_result]\n \u2502   The execution of the generated python code above has succeeded\n \u2502\n \u2502   The result of above Python code after execution is:\n \u2502   True\n \u251c\u2500\u25ba [artifact_paths] []\n \u251c\u2500\u2500\u25cf The following python code has been executed:\n \u2502   ```python\n \u2502   # Step 2: Validate the Role\n \u2502   recognized_roles = [\"Software Engineer\", \"Data Analyst\", \"Project Manager\", \"DevOps Specialist\", \"QA Tester\"]\n \u2502   role = \"Software Engineer\"\n \u2502\n \u2502   is_role_recognized = role in recognized_roles\n \u2502   is_role_recognized\n \u2502   ```\n \u2502\n \u2502\n \u2502   The execution of the generated python code above has succeeded\n \u2502   \n \u2502   The result of above Python code after execution is:\n \u2502   True\n \u2570\u2500\u2500\u25cf sending message to Planner\n \u256d\u2500\u2500\u2500< Planner >\n \u251c\u2500\u25ba [plan_reasoning] The role 'Software Engineer' is recognized among the list of roles. The next step is to construct the SQL query using the extracted details.\n \u251c\u2500\u25ba [init_plan]\n \u2502   1. Extract the specified employee data from the summary provided.\n \u2502   2. Validate the role against the recognized roles list <sequentially depends on 1>\n \u2502   3. Construct the SQL query using the extracted details <sequentially depends on 2>\n \u2502   4. Report the constructed SQL query to the user <interactively depends on 3>\n \u251c\u2500\u25ba [plan]\n \u2502   1. Extract the specified employee data from the summary provided.\n \u2502   2. Validate the role against the recognized roles list.\n \u2502   3. Construct the SQL query using the extracted details.\n \u2502   4. Report the constructed SQL query to the user.\n \u251c\u2500\u25ba [current_plan_step] 3. Construct the SQL query using the extracted details.\n \u251c\u2500\u25ba [stop] InProcess\n \u251c\u2500\u2500\u25cf Please construct the SQL query using the extracted details: Employee ID 'E12345', Department 'Development', Project Code 'X987', Role 'Software Engineer', Manager 'J. Doe.', and Location 'Remote'. The SQL query should be  \n \u2502   in the format provided in the task instructions.\n \u251c\u2500\u25ba [shared_memory_entry] Add the plan to the shared memory\n \u2570\u2500\u2500\u25cf sending message to CodeInterpreter\n \u256d\u2500\u2500\u2500< CodeInterpreter >\n \u251c\u2500\u25ba [thought] I will construct the SQL query using the extracted details from the previous successful round.\n \u251c\u2500\u25ba [reply_type] python\n \u251c\u2500\u25ba [reply_content]\n \u2502   # Step 3: Construct SQL Query\n \u2502   employee_id = 'E12345'\n \u2502   department = 'Development'\n \u2502   project_code = 'X987'\n \u2502   role = 'Software Engineer'\n \u2502   manager = 'J. Doe.'\n \u2502   location = 'Remote.'\n \u2502\n \u2502   sql_query = f\"\"\"\n \u2502   SELECT EmployeeID, Department, ProjectCode, Role, Manager, Location\n \u2502   FROM EmployeeRecords\n \u2502   WHERE EmployeeID = '{employee_id}'\n \u2502   AND Department = '{department}'\n \u2502   AND ProjectCode = '{project_code}'\n \u2502   AND Role = '{role}'\n \u2502   AND Manager = '{manager}'\n \u2502   AND Location = '{location}'\n \u2502   ORDER BY EmployeeID;\n \u2502   \"\"\"\n \u2502\n \u2502   sql_query\n \u251c\u2500\u25ba [verification] NONE\n \u251c\u2500\u25ba [code_error] No code verification is performed.\n \u251c\u2500\u25ba [execution_status] SUCCESS\n \u251c\u2500\u25ba [execution_result]\n \u2502   The execution of the generated python code above has succeeded\n \u2502\n \u2502   The result of above Python code after execution is:\n \u2502\n \u2502   SELECT EmployeeID, Department, ProjectCode, Role, Manager, Location\n \u2502   FROM EmployeeRecords\n \u2502   WHERE EmployeeID = 'E12345'\n \u2502   AND Department = 'Development'\n \u2502   AND ProjectCode = 'X987'\n \u2502   AND Role = 'Software Engineer'\n \u2502   AND Manager = 'J. Doe.'\n \u2502   AND Location = 'Remote.'\n \u2502   ORDER BY EmployeeID;\n \u2502\n \u251c\u2500\u25ba [artifact_paths] []\n \u251c\u2500\u2500\u25cf The following python code has been executed:\n \u2502   ```python\n \u2502   # Step 3: Construct SQL Query\n \u2502   employee_id = 'E12345'\n \u2502   department = 'Development'\n \u2502   project_code = 'X987'\n \u2502   role = 'Software Engineer'\n \u2502   manager = 'J. Doe.'\n \u2502   location = 'Remote.'\n \u2502\n \u2502   sql_query = f\"\"\"\n \u2502   SELECT EmployeeID, Department, ProjectCode, Role, Manager, Location\n \u2502   FROM EmployeeRecords\n \u2502   WHERE EmployeeID = '{employee_id}'\n \u2502   AND Department = '{department}'\n \u2502   AND ProjectCode = '{project_code}'\n \u2502   AND Role = '{role}'\n \u2502   AND Manager = '{manager}'\n \u2502   AND Location = '{location}'\n \u2502   ORDER BY EmployeeID;\n \u2502   \"\"\"\n \u2502\n \u2502   sql_query\n \u2502   ```\n \u2502\n \u2502\n \u2502   The execution of the generated python code above has succeeded\n \u2502\n \u2502   The result of above Python code after execution is:\n \u2502\n \u2502   SELECT EmployeeID, Department, ProjectCode, Role, Manager, Location\n \u2502   FROM EmployeeRecords\n \u2502   WHERE EmployeeID = 'E12345'\n \u2502   AND Department = 'Development'\n \u2502   AND ProjectCode = 'X987'\n \u2502   AND Role = 'Software Engineer'\n \u2502   AND Manager = 'J. Doe.'\n \u2502   AND Location = 'Remote.'\n \u2502   ORDER BY EmployeeID;\n \u2502\n \u2570\u2500\u2500\u25cf sending message to Planner\n \u256d\u2500\u2500\u2500< Planner >\n \u251c\u2500\u25ba [plan_reasoning] The SQL query has been successfully constructed using the extracted employee details. The task is now complete, and the constructed SQL query can be reported to the user.\n \u251c\u2500\u25ba [init_plan]\n \u2502   1. Extract the specified employee data from the summary provided.\n \u2502   2. Validate the role against the recognized roles list <sequentially depends on 1>\n \u2502   3. Construct the SQL query using the extracted details <sequentially depends on 2>\n \u2502   4. Report the constructed SQL query to the user <interactively depends on 3>\n \u251c\u2500\u25ba [plan]\n \u2502   1. Extract the specified employee data from the summary provided.\n \u2502   2. Validate the role against the recognized roles list.\n \u2502   3. Construct the SQL query using the extracted details.\n \u2502   4. Report the constructed SQL query to the user.\n \u251c\u2500\u25ba [current_plan_step] 4. Report the constructed SQL query to the user.\n \u251c\u2500\u25ba [stop] Completed\n \u251c\u2500\u2500\u25cf The SQL query has been successfully constructed using the extracted details:\n \u2502\n \u2502   ```\n \u2502   SELECT EmployeeID, Department, ProjectCode, Role, Manager, Location\n \u2502   FROM EmployeeRecords\n \u2502   WHERE EmployeeID = 'E12345'\n \u2502   AND Department = 'Development'\n \u2502   AND ProjectCode = 'X987'\n \u2502   AND Role = 'Software Engineer'\n \u2502   AND Manager = 'J. Doe.'\n \u2502   AND Location = 'Remote.'\n \u2502   ORDER BY EmployeeID;\n \u2502   ```\n \u251c\u2500\u25ba [shared_memory_entry] Add the plan to the shared memory\n \u2570\u2500\u2500\u25cf sending message to User\n TaskWeaver \u25b6  The SQL query has been successfully constructed using the extracted details:\n\nSELECT EmployeeID, Department, ProjectCode, Role, Manager, Location\nFROM EmployeeRecords\nWHERE EmployeeID = 'E12345'\nAND Department = 'Development'\nAND ProjectCode = 'X987'\nAND Role = 'Software Engineer'\nAND Manager = 'J. Doe.'\nAND Location = 'Remote.'\nORDER BY EmployeeID;\n"})}),"\n",(0,o.jsx)(t.p,{children:"The log is quite lengthy, but it is quite clear and easy to understand. For each step, the Planner always asks the Code Interpreter to generate the code. Finally, the task is completed successfully. However, it is not the most efficient way to solve the task because the Planner can leverage its reasoning capabilities to extract information and construct the SQL query directly."}),"\n",(0,o.jsxs)(t.p,{children:["We have tried to add instructions in the Planner's prompt to emphasize the reasoning power, but the Planner still calls the Code Interpreter to generate the code. For a long time, we don't quite understand the reason behind this behavior. After many discussions and experiments, we finally realized that it is caused by the design of the Planner's response schema. The Planner needs to talk to another Role in the system each time. But if we want the Planner to use reasoning to solve the current subtask, who should the Planner talk to? Ideally, it should continue until the subtask that requires the Code Interpreter to generate the code. But how can we design the schema to support this? Because the Planner is explicitly tracking the progress, i.e., the ",(0,o.jsx)(t.code,{children:"current_plan_step"}),", it is confusing to let the Planner continue the reasoning process through future steps."]}),"\n",(0,o.jsxs)(t.p,{children:["We value the progress tracking more than the efficiency of the reasoning process, because this is critical for complex multi-step tasks. But we also want to improve the reasoning process to make the agent more intelligent. So, our choice is to add a special Role called ",(0,o.jsx)(t.code,{children:"Recepta"})," to listen to the Planner's reasoning process when the Planner wants to use reasoning to solve the current subtask. The ",(0,o.jsx)(t.code,{children:"Recepta"}),' always answers "Got it. Please go ahead!" to the Planner. The Planner can then continue the reasoning process until the subtask that requires the Code Interpreter to generate the code. The ',(0,o.jsx)(t.code,{children:"Recepta"})," is not a real Role in the system, but a design pattern to support the reasoning process in the Planner."]}),"\n",(0,o.jsxs)(t.p,{children:["Now, let's look at the output of TaskWeaver with ",(0,o.jsx)(t.code,{children:"Recepta"}),":"]}),"\n",(0,o.jsx)(t.pre,{children:(0,o.jsx)(t.code,{className:"language-commandline",children:"\u256d\u2500\u2500\u2500< Planner >\n\u251c\u2500\u25ba [plan_reasoning] The user has provided a set of instructions to follow step by step. The task involves extracting employee data from a summary, validating the role, and constructing an SQL query. I will follow these steps sequentially.\n\u251c\u2500\u25ba [init_plan]\n\u2502   1. Extract the following information from the employee summary: `Employee ID`, `Department`, `Project Code`, `Role`, `Manager`, `Location`\n\u2502   2. Validate the role <interactively depends on 1>\n\u2502   3. Construct and print the SQL query using the extracted details <interactively depends on 1>\n\u2502   4. Check the execution result and report the result to the user <interactively depends on 1 and 3>\n\u251c\u2500\u25ba [plan]\n\u2502   1. Extract information from the employee summary\n\u2502   2. Validate the role\n\u2502   3. Construct SQL query using the extracted details\n\u2502   4. Report the result to the user\n\u251c\u2500\u25ba [current_plan_step] 1. Extract information from the employee summary\n\u251c\u2500\u25ba [stop] InProcess\n\u251c\u2500\u2500\u25cf Thought: I can read and comprehend the employee summary to extract the required information.\n\u2502   Result: the `Employee ID` is `E12345`, the `Department` is `Development`, the `Project Code` is `X987`, the `Role` is `Software Engineer`, the `Manager` is `J. Doe`, and the `Location` is `Remote`.\n\u251c\u2500\u25ba [shared_memory_entry] Add the plan to the shared memory\n\u2570\u2500\u2500\u25cf sending message to Recepta\n\u256d\u2500\u2500\u2500< Recepta >\n\u251c\u2500\u2500\u25cf Got it. Now, please go ahead!\n\u2570\u2500\u2500\u25cf sending message to Planner\n\u256d\u2500\u2500\u2500< Planner >\n\u251c\u2500\u25ba [plan_reasoning] I have extracted the information from the employee summary. The next step is to verify if the role is one of the recognized roles.\n\u251c\u2500\u25ba [init_plan]\n\u2502   1. Extract the following information from the employee summary: `Employee ID`, `Department`, `Project Code`, `Role`, `Manager`, `Location`\n\u2502   2. Validate the role <interactively depends on 1>\n\u2502   3. Construct and print the SQL query using the extracted details <interactively depends on 1>\n\u2502   4. Check the execution result and report the result to the user <interactively depends on 1 and 3>\n\u251c\u2500\u25ba [plan]\n\u2502   1. Extract information from the employee summary\n\u2502   2. Validate the role\n\u2502   3. Construct SQL query using the extracted details\n\u2502   4. Report the result to the user\n\u251c\u2500\u25ba [current_plan_step] 2. Validate the role\n\u251c\u2500\u25ba [stop] InProcess\n\u251c\u2500\u2500\u25cf Thought: I can verify if the role is one of the recognized roles with my pattern matching capability.\n\u2502   Thought: The recognized roles are `Software Engineer, Data Analyst, Project Manager, DevOps Specialist, QA Tester`.\n\u2502   Result: The role is `Software Engineer`, which is recognized.\n\u251c\u2500\u25ba [shared_memory_entry] Add the plan to the shared memory\n\u2570\u2500\u2500\u25cf sending message to Recepta\n\u256d\u2500\u2500\u2500< Recepta >\n\u251c\u2500\u2500\u25cf Got it. Now, please go ahead!\n\u2570\u2500\u2500\u25cf sending message to Planner\n\u256d\u2500\u2500\u2500< Planner >\n\u251c\u2500\u25ba [plan_reasoning] I can prepare and print the SQL query using the extracted details to the User.\n\u251c\u2500\u25ba [init_plan]\n\u2502   1. Extract the following information from the employee summary: `Employee ID`, `Department`, `Project Code`, `Role`, `Manager`, `Location`\n\u2502   2. Validate the role <interactively depends on 1>\n\u2502   3. Construct and print the SQL query using the extracted details <interactively depends on 1>\n\u2502   4. Check the execution result and report the result to the user <interactively depends on 1 and 3>\n\u251c\u2500\u25ba [plan]\n\u2502   1. Extract information from the employee summary\n\u2502   2. Validate the role\n\u2502   3. Construct SQL query using the extracted details\n\u2502   4. Report the result to the user\n\u251c\u2500\u25ba [current_plan_step] 3. Construct and print the SQL query using the extracted details and report the result to the user\n\u251c\u2500\u25ba [stop] Completed\n\u251c\u2500\u2500\u25cf The role is `Software Engineer`, which is recognized.\n\u2502\n\u2502   Here is the SQL query using the extracted details:\n\u2502   ```sql\n\u2502   SELECT EmployeeID, Department, ProjectCode, Role, Manager, Location\n\u2502   FROM EmployeeRecords\n\u2502   WHERE EmployeeID = 'E12345'\n\u2502   AND Department = 'Development'\n\u2502   AND ProjectCode = 'X987'\n\u2502   AND Role = 'Software Engineer'\n\u2502   AND Manager = 'J. Doe'\n\u2502   AND Location = 'Remote'\n\u2502   ORDER BY EmployeeID;\n\u2502   ```\n\u251c\u2500\u25ba [shared_memory_entry] Add the plan to the shared memory\n\u2570\u2500\u2500\u25cf sending message to User\n TaskWeaver \u25b6  The role is `Software Engineer`, which is recognized.\n\nHere is the SQL query using the extracted details:\n\nSELECT EmployeeID, Department, ProjectCode, Role, Manager, Location\nFROM EmployeeRecords\nWHERE EmployeeID = 'E12345'\nAND Department = 'Development'\nAND ProjectCode = 'X987'\nAND Role = 'Software Engineer'\nAND Manager = 'J. Doe'\nAND Location = 'Remote'\nORDER BY EmployeeID;\n"})}),"\n",(0,o.jsx)(t.p,{children:"The new log is not only shorter but also more efficient. It is also more reliable according to our observations. Writing code with regex to extract information from text is error-prone."}),"\n",(0,o.jsxs)(t.p,{children:["In summary, we have experimented the idea of adding a special Role called ",(0,o.jsx)(t.code,{children:"Recepta"})," to support the reasoning process in the Planner. The ",(0,o.jsx)(t.code,{children:"Recepta"})," is not a real Role in the system, but a design pattern to support the reasoning process in the Planner. This design pattern is simple and effective. It is also flexible and can be extended to support more complex reasoning processes in the Planner. We believe that this design pattern can be useful for building more intelligent agents in the future."]}),"\n",(0,o.jsx)(t.p,{children:"To enable it in TaskWeaver, the user needs to configure the roles in the configure file with the following content:"}),"\n",(0,o.jsx)(t.pre,{children:(0,o.jsx)(t.code,{className:"language-json",children:'"session.roles": [\n    "planner",\n    "code_interpreter",\n    "recepta"\n]\n'})}),"\n",(0,o.jsxs)(t.p,{children:["The ",(0,o.jsx)(t.code,{children:"recepta"})," role is added to the list of roles."]})]})}function h(e={}){const{wrapper:t}={...(0,r.R)(),...e.components};return t?(0,o.jsx)(t,{...e,children:(0,o.jsx)(d,{...e})}):d(e)}},8453:(e,t,n)=>{n.d(t,{R:()=>s,x:()=>i});var o=n(6540);const r={},a=o.createContext(r);function s(e){const t=o.useContext(a);return o.useMemo((function(){return"function"==typeof e?e(t):{...t,...e}}),[t,e])}function i(e){let t;return t=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:s(e.components),o.createElement(a.Provider,{value:t},e.children)}}}]);