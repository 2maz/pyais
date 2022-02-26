import textwrap
import unittest

from pyais import NMEAMessage
from pyais.ais_types import AISType
from pyais.constants import ManeuverIndicator, NavigationStatus, ShipType, NavAid, EpfdType, StationType, TransmitMode
from pyais.decode import decode
from pyais.exceptions import UnknownMessageException
from pyais.messages import MessageType18
from pyais.stream import ByteStream


class TestAIS(unittest.TestCase):
    """
    TestCases for AIS message decoding and assembling.

    The Test messages are from multiple sources and are scrambled together.
    Raw messages are decoded by either hand or some online decoder.
    As my main source of AIS messages I used this dumb:
    https://www.aishub.net/ais-dispatcher

    As my main decoder I used this decoder:
    http://ais.tbsalling.dk

    The latter sometimes is a bit weird and therefore I used aislib to verify my results.
    """

    def test_to_json(self):
        json_dump = decode(b"!AIVDM,1,1,,A,15NPOOPP00o?b=bE`UNv4?w428D;,0*24").to_json()
        text = textwrap.dedent("""{
    "msg_type": 1,
    "repeat": 0,
    "mmsi": "367533950",
    "status": 0,
    "turn": -128,
    "speed": 0.0,
    "accuracy": 1,
    "lon": -122.408232,
    "lat": 37.808418,
    "course": 360.0,
    "heading": 511,
    "second": 34,
    "maneuver": 0,
    "spare": 0,
    "raim": true,
    "radio": 34059
}""")
        self.assertEqual(json_dump, text)

    @unittest.skip("TODO")
    def test_msg_type(self):
        """
        Test if msg type is correct
        """
        nmea = NMEAMessage(b"!AIVDM,1,1,,B,15M67FC000G?ufbE`FepT@3n00Sa,0*5C")
        assert nmea.decode().msg_type == AISType.POS_CLASS_A1

        nmea = NMEAMessage(b"!AIVDM,1,1,,B,15NG6V0P01G?cFhE`R2IU?wn28R>,0*05")
        assert nmea.decode().msg_type == AISType.POS_CLASS_A1

        nmea = NMEAMessage.assemble_from_iterable(messages=[
            NMEAMessage(b"!AIVDM,2,1,4,A,55O0W7`00001L@gCWGA2uItLth@DqtL5@F22220j1h742t0Ht0000000,0*08"),
            NMEAMessage(b"!AIVDM,2,2,4,A,000000000000000,2*20")
        ])
        assert nmea.decode().msg_type == AISType.STATIC_AND_VOYAGE

    def test_msg_type_1_a(self):
        result = decode(b"!AIVDM,1,1,,B,15M67FC000G?ufbE`FepT@3n00Sa,0*5C").asdict()
        assert result == {
            'msg_type': 1,
            'repeat': 0,
            'mmsi': '366053209',
            'status': NavigationStatus.RestrictedManoeuverability,
            'turn': 0,
            'speed': 0.0,
            'accuracy': 0,
            'lon': -122.341618,
            'lat': 37.802118,
            'course': 219.3,
            'heading': 1,
            'second': 59,
            'maneuver': ManeuverIndicator.NotAvailable,
            'raim': False,
            'radio': 2281,
            'spare': 0
        }

    def test_msg_type_1_b(self):
        msg = decode(b"!AIVDM,1,1,,A,15NPOOPP00o?b=bE`UNv4?w428D;,0*24").asdict()
        assert msg['msg_type'] == 1
        assert msg['mmsi'] == '367533950'
        assert msg['repeat'] == 0
        assert msg['status'] == NavigationStatus.UnderWayUsingEngine
        assert msg['turn'] == -128
        assert msg['speed'] == 0
        assert msg['accuracy'] == 1
        assert round(msg['lat'], 4) == 37.8084
        assert round(msg['lon'], 4) == -122.4082
        assert msg['course'] == 360
        assert msg['heading'] == 511
        assert msg['second'] == 34
        assert msg['maneuver'] == ManeuverIndicator.NotAvailable
        assert msg['raim']

    def test_msg_type_1_c(self):
        msg = decode(b"!AIVDM,1,1,,B,181:Kjh01ewHFRPDK1s3IRcn06sd,0*08").asdict()
        assert msg['course'] == 87.0
        assert msg['mmsi'] == '538090443'
        assert msg['speed'] == 10.9

    def test_decode_pos_1_2_3(self):
        # weired message of type 0 as part of issue #4
        content = decode(b"!AIVDM,1,1,,B,0S9edj0P03PecbBN`ja@0?w42cFC,0*7C").asdict()

        assert content['repeat'] == 2
        assert content['mmsi'] == "211512520"
        assert content['turn'] == -128
        assert content['speed'] == 0.3
        assert round(content['lat'], 4) == 53.5427
        assert round(content['lon'], 4) == 9.9794
        assert round(content['course'], 1) == 0.0

        assert decode(b"!AIVDM,1,1,,B,0S9edj0P03PecbBN`ja@0?w42cFC,0*7C").to_json()

    def test_msg_type_3(self):
        msg = decode(b"!AIVDM,1,1,,A,35NSH95001G?wopE`beasVk@0E5:,0*6F").asdict()
        assert msg['msg_type'] == 3
        assert msg['mmsi'] == "367581220"
        assert msg['repeat'] == 0
        assert msg['status'] == NavigationStatus.Moored
        assert msg['turn'] == 0
        assert msg['speed'] == 0.1
        assert msg['accuracy'] == 0
        assert round(msg['lat'], 4) == 37.8107
        assert round(msg['lon'], 4) == -122.3343
        assert round(msg['course'], 1) == 254.2
        assert msg['heading'] == 217
        assert msg['second'] == 40
        assert msg['maneuver'] == ManeuverIndicator.NotAvailable
        assert not msg['raim']

    def test_msg_type_4_a(self):
        msg = decode(b"!AIVDM,1,1,,A,403OviQuMGCqWrRO9>E6fE700@GO,0*4D").asdict()
        assert msg['lon'] == -76.352362
        assert msg['lat'] == 36.883767
        assert msg['accuracy'] == 1
        assert msg['year'] == 2007
        assert msg['month'] == 5
        assert msg['day'] == 14
        assert msg['minute'] == 57
        assert msg['second'] == 39

    def test_msg_type_4_b(self):
        msg = decode(b"!AIVDM,1,1,,B,403OtVAv>lba;o?Ia`E`4G?02H6k,0*44").asdict()
        assert round(msg['lon'], 4) == -122.4648
        assert round(msg['lat'], 4) == 37.7943
        assert msg['mmsi'] == "003669145"
        assert msg['accuracy'] == 1
        assert msg['year'] == 2019
        assert msg['month'] == 11
        assert msg['day'] == 9
        assert msg['hour'] == 10
        assert msg['minute'] == 41
        assert msg['second'] == 11
        assert msg['epfd'].value == 0
        assert msg['epfd'] == EpfdType.Undefined

    def test_msg_type_5(self):
        msg = decode(
            "!AIVDM,2,1,1,A,55?MbV02;H;s<HtKR20EHE:0@T4@Dn2222222216L961O5Gf0NSQEp6ClRp8,0*1C",
            "!AIVDM,2,2,1,A,88888888880,2*25"
        ).asdict()
        assert msg['callsign'] == "3FOF8"
        assert msg['shipname'] == "EVER DIADEM"
        assert msg['ship_type'] == ShipType.Cargo
        assert msg['to_bow'] == 225
        assert msg['to_stern'] == 70
        assert msg['to_port'] == 1
        assert msg['to_starboard'] == 31
        assert msg['draught'] == 12.2
        assert msg['destination'] == "NEW YORK"
        assert msg['dte'] == 0
        assert msg['epfd'] == EpfdType.GPS

    def test_msg_type_6(self):
        msg = decode(b"!AIVDM,1,1,,B,6B?n;be:cbapalgc;i6?Ow4,2*4A").asdict()
        assert msg['seqno'] == 3
        assert msg['dest_mmsi'] == "313240222"
        assert msg['mmsi'] == "150834090"
        assert msg['dac'] == 669
        assert msg['fid'] == 11
        assert not msg['retransmit']
        assert msg['data'] == 258587390607345

    def test_msg_type_7(self):
        msg = decode(b"!AIVDM,1,1,,A,702R5`hwCjq8,0*6B").asdict()
        assert msg['mmsi'] == "002655651"
        assert msg['msg_type'] == 7
        assert msg['mmsi1'] == "265538450"
        assert msg['mmsiseq1'] == 0
        assert msg['mmsi2'] is None
        assert msg['mmsi3'] is None
        assert msg['mmsi4'] is None

    def test_msg_type_8(self):
        msg = decode(b"!AIVDM,1,1,,A,85Mwp`1Kf3aCnsNvBWLi=wQuNhA5t43N`5nCuI=p<IBfVqnMgPGs,0*47").asdict()

        assert msg['repeat'] == 0
        assert msg['mmsi'] == "366999712"
        assert msg['dac'] == 366
        assert msg['fid'] == 56
        assert msg['data'] == 26382309960366212432958701962051450160982977169991995217145869625277036758523

    def test_msg_type_9(self):
        msg = decode(b"!AIVDM,1,1,,B,91b55wi;hbOS@OdQAC062Ch2089h,0*30").asdict()
        assert msg['msg_type'] == 9
        assert msg['repeat'] == 0
        assert msg['mmsi'] == "111232511"
        assert msg['alt'] == 303
        assert msg['speed'] == 42
        assert msg['accuracy'] == 0
        assert round(msg['lon'], 5) == -6.27884
        assert round(msg['lat'], 5) == 58.144
        assert msg['course'] == 154.5
        assert msg['second'] == 15
        assert msg['dte'] == 1
        assert msg['radio'] == 33392
        assert not msg['raim']

    def test_msg_type_10_a(self):
        msg = decode(b"!AIVDM,1,1,,B,:5MlU41GMK6@,0*6C").asdict()
        assert msg['dest_mmsi'] == "366832740"
        assert msg['repeat'] == 0

    def test_msg_type_10_b(self):
        msg = decode(b"!AIVDM,1,1,,B,:6TMCD1GOS60,0*5B").asdict()
        assert msg['dest_mmsi'] == "366972000"
        assert msg['repeat'] == 0

    def test_msg_type_11(self):
        msg = decode(b"!AIVDM,1,1,,B,;4R33:1uUK2F`q?mOt@@GoQ00000,0*5D").asdict()
        assert round(msg['lon'], 4) == -94.4077
        assert round(msg['lat'], 4) == 28.4091
        assert msg['accuracy'] == 1
        assert msg['msg_type'] == 11
        assert msg['year'] == 2009
        assert msg['month'] == 5
        assert msg['day'] == 22
        assert msg['hour'] == 2
        assert msg['minute'] == 22
        assert msg['second'] == 40

    def test_msg_type_12_a(self):
        msg = decode(b"!AIVDM,1,1,,A,<5?SIj1;GbD07??4,0*38").asdict()
        assert msg['msg_type'] == 12
        assert msg['repeat'] == 0
        assert msg['mmsi'] == "351853000"
        assert msg['seqno'] == 0
        assert msg['dest_mmsi'] == "316123456"
        assert msg['retransmit'] == 0
        assert msg['text'] == "GOOD"

    def test_msg_type_12_b(self):
        msg = decode(b"!AIVDM,1,1,,A,<42Lati0W:Ov=C7P6B?=Pjoihhjhqq0,2*2B")
        assert msg.msg_type == 12
        assert msg.repeat == 0
        assert msg.mmsi == "271002099"
        assert msg.seqno == 0
        assert msg.dest_mmsi == "271002111"
        assert msg.retransmit == 1

    def test_msg_type_13(self):
        msg = decode(b"!AIVDM,1,1,,A,=39UOj0jFs9R,0*65").asdict()
        assert msg['msg_type'] == 13
        assert msg['repeat'] == 0
        assert msg['mmsi'] == "211378120"
        assert msg['mmsi1'] == "211217560"

    def test_msg_type_14(self):
        msg = decode(b"!AIVDM,1,1,,A,>5?Per18=HB1U:1@E=B0m<L,2*51").asdict()
        assert msg['msg_type'] == 14
        assert msg['repeat'] == 0
        assert msg['mmsi'] == "351809000"
        assert msg['text'] == "RCVD YR TEST MSG"

    def test_msg_type_15_a(self):
        msg = decode(b"!AIVDM,1,1,,A,?5OP=l00052HD00,2*5B").asdict()
        assert msg['msg_type'] == 15
        assert msg['repeat'] == 0
        assert msg['mmsi'] == "368578000"
        assert msg['offset1_1'] == 0
        assert msg['mmsi1'] == '000005158'
        assert msg['offset1_2'] is None
        assert msg['mmsi2'] is None

    def test_msg_type_15_b(self):
        msg = decode(b"!AIVDM,1,1,,B,?h3Ovn1GP<K0<P@59a0,2*04").asdict()
        assert msg['msg_type'] == 15
        assert msg['repeat'] == 3
        assert msg['mmsi'] == "003669720"
        assert msg['mmsi1'] == "367014320"
        assert msg['mmsi2'] == "000000000"
        assert msg['type1_1'] == 3
        assert msg['type1_2'] == 5
        assert msg['offset1_2'] == 617
        assert msg['offset1_1'] == 516

    def test_msg_type_16(self):
        msg = decode(b"!AIVDM,1,1,,A,@01uEO@mMk7P<P00,0*18").asdict()

        assert msg['msg_type'] == 16
        assert msg['repeat'] == 0
        assert msg['mmsi'] == "002053501"
        assert msg['mmsi1'] == "224251000"
        assert msg['offset1'] == 200
        assert msg['increment1'] == 0
        assert msg['mmsi2'] == '000000000'
        assert msg['offset2'] is None
        assert msg['increment2'] is None

    def test_msg_type_17_a(self):
        msg = decode(
            b"!AIVDM,2,1,5,A,A02VqLPA4I6C07h5Ed1h<OrsuBTTwS?r:C?w`?la<gno1RTRwSP9:BcurA8a,0*3A",
            b"!AIVDM,2,2,5,A,:Oko02TSwu8<:Jbb,0*11"
        ).asdict()
        n = 0x7c0556c07031febbf52924fe33fa2933ffa0fd2932fdb7062922fe3809292afde9122929fcf7002923ffd20c29aaaa
        assert msg['msg_type'] == 17
        assert msg['repeat'] == 0
        assert msg['mmsi'] == "002734450"
        assert msg['lon'] == 1747.8
        assert msg['lat'] == 3599.2
        assert msg['data'] == n

    def test_msg_type_17_b(self):
        msg = decode(b"!AIVDM,1,1,,A,A0476BQ>J8`<h2JpH:4P0?j@2mTEw8`=DP1DEnqvj0,0*79").asdict()
        assert msg['msg_type'] == 17
        assert msg['repeat'] == 0
        assert msg['mmsi'] == "004310602"
        assert msg['lat'] == 2058.2
        assert msg['lon'] == 8029.0
        assert msg['data'] == 0x26b860a12000fc900b5915fc8a0d520054576e7ec80

    def test_msg_type_18(self):
        msg = decode(b"!AIVDM,1,1,,A,B5NJ;PP005l4ot5Isbl03wsUkP06,0*76").asdict()
        print(msg)
        assert msg['msg_type'] == 18
        assert msg['mmsi'] == "367430530"
        assert msg['speed'] == 0
        assert msg['accuracy'] == 0
        assert round(msg['lat'], 2) == 37.79
        assert round(msg['lon'], 2) == -122.27
        assert msg['course'] == 0
        assert msg['heading'] == 511
        assert msg['second'] == 55
        assert msg['reserved_2'] == 0
        assert msg['cs'] == 1
        assert msg['display'] == 0
        assert msg['dsc'] == 1
        assert msg['band'] == 1
        assert msg['msg22'] == 1
        assert not msg['assigned']
        assert not msg['raim']

    def test_msg_type_19(self):
        msg = decode(b"!AIVDM,1,1,,B,C5N3SRgPEnJGEBT>NhWAwwo862PaLELTBJ:V00000000S0D:R220,0*0B").asdict()
        assert msg['msg_type'] == 19
        assert msg['mmsi'] == "367059850"
        assert msg['speed'] == 8.7
        assert msg['accuracy'] == 0
        assert msg['lat'] == 29.543695
        assert msg['lon'], 2 == -88.810394
        assert round(msg['course'], 2) == 335.9
        assert msg['heading'] == 511
        assert msg['second'] == 46
        assert msg['shipname'] == "CAPT.J.RIMES"
        assert msg['ship_type'] == ShipType(70)
        assert msg['ship_type'] == ShipType.Cargo
        assert msg['to_bow'] == 5
        assert msg['to_stern'] == 21
        assert msg['to_port'] == 4
        assert msg['to_starboard'] == 4
        assert msg['epfd'] == EpfdType.GPS
        assert msg['dte'] == 0
        assert msg['assigned'] == 0

    def test_msg_type_20(self):
        msg = decode(b"!AIVDM,1,1,,A,D028rqP<QNfp000000000000000,2*0C").asdict()
        assert msg['msg_type'] == 20
        assert msg['mmsi'] == "002243302"
        assert msg['offset1'] == 200
        assert msg['number1'] == 5
        assert msg['timeout1'] == 7
        assert msg['increment1'] == 750

        # All other values are zero
        for k, v in msg.items():
            if k not in ('msg_type', 'mmsi', 'offset1', 'number1', 'timeout1', 'increment1'):
                assert not v

    def test_msg_type_21(self):
        msg = decode(
            b"!AIVDM,2,1,7,B,E4eHJhPR37q0000000000000000KUOSc=rq4h00000a,0*4A",
            b"!AIVDM,2,2,7,B,@20,4*54"
        ).asdict()
        assert msg['msg_type'] == 21
        assert msg['mmsi'] == "316021442"
        assert msg['aid_type'] == NavAid.REFERENCE_POINT
        assert msg['shipname'] == "DFO2"
        assert msg['accuracy'] == 1
        assert msg['lat'] == 48.65457
        assert msg['lon'] == -123.429155
        assert not msg['to_bow']
        assert not msg['to_stern']
        assert not msg['to_port']
        assert not msg['to_starboard']

        assert msg['off_position']
        assert msg['regional'] == 0
        assert msg['raim']
        assert msg['virtual_aid'] == 0
        assert msg['assigned'] == 0
        assert msg['name_ext'] is None
        assert msg['epfd'] == EpfdType.GPS

    def test_msg_type_22_broadcast(self):
        # Broadcast
        msg = decode(b"!AIVDM,1,1,,B,F030p:j2N2P5aJR0r;6f3rj10000,0*11").asdict()
        assert msg['msg_type'] == 22
        assert msg['mmsi'] == "003160107"
        assert msg['channel_a'] == 2087
        assert msg['channel_b'] == 2088
        assert msg['power'] == 0

        assert msg['ne_lon'] == -7710.0
        assert msg['ne_lat'] == 3300.0
        assert msg['sw_lon'] == -8020.0
        assert msg['sw_lat'] == 3210

        assert msg['band_a'] == 0
        assert msg['band_b'] == 0
        assert msg['zonesize'] == 2

        assert 'dest1' not in msg.keys()
        assert 'dest2' not in msg.keys()

    def test_msg_type_22_addressed(self):
        # Addressed
        msg = decode(b"!AIVDM,1,1,,A,F@@W>gOP00PH=JrN9l000?wB2HH;,0*44").asdict()
        assert msg['msg_type'] == 22
        assert msg['mmsi'] == "017419965"
        assert msg['channel_a'] == 3584
        assert msg['channel_b'] == 8
        assert msg['power'] == 1
        assert msg['addressed'] == 1

        assert msg['dest1'] == "028144881"
        assert msg['dest2'] == "268435519"

        assert msg['band_a'] == 0
        assert msg['band_b'] == 0
        assert msg['zonesize'] == 4

        assert 'ne_lon' not in msg.keys()
        assert 'ne_lat' not in msg.keys()
        assert 'sw_lon' not in msg.keys()
        assert 'sw_lat' not in msg.keys()

    def test_msg_type_23(self):
        msg = decode(b"!AIVDM,1,1,,B,G02:Kn01R`sn@291nj600000900,2*12").asdict()
        assert msg['msg_type'] == 23
        assert msg['mmsi'] == "002268120"
        assert msg['ne_lon'] == 157.8
        assert msg['ship_type'] == ShipType.NotAvailable
        assert msg['ne_lat'] == 3064.2
        assert msg['sw_lon'] == 109.6
        assert msg['sw_lat'] == 3040.8
        assert msg['station_type'] == StationType.REGIONAL
        assert msg['txrx'] == TransmitMode.TXA_TXB_RXA_RXB
        assert msg['interval'] == 9
        assert msg['quiet'] == 0

    def test_msg_type_24(self):
        msg = decode(b"!AIVDM,1,1,,A,H52KMeDU653hhhi0000000000000,0*1A").asdict()
        assert msg['msg_type'] == 24
        assert msg['mmsi'] == "338091445"
        assert msg['partno'] == 1
        assert msg['ship_type'] == ShipType.PleasureCraft
        assert msg['vendorid'] == "FEC"
        assert msg['callsign'] == ""
        assert msg['to_bow'] == 0
        assert msg['to_stern'] == 0
        assert msg['to_port'] == 0
        assert msg['to_starboard'] == 0

    def test_msg_type_25_a(self):
        msg = decode(b"!AIVDM,1,1,,A,I6SWo?8P00a3PKpEKEVj0?vNP<65,0*73").asdict()

        assert msg['msg_type'] == 25
        assert msg['addressed']
        assert not msg['structured']
        assert msg['dest_mmsi'] == "134218384"

    def test_msg_type_25_b(self):
        msg = decode(b"!AIVDO,1,1,,A,I6SWo?<P00a00;Cwwwwwwwwwwww0,0*4A").asdict()
        assert msg == {
            'addressed': 1,
            'data': 1208925819614629174706112,
            'dest_mmsi': '134218384',
            'mmsi': '440006460',
            'repeat': 0,
            'structured': 1,
            'app_id': 45,
            'msg_type': 25
        }

    def test_msg_type_25_c(self):
        msg = decode(b"!AIVDO,1,1,,A,I6SWo?8P00a0003wwwwwwwwwwww0,0*35").asdict()
        assert msg == {
            'addressed': 1,
            'data': 1208925819614629174706112,
            'dest_mmsi': '134218384',
            'mmsi': '440006460',
            'repeat': 0,
            'structured': 0,
            'msg_type': 25
        }

    def test_msg_type_26_a(self):
        msg = decode(b"!AIVDM,1,1,,A,JB3R0GO7p>vQL8tjw0b5hqpd0706kh9d3lR2vbl0400,2*40").asdict()
        assert msg['msg_type'] == 26
        assert msg['addressed']
        assert msg['structured']
        assert msg['dest_mmsi'] == "838351848"
        assert msg['data'] == 0x332fc0a85c39e2c007006cf026c0f4882faad001000

    def test_msg_type_26_b(self):
        msg = decode(b"!AIVDM,1,1,,A,J0@00@370>t0Lh3P0000200H:2rN92,4*14").asdict()
        assert msg['msg_type'] == 26
        assert not msg['addressed']
        assert not msg['structured']
        assert msg['data'] == 0xc700ef007300e0000000080018282e9e24

    def test_msg_type_27(self):
        msg = decode(b"!AIVDM,1,1,,B,KC5E2b@U19PFdLbMuc5=ROv62<7m,0*16").asdict()
        assert msg['msg_type'] == 27
        assert msg['mmsi'] == "206914217"
        assert msg['accuracy'] == 0
        assert msg['raim'] == 0
        assert msg['status'] == NavigationStatus.NotUnderCommand
        assert msg['lon'] == 137.023333
        assert msg['lat'] == 4.84
        assert msg['speed'] == 57
        assert msg['course'] == 167
        assert msg['gnss'] == 0

    def test_broken_messages(self):
        # Undefined epfd
        assert decode(b"!AIVDM,1,1,,B,4>O7m7Iu@<9qUfbtm`vSnwvH20S8,0*46").asdict()['epfd'] == EpfdType.Undefined

    def test_multiline_message(self):
        # these messages caused issue #3
        msg_1_part_0 = b'!AIVDM,2,1,1,A,538CQ>02A;h?D9QC800pu8@T>0P4l9E8L0000017Ah:;;5r50Ahm5;C0,0*07'
        msg_1_part_1 = b'!AIVDM,2,2,1,A,F@V@00000000000,2*35'

        assert decode(msg_1_part_0, msg_1_part_1).to_json()

        msg_2_part_0 = b'!AIVDM,2,1,9,A,538CQ>02A;h?D9QC800pu8@T>0P4l9E8L0000017Ah:;;5r50Ahm5;C0,0*0F'
        msg_2_part_1 = b'!AIVDM,2,2,9,A,F@V@00000000000,2*3D'

        assert decode(msg_2_part_0, msg_2_part_1).to_json()

    def test_byte_stream(self):
        messages = [
            b'!AIVDM,2,1,1,A,538CQ>02A;h?D9QC800pu8@T>0P4l9E8L0000017Ah:;;5r50Ahm5;C0,0*07',
            b'!AIVDM,2,2,1,A,F@V@00000000000,2*35',
            b'!AIVDM,2,1,9,A,538CQ>02A;h?D9QC800pu8@T>0P4l9E8L0000017Ah:;;5r50Ahm5;C0,0*0F',
            b'!AIVDM,2,2,9,A,F@V@00000000000,2*3D',
        ]
        counter = 0
        for msg in ByteStream(messages):
            decoded = msg.decode().asdict()
            assert decoded['shipname'] == 'NORDIC HAMBURG'
            assert decoded['mmsi'] == "210035000"
            assert decoded
            counter += 1
        assert counter == 2

    def test_empty_channel(self):
        msg = b"!AIVDO,1,1,,,B>qc:003wk?8mP=18D3Q3wgTiT;T,0*13"

        self.assertEqual(NMEAMessage(msg).channel, "")

        content = decode(msg).asdict()
        self.assertEqual(content["msg_type"], 18)
        self.assertEqual(content["repeat"], 0)
        self.assertEqual(content["mmsi"], "1000000000")
        self.assertEqual(content["speed"], 1023)
        self.assertEqual(content["accuracy"], 0)
        self.assertEqual(str(content["lon"]), "181.0")
        self.assertEqual(str(content["lat"]), "91.0")
        self.assertEqual(str(content["course"]), "360.0")
        self.assertEqual(content["heading"], 511)
        self.assertEqual(content["second"], 31)
        self.assertEqual(content["reserved_2"], 0)
        self.assertEqual(content["cs"], 1)
        self.assertEqual(content["display"], 0)
        self.assertEqual(content["band"], 1)
        self.assertEqual(content["radio"], 410340)

    def test_msg_with_more_that_82_chars_payload(self):
        content = decode(
            "!AIVDM,1,1,,B,53ktrJ82>ia4=50<0020<5=@Dhv0t8T@u<0000001PV854Si0;mR@CPH13p0hDm1C3h0000,2*35"
        ).asdict()

        self.assertEqual(content["msg_type"], 5)
        self.assertEqual(content["mmsi"], "255801960")
        self.assertEqual(content["repeat"], 0)
        self.assertEqual(content["ais_version"], 2)
        self.assertEqual(content["imo"], 9356945)
        self.assertEqual(content["callsign"], "CQPC")
        self.assertEqual(content["shipname"], "CASTELO OBIDOS")
        self.assertEqual(content["ship_type"], ShipType.NotAvailable)
        self.assertEqual(content["to_bow"], 12)
        self.assertEqual(content["to_stern"], 38)
        self.assertEqual(content["to_port"], 8)
        self.assertEqual(content["to_starboard"], 5)
        self.assertEqual(content["epfd"], EpfdType.GPS)
        self.assertEqual(content["month"], 2)
        self.assertEqual(content["day"], 7)
        self.assertEqual(content["hour"], 17)
        self.assertEqual(content["minute"], 0)
        self.assertEqual(content["draught"], 4.7)
        self.assertEqual(content["destination"], "VIANA DO CASTELO")

    def test_nmea_decode(self):
        nmea = NMEAMessage(b"!AIVDO,1,1,,,B>qc:003wk?8mP=18D3Q3wgTiT;T,0*13")
        decoded = nmea.decode()
        assert decoded.msg_type == 18
        assert isinstance(decoded, MessageType18)

    def test_nmea_decode_unknown_msg(self):
        with self.assertRaises(UnknownMessageException):
            nmea = NMEAMessage(b"!AIVDO,1,1,,,B>qc:003wk?8mP=18D3Q3wgTiT;T,0*13")
            nmea.ais_id = 28
            nmea.decode()

    def test_decode_out_of_order(self):
        parts = [
            b"!AIVDM,2,2,4,A,000000000000000,2*20",
            b"!AIVDM,2,1,4,A,55O0W7`00001L@gCWGA2uItLth@DqtL5@F22220j1h742t0Ht0000000,0*08",
        ]

        decoded = decode(*parts)

        assert decoded.asdict()['mmsi'] == '368060190'

    def test_issue_46_a(self):
        msg = b"!ARVDM,2,1,3,B,E>m1c1>9TV`9WW@97QUP0000000F@lEpmdceP00003b,0*5C"
        decoded = NMEAMessage(msg).decode()

        self.assertEqual(decoded.msg_type, 21)
        self.assertEqual(decoded.repeat, 0)
        self.assertEqual(decoded.mmsi, '995126020')
        self.assertEqual(decoded.aid_type, NavAid.ISOLATED_DANGER)
        self.assertEqual(decoded.shipname, 'SIMPSON ROCK')
        self.assertEqual(decoded.accuracy, True)
        self.assertEqual(decoded.lon, 175.119987)
        self.assertEqual(decoded.lat, -36.0075)
        self.assertEqual(decoded.to_bow, 0)
        self.assertEqual(decoded.to_stern, 0)
        self.assertEqual(decoded.to_port, 0)
        self.assertEqual(decoded.to_starboard, 0)
        self.assertEqual(decoded.epfd, EpfdType.Surveyed)
        self.assertEqual(decoded.second, 10)

        # The following fields are None
        self.assertIsNone(decoded.off_position)
        self.assertIsNone(decoded.regional)
        self.assertIsNone(decoded.raim)
        self.assertIsNone(decoded.virtual_aid)
        self.assertIsNone(decoded.assigned)
        self.assertIsNone(decoded.name_ext)

    def test_issue_46_b(self):
        msg = b"!AIVDM,1,1,,B,E>lt;KLab21@1bb@I@@@@@@@@@@D8k2tnmvs000003v0@,2*52"
        decoded = NMEAMessage(msg).decode()

        self.assertEqual(decoded.msg_type, 21)
        self.assertEqual(decoded.repeat, 0)
        self.assertEqual(decoded.mmsi, '995036013')
        self.assertEqual(decoded.aid_type, NavAid.STARBOARD_HAND_MARK)
        self.assertEqual(decoded.shipname, 'STDB CUT 2')
        self.assertEqual(decoded.accuracy, True)
        self.assertEqual(decoded.lon, 115.691833)
        self.assertEqual(decoded.lat, -32.004333)
        self.assertEqual(decoded.to_bow, 0)
        self.assertEqual(decoded.to_stern, 0)
        self.assertEqual(decoded.to_port, 0)
        self.assertEqual(decoded.to_starboard, 0)
        self.assertEqual(decoded.epfd, EpfdType.Surveyed)
        self.assertEqual(decoded.second, 60)
        self.assertEqual(decoded.off_position, False)
        self.assertEqual(decoded.regional, 4)

        # The following fields are None
        self.assertIsNone(decoded.raim)
        self.assertIsNone(decoded.virtual_aid)
        self.assertIsNone(decoded.assigned)
        self.assertIsNone(decoded.name_ext)

    def test_msg_too_short_enum_is_none(self):
        msg = b"!AIVDM,1,1,,B,E>lt;,2*52"
        decoded = NMEAMessage(msg).decode()

        self.assertEqual(decoded.msg_type, 21)
        self.assertEqual(decoded.repeat, 0)
        self.assertEqual(decoded.mmsi, '000971714')
        self.assertIsNone(decoded.aid_type)
        self.assertIsNone(decoded.epfd)

        msg = b"!AIVDM,1,1,,B,15M6,0*5C"
        decoded = NMEAMessage(msg).decode()
        self.assertIsNone(decoded.maneuver)

        msg = b"!AIVDM,2,1,1,A,55?MbV02;H,0*00"
        decoded = NMEAMessage(msg).decode()
        self.assertIsNone(decoded.ship_type)
        self.assertIsNone(decoded.epfd)

    def test_to_dict_non_enum(self):
        """Enum types do not use None if the fields are missing when partial decoding"""
        msg = b"!AIVDM,1,1,,B,E>lt;KLab21@1bb@I@@@@@@@@@@D8k2tnmvs000003v0@,2*52"
        decoded = NMEAMessage(msg).decode()

        d = decoded.asdict(enum_as_int=True)
        self.assertEqual(
            d, {'accuracy': True,
                'aid_type': 25,
                'assigned': None,
                'epfd': 7,
                'lat': -32.004333,
                'lon': 115.691833,
                'mmsi': '995036013',
                'msg_type': 21,
                'name_ext': None,
                'off_position': False,
                'raim': None,
                'regional': 4,
                'repeat': 0,
                'second': 60,
                'shipname': 'STDB CUT 2',
                'spare': None,
                'to_bow': 0,
                'to_port': 0,
                'to_starboard': 0,
                'to_stern': 0,
                'virtual_aid': None}
        )

    def test_decode_and_merge(self):
        msg = b"!AIVDM,1,1,,B,E>lt;KLab21@1bb@I@@@@@@@@@@D8k2tnmvs000003v0@,2*52"
        decoded = NMEAMessage(msg)

        d = decoded.decode_and_merge(enum_as_int=True)

        self.assertEqual(
            d, {'accuracy': True,
                'aid_type': 25,
                'ais_id': 21,
                'assigned': None,
                'channel': 'B',
                'checksum': 82,
                'epfd': 7,
                'fill_bits': 2,
                'frag_cnt': 1,
                'frag_num': 1,
                'lat': -32.004333,
                'lon': 115.691833,
                'mmsi': '995036013',
                'msg_type': 21,
                'name_ext': None,
                'off_position': False,
                'payload': 'E>lt;KLab21@1bb@I@@@@@@@@@@D8k2tnmvs000003v0@',
                'raim': None,
                'raw': '!AIVDM,1,1,,B,E>lt;KLab21@1bb@I@@@@@@@@@@D8k2tnmvs000003v0@,2*52',
                'regional': 4,
                'repeat': 0,
                'second': 60,
                'seq_id': None,
                'shipname': 'STDB CUT 2',
                'spare': None,
                'talker': 'AI',
                'to_bow': 0,
                'to_port': 0,
                'to_starboard': 0,
                'to_stern': 0,
                'type': 'VDM',
                'virtual_aid': None}
        )

        d = decoded.decode_and_merge(enum_as_int=False)
        self.assertEqual(
            d, {'accuracy': True,
                'aid_type': NavAid.STARBOARD_HAND_MARK,
                'ais_id': 21,
                'assigned': None,
                'channel': 'B',
                'checksum': 82,
                'epfd': EpfdType.Surveyed,
                'fill_bits': 2,
                'frag_cnt': 1,
                'frag_num': 1,
                'lat': -32.004333,
                'lon': 115.691833,
                'mmsi': '995036013',
                'msg_type': 21,
                'name_ext': None,
                'off_position': False,
                'payload': 'E>lt;KLab21@1bb@I@@@@@@@@@@D8k2tnmvs000003v0@',
                'raim': None,
                'raw': '!AIVDM,1,1,,B,E>lt;KLab21@1bb@I@@@@@@@@@@D8k2tnmvs000003v0@,2*52',
                'regional': 4,
                'repeat': 0,
                'second': 60,
                'seq_id': None,
                'shipname': 'STDB CUT 2',
                'spare': None,
                'talker': 'AI',
                'to_bow': 0,
                'to_port': 0,
                'to_starboard': 0,
                'to_stern': 0,
                'type': 'VDM',
                'virtual_aid': None}
        )
