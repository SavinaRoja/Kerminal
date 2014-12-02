Kerminal
========

Kerminal is a terminal user interface (TUI) for Kerbal Space Progam via the
Telemachus mod. With it you can view (and log) data regarding your craft's
status and the environment around it, as well as transmit instructions. Many
advanced features are on the horizon for Kerminal.

Kerminal interacts with the websocket server that Telemachus provides to provide
the interface; Kerminal thus inherits all of its features and limitations.
Terminal applications possess a different range of talents than browser
applications, so it will not make sense to try to make Kerminal to be a
text-based clone of the browser javascript interface, but rather it will evolve
a unique feature set.

Dependencies
------------

In order to use Kerminal, the following are **required**:

 * Kerbal Space Program must have the Telemachus mod installed in order to
   communicate with external programs (such as Kerminal).
 * Python 3.4 or higher
 * For windows users: as Cygwin does not support Python 3.4, install the curses
   unofficial binary for your system in order to use Kerminal.
 * The following Python modules: `npyscreen2`, `autobahn`, `docopt`

`npyscreen2` may be found at: https://github.com/SavinaRoja/npyscreen2

In order to utilize the MechJeb SmartASS commands available through Telemachus
you will need to also have the MechJeb mod installed. Kerminal should alert
you if MechJeb is not available on your craft.

