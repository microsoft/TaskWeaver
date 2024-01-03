"use strict";(self.webpackChunkwebsite=self.webpackChunkwebsite||[]).push([[5887],{5461:(e,n,r)=>{r.r(n),r.d(n,{assets:()=>l,contentTitle:()=>o,default:()=>d,frontMatter:()=>s,metadata:()=>a,toc:()=>c});var t=r(5893),i=r(1151);const s={},o="Auto Plugin Selection",a={id:"customization/plugin/plugin_selection",title:"Auto Plugin Selection",description:"In TaskWeaver, we provide an auto plugin selection mechanism to dynamically select the best plugin for each user request.",source:"@site/docs/customization/plugin/plugin_selection.md",sourceDirName:"customization/plugin",slug:"/customization/plugin/plugin_selection",permalink:"/TaskWeaver/docs/customization/plugin/plugin_selection",draft:!1,unlisted:!1,editUrl:"https://github.com/microsoft/TaskWeaver/tree/docs/website/docs/customization/plugin/plugin_selection.md",tags:[],version:"current",frontMatter:{},sidebar:"documentSidebar",previous:{title:"Plugin Introduction",permalink:"/TaskWeaver/docs/plugin/plugin_intro"},next:{title:"Embedding",permalink:"/TaskWeaver/docs/customization/plugin/embedding"}},l={},c=[{value:"Auto Plugin Selection Overview",id:"auto-plugin-selection-overview",level:2},{value:"Auto Plugin Selection Configuration",id:"auto-plugin-selection-configuration",level:2},{value:"Auto Plugin Selection Example",id:"auto-plugin-selection-example",level:2}];function u(e){const n={a:"a",code:"code",h1:"h1",h2:"h2",img:"img",li:"li",ol:"ol",p:"p",pre:"pre",ul:"ul",...(0,i.a)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(n.h1,{id:"auto-plugin-selection",children:"Auto Plugin Selection"}),"\n",(0,t.jsx)(n.p,{children:"In TaskWeaver, we provide an auto plugin selection mechanism to dynamically select the best plugin for each user request.\r\nIt targets to solve the following two problems:"}),"\n",(0,t.jsxs)(n.ol,{children:["\n",(0,t.jsx)(n.li,{children:"An excessive number of plugins may cause confusion for LLM, leading to inaccuracies in generating the correct code."}),"\n",(0,t.jsx)(n.li,{children:"A large number of plugins could lead to increased token usage (potentially exceeding the token limit of LLM) and extended response time."}),"\n"]}),"\n",(0,t.jsx)(n.h2,{id:"auto-plugin-selection-overview",children:"Auto Plugin Selection Overview"}),"\n",(0,t.jsxs)(n.p,{children:["Below is the overview workflow of the auto plugin selection mechanism.\r\n",(0,t.jsx)(n.img,{alt:"Auto Plugin Selection Overview",src:r(8936).Z+"",width:"1846",height:"543"})]}),"\n",(0,t.jsx)(n.p,{children:"NOTE: the automatic plugin selection mechanism is only activated during the code generation process in the Code Interpreter and does not affect the planning process of the Planner."}),"\n",(0,t.jsxs)(n.p,{children:["At the start of TaskWeaver initialization, the automatic plugin selector is activated to generate embedding vectors for all plugins, including their names and descriptions.\r\nThe embedding vectors are created using the specified embedding model configured in the ",(0,t.jsx)(n.code,{children:"taskweaver_config.json"})," file.\r\nFor more information, please refer to the ",(0,t.jsx)(n.a,{href:"/TaskWeaver/docs/customization/plugin/embedding",children:"embedding"})," documentation."]}),"\n",(0,t.jsxs)(n.p,{children:["When the Planner sends a request to the Code Interpreter, the auto plugin selection mechanism will be triggered.\r\nIt will first generate an embedding vector for the request using the same embedding model.\r\nThen, it will calculate the cosine similarity between the request embedding vector and the embedding vectors of all plugins.\r\nIt will select the top-k plugins with the highest cosine similarity scores and  load them into the ",(0,t.jsx)(n.code,{children:"code_generator"})," prompt."]}),"\n",(0,t.jsxs)(n.p,{children:["Upon completing the code generation, the ",(0,t.jsx)(n.code,{children:"code_generator"})," employs one or more plugins to produce the desired code.\r\nWe have established a plugin pool to store the plugins involved in the code generation process while filtering out any unused ones.\r\nDuring the subsequent automatic plugin selection phase, newly chosen plugins are appended to the existing ones."]}),"\n",(0,t.jsx)(n.h2,{id:"auto-plugin-selection-configuration",children:"Auto Plugin Selection Configuration"}),"\n",(0,t.jsxs)(n.ul,{children:["\n",(0,t.jsxs)(n.li,{children:[(0,t.jsx)(n.code,{children:"code_generator.enable_auto_plugin_selection"}),": Whether to enable auto plugin selection. The default value is ",(0,t.jsx)(n.code,{children:"false"}),"."]}),"\n",(0,t.jsxs)(n.li,{children:[(0,t.jsx)(n.code,{children:"code_generator.auto_plugin_selection_topk"}),":\tThe number of auto selected plugins in each round. The default value is ",(0,t.jsx)(n.code,{children:"3"}),"."]}),"\n"]}),"\n",(0,t.jsx)(n.h2,{id:"auto-plugin-selection-example",children:"Auto Plugin Selection Example"}),"\n",(0,t.jsx)(n.p,{children:"We show the auto plugin selection mechanism in the following example."}),"\n",(0,t.jsx)(n.p,{children:"First, we start TaskWeaver with the auto plugin selection mechanism enabled."}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-bash",children:"=========================================================\r\n _____         _     _       __\r\n|_   _|_ _ ___| | _ | |     / /__  ____ __   _____  _____\r\n  | |/ _` / __| |/ /| | /| / / _ \\/ __ `/ | / / _ \\/ ___/\r\n  | | (_| \\__ \\   < | |/ |/ /  __/ /_/ /| |/ /  __/ /\r\n  |_|\\__,_|___/_|\\_\\|__/|__/\\___/\\__,_/ |___/\\___/_/\r\n=========================================================\r\nTaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?\r\nHuman: \n"})}),"\n",(0,t.jsxs)(n.p,{children:["Then we can check the log file ",(0,t.jsx)(n.code,{children:"task_weaver.log"})," in the ",(0,t.jsx)(n.code,{children:"logs"})," folder to see the auto plugin selector is initialized successfully because the ",(0,t.jsx)(n.code,{children:"Plugin embeddings generated"})," message is printed."]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-bash",children:"2023-12-18 14:23:44,197 - INFO - Planner initialized successfully\r\n2023-12-18 14:24:10,488 - INFO - Plugin embeddings generated\r\n2023-12-18 14:24:10,490 - INFO - CodeInterpreter initialized successfully.\r\n2023-12-18 14:24:10,490 - INFO - Session 20231218-062343-c18494b1 is initialized\n"})}),"\n",(0,t.jsx)(n.p,{children:'We ask TaskWeaver to "search Xbox price for me".\r\nThe Planner instructs the Code Interpreter to search Xbox price.'}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-bash",children:"TaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?\r\nHuman: search xbox price for me\r\n>>> [INIT_PLAN]\r\n1. search xbox price\r\n2. report the result to the user <interactively depends on 1>\r\n>>> [PLAN]\r\n1. instruct CodeInterpreter to search xbox price\r\n2. report the result to the user\r\n>>> [CURRENT_PLAN_STEP]\r\n1. instruct CodeInterpreter to search xbox price\r\n>>> [SEND_TO]\r\nCodeInterpreter\r\n>>> [MESSAGE]\r\nPlease search xbox price\r\n>>> [PLANNER->CODEINTERPRETER]\r\nPlease search xbox price\n"})}),"\n",(0,t.jsxs)(n.p,{children:["Back to the Code Interpreter, the auto plugin selection mechanism is triggered.\r\nWe can check the log file ",(0,t.jsx)(n.code,{children:"task_weaver.log"})," again to see the auto plugin selector selected the top-3 plugins with the highest cosine similarity scores."]}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-bash",children:"023-12-18 14:24:34,513 - INFO - Planner talk to CodeInterpreter: Please search xbox price using klarna_search plugin\r\n2023-12-18 14:24:34,669 - INFO - Selected plugins: ['klarna_search', 'sql_pull_data', 'paper_summary']\r\n2023-12-18 14:24:34,669 - INFO - Selected plugin pool: ['klarna_search', 'sql_pull_data', 'paper_summary']\n"})}),"\n",(0,t.jsx)(n.p,{children:"Then the Code Interpreter will generate the code using the selected plugins."}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-bash",children:">>> [THOUGHT]\r\nProgramApe will call the klarna_search plugin function to search for Xbox prices.\r\n>>> [PYTHON]\r\nsearch_results, description = klarna_search(query=\"xbox\")\r\nsearch_results, description\r\n>>> [VERIFICATION]\r\nNONE\r\n>>> [STATUS]\r\nSUCCESS\r\n>>> [RESULT]\r\nThe execution of the generated python code above has succeeded\r\n\r\nThe result of above Python code after execution is:\r\n(                                                 name    price                                                url                                         attributes\r\n 0             Microsoft Xbox Series X - Black Edition  $399.00  https://www.klarna.com/us/shopping/pl/cl52/495...  [Release Year:2020, Included Accessories:1 gam...\r\n 1                 Microsoft Xbox Series S 1TB - Black  $349.00  https://www.klarna.com/us/shopping/pl/cl52/320...  [Included Accessories:1 gamepad, Media Type:DV...\r\n ..                                                ...      ...                                                ...                                                ...\r\n 3                      Xbox Series S \u2013 Starter Bundle  $239.00  https://www.klarna.com/us/shopping/pl/cl52/320...                                [Platform:Xbox One]\r\n 4   Microsoft Xbox Series X 1TB Console - Diablo I...  $385.58  https://www.klarna.com/us/shopping/pl/cl52/320...  [Release Year:2023, Included Accessories:1 gam...\r\n\r\n [5 rows x 4 columns],\r\n 'The response is a dataframe with the following columns: name, price, url, attributes. The attributes column is a list of tags. The price is in the format of $xx.xx.')\r\n>>> [CODEINTERPRETER->PLANNER]\r\nThe following python code has been executed:\r\n```python\r\nsearch_results, description = klarna_search(query=\"xbox\")\r\nsearch_results, description\r\n```\r\n\r\nThe execution of the generated python code above has succeeded\r\n\r\nThe result of above Python code after execution is:\r\n(                                                 name    price                                                url                                         attributes\r\n 0             Microsoft Xbox Series X - Black Edition  $399.00  https://www.klarna.com/us/shopping/pl/cl52/495...  [Release Year:2020, Included Accessories:1 gam...\r\n 1                 Microsoft Xbox Series S 1TB - Black  $349.00  https://www.klarna.com/us/shopping/pl/cl52/320...  [Included Accessories:1 gamepad, Media Type:DV...\r\n ..                                                ...      ...                                                ...                                                ...\r\n 3                      Xbox Series S \u2013 Starter Bundle  $239.00  https://www.klarna.com/us/shopping/pl/cl52/320...                                [Platform:Xbox One]\r\n 4   Microsoft Xbox Series X 1TB Console - Diablo I...  $385.58  https://www.klarna.com/us/shopping/pl/cl52/320...  [Release Year:2023, Included Accessories:1 gam...\r\n\r\n [5 rows x 4 columns],\r\n 'The response is a dataframe with the following columns: name, price, url, attributes. The attributes column is a list of tags. The price is in the format of $xx.xx.')\n"})}),"\n",(0,t.jsx)(n.p,{children:"Finally, the Planner will report the result to the user."}),"\n",(0,t.jsx)(n.pre,{children:(0,t.jsx)(n.code,{className:"language-bash",children:">>> [INIT_PLAN]\r\n1. search xbox price using klarna_search plugin\r\n2. report the result to the user <interactively depends on 1>\r\n>>> [PLAN]\r\n1. instruct CodeInterpreter to search xbox price using klarna_search plugin\r\n2. report the result to the user\r\n>>> [CURRENT_PLAN_STEP]\r\n2. report the result to the user\r\n>>> [SEND_TO]\r\nUser\r\n>>> [MESSAGE]\r\nHere are some Xbox prices I found:\r\n\r\n1. Microsoft Xbox Series X - Black Edition: $399.00\r\n2. Microsoft Xbox Series S 1TB - Black: $349.00\r\n3. Xbox Series S \u2013 Starter Bundle: $239.00\r\n4. Microsoft Xbox Series X 1TB Console - Diablo Immortal Edition: $385.58\r\n\r\nPlease note that these prices are subject to change and availability.\r\n>>> [PLANNER->USER]\r\nHere are some Xbox prices I found:\r\n\r\n1. Microsoft Xbox Series X - Black Edition: $399.00\r\n2. Microsoft Xbox Series S 1TB - Black: $349.00\r\n3. Xbox Series S \u2013 Starter Bundle: $239.00\r\n4. Microsoft Xbox Series X 1TB Console - Diablo Immortal Edition: $385.58\r\n\r\nPlease note that these prices are subject to change and availability.\r\nTaskWeaver: Here are some Xbox prices I found:\r\n\r\n1. Microsoft Xbox Series X - Black Edition: $399.00\r\n2. Microsoft Xbox Series S 1TB - Black: $349.00\r\n3. Xbox Series S \u2013 Starter Bundle: $239.00\r\n4. Microsoft Xbox Series X 1TB Console - Diablo Immortal Edition: $385.58\r\n\r\nPlease note that these prices are subject to change and availability.\n"})})]})}function d(e={}){const{wrapper:n}={...(0,i.a)(),...e.components};return n?(0,t.jsx)(n,{...e,children:(0,t.jsx)(u,{...e})}):u(e)}},8936:(e,n,r)=>{r.d(n,{Z:()=>t});const t=r.p+"assets/images/APS-1dc4d286038dedc17487146cec8214fd.png"},1151:(e,n,r)=>{r.d(n,{Z:()=>a,a:()=>o});var t=r(7294);const i={},s=t.createContext(i);function o(e){const n=t.useContext(s);return t.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function a(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(i):e.components||i:o(e.components),t.createElement(s.Provider,{value:n},e.children)}}}]);