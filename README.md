## Domain Switch

cross-platform Domain Switcher for fast workspace setup and restore, compiled with Qt5.

### Structure

(GUI --->) Operator ---> ops_collection ---> ops_base

* ***ops_base*** ; for virtual ops interface.
* ***ops_collection, ops for software***; for collection of multi-PCS implementation and registry.
* ***Operator, ops for domain*** ; for user interaction over CLi, and API for GUI.

P.S. PCS, Platform\*Category\*Software

### Functions

1. **Setup** a new *domamin*,  **Restore**/**Rename**/**Delete** an existing *domain*
   * **Setup**: **Sense** the *software* supported, **Save** the {size, pose, contents (webpages, files)} to the *workspace*
   * **Restore**: **Load** the saved profile, restore the software based on certain *ops*
2. **ops** with platform depending prefix, compiled under compiling-definition.


###TODO

- Registry implementation, with ID indexed
- Setup *profile* format & *workspace* structure
- Test scripts
- Shell scripts & keyboard shorcuts boding for fast switch
- GUI for convinient operation
- Cross-platform support