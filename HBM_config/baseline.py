import m5
from m5.objects import *
from caches import *

import argparse

parser = argparse.ArgumentParser(description='A O3 System with 2-level cache.')
parser.add\_argument("binary",default="",nargs="?",type=str,help="Path to the binary to execute.")
parser.add\_argument("--l1i_size",help="L1 instruction cache size, Default 16kB.")
parser.add\_argument("--l1d_size",help="L1 data cache size. Default: Default: 64kB.")
parser.add\_argument("--l2_size",help="L2 cache size. Default: 256kB.")

options = parser.parser\_args()

#Here is our baseline processor
#It uses the O3 processor as the model CPU
#It has two layer of caches--L1 and L2

#create system simObject
system = System()

#set clock and voltage of this system
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()

#set how memory will be simulated
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]

#create cpu
system.cpu = O3CPU()

#create L1 caches
system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()

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
system.l2cache = L2Cache()
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
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports


#create the process to simulate the system
binary = 'tests/test-progs/hello/bin/x86/linux/hello'

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
