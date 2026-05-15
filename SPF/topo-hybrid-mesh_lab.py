#!/usr/bin/env python3
"""Hybrid mesh topology for SPF routing experiments.

This topology is designed for Dijkstra, BFS, and Bellman-Ford experiments.
It features redundant inter-switch links and multiple alternate paths, so
SPF routing can be observed under normal operation, bottleneck stress,
and link-failure conditions.

Topology:
    h1    h2
     |     |
     s1----s2
      \   / |
       s3-- | \
        | \ |  \
        |  s5---s6
        |  |  \  |
       s4----+  |
       |      \ |
       h3      h4

Host attachments:
    h1 -> s1
    h2 -> s1
    h3 -> s4
    h4 -> s6

Switch links:
    s1 <-> s2
    s1 <-> s3
    s2 <-> s3
    s2 <-> s4
    s2 <-> s5
    s3 <-> s5
    s3 <-> s6
    s4 <-> s5
    s5 <-> s6

All links use TCLink with 100 Mbps and 2 ms delay.
"""

from functools import partial

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class HybridMeshTopo(Topo):
    """Hybrid mesh topology for SPF and redundancy experiments."""

    def addSwitch(self, name, **opts):
        kwargs = {"protocols": "OpenFlow10,OpenFlow13"}
        kwargs.update(opts)
        return super(HybridMeshTopo, self).addSwitch(name, **kwargs)

    def __init__(self):
        Topo.__init__(self)

        info('*** Adding hosts\n')
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')

        info('*** Adding switches\n')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')

        info('*** Adding host links\n')
        self.addLink(s1, h1, port1=1, port2=1)
        self.addLink(s1, h2, port1=2, port2=1)
        self.addLink(s4, h3, port1=1, port2=1)
        self.addLink(s6, h4, port1=1, port2=1)

        info('*** Adding inter-switch links\n')
        self.addLink(s1, s2, port1=3, port2=1, bw=100, delay='2ms', use_hfsc=True)
        self.addLink(s1, s3, port1=4, port2=1, bw=100, delay='2ms', use_hfsc=True)
        self.addLink(s2, s3, port1=2, port2=2, bw=100, delay='2ms', use_hfsc=True)
        self.addLink(s2, s4, port1=3, port2=2, bw=100, delay='2ms', use_hfsc=True)
        self.addLink(s2, s5, port1=4, port2=1, bw=100, delay='2ms', use_hfsc=True)
        self.addLink(s3, s5, port1=3, port2=2, bw=100, delay='2ms', use_hfsc=True)
        self.addLink(s3, s6, port1=4, port2=2, bw=100, delay='2ms', use_hfsc=True)
        self.addLink(s4, s5, port1=3, port2=3, bw=100, delay='2ms', use_hfsc=True)
        self.addLink(s5, s6, port1=4, port2=3, bw=100, delay='2ms', use_hfsc=True)


def run():
    topo = HybridMeshTopo()
    net = Mininet(
        topo=topo,
        controller=partial(RemoteController, ip='127.0.0.1', port=6633),
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True,
        waitConnected=True,
    )

    net.start()

    info('*** Dumping host connections\n')
    dumpNodeConnections(net.hosts)

    info('*** Testing network connectivity\n')
    net.pingAll()

    info('*** Starting CLI\n')
    CLI(net)

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
