#!/usr/bin/env python3
"""
Autonomica System Metrics Collector
This script collects system performance metrics and exposes them via HTTP for Prometheus scraping.

Implements part of Subtask 8.2: Set up performance metrics collection
"""

import time
import psutil
import threading
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info
from prometheus_client.core import REGISTRY
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# System metrics
SYSTEM_INFO = Info('system', 'System information')
CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage', ['core'])
MEMORY_USAGE = Gauge('system_memory_usage_bytes', 'Memory usage in bytes')
MEMORY_AVAILABLE = Gauge('system_memory_available_bytes', 'Available memory in bytes')
MEMORY_PERCENT = Gauge('system_memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('system_disk_usage_bytes', 'Disk usage in bytes', ['mountpoint'])
DISK_PERCENT = Gauge('system_disk_usage_percent', 'Disk usage percentage', ['mountpoint'])
NETWORK_BYTES_SENT = Counter('system_network_bytes_sent_total', 'Total bytes sent', ['interface'])
NETWORK_BYTES_RECV = Counter('system_network_bytes_recv_total', 'Total bytes received', ['interface'])
NETWORK_PACKETS_SENT = Counter('system_network_packets_sent_total', 'Total packets sent', ['interface'])
NETWORK_PACKETS_RECV = Counter('system_network_packets_recv_total', 'Total packets received', ['interface'])
LOAD_AVERAGE = Gauge('system_load_average', 'System load average', ['period'])
PROCESS_COUNT = Gauge('system_process_count', 'Number of running processes')
BOOT_TIME = Gauge('system_boot_time_seconds', 'System boot time in seconds since epoch')

# Performance metrics
CPU_FREQ = Gauge('system_cpu_frequency_hz', 'CPU frequency in Hz', ['core'])
CPU_TEMP = Gauge('system_cpu_temperature_celsius', 'CPU temperature in Celsius', ['core'])
SWAP_USAGE = Gauge('system_swap_usage_bytes', 'Swap usage in bytes')
SWAP_PERCENT = Gauge('system_swap_usage_percent', 'Swap usage percentage')

# Container metrics (if running in Docker)
CONTAINER_CPU_USAGE = Gauge('container_cpu_usage_percent', 'Container CPU usage percentage')
CONTAINER_MEMORY_USAGE = Gauge('container_memory_usage_bytes', 'Container memory usage in bytes')
CONTAINER_DISK_IO_READ = Counter('container_disk_io_read_bytes_total', 'Container disk read bytes')
CONTAINER_DISK_IO_WRITE = Counter('container_disk_io_write_bytes_total', 'Container disk write bytes')

class SystemMetricsCollector:
    """Collects system metrics and updates Prometheus metrics."""
    
    def __init__(self, collection_interval=15):
        self.collection_interval = collection_interval
        self.running = False
        self.collector_thread = None
        
        # Initialize system info
        self._init_system_info()
    
    def _init_system_info(self):
        """Initialize system information metrics."""
        try:
            # System information
            SYSTEM_INFO.info({
                'os': psutil.sys.platform,
                'python_version': psutil.sys.version,
                'architecture': psutil.sys.architecture()[0],
                'machine': psutil.sys.machine(),
                'processor': psutil.sys.processor()
            })
            
            # Boot time
            BOOT_TIME.set(psutil.boot_time())
            
            logger.info("System information initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize system info: {e}")
    
    def collect_cpu_metrics(self):
        """Collect CPU-related metrics."""
        try:
            # CPU usage per core
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            for i, percent in enumerate(cpu_percent):
                CPU_USAGE.labels(core=f"cpu{i}").set(percent)
            
            # CPU frequency
            try:
                cpu_freq = psutil.cpu_freq(percpu=True)
                if cpu_freq:
                    for i, freq in enumerate(cpu_freq):
                        if freq and freq.current:
                            CPU_FREQ.labels(core=f"cpu{i}").set(freq.current)
            except Exception:
                pass  # CPU frequency not available on all systems
            
            # CPU temperature (Linux only)
            try:
                if psutil.sys.platform.startswith('linux'):
                    import subprocess
                    result = subprocess.run(['sensors', '-j'], capture_output=True, text=True)
                    if result.returncode == 0:
                        import json
                        sensors_data = json.loads(result.stdout)
                        for core, temp in self._extract_cpu_temps(sensors_data):
                            CPU_TEMP.labels(core=core).set(temp)
            except Exception:
                pass  # Temperature sensors not available
            
            logger.debug("CPU metrics collected successfully")
        except Exception as e:
            logger.error(f"Failed to collect CPU metrics: {e}")
    
    def _extract_cpu_temps(self, sensors_data):
        """Extract CPU temperatures from sensors output."""
        temps = []
        try:
            for device, data in sensors_data.items():
                if 'temp' in data:
                    for temp_key, temp_data in data['temp'].items():
                        if 'temp1_input' in temp_data:
                            temp = temp_data['temp1_input']
                            if temp is not None:
                                temps.append((device, temp))
        except Exception:
            pass
        return temps
    
    def collect_memory_metrics(self):
        """Collect memory-related metrics."""
        try:
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            MEMORY_AVAILABLE.set(memory.available)
            MEMORY_PERCENT.set(memory.percent)
            
            # Swap metrics
            swap = psutil.swap_memory()
            SWAP_USAGE.set(swap.used)
            SWAP_PERCENT.set(swap.percent)
            
            logger.debug("Memory metrics collected successfully")
        except Exception as e:
            logger.error(f"Failed to collect memory metrics: {e}")
    
    def collect_disk_metrics(self):
        """Collect disk-related metrics."""
        try:
            disk_usage = psutil.disk_usage('/')
            DISK_USAGE.labels(mountpoint='/').set(disk_usage.used)
            DISK_PERCENT.labels(mountpoint='/').set(disk_usage.percent)
            
            # Additional mount points
            try:
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    if partition.mountpoint and partition.mountpoint != '/':
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            DISK_USAGE.labels(mountpoint=partition.mountpoint).set(usage.used)
                            DISK_PERCENT.labels(mountpoint=partition.mountpoint).set(usage.percent)
                        except Exception:
                            pass  # Skip inaccessible mount points
            except Exception:
                pass
            
            logger.debug("Disk metrics collected successfully")
        except Exception as e:
            logger.error(f"Failed to collect disk metrics: {e}")
    
    def collect_network_metrics(self):
        """Collect network-related metrics."""
        try:
            net_io = psutil.net_io_counters(pernic=True)
            for interface, stats in net_io.items():
                NETWORK_BYTES_SENT.labels(interface=interface).inc(stats.bytes_sent)
                NETWORK_BYTES_RECV.labels(interface=interface).inc(stats.bytes_recv)
                NETWORK_PACKETS_SENT.labels(interface=interface).inc(stats.packets_sent)
                NETWORK_PACKETS_RECV.labels(interface=interface).inc(stats.packets_recv)
            
            logger.debug("Network metrics collected successfully")
        except Exception as e:
            logger.error(f"Failed to collect network metrics: {e}")
    
    def collect_system_metrics(self):
        """Collect general system metrics."""
        try:
            # Load average
            load_avg = psutil.getloadavg()
            LOAD_AVERAGE.labels(period='1min').set(load_avg[0])
            LOAD_AVERAGE.labels(period='5min').set(load_avg[1])
            LOAD_AVERAGE.labels(period='15min').set(load_avg[2])
            
            # Process count
            PROCESS_COUNT.set(len(psutil.pids()))
            
            logger.debug("System metrics collected successfully")
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def collect_container_metrics(self):
        """Collect container-specific metrics if running in Docker."""
        try:
            # Check if running in container
            if os.path.exists('/.dockerenv'):
                # Container CPU and memory usage
                process = psutil.Process()
                CONTAINER_CPU_USAGE.set(process.cpu_percent())
                CONTAINER_MEMORY_USAGE.set(process.memory_info().rss)
                
                # Container disk I/O
                io_counters = process.io_counters()
                CONTAINER_DISK_IO_READ.inc(io_counters.read_bytes)
                CONTAINER_DISK_IO_WRITE.inc(io_counters.write_bytes)
                
                logger.debug("Container metrics collected successfully")
        except Exception as e:
            logger.debug(f"Container metrics not available: {e}")
    
    def collect_all_metrics(self):
        """Collect all system metrics."""
        try:
            self.collect_cpu_metrics()
            self.collect_memory_metrics()
            self.collect_disk_metrics()
            self.collect_network_metrics()
            self.collect_system_metrics()
            self.collect_container_metrics()
            
            logger.info("All system metrics collected successfully")
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
    
    def start_collection(self):
        """Start the metrics collection loop."""
        if self.running:
            logger.warning("Metrics collection already running")
            return
        
        self.running = True
        self.collector_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collector_thread.start()
        logger.info(f"Metrics collection started with {self.collection_interval}s interval")
    
    def stop_collection(self):
        """Stop the metrics collection loop."""
        self.running = False
        if self.collector_thread:
            self.collector_thread.join(timeout=5)
        logger.info("Metrics collection stopped")
    
    def _collection_loop(self):
        """Main collection loop."""
        while self.running:
            try:
                self.collect_all_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(self.collection_interval)

def main():
    """Main function to run the metrics collector."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomica System Metrics Collector')
    parser.add_argument('--port', type=int, default=8000, help='HTTP server port (default: 8000)')
    parser.add_argument('--interval', type=int, default=15, help='Collection interval in seconds (default: 15)')
    parser.add_argument('--host', default='0.0.0.0', help='HTTP server host (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Autonomica System Metrics Collector...")
    logger.info(f"📊 Metrics will be available at http://{args.host}:{args.port}/metrics")
    logger.info(f"⏰ Collection interval: {args.interval} seconds")
    
    try:
        # Start HTTP server for Prometheus scraping
        start_http_server(args.port, addr=args.host)
        logger.info(f"✅ HTTP server started on {args.host}:{args.port}")
        
        # Create and start metrics collector
        collector = SystemMetricsCollector(collection_interval=args.interval)
        collector.start_collection()
        
        logger.info("✅ Metrics collector started successfully")
        logger.info("📋 Press Ctrl+C to stop")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal, shutting down...")
            collector.stop_collection()
            logger.info("✅ Shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Failed to start metrics collector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()