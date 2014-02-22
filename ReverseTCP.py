#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtNetwork
import sys
import gc
import argparse

def debug(o):
  print o

class SocketMerger(QtCore.QObject):
  """
    Class used to "merge" two sockets together
  """
  disconnected = QtCore.pyqtSignal()
  def __init__(self, parent = None):
    """
      Constructor
        Basically does nothing...
    """
    QtCore.QObject.__init__(self, parent)
    self.worker1 = None
    self.worker2 = None
    self.socket1 = None
    self.socket2 = None
    
  def tryWrite(self, source, dest):
    """
      Try to write data from source to dest
    """
    if source.waitForReadyRead(1):
        while source.bytesAvailable() > 0:
          dest.write(source.read(source.bytesAvailable()))
          
  def tryClose(self, socket):
    """
      Close the socket if needed
    """
    if self.socketConnected(socket):
      socket.close()
    pass
  
  def mergeSockets(self, socket1, socket2):
    """
      Try to write data from a socket to the other while they are connected
    """
    debug("Merging...")
    self.socket1 = socket1
    self.socket2 = socket2
    while self.socketConnected(self.socket1) and self.socketConnected(self.socket2):
      self.tryWrite(self.socket2, self.socket1)
      self.tryWrite(self.socket1, self.socket2)
    self.tryClose(self.socket1)
    self.tryClose(self.socket2)
    debug("Merge finished")
    self.disconnected.emit()

  def socketConnected(self, socket):
    """
      check if the socket is connected or not
    """
    return socket.state() == QtNetwork.QAbstractSocket.ConnectedState or socket.state() == QtNetwork.QAbstractSocket.BoundState

class Local(QtCore.QObject):
  """
    Class used on the local side (say the host that can be accessed from anywhere)
  """
  def __init__(self, remote_port, local_port, parent = None):
    """
      Constructor
    """
    QtCore.QObject.__init__(self, parent)
    self.remote_port = remote_port
    self.local_port = local_port
    self.remote_server = QtNetwork.QTcpServer(self)
    self.local_server = QtNetwork.QTcpServer(self)
    self.merger = SocketMerger(self)
    self.remote_socket = None
    self.local_socket = None

    self.remote_server.newConnection.connect(self.remoteConnection, QtCore.Qt.QueuedConnection)
    self.local_server.newConnection.connect(self.localConnection, QtCore.Qt.QueuedConnection)
    self.merger.disconnected.connect(self.run, QtCore.Qt.QueuedConnection)
    pass

  def remoteConnection(self):
    """
      Slot called when a connection comes from remote
    """
    debug("Remote connection on %d"%(self.remote_port))
    self.remote_socket = self.remote_server.nextPendingConnection()
    self.checkRun()
    pass

  def localConnection(self):
    """
      Slot called when a connection comes from local
    """
    debug("Local connection on %d"%(self.local_port))
    self.local_socket = self.local_server.nextPendingConnection()
    if not self.remote_server.isListening():
      self.remote_server.listen(QtNetwork.QHostAddress.Any, self.remote_port)
    self.checkRun()
    pass

  def checkRun(self):
    """
      Merge the two sockets if both are available
    """
    if not self.remote_socket is None and not self.local_socket is None:
      self.merger.mergeSockets(self.remote_socket, self.local_socket)
      del self.remote_socket
      del self.local_socket
      self.remote_socket = None
      self.local_socket = None

    pass

  def run(self):
    """
      Main method that starts listening on ports
    """
    gc.collect()
    if self.remote_server.isListening():
      self.remote_server.close()
    if self.local_server.isListening():
      self.local_server.close()
    self.local_server.listen(QtNetwork.QHostAddress.Any, self.local_port)
    pass
  
class Remote(QtCore.QObject):
  """
    Class used on the side side (say the host that is behind a firewall)
  """
  def __init__(self, remote_hostname, remote_port, local_hostname, local_port, parent = None):
    """
      Constructor
    """
    QtCore.QObject.__init__(self, parent)
    self.remote_hostname = remote_hostname
    self.remote_port = remote_port
    self.local_hostname = local_hostname
    self.local_port = local_port
    self.merger = SocketMerger(self)
    self.remote_socket = None
    self.local_socket = None

    pass

  def connectSocket(self, socket, hostname, port):
    """
      Connect the socket on givent hostname and port
    """
    debug("Connecting to %s:%d"%(hostname, port))
    while not socket.waitForConnected():
      socket.connectToHost(hostname, port)

  def run(self):
    """
      Main method that connects sockets on both sides and "merge" them
    """
    while True:
      if not self.remote_socket is None:
        del self.remote_socket
      if not self.local_socket is None:
        del self.local_socket
      self.remote_socket = QtNetwork.QTcpSocket(self)
      self.local_socket = QtNetwork.QTcpSocket(self)
      #connect to remote
      self.connectSocket(self.remote_socket, self.remote_hostname, self.remote_port)
      #Connect to local only when remote is connected
      self.connectSocket(self.local_socket, self.local_hostname, self.local_port)
      #plug them together...
      self.merger.mergeSockets(self.local_socket, self.remote_socket)
      gc.collect()
    pass

def parse_config_file(config_file):
  pass

class ReverseStringAction(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):
    tmp = values.split(":")
    setattr(namespace, "local_local_port", int(tmp[0]))
    if len(tmp) > 1:
      setattr(namespace, "remote_local_hostname", tmp[1])
      setattr(namespace, "remote_local_port", int(tmp[2]))
    #print '%r' % (namespace)
    
def main():
  app = QtCore.QCoreApplication(sys.argv)
  parser = argparse.ArgumentParser(
                description="Create a reverse tcp connection. The 'remote side' is behind a firewall and the 'local side' is publicly accessible",
                epilog='Use the exact same command line arguments on both remote and local side, except -l and -r. '
                      )
  
  remote_local = parser.add_mutually_exclusive_group(required=True)
  remote_local.add_argument("-l", "--local", help="Set local mode", action="store_true")
  remote_local.add_argument("-r", "--remote", help="Set remote mode", action="store_true")

  #parser.add_argument("-c", "--config_file", help="Load the given config file")

  args = parser.add_argument_group()
  
  args.add_argument("-p", "--port", metavar="port", dest="access_port", type=int, help="For remote side, which port to connect to local. For local side, publicly accessible port where to listen for remote connection. ")
  args.add_argument("-R", "--reverse-string", metavar="port:host:hostport", action=ReverseStringAction, help="The same as reverse ssh : port 'port' of the local side will be connected on port 'hostport' of host 'host' on the remote side")
  args.add_argument("hostname", nargs='?', help="For remote side, the host to connect to. Ignored on local side")
  
  arguments = parser.parse_args()

  if arguments.local:
    obj = Local(arguments.access_port, arguments.local_local_port)
    pass
  elif arguments.remote:
    obj = Remote(arguments.hostname, arguments.access_port, arguments.remote_local_hostname, arguments.remote_local_port)
    pass
  obj.run()
  sys.exit(app.exec_())
  pass

if __name__ == "__main__":
  main()
