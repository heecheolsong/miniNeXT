#!/usr/bin/env python
'''@package topo

Network topology creation.

@author Brandon Heller (brandonh@stanford.edu)

This package includes code to represent network topologies.

A Topo object can be a topology database for NOX, can represent a physical
setup for testing, and can even be emulated with the Mininet package.
'''

from mininet.util import irange, natural, naturalSeq

class MultiGraph( object ):
    "Utility class to track nodes and edges - replaces networkx.Graph"

    def __init__( self ):
        self.data = {}

    def add_node( self, node ):
        "Add node to graph"
        self.data.setdefault( node, [] )

    def add_edge( self, src, dest ):
        "Add edge to graph"
        src, dest = sorted( ( src, dest ) )
        self.add_node( src )
        self.add_node( dest )
        self.data[ src ].append( dest )

    def nodes( self ):
        "Return list of graph nodes"
        return self.data.keys()

    def edges( self ):
        "Iterator: return graph edges"
        for src in self.data.keys():
            for dest in self.data[ src ]:
                yield ( src, dest )

    def __getitem__( self, node ):
        "Return link dict for the given node"
        return self.data[node]


class Topo(object):
    "Data center network representation for structured multi-trees."

    def __init__(self, hopts=None, sopts=None, lopts=None, lropts=None,
                 lsopts=None, tpropts=None, hiopts=None):
        """Topo object:
           hinfo:   default host options
           sopts:   default switch options
           lopts:   default link options
           lropts:  default legacy router options
           lsopts:  default legacy switch options
           tpropts: default transit portal router options
           hiopts:  default host interface options"""
        self.g = MultiGraph()
        self.node_info = {}
        self.link_info = {}  # (src, dst) tuples hash to EdgeInfo objects
        self.hopts = {} if hopts is None else hopts
        self.sopts = {} if sopts is None else sopts
        self.lopts = {} if lopts is None else lopts
        self.lropts = {} if lropts is None else lropts
        self.lsopts = {} if lsopts is None else lsopts
        self.tpropts = {} if tpropts is None else tpropts
        self.hiopts = {} if hiopts is None else hiopts
        self.ports = {}  # ports[src][dst] is port on src that connects to dst

    def addNode(self, name, **opts):
        """Add Node to graph.
           name: name
           opts: node options
           returns: node name"""
        self.g.add_node(name)
        self.node_info[name] = opts
        return name

    def addHost(self, name, **opts):
        """Convenience method: Add host to graph.
           name: host name
           opts: host options
           returns: host name"""
        if not opts and self.hopts:
            opts = self.hopts
        return self.addNode(name, isHost=True, **opts)

    def addSwitch(self, name, **opts):
        """Convenience method: Add switch to graph.
           name: switch name
           opts: switch options
           returns: switch name"""
        if not opts and self.sopts:
            opts = self.sopts
        result = self.addNode(name, isSwitch=True, **opts)
        return result

    def addLegacySwitch(self, name, **opts):
        """Convenience method: Add legacy switch (bridge) to graph.
           name: legacy switch name
           opts: legacy switch options
           returns: legacy switch name"""
        if not opts and self.lsopts:
            opts = self.lsopts
        result = self.addNode(name, isLegacySwitch=True, **opts)
        return result

    def addHostInterface(self, name, **opts):
        """Convenience method: Add host interface (bridge) to graph.
           name: host interface name
           opts: host interface options (physical interface to bridge to)
           returns: host interface name"""
        if not opts and self.hiopts:
            opts = self.hiopts
        result = self.addNode(name, isHostInterface=True, **opts)
        return result

    def addLegacyRouter(self, name, **opts):
        """Convenience method: Add legacy router to graph.
           name: legacy router name
           opts: legacy router options
           returns: legacy router name"""
        if not opts and self.lropts:
            opts = self.lropts
        result = self.addNode(name, isLegacyRouter=True, **opts)
        return result

    def addTransitPortalRouter(self, name, **opts):
        """Convenience method: Add Transit Portal router / endpoint to graph.
           name: TP router name
           opts: TP router options
           returns: TP router name"""
        if not opts and self.tpropts:
            opts = self.tpropts
        result = self.addNode(name, isTransitPortalRouter=True, **opts)
        return result

    def addLink(self, node1, node2, port1=None, port2=None,
                **opts):
        """node1, node2: nodes to link together
           port1, port2: ports (optional)
           opts: link options (optional)
           returns: link info key"""
        if not opts and self.lopts:
            opts = self.lopts
        self.addPort(node1, node2, port1, port2)
        key = tuple(self.sorted([node1, node2]))
        self.link_info[key] = opts
        self.g.add_edge(*key)
        return key

    def addPort(self, src, dst, sport=None, dport=None):
        '''Generate port mapping for new edge.
        @param src source switch name
        @param dst destination switch name
        '''
        self.ports.setdefault(src, {})
        self.ports.setdefault(dst, {})
        # New port: number of outlinks + base
        src_base = 1 if self.isSwitch(src) else 0
        dst_base = 1 if self.isSwitch(dst) else 0
        if sport is None:
            sport = len(self.ports[src]) + src_base
        if dport is None:
            dport = len(self.ports[dst]) + dst_base
        self.ports[src][dst] = sport
        self.ports[dst][src] = dport

    def nodes(self, sort=True):
        "Return nodes in graph"
        if sort:
            return self.sorted( self.g.nodes() )
        else:
            return self.g.nodes()

    def isHost(self, n):
        '''Returns true if node is a host.'''
        info = self.node_info[n]
        return info and info.get('isHost', False)

    def isSwitch(self, n):
        '''Returns true if node is a switch.'''
        info = self.node_info[n]
        return info and info.get('isSwitch', False)

    def isLegacySwitch(self, n):
        '''Returns true if node is a legacy switch.'''
        info = self.node_info[n]
        return info and info.get('isLegacySwitch', False)

    def isLegacyRouter(self, n):
        '''Returns true if node is a legacy router.'''
        info = self.node_info[n]
        return info and info.get('isLegacyRouter', False)

    def isTransitPortalRouter(self, n):
        '''Returns true if node is a Transit Portal router.'''
        info = self.node_info[n]
        return info and info.get('isTransitPortalRouter', False)

    def isHostInterface(self, n):
        '''Returns true if node is a host interface.'''
        info = self.node_info[n]
        return info and info.get('isHostInterface', False)

    def switches(self, sort=True):
        '''Return switches.
        sort: sort switches alphabetically
        @return dpids list of dpids
        '''
        return [n for n in self.nodes(sort) if self.isSwitch(n)]

    def legacySwitches(self, sort=True):
        '''Return legacy switches.
        sort: sort legacy switches alphabetically
        @return legacySwitches list of legacy switches
        '''
        return [n for n in self.nodes(sort) if self.isLegacySwitch(n)]

    def legacyRouters(self, sort=True):
        '''Return legacy routers.
        sort: sort legacy routers alphabetically
        @return legacyRouters list of legacy routers
        '''
        return [n for n in self.nodes(sort) if self.isLegacyRouter(n)]

    def transitPortalRouters(self, sort=True):
        '''Return legacy routers.
        sort: sort transit portal routers alphabetically
        @return tpRouters list of transit portal routers
        '''
        return [n for n in self.nodes(sort) if self.isTransitPortalRouter(n)]

    def hostInterfaces(self, sort=True):
        '''Return host interfaces.
        sort: sort host interfaces alphabetically
        @return interfaces list of host interfaces
        '''
        return [n for n in self.nodes(sort) if self.isHostInterface(n)]

    def hosts(self, sort=True):
        '''Return hosts.
        sort: sort hosts alphabetically
        @return hosts list of hosts
        '''
        return [n for n in self.nodes(sort) if self.isHost(n)]

    def links(self, sort=True):
        '''Return links.
        sort: sort links alphabetically
        @return links list of name pairs
        '''
        if not sort:
            return self.g.edges()
        else:
            links = [tuple(self.sorted(e)) for e in self.g.edges()]
            return sorted( links, key=naturalSeq )

    def port(self, src, dst):
        '''Get port number.

        @param src source switch name
        @param dst destination switch name
        @return tuple (src_port, dst_port):
            src_port: port on source switch leading to the destination switch
            dst_port: port on destination switch leading to the source switch
        '''
        if src in self.ports and dst in self.ports[src]:
            assert dst in self.ports and src in self.ports[dst]
            return (self.ports[src][dst], self.ports[dst][src])

    def linkInfo( self, src, dst ):
        "Return link metadata"
        src, dst = self.sorted([src, dst])
        return self.link_info[(src, dst)]

    def setlinkInfo( self, src, dst, info ):
        "Set link metadata"
        src, dst = self.sorted([src, dst])
        self.link_info[(src, dst)] = info

    def nodeInfo( self, name ):
        "Return metadata (dict) for node"
        info = self.node_info[ name ]
        return info if info is not None else {}

    def setNodeInfo( self, name, info ):
        "Set metadata (dict) for node"
        self.node_info[ name ] = info

    @staticmethod
    def sorted( items ):
        "Items sorted in natural (i.e. alphabetical) order"
        return sorted(items, key=natural)

