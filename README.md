\# SDN QoS Priority Controller



\## Problem Statement



Implement an SDN-based QoS (Quality of Service) solution using Mininet and Ryu SDN controller that prioritizes delay-sensitive traffic (Video, VoIP) over best-effort traffic (HTTP, FTP) using OpenFlow flow rules and queue-based scheduling. The system demonstrates measurable differences in network performance.



\---



\## Tools and Technologies



\* Ubuntu 24.04 (VirtualBox VM)

\* Mininet 2.3.0

\* Ryu Controller 4.34

\* OpenFlow 1.3

\* Open vSwitch (OVS)

\* iperf, ping, ovs-ofctl



\---



\## Network Topology



Single switch topology with 4 hosts controlled by a remote Ryu controller:



h1 (10.0.0.1) ---+

h2 (10.0.0.2) ---+--- s1 (OVS Switch) --- Ryu Controller

h3 (10.0.0.3) ---+

h4 (10.0.0.4) ---+



\### Traffic Classification



\* h1 → Video traffic (RTP, port 5004) → HIGH priority

\* h2 → VoIP traffic (SIP, port 5060) → HIGH priority

\* h3 → HTTP traffic (port 80) → LOW priority

\* h4 → FTP traffic (port 21) → LOW priority



\---



\## QoS Flow Rule Design



| Traffic Type | Protocol | Port | OpenFlow Priority | Queue | Action                    |

| ------------ | -------- | ---- | ----------------- | ----- | ------------------------- |

| RTP/Video    | UDP      | 5004 | 200               | 1     | Forward (high priority)   |

| SIP/VoIP     | UDP/TCP  | 5060 | 200               | 1     | Forward (high priority)   |

| HTTP         | TCP      | 80   | 100               | 0     | Forward (normal priority) |

| FTP          | TCP      | 21   | 100               | 0     | Forward (normal priority) |



\---



\## Queue Configuration (QoS Setup)



Queues are configured in Open vSwitch to enforce bandwidth-based prioritization:



```bash

sudo ovs-vsctl set port s1-eth1 qos=@newqos \\

\-- --id=@newqos create QoS type=linux-htb other-config:max-rate=10000000 \\

queues=0=@q0,1=@q1 \\

\-- --id=@q0 create Queue other-config:max-rate=5000000 \\

\-- --id=@q1 create Queue other-config:max-rate=8000000

```



\* Queue 1 → High priority (Video, VoIP)

\* Queue 0 → Normal priority (HTTP, FTP)



\---



\## Controller–Switch Interaction



1\. Switch connects to the Ryu controller.

2\. A table-miss rule sends unknown packets to the controller (packet\_in event).

3\. The controller inspects packet fields (IP protocol, destination port).

4\. Based on traffic type, a matching QoS rule is selected.

5\. The controller installs a flow rule in the switch with:



&#x20;  \* Match fields (protocol + port)

&#x20;  \* Action (forward)

&#x20;  \* Queue assignment (set\_queue)

&#x20;  \* Priority value



\---



\## Setup and Installation



\### Prerequisites



\* Ubuntu 20.04 / 22.04 / 24.04

\* VirtualBox / VMware



\### Step 1 - Install Mininet



```bash

sudo apt update

sudo apt install mininet python3-pip python3-venv -y

```



\### Step 2 - Install Ryu Controller



```bash

python3 -m venv \~/ryu-env

source \~/ryu-env/bin/activate

pip install setuptools==67.6.0

pip install eventlet==0.35.2

pip install ryu

```



(Optional fix for compatibility)



```bash

sed -i 's/from eventlet.wsgi import ALREADY\_HANDLED/ALREADY\_HANDLED = b""/' \\

\~/ryu-env/lib/python3.12/site-packages/ryu/app/wsgi.py

```



\### Step 3 - Verify Installation



```bash

ryu-manager --version

sudo mn --test pingall

```



\---



\## How to Run



\### Terminal 1 - Start Ryu Controller



```bash

source \~/ryu-env/bin/activate

ryu-manager qos\_controller.py

```



\### Terminal 2 - Start Mininet Topology



```bash

sudo python3 qos\_topo.py

```



\---



\## Test Scenarios and Expected Output



\### Scenario 1 - Basic Connectivity



```bash

mininet> pingall

```



Expected result: All hosts can communicate successfully with 0% packet loss.



\---



\### Scenario 2 - Flow Table Verification



```bash

mininet> sh ovs-ofctl dump-flows s1

```



Expected result:



\* High priority flows (priority=200) for Video and VoIP

\* Normal flows (priority=100) for HTTP and FTP

\* Queue assignment visible in actions



\---



\### Scenario 3 - Throughput Measurement (iperf)



```bash

mininet> h1 iperf -s \&

mininet> h3 iperf -c 10.0.0.1 -t 5

```



Expected result:

High priority traffic achieves better throughput compared to low priority traffic, especially under network congestion.



\---



\### Scenario 4 - Latency Measurement (ping)



```bash

mininet> h1 ping -c 5 h3

mininet> h2 ping -c 5 h4

```



Expected result:

High priority traffic experiences lower delay compared to low priority traffic under congestion.



\---



\## Proof of Execution



Screenshots included:



\* Ryu controller running

\* Mininet topology execution

\* pingall output (0% loss)

\* ovs-ofctl flow table

\* iperf throughput comparison

\* ping latency comparison



\---



\## SDN Controller Logic



The Ryu controller performs:



1\. \*\*Switch Initialization\*\*



&#x20;  \* Installs default rules and prepares flow table



2\. \*\*Packet Handling\*\*



&#x20;  \* Handles packet\_in events for unknown packets



3\. \*\*Traffic Classification\*\*



&#x20;  \* Matches based on:



&#x20;    \* IP protocol (TCP/UDP)

&#x20;    \* Destination port



4\. \*\*Flow Rule Installation\*\*



&#x20;  \* Applies match-action rules

&#x20;  \* Assigns priority levels (200 vs 100)

&#x20;  \* Uses set\_queue action for QoS enforcement



\---



\## Key Observation



The QoS mechanism ensures that delay-sensitive applications (VoIP, Video) receive higher bandwidth and lower latency compared to best-effort traffic (HTTP, FTP), especially during network congestion.



\---



\## Cleanup



```bash

sudo mn -c

```



\---



\## References



1\. Mininet Documentation - http://mininet.org

2\. Ryu SDN Framework - https://ryu-sdn.org

3\. OpenFlow 1.3 Specification - https://opennetworking.org

4\. PES University UE24CS252B Computer Networks Lab



