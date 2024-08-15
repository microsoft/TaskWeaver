"use strict";(self.webpackChunkwebsite=self.webpackChunkwebsite||[]).push([[4904],{6893:(e,t,n)=>{n.r(t),n.d(t,{assets:()=>h,contentTitle:()=>s,default:()=>c,frontMatter:()=>o,metadata:()=>i,toc:()=>l});var a=n(5893),r=n(1151);const o={},s="Roles in TaskWeaver",i={permalink:"/TaskWeaver/blog/role",editUrl:"https://github.com/microsoft/TaskWeaver/tree/main/website/blog/role.md",source:"@site/blog/role.md",title:"Roles in TaskWeaver",description:'We frame TaskWeaver as a code-first agent framework. The term "code-first" means that the agent is designed to',date:"2024-08-15T06:57:25.000Z",formattedDate:"August 15, 2024",tags:[],readingTime:6.135,hasTruncateMarker:!1,authors:[],frontMatter:{},unlisted:!1,prevItem:{title:"Plugins In-Depth",permalink:"/TaskWeaver/blog/plugin"}},h={authorsImageUrls:[]},l=[];function d(e){const t={a:"a",code:"code",em:"em",mermaid:"mermaid",p:"p",pre:"pre",strong:"strong",...(0,r.a)(),...e.components};return(0,a.jsxs)(a.Fragment,{children:[(0,a.jsxs)(t.p,{children:["We frame TaskWeaver as a ",(0,a.jsx)(t.strong,{children:"code-first"})," agent framework. The term \"code-first\" means that the agent is designed to\nconvert the user's request into one or multiple runnable code snippets and then execute them to generate the response.\nThe philosophy behind this design is to consider programming languages as the de facto language for communication in cyber-physical systems,\njust like the natural language for human communication. Therefore, TaskWeaver translates the user's request in natural language into\nprogramming languages, which can be executed by the system to perform the desired tasks."]}),"\n",(0,a.jsxs)(t.p,{children:["Under this design, when the developer needs to extend the agent's capability, they can write a new plugin.\nA plugin is a piece of code wrapped in a class that can be called as a function by the agent in the generated code snippets.\nLet's consider an example: ",(0,a.jsx)(t.em,{children:"the agent is asked to load a CSV file and perform anomaly detection on the data"}),".\nThe workflow of the agent is in the diagram below. It is very natural to represent data to be processed in variables and this task in code snippets."]}),"\n",(0,a.jsx)(t.mermaid,{value:'flowchart TD\n    A[User] --"read a.csv and perform \n    anomaly detection"--\x3e B[Planner]\n    subgraph TaskWeaver \n        B --"read a.csv and call the \n        anomaly_detection plugin\n        to find anomalies in the data"--\x3e C[Code Generator]\n        subgraph Code Interpreter\n            C --"df=pd.read_csv(\'a.csv\')\n            anomaly_df=anomaly_detection(df)"--\x3e D[Code Executor]\n        end\n    end\n    D --result--\x3e B\n    B --response--\x3e A'}),"\n",(0,a.jsxs)(t.p,{children:["However, we do find challenges for other tasks that are not naturally represented in code snippets.\nLet's consider another example: ",(0,a.jsx)(t.em,{children:"the agent is asked to read a manual and follow the instructions to process the data"}),".\nWe first assume there is a plugin that can read the manual and extract the instructions, called ",(0,a.jsx)(t.code,{children:"read_manual"}),".\nThe workflow of the agent is in the diagram below.\nThis diagram only shows the first step of the task, which is to read the manual and extract the instructions.\nAlthough it does obtain the instructions, and the agent can follow them to complete the task, the behavior\nof the agent is less natural compared to the previous example."]}),"\n",(0,a.jsx)(t.mermaid,{value:'flowchart TD\n    A[User] --"read the manual and follow \n    the instructions to process the data"--\x3e B[Planner]\n    subgraph TaskWeaver \n        B --"step 1: read the manual by \n        calling the read_manual \n        plugin to extract  the instructions"--\x3e C[Code Generator]\n        subgraph Code Interpreter\n            C --"instructions=read_manual()\n            follow_instructions(instructions)"--\x3e D[Code Executor]\n        end\n    end\n    D --instructions--\x3e B'}),"\n",(0,a.jsxs)(t.p,{children:["Why? First, there is no need to generate code to read the manual and extract the instructions.\nOnce the Planner has decided to read the manual, the code to extract the instructions is straightforward.\nEven though that there might be dynamic parts in the code such as some arguments in the function ",(0,a.jsx)(t.code,{children:"read_manual"}),",\nit could be handled by the Planner. Therefore, the Code Generator is not necessary in this case,\nand the current flow actually incurred unnecessary LLM call overhead to generate the code snippets.\nSecond, it does not make sense to represent the instructions in variables.\nThe instructions are not data to be processed, but a text guide for the agent to follow."]}),"\n",(0,a.jsxs)(t.p,{children:["For these reasons, we introduced the concept of ",(0,a.jsx)(t.a,{href:"/docs/concepts/role",children:"roles"})," in TaskWeaver.\nRoles are actually not new in TaskWeaver as there are already roles like ",(0,a.jsx)(t.code,{children:"Planner"})," and ",(0,a.jsx)(t.code,{children:"CodeInterpreter"}),".\nTo add a new role, the developer can follow the documentation ",(0,a.jsx)(t.a,{href:"/docs/concepts/role",children:"here"}),".\nIn general, a role is a class that inherits the ",(0,a.jsx)(t.code,{children:"Role"})," class and implements the ",(0,a.jsx)(t.code,{children:"reply"})," method.\nThe ",(0,a.jsx)(t.code,{children:"reply"})," method is the function that the agent calls to interact with the role, which has the\nfollowing signature:"]}),"\n",(0,a.jsx)(t.pre,{children:(0,a.jsx)(t.code,{className:"language-python",children:"def reply(self, memory: Memory, **kwargs) -> Post:\n    # implementation\n"})}),"\n",(0,a.jsxs)(t.p,{children:["It takes the ",(0,a.jsx)(t.code,{children:"memory"})," object, which is the memory of the agent, and returns a ",(0,a.jsx)(t.a,{href:"/docs/concepts/post",children:"Post"})," object, which is the response of the role to the Planner.\nWith the ",(0,a.jsx)(t.code,{children:"memory"})," object, the role can access the history of the conversation and the context of the conversation.\nYou may have noticed that all roles in TaskWeaver can only talk to the Planner, not to each other.\nIf a role needs to talk to another role, it should go through the Planner.\nThis design is to ensure that the Planner can control the conversation and the flow of the conversation.\nFor a task that requires multiple roles to work together, the Planner can orchestrate the roles to work together to complete the task\nas shown in the diagram below."]}),"\n",(0,a.jsx)(t.mermaid,{value:'flowchart TD\n    A[User] --"request"--\x3e B[Planner]\n    subgraph TaskWeaver \n        B --"step 1"--\x3e C[Role 1]\n        C --reply--\x3e B\n        B --"step 2"--\x3e D[Role 2]\n        D --reply--\x3e B\n        B --"step 3"--\x3e E[Role 3]\n        E --reply--\x3e B\n    end\n    B --response--\x3e A'}),"\n",(0,a.jsxs)(t.p,{children:["The communication between the Planner and the roles is done through the ",(0,a.jsx)(t.a,{href:"/docs/concepts/post",children:"Post"})," object.\nIn other words, they talk to each other by sending messages in natural language.\nWhat if a role needs to send some data to another role? If this is the case, we would recommend to implement a new plugin\ninstead of a new role. Otherwise, you may need to store the data in an external storage like a database and let the other role to access it."]}),"\n",(0,a.jsxs)(t.p,{children:["There is a challenge in implementing multiple roles that is missing information.\nConsider the case in our previous example where the agent is asked to read a manual and follow the instructions to process the data.\nWhen the Planner obtains the instructions from a role called ",(0,a.jsx)(t.code,{children:"manual_reader"}),", it needs to pass the instructions to the CodeInterpreter role to execute the instructions.\nSometimes, the Planner may miss critical information that is needed by the CodeInterpreter role.\nEven though we can emphasize the importance of the Planner to pass all the necessary information to the roles in the prompt,\nit is still possible that the Planner misses some information."]}),"\n",(0,a.jsxs)(t.p,{children:["To address this challenge, we introduce the concept of ",(0,a.jsx)(t.code,{children:"board"})," in TaskWeaver.\nThe ",(0,a.jsx)(t.code,{children:"board"})," is a shared memory space that can be accessed by all roles, which is associated with the current ",(0,a.jsx)(t.a,{href:"/docs/concepts/round",children:"Round"}),".\nThe ",(0,a.jsx)(t.code,{children:"board"})," is a dictionary-like object that can store any information that is needed by the roles.\nEach role can decide to write or read any information from the ",(0,a.jsx)(t.code,{children:"board"}),"."]}),"\n",(0,a.jsx)(t.pre,{children:(0,a.jsx)(t.code,{className:"language-python",children:' def write_board(self, role_alias: str, bulletin: str) -> None:\n    """Add a bulletin to the round."""\n    self.board[role_alias] = bulletin\n\ndef read_board(self, role_alias: Optional[str] = None) -> Union[Dict[str, str], str]:\n    """Read the bulletin of the round."""\n    if role_alias is None:\n        return self.board\n    return self.board.get(role_alias, None)\n'})}),"\n",(0,a.jsxs)(t.p,{children:["One concrete example of using the ",(0,a.jsx)(t.code,{children:"board"})," is to pass the user's request to the CodeInterpreter role.\nWhen the Planner receives the user's request, it can write the request and its step-wise plan to the ",(0,a.jsx)(t.code,{children:"board"}),".\nThe CodeInterpreter role can then read the request and the plan from the ",(0,a.jsx)(t.code,{children:"board"})," to execute the plan."]}),"\n",(0,a.jsxs)(t.p,{children:["In summary, the concept of roles in TaskWeaver is to provide a way to extend the agent's capability by implementing new roles.\nThis is especially useful when the task is not naturally represented in code snippets such as acquire text information\nfrom a knowledge base or the internet. Implementing a new role is straightforward by inheriting the ",(0,a.jsx)(t.code,{children:"Role"})," class and implementing the ",(0,a.jsx)(t.code,{children:"reply"})," method.\nAll extra roles should be put in the ",(0,a.jsx)(t.code,{children:"TaskWeaver/taskweaver/ext_role"})," folder, which will be automatically loaded by TaskWeaver.\nWe have provided a few sample roles in the ",(0,a.jsx)(t.code,{children:"TaskWeaver/taskweaver/ext_role"})," folder, such as the ",(0,a.jsx)(t.code,{children:"Echo"})," role that echoes the user's message back to the user.\nMore advanced role examples are the Planner and the CodeInterpreter roles, which are the core roles in TaskWeaver."]})]})}function c(e={}){const{wrapper:t}={...(0,r.a)(),...e.components};return t?(0,a.jsx)(t,{...e,children:(0,a.jsx)(d,{...e})}):d(e)}},1151:(e,t,n)=>{n.d(t,{Z:()=>i,a:()=>s});var a=n(7294);const r={},o=a.createContext(r);function s(e){const t=a.useContext(o);return a.useMemo((function(){return"function"==typeof e?e(t):{...t,...e}}),[t,e])}function i(e){let t;return t=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:s(e.components),a.createElement(o.Provider,{value:t},e.children)}}}]);