class SingleSwitchTopo(Topo):
    '''Single switch connected to k hosts.'''

    def __init__(self, k=2, **opts):
        '''Init.

        @param k number of hosts
        @param enable_all enables all nodes and switches?
        '''
        super(SingleSwitchTopo, self).__init__(**opts)

        self.k = k

        switch = self.addSwitch('s1')
        for h in irange(1, k):
            host = self.addHost('h%s' % h)
            self.addLink(host, switch)


class SingleSwitchReversedTopo(Topo):
    '''Single switch connected to k hosts, with reversed ports.

    The lowest-numbered host is connected to the highest-numbered port.

    Useful to verify that Mininet properly handles custom port numberings.
    '''
    def __init__(self, k=2, **opts):
        '''Init.

        @param k number of hosts
        @param enable_all enables all nodes and switches?
        '''
        super(SingleSwitchReversedTopo, self).__init__(**opts)
        self.k = k
        switch = self.addSwitch('s1')
        for h in irange(1, k):
            host = self.addHost('h%s' % h)
            self.addLink(host, switch,
                         port1=0, port2=(k - h + 1))

class LinearTopo(Topo):
    "Linear topology of k switches, with n hosts per switch."

    def __init__(self, k=2, n=1, **opts):
        """Init.
           k: number of switches
           n: number of hosts per switch
           hconf: host configuration options
           lconf: link configuration options"""

        super(LinearTopo, self).__init__(**opts)

        self.k = k
        self.n = n

        if n == 1:
            genHostName = lambda i, j: 'h%s' % i
        else:
            genHostName = lambda i, j: 'h%ss%d' % (j, i)


        lastSwitch = None
        for i in irange(1, k):
            # Add switch
            switch = self.addSwitch('s%s' % i)
            # Add hosts to switch
            for j in irange(1, n):
                host = self.addHost(genHostName(i, j))
                self.addLink(host, switch)
            # Connect switch to previous
            if lastSwitch:
                self.addLink(switch, lastSwitch)
            lastSwitch = switch
