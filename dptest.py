import packetutil
import dpkt

class PcapReader:
    def __init__(self,path):
        self.path = path

    def getPacketData(self):
        count = 0
        pair = {}
        stream_data = [[]]
        size = 0

        with open(self.path,'rb') as f:
            pcap = dpkt.pcap.Reader(f)

            for ts, buf in pcap:
                try:
                    eth = dpkt.sll.SLL(buf)
                    ip = eth.data
                    tcp = ip.data

                    if (tcp.flags & dpkt.tcp.TH_SYN):
                        if (tcp.flags & dpkt.tcp.TH_ACK) == 0:
                            src_pair = (ip.src, tcp.sport)
                            dst_pair = (ip.dst, tcp.dport)
                            pair[count] = (src_pair, dst_pair)
                            count += 1

                    size = len(stream_data)
                    if len(pair) - size > 0:
                        for i in range(len(pair) - size):
                            stream_data.append([])

                    if len(tcp.data) != 0:
                        for i in range(len(pair)):
                            if pair[i][0][0] == ip.src and pair[i][0][1] == tcp.sport and pair[i][1][0] == ip.dst and pair[i][1][1] == tcp.dport:
                                stream_data[i].append(packetutil.Packet(direction=True, packet=tcp.data))
                                break
                            elif pair[i][0][0] == ip.dst and pair[i][0][1] == tcp.dport and pair[i][1][0] == ip.src and pair[i][1][1] == tcp.sport:
                                stream_data[i].append(packetutil.Packet(direction=False, packet=tcp.data))
                                break
                            else:
                                pass
                except Exception as e:
                    pass

        f.close()
        print("Dddd")
        print(pair[9])
        return stream_data
