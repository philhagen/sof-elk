#!/usr/bin/python3

long = {}
long[1] = 'FIN'
long[2] = 'SYN'
long[4] = 'RST'
long[8] = 'PSH'
long[16] = 'ACK'
long[32] = 'URG'
long[64] = 'ECE'
long[128] = 'CWR'
long[256] = 'NS'

nfdump = {}
nfdump[1] = 'F'
nfdump[2] = 'S'
nfdump[4] = 'R'
nfdump[8] = 'P'
nfdump[16] = 'A'
nfdump[32] = 'U'


def convert(val, type='nfdump'):
    longflags = []
    nfdumpflags = ''
    for flag in (256, 128, 64, 32, 16, 8, 4, 2, 1):
        if val & flag != 0:
            longflags.append(long[flag])
            if flag <= 63:
                nfdumpflags += nfdump[flag]
        elif flag <= 63:
            nfdumpflags += '.'

    if longflags == []:
            longflags.append('NULL')
    longflags.reverse()
    longflags_string = '-'.join(longflags)

    if val > 63:
        nfdumpflags = '0x%X' % val

    if type == 'long':
        print('"0x%X": "%s"' % (val, longflags_string))
    elif type == 'nfdump':
        print('"%d": "%s"' % (val, nfdumpflags))


for i in range(0, 256):
    convert(i, 'nfdump')
