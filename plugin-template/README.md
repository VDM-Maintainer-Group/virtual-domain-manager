# Plugin Development Norm

Design Pricinple, **PCS**, Platform\*Category\*Software

## API and Wrapper

A plugin should address its **category** and implement the API. The framework will call plugin through APIs with some environment parameters. Here follows the **API table**:

| API NAME  |               DESCRIPTION                |
| :-------: | :--------------------------------------: |
|   init    | Execute once the plugin is loaded, import your modules and setup environment here. |
|  onSave   | Execute when to **save** current domain  |
| onResume  | Execute when to **restore** current domain |
|  onExit   | Execute when to **close** current domain |
| onTrigger | Execute when user manually call this plugin |
| onDaemon  | Executed in manager-daemon (not to implement yet) |

For **different categories** of plugin, diffenrent wrapped python modules and built-in functions are provided. Here follows the **category table**:

| CATEGORY | WRAPPED FUNCTION |
| :------: | :--------------: |
|  System  |  (placeholder)   |
|  Editor  |  (placeholder)   |
| Browser  |  (placeholder)   |



## Develop Procedure

1. workspace init: use `npm init` for convinient, or copy the `package.json` and modify.
2. (todo)
