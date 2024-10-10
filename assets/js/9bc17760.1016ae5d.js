"use strict";(self.webpackChunkwebsite=self.webpackChunkwebsite||[]).push([[6302],{254:(e,n,l)=>{l.r(n),l.d(n,{assets:()=>r,contentTitle:()=>s,default:()=>h,frontMatter:()=>t,metadata:()=>d,toc:()=>c});var o=l(4848),i=l(8453);const t={id:"plugin_only",description:"The Plugin Only Mode",slug:"/plugin/plugin_only"},s="The Plugin-Only Mode",d={id:"advanced/plugin_only",title:"The Plugin-Only Mode",description:"The Plugin Only Mode",source:"@site/docs/advanced/plugin_only.md",sourceDirName:"advanced",slug:"/plugin/plugin_only",permalink:"/TaskWeaver/docs/plugin/plugin_only",draft:!1,unlisted:!1,editUrl:"https://github.com/microsoft/TaskWeaver/tree/main/website/docs/advanced/plugin_only.md",tags:[],version:"current",frontMatter:{id:"plugin_only",description:"The Plugin Only Mode",slug:"/plugin/plugin_only"},sidebar:"documentSidebar",previous:{title:"Telemetry",permalink:"/TaskWeaver/docs/advanced/telemetry"}},r={},c=[{value:"What is the plugin-only mode?",id:"what-is-the-plugin-only-mode",level:2},{value:"How is the plugin-only mode implemented?",id:"how-is-the-plugin-only-mode-implemented",level:2},{value:"Which models support the plugin-only mode?",id:"which-models-support-the-plugin-only-mode",level:2}];function a(e){const n={a:"a",admonition:"admonition",code:"code",h1:"h1",h2:"h2",header:"header",li:"li",ol:"ol",p:"p",pre:"pre",ul:"ul",...(0,i.R)(),...e.components};return(0,o.jsxs)(o.Fragment,{children:[(0,o.jsx)(n.header,{children:(0,o.jsx)(n.h1,{id:"the-plugin-only-mode",children:"The Plugin-Only Mode"})}),"\n",(0,o.jsx)(n.h2,{id:"what-is-the-plugin-only-mode",children:"What is the plugin-only mode?"}),"\n",(0,o.jsx)(n.p,{children:"The plugin-only mode is a restricted mode of TaskWeaver that only allows you to use plugins.\nCompared to the full mode, the plugin-only mode has the following restrictions:"}),"\n",(0,o.jsxs)(n.ol,{children:["\n",(0,o.jsxs)(n.li,{children:["\n",(0,o.jsxs)(n.p,{children:["The generated code only contains the calls to the plugins.\nFor example, the following code only calls the ",(0,o.jsx)(n.code,{children:"ascii_render"}),' plugin and does not contain any "free-form" code.']}),"\n",(0,o.jsx)(n.pre,{children:(0,o.jsx)(n.code,{className:"language-python",children:'r1=ascii_render(**{"text":"Hello"})\nr1\n'})}),"\n"]}),"\n",(0,o.jsxs)(n.li,{children:["\n",(0,o.jsxs)(n.p,{children:["Only the plugins with ",(0,o.jsx)(n.code,{children:"plugin_only: true"})," in the yaml file will be loaded.\nFor example, the following plugin will be loaded in the plugin-only mode:"]}),"\n",(0,o.jsx)(n.pre,{children:(0,o.jsx)(n.code,{className:"language-yaml",children:"name: ascii_render\nplugin_only: true\n...\n"})}),"\n",(0,o.jsxs)(n.p,{children:["If this field is not specified, the default value is ",(0,o.jsx)(n.code,{children:"false"}),".\nFor plugins in the plugin-only mode, the argument type can only be ",(0,o.jsx)(n.code,{children:"str"}),", ",(0,o.jsx)(n.code,{children:"int"}),", ",(0,o.jsx)(n.code,{children:"boolean"}),", or ",(0,o.jsx)(n.code,{children:"float"}),".\nOther types such as ",(0,o.jsx)(n.code,{children:"DataFrame"}),' are not allowed.\nEssentially, we consider these plugins only produce "text-like" output that can be directly consumed by the LLM.']}),"\n"]}),"\n"]}),"\n",(0,o.jsxs)(n.p,{children:["To support the plugin-only mode, we developed a new role called ",(0,o.jsx)(n.code,{children:"PluginOrchestrator"}),".\nTo enable the plugin-only mode, you can add the configuration ",(0,o.jsx)(n.code,{children:'"session.roles": ["planner", "code_interpreter_plugin_only"]'}),"\nin the project configuration file ",(0,o.jsx)(n.code,{children:"taskweaver_config.json"}),"."]}),"\n",(0,o.jsx)(n.admonition,{type:"info",children:(0,o.jsx)(n.p,{children:"Although the plugin-only mode is restricted, it is still useful in some scenarios.\nFor example, you may want to use TaskWeaver to only generate the code to call a certain plugin,\nand you want to get the response from the plugin directly, without generating any other code\nfor safety reasons."})}),"\n",(0,o.jsx)(n.h2,{id:"how-is-the-plugin-only-mode-implemented",children:"How is the plugin-only mode implemented?"}),"\n",(0,o.jsxs)(n.p,{children:["The plugin-only mode is implemented based on the ",(0,o.jsx)(n.a,{href:"https://platform.openai.com/docs/guides/function-calling",children:"function calling"})," mode of LLMs.\nIn this mode, the LLM is trained to generate a JSON object that contains the function name and the arguments.\nFor example, the following JSON object is generated by the LLM:"]}),"\n",(0,o.jsx)(n.pre,{children:(0,o.jsx)(n.code,{className:"language-json",children:'{\n  "function": "ascii_render",\n  "arguments": {\n    "text": "Hello"\n  }\n}\n'})}),"\n",(0,o.jsx)(n.p,{children:"With this JSON object, we assemble the code to call the plugin:"}),"\n",(0,o.jsx)(n.pre,{children:(0,o.jsx)(n.code,{className:"language-python",children:'r1=ascii_render(**{"text":"Hello"})\nr1\n'})}),"\n",(0,o.jsx)(n.p,{children:"Then, we execute the code and get the response from the plugin.\nTherefore, the code is not directly generated by the LLM in the plugin-only mode."}),"\n",(0,o.jsx)(n.h2,{id:"which-models-support-the-plugin-only-mode",children:"Which models support the plugin-only mode?"}),"\n",(0,o.jsx)(n.p,{children:"Currently, the plugin-only mode is only supported by"}),"\n",(0,o.jsxs)(n.ul,{children:["\n",(0,o.jsx)(n.li,{children:(0,o.jsx)(n.a,{href:"https://platform.openai.com/docs/guides/function-calling",children:"OpenAI models"})}),"\n",(0,o.jsx)(n.li,{children:(0,o.jsx)(n.a,{href:"https://open.bigmodel.cn/dev/api",children:"ZhipuAI models"})}),"\n"]}),"\n",(0,o.jsx)(n.p,{children:"Likely other models that are compatible with the OpenAI models will also support the plugin-only mode."})]})}function h(e={}){const{wrapper:n}={...(0,i.R)(),...e.components};return n?(0,o.jsx)(n,{...e,children:(0,o.jsx)(a,{...e})}):a(e)}},8453:(e,n,l)=>{l.d(n,{R:()=>s,x:()=>d});var o=l(6540);const i={},t=o.createContext(i);function s(e){const n=o.useContext(t);return o.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function d(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(i):e.components||i:s(e.components),o.createElement(t.Provider,{value:n},e.children)}}}]);