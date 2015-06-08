from pycanopen import *
nmtECData=(c_uint8*8)()
nmtECData[:]=[5, 0, 0, 0, 0, 0, 0, 0]
pdo1Data=(c_uint8*8)()
pdo1Data[:]=[0xdb, 0x11, 0x64, 1, 0, 0, 0, 0]
personality=[CANopenFrame(function_code = 0xe, data = CANopenPayload(data = nmtECData), data_len = 1),
             CANopenFrame(function_code = 0x4, data = CANopenPayload(data = pdo1Data), data_len = 8),
             CANopenFrame(function_code = 0x4, data = CANopenPayload(data = pdo1Data), data_len = 8)]
personalityLengths=[2, 3]