/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-nocheck

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // By default, Docusaurus generates a sidebar from the docs folder structure
  // tutorialSidebar: [{type: 'autogenerated', dirName: '.'}],

  // But you can create a sidebar manually
  
  documentSidebar: [
    'overview',
    'quickstart',    
    {
      type: 'category',
      label: 'Usage Options',
      link: {
        type: 'generated-index',
        title: 'Usage Options',
        description: 'Learn how to run TaskWeaver in different ways',
        slug: '/usage',
      },
      collapsible: true,
      collapsed: false,
      items: [
        'usage/cmd',
        'usage/webui',
        'usage/library'],
    },
    {
      type: 'category',
      label: 'Supported LLMs',
      link: {
        type: 'generated-index',
        title: 'LLMs',
        description: 'Learn how to call models from different LLMs',
        slug: '/llms',
      },
      collapsible: true,
      collapsed: true,
      items: ['llms/openai', 'llms/aoai', 'llms/liteLLM', 'llms/ollama', 'llms/gemini', 'llms/qwen', 'llms/glm', 'llms/customized_llm_api', 'llms/multi-llm'],
    },
    {
      type: 'category',
      label: 'Configurations',
      link: {
        type: 'generated-index',
        title: 'LLMs',
        description: 'Learn about TaskWeaver configurations',
        slug: 'advanced',
      },
      collapsible: true,
      collapsed: false,
      items: ['configurations/overview', 'configurations/configurations_in_detail' ],// 'configurations/planner', 'configurations/session', 'configurations/embedding'
    },
    {
      type: 'category',
      label: 'Customization',
      link: {
        type: 'generated-index',
        title: 'LLMs',
        description: 'Learn how to customize TaskWeaver',
        slug: 'customization',
      },
      collapsible: true,
      collapsed: false,
      items: [{
        type: 'category',
        label: 'Plugin',
        collapsible: true,
        collapsed: true,
        items: ['customization/plugin/plugin_intro', 'customization/plugin/plugin_selection', 'customization/plugin/develop_plugin', 'customization/plugin/multi_yaml_single_impl', 'customization/plugin/plugin_only'],
      },
      {
        type: 'category',
        label: 'Example',
        collapsible: true,
        collapsed: true,
        items: ['customization/example/example'],
      },
      {
        type: 'category',
        label: 'Experience',
        collapsible: true,
        collapsed: true,
        items: ['customization/experience'],
      },
    ],
    },
    {
      type: 'category',
      label: 'Advanced Features',
      // link: {
      //   type: 'generated-index',
      //   title: 'LLMs',
      //   description: 'Learn about the advanced features of TaskWeaver',
      //   slug: 'advanced',
      // },
      collapsible: true,
      collapsed: false,
      items: ['advanced/compression', 'advanced/code_verification', 'advanced/code_execution', 'advanced/cli_only', 'advanced/telemetry'],
    },
    // 'example',
    'FAQ'
  ],
  
};

export default sidebars;
