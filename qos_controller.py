from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp

class QoSController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    HIGH_PRIORITY_PORTS = {
        5004: 'RTP/Video',
        5060: 'SIP/VoIP',
    }
    LOW_PRIORITY_PORTS = {
        80:  'HTTP',
        21:  'FTP',
    }

    def __init__(self, *args, **kwargs):
        super(QoSController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto  = datapath.ofproto
        parser   = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        for port, name in self.HIGH_PRIORITY_PORTS.items():
            self._install_qos_rule(datapath, port, priority=200,
                                   queue_id=1, label=name)

        for port, name in self.LOW_PRIORITY_PORTS.items():
            self._install_qos_rule(datapath, port, priority=100,
                                   queue_id=0, label=name)

        self.logger.info("QoS rules installed on switch %s", datapath.id)

    def _install_qos_rule(self, datapath, tp_dst, priority, queue_id, label):
        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser

        match = parser.OFPMatch(eth_type=0x0800,
                                ip_proto=6,
                                tcp_dst=tp_dst)
        actions = [
            parser.OFPActionSetQueue(queue_id),
            parser.OFPActionOutput(ofproto.OFPP_NORMAL)
        ]
        self.add_flow(datapath, priority, match, actions)
        self.logger.info("Rule: %s port=%d priority=%d queue=%d",
                         label, tp_dst, priority, queue_id)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg      = ev.msg
        datapath = msg.datapath
        ofproto  = datapath.ofproto
        parser   = datapath.ofproto_parser
        in_port  = msg.match['in_port']

        pkt     = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        if eth_pkt is None:
            return

        dst  = eth_pkt.dst
        src  = eth_pkt.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        out_port = (self.mac_to_port[dpid][dst]
                    if dst in self.mac_to_port[dpid]
                    else ofproto.OFPP_FLOOD)

        actions = [parser.OFPActionOutput(out_port)]
        if msg.buffer_id != ofproto.OFP_NO_BUFFER:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id,
                in_port=in_port, actions=actions)
        else:
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=in_port, actions=actions,
                data=msg.data)
        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions,
                 idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(
                    ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst,
            idle_timeout=idle_timeout, hard_timeout=hard_timeout)
        datapath.send_msg(mod)
