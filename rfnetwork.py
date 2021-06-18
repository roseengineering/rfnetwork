
import warnings
import numpy as np
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def parse_args():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-n", "--name", default='network', help='subcircuit name')
    parser.add_argument("-s", "--source", type=complex, default=None, help='source impedance')
    parser.add_argument("-l", "--line", type=float, default=50, help='load impedance or Zo')
    parser.add_argument("-q", "--quality", type=float, default=1, help='q factor')
    parser.add_argument("-f", "--frequency", type=float, default=None, help='frequency')
    parser.add_argument("-b", "--bandwidth", type=float, default=None, help='bandwidth')
    parser.add_argument("-r", "--reverse", action="store_true", help="reverse")
    parser.add_argument("--lcc", action="store_true", help="use a LCC network")
    parser.add_argument("--tee", action="store_true", help="use a TEE network")
    parser.add_argument("--pi", action="store_true", help="use a PI network")
    return parser.parse_args()


def divide(a, b):
    with np.errstate(divide='ignore'):
        return np.divide(a, b)


def s2p(zg):
    rs = zg.real
    xs = zg.imag
    rp = rs * (1 + (xs / rs)**2)
    xp = divide(rp, xs / rs)
    return rp, xp


def net_lcc(zg, rl, q):
    # o--L1--+--C2--o
    #        C1
    # only applicable for rg < rl
    assert(zg.real < rl)
    b = zg.real * (q**2 + 1)
    a = np.sqrt(b / rl - 1)
    xl1 = q * zg.real - zg.imag
    xc2 = a * rl
    xc1 = divide(b, q - a)
    return xl1, -xc1, -xc2


def net_pi(zg, rl, q):
    # o--+--L1--+--o
    #    C1     C2
    # only practical for rg > rl otherwise L1 becomes too small
    rg, xg = s2p(zg)
    if rg < rl: warnings.warn("Impractical")
    xc1 = rg / q
    xc1 = 1 / (1 / xc1 + 1 / xg)
    xc2 = rl * np.sqrt(rg / rl / ((q**2 + 1) - (rg / rl)))
    xl1 = (q * rg + rg * rl / xc2) / (q**2 + 1)
    return -xc1, xl1, -xc2


def net_tee(zg, rl, q):
    # o--L1--+--L2--o
    #        C1
    # very high collector efficiencies
    # rg can be > or < rl
    a = zg.real * (q**2 + 1)
    b = np.sqrt(a / rl - 1)
    xl1 = q * zg.real - zg.imag
    xl2 = rl * b
    xc1 = a / (q + b)
    return xl1, -xc1, xl2


def validate(cir, mode, zg, rl):
    x = rl
    for i in reversed(range(len(cir))):
        if i % 2 != (mode == 's'):  # series
            x += 1j * cir[i] 
        else:                       # shunt
            x = 1 / (-1j / cir[i] + 1 / x)
    err = abs(zg - np.conjugate(x))
    assert(err < 1e-9)
    return x


def netlist(cir, f, mode, name):
    n = 0
    node = 1
    data = []
    for n, x in enumerate(cir):
        a = node
        if n % 2 != (mode == 's'):
            b = a + 1
            node = b
        else:
            b = 0

        if x < 0:
            val = -1 / (2 * np.pi * f * x)
            data.append('C{} {} {} {:.6g}pF'.format(n+1, a, b, val*1e12))
        else:
            val = x / (2 * np.pi * f)
            data.append('L{} {} {} {:.6g}nH'.format(n+1, a, b, val*1e9)) 

    print('.subckt {} 1 {}'.format(name, node))
    for ln in data: print(ln)
    print('.ends')


def main():
    if not args.source:
        raise RuntimeError("Please give a source impedance.")
    if args.line.imag != 0:
        raise RuntimeError("The load impedance cannot be complex.")

    name = args.name
    f = args.frequency
    bw = args.bandwidth 
    zg = args.source
    rl = args.line
    q = args.quality
    if f and bw: 
        q = f / bw

    # pick network
    if args.lcc:
        cir = net_lcc(zg=zg, rl=rl, q=q)
        mode = 's'
    elif args.tee:
        cir = net_tee(zg=zg, rl=rl, q=q)
        mode = 's'
    elif args.pi:
        cir = net_pi(zg=zg, rl=rl, q=q)
        mode = 'p'
    else:
        print(s2p(zg))
        raise RuntimeError("Please pick a matching network.")

    zin = validate(cir, mode, zg, rl)

    if args.reverse:
        cir = list(reversed(cir))

    if not f: 
        print('The subcircuit cannot be printed since no frequency has given.') 
        print('Here are the impedances instead:', list(cir))
        return

    print('* Fd  = {:.6g} MHz'.format(f / 1e6))
    print('* BW  = {:.6g} MHz'.format(f / q / 1e6))
    print('* Q   = {:.6g}'.format(q))
    print('* RL  = {:.6g}'.format(rl))
    print('* ZG  = {:.6g}'.format(zg))
    print('* Zin = {:.6g}'.format(np.round(zin, 9)))
    print('')

    netlist(cir, f=f, mode=mode, name=name)


if __name__ == "__main__":
    args = parse_args()
    main()


