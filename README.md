ReverseTCP
==========

Provides a simple tunnelling in order to access services behind a firewall (just like reverse ssh). 

It is PyQt4 implementation

Let's set an example :
-----

### Description of the 'remote side' : 
 * It is a host we want to access, but it is behind a firewall and is not publicly accessible 
 * Let's give it the hostname `remote` 
 * Let's say we want to access it via ssh on port 22

### Description of the 'local side' : 
 * It is a host publicly accessible (at least one port)
 * Let's give it the hostname `local`
 * Let's say it is publicly accessible as `local.localdomain.net` on port 3232
 * We will want to access the remote side on local 3235 port

### Run on the 'remote side' : 
    ./ReverseTCP.py -r -R 3235:remote:22 -p 3232 local.localdomain.net

### Run on the 'local side' : 
    ./ReverseTCP.py -l -R 3235 -p 3232 
    ssh -p 3235 localhost

### More simple for the 'local side': 
    ./ReverseTCP.py -l -R 3235:remote:22 -p 3232 local.localdomain.net
    ssh -p 3235 localhost
Man can use the exact same command line (except -l/-r). Extra informations are ignored...
    
Beware that this is much less secure than reverse ssh, but it is much easier to use (especially when using Windows as local side, because installing a ssh server on Windows is quite hard...). It has not been tested on Windows yet, but as it is PyQt, it should work just fine !

TODO (future evolutions) :
-----
 * Add a little protocol for auto configuration on local side
 * crypto (ssl sockets) for security
 * Support of multiple remote sides on local side (it may be already the case)
 * Maybe more protocol : 
  * Remote : send id/description, no conf for local port (only listen on local side, just like ssh)
  * Local : get the id/description, auto allocate local random port
  * Local : generate a webpage for visualization of remote sides and get descriptions and urls. 
