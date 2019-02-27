## Fullscreen Overlay

VDM needs a *virtual desktop* to differ from the original desktop, which is called the *overlay*.

The *display, switch and manage* functions are displayed on this overlay to replace the default GUI version of VDM, to provide immersive experience.

### API
* theme change
    ```C
    setBackground(color, opacity, isBlurred); // (optional with dde glass blur effect)
    drawPromptArea(const *painter);
    setPromptAreaSize(anchor, height, width, isFullscreen);
    ```
* callback function, then perform the switch process
    ```C
    backgroundLoaded(*func);
    workspaceLoading(*func);
    ```
