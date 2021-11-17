#This configs file is designed for HW 2. But some features from HW 1 are kept for flexlibility
#It is not allowed to change CPU model in this configs file because we are studying how the opertaion latency and issue latency of pipelined processor impact the system.
import m5
from m5.objects import *
from caches import *
from cpu import *

import argparse

parser = argparse.ArgumentParser(description='A simple System with 2-level cache.')
parser.add_argument("binary",default="",nargs="?",type=str,help="Path to the binary to execute.")
parser.add_argument("--l1i_size",help="L1 instruction cache size, Default 16kB.")
parser.add_argument("--l1d_size",help="L1 data cache size. Default: Default: 64kB.")
parser.add_argument("--l2_size",help="L2 cache size. Default: 256kB.")
parser.add_argument("--clock",help="frequency used for the CPU. Default: 1GHz")
parser.add_argument("--memory",help="Main memory used. Choose from DDR3_1600_8x8, DDR3_2133_8x8, LPDDR2_S4_1066_1x32, HBM_1000_4H_1x64. Default: DDR3_1600_8x8")
parser.add_argument("--fpu_operation_latency", help="operation latency of the FloatSimd Functional unit")
parser.add_argument("--fpu_issue_latency", help="issue latency of the FloatSimd Functional unit")
parser.add_argument("--intfu_operation_latency", help="issue latency of the FloatSimd Functional unit")

options = parser.parse_args()

#create system simObject
system = System()

#set clock and voltage of this system
system.clk_domain = SrcClockDomain()
if not options or not options.clock:
    system.clk_domain.clock = '1GHz'
else:
    system.clk_domain.clock = options.clock
system.clk_domain.voltage_domain = VoltageDomain()

#set how memory will be simulated
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]

#create cpu
#define the operation latency and issue latency for my minor CPU
system.cpu = MyMinorCPU(options)

#create L1 caches
system.cpu.icache = L1ICache(options)
system.cpu.dcache = L1DCache(options)

#connect L1 caches to CPU
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

#create bus to connect L1 cache and L2 cache
system.l2bus = L2XBar()

system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

#system wide bus
system.membus = SystemXBar()

#connect L1 and L2 caches
system.l2cache = L2Cache(options)
system.l2cache.connectCPUSideBus(system.l2bus)
system.l2cache.connectMemSideBus(system.membus)

#set I/O controller and connect mem bus
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

#create a memory controller and connect it to the membus
system.mem_ctrl = MemCtrl()
if not options or not options.memory:
    system.mem_ctrl.dram = DDR3_1600_8x8()
else:
    if options.memory == "HBM_1000_4H_1x64":
        system.mem_ctrl.dram = HBM_1000_4H_1x64()
    elif options.memory == "LPDDR2_S4_1066_1x32":
        system.mem_ctrl.dram = LPDDR2_S4_1066_1x32()
    elif options.memory == "DDR3_2133_8x8":
        system.mem_ctrl.dram = DDR3_2133_8x8()
    elif options.memory == "DDR3_1600_8x8":
        system.mem_ctrl.dram = DDR3_1600_8x8()
    else:
        print("mem model does not exist, using default")
        system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports


#create the process to simulate the system
binary = 'tests/test-progs/daxpy/daxpy'

system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()



#Instantiate the system and begin execution
root = Root(full_system = False, system = system)
m5.instantiate()

#Begin simulation
print("Beginning simulation")
exit_event = m5.simulate()

#End simulation
print('Exiting @ tick {} because {}'.format(m5.curTick(), exit_event.getCause()))
