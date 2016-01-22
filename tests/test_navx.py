
from robotpy_ext.common_drivers.navx._impl import AHRSProtocol

def test_decoding():
    
    data = [0]*4
    
    AHRSProtocol.encodeBinaryUint16(42, data, 0)
    assert AHRSProtocol.decodeBinaryUint16(data, 0) == 42
    
    AHRSProtocol.encodeBinaryUint16(40000, data, 0)
    assert AHRSProtocol.decodeBinaryUint16(data, 0) == 40000
    
    AHRSProtocol.encodeBinaryInt16(-42, data, 0)
    assert AHRSProtocol.decodeBinaryInt16(data, 0) == -42
    
    AHRSProtocol.encodeBinaryInt16(42, data, 0)
    assert AHRSProtocol.decodeBinaryInt16(data, 0) == 42

    AHRSProtocol.encodeProtocolSignedThousandthsFloat(32.0, data, 0)
    assert abs(AHRSProtocol.decodeProtocolSignedThousandthsFloat(data, 0) - 32.0) < 0.001