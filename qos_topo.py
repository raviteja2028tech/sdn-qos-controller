from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink

def qos_topology():
    net = Mininet(controller=RemoteController,
                  switch=OVSSwitch,
                  link=TCLink)

    c0 = net.addController('c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           port=6633)

    s1 = net.addSwitch('s1')

    h1 = net.addHost('h1', ip='10.0.0.1')  # Video - high priority
    h2 = net.addHost('h2', ip='10.0.0.2')  # VoIP  - high priority
    h3 = net.addHost('h3', ip='10.0.0.3')  # HTTP  - low priority
    h4 = net.addHost('h4', ip='10.0.0.4')  # FTP   - low priority

    net.addLink(h1, s1, bw=10)
    net.addLink(h2, s1, bw=10)
    net.addLink(h3, s1, bw=10)
    net.addLink(h4, s1, bw=10)

    net.start()
    print("*** QoS topology running")
    print("*** h1=video, h2=voip, h3=http, h4=ftp")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    qos_topology()
