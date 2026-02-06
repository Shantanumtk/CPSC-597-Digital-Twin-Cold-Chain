"""
Cold Chain Digital Twin - Edge Layer Sensor Simulator
Simulates 20+ IoT sensors for cold rooms and refrigerated trucks
Publishing telemetry via MQTT (QoS 1/2, JSON payloads)
"""

import json
import time
import random
import threading
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional
import paho.mqtt.client as mqtt


# Configuration from environment
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_QOS = int(os.getenv("MQTT_QOS", 1))
PUBLISH_INTERVAL = float(os.getenv("PUBLISH_INTERVAL", 5.0))  # seconds


@dataclass
class ColdRoomTelemetry:
    """Telemetry payload for cold room sensors"""
    sensor_id: str
    site_id: str
    room_id: str
    asset_type: str
    timestamp: str
    temperature_c: float
    humidity_pct: float
    door_open: bool
    compressor_running: bool
    compressor_cycle_count: int
    power_status: str  # "normal", "brownout", "backup"
    

@dataclass
class TruckTelemetry:
    """Telemetry payload for refrigerated truck sensors"""
    sensor_id: str
    truck_id: str
    fleet_id: str
    asset_type: str
    timestamp: str
    temperature_c: float
    humidity_pct: float
    door_open: bool
    compressor_running: bool
    latitude: float
    longitude: float
    speed_kmh: float
    engine_running: bool


class ColdRoomSensor:
    """Simulates a cold room with realistic thermal dynamics"""
    
    def __init__(self, site_id: str, room_id: str, target_temp: float = -20.0):
        self.sensor_id = f"sensor-room-{site_id}-{room_id}"
        self.site_id = site_id
        self.room_id = room_id
        self.target_temp = target_temp
        self.current_temp = target_temp + random.uniform(-0.5, 0.5)
        self.humidity = random.uniform(45, 55)
        self.door_open = False
        self.compressor_running = True
        self.compressor_cycles = 0
        self.power_status = "normal"
        self.door_open_since: Optional[float] = None
        
        # Thermal dynamics parameters
        self.cooling_rate = 0.3  # degrees per interval when compressor on
        self.warming_rate = 0.1  # degrees per interval ambient warming
        self.door_warming_rate = 0.8  # faster warming when door open
        
    def simulate_step(self):
        """Advance simulation by one time step"""
        
        # Random events
        self._simulate_door_events()
        self._simulate_compressor_events()
        self._simulate_power_events()
        
        # Thermal dynamics
        if self.door_open:
            # Rapid warming when door is open
            self.current_temp += random.uniform(0.3, self.door_warming_rate)
            self.humidity += random.uniform(1, 3)
        elif self.compressor_running:
            # Cooling when compressor is on
            if self.current_temp > self.target_temp:
                self.current_temp -= random.uniform(0.1, self.cooling_rate)
        else:
            # Slow warming when compressor is off
            self.current_temp += random.uniform(0.05, self.warming_rate)
            
        # Humidity regulation
        if self.compressor_running and not self.door_open:
            self.humidity = max(40, self.humidity - random.uniform(0, 0.5))
        
        # Clamp values to realistic ranges
        self.humidity = max(30, min(95, self.humidity))
        
        # Add sensor noise
        temp_noise = random.gauss(0, 0.1)
        humidity_noise = random.gauss(0, 0.5)
        
        return ColdRoomTelemetry(
            sensor_id=self.sensor_id,
            site_id=self.site_id,
            room_id=self.room_id,
            asset_type="cold_room",
            timestamp=datetime.now(timezone.utc).isoformat(),
            temperature_c=round(self.current_temp + temp_noise, 2),
            humidity_pct=round(self.humidity + humidity_noise, 1),
            door_open=self.door_open,
            compressor_running=self.compressor_running,
            compressor_cycle_count=self.compressor_cycles,
            power_status=self.power_status
        )
    
    def _simulate_door_events(self):
        """Simulate realistic door open/close patterns"""
        if self.door_open:
            # Door has been open - check if it should close
            if self.door_open_since:
                open_duration = time.time() - self.door_open_since
                # Most door events are 30-120 seconds (loading)
                if open_duration > random.uniform(30, 120):
                    self.door_open = False
                    self.door_open_since = None
        else:
            # 2% chance of door opening each interval (simulates loading events)
            if random.random() < 0.02:
                self.door_open = True
                self.door_open_since = time.time()
                
    def _simulate_compressor_events(self):
        """Simulate compressor cycling"""
        if self.compressor_running:
            # Compressor cycles off when temp is well below target
            if self.current_temp < self.target_temp - 2:
                if random.random() < 0.1:
                    self.compressor_running = False
        else:
            # Compressor turns on when temp rises above target
            if self.current_temp > self.target_temp + 1:
                self.compressor_running = True
                self.compressor_cycles += 1
                
    def _simulate_power_events(self):
        """Simulate power fluctuations"""
        if self.power_status == "normal":
            # 0.5% chance of power issue
            if random.random() < 0.005:
                self.power_status = random.choice(["brownout", "backup"])
        else:
            # 20% chance of returning to normal each interval
            if random.random() < 0.2:
                self.power_status = "normal"
    
    @property
    def mqtt_topic(self) -> str:
        return f"warehouse/{self.site_id}/room/{self.room_id}/telemetry"


class TruckSensor:
    """Simulates a refrigerated truck with GPS and thermal dynamics"""
    
    # Predefined routes (lat, lon waypoints) - California area
    ROUTES = {
        "route_la_sf": [
            (34.0522, -118.2437),  # Los Angeles
            (34.4208, -119.6982),  # Santa Barbara
            (35.2828, -120.6596),  # San Luis Obispo
            (36.7783, -119.4179),  # Fresno
            (37.3382, -121.8863),  # San Jose
            (37.7749, -122.4194),  # San Francisco
        ],
        "route_sd_la": [
            (32.7157, -117.1611),  # San Diego
            (33.1959, -117.3795),  # Oceanside
            (33.4484, -117.6323),  # San Clemente
            (33.6846, -117.8265),  # Irvine
            (33.8366, -117.9143),  # Anaheim
            (34.0522, -118.2437),  # Los Angeles
        ],
        "route_fullerton_local": [
            (33.8704, -117.9242),  # Fullerton
            (33.8353, -117.9145),  # Anaheim
            (33.7879, -117.8531),  # Orange
            (33.7175, -117.8311),  # Irvine
            (33.8704, -117.9242),  # Back to Fullerton
        ]
    }
    
    def __init__(self, truck_id: str, fleet_id: str = "fleet1", 
                 target_temp: float = -18.0, route_name: str = None):
        self.sensor_id = f"sensor-truck-{truck_id}"
        self.truck_id = truck_id
        self.fleet_id = fleet_id
        self.target_temp = target_temp
        self.current_temp = target_temp + random.uniform(-0.5, 0.5)
        self.humidity = random.uniform(40, 50)
        self.door_open = False
        self.compressor_running = True
        self.engine_running = True
        
        # GPS simulation
        self.route_name = route_name or random.choice(list(self.ROUTES.keys()))
        self.route = self.ROUTES[self.route_name]
        self.route_index = 0
        self.route_progress = 0.0  # 0-1 between waypoints
        self.speed = random.uniform(60, 90)  # km/h
        
        # Position
        self.latitude, self.longitude = self.route[0]
        
        # Thermal dynamics
        self.cooling_rate = 0.25
        self.warming_rate = 0.15
        self.door_warming_rate = 1.0
        self.door_open_since: Optional[float] = None
        
    def simulate_step(self):
        """Advance simulation by one time step"""
        
        self._simulate_movement()
        self._simulate_door_events()
        self._simulate_thermal_dynamics()
        
        # Add sensor noise
        temp_noise = random.gauss(0, 0.15)
        humidity_noise = random.gauss(0, 0.8)
        
        return TruckTelemetry(
            sensor_id=self.sensor_id,
            truck_id=self.truck_id,
            fleet_id=self.fleet_id,
            asset_type="refrigerated_truck",
            timestamp=datetime.now(timezone.utc).isoformat(),
            temperature_c=round(self.current_temp + temp_noise, 2),
            humidity_pct=round(self.humidity + humidity_noise, 1),
            door_open=self.door_open,
            compressor_running=self.compressor_running,
            latitude=round(self.latitude, 6),
            longitude=round(self.longitude, 6),
            speed_kmh=round(self.speed, 1) if self.engine_running else 0,
            engine_running=self.engine_running
        )
    
    def _simulate_movement(self):
        """Simulate truck movement along route"""
        if not self.engine_running:
            self.speed = 0
            return
            
        # Progress along route
        self.route_progress += random.uniform(0.01, 0.03)
        
        if self.route_progress >= 1.0:
            # Move to next waypoint
            self.route_index = (self.route_index + 1) % len(self.route)
            self.route_progress = 0.0
            
            # Chance to stop at waypoint (delivery)
            if random.random() < 0.3:
                self.engine_running = False
                self.door_open = True
                self.door_open_since = time.time()
        
        # Interpolate position between waypoints
        current_wp = self.route[self.route_index]
        next_wp = self.route[(self.route_index + 1) % len(self.route)]
        
        self.latitude = current_wp[0] + (next_wp[0] - current_wp[0]) * self.route_progress
        self.longitude = current_wp[1] + (next_wp[1] - current_wp[1]) * self.route_progress
        
        # Vary speed
        self.speed = max(0, min(120, self.speed + random.uniform(-5, 5)))
        
    def _simulate_door_events(self):
        """Simulate door and delivery events"""
        if self.door_open and self.door_open_since:
            open_duration = time.time() - self.door_open_since
            # Delivery stops are 60-300 seconds
            if open_duration > random.uniform(60, 300):
                self.door_open = False
                self.door_open_since = None
                self.engine_running = True
                self.speed = random.uniform(30, 50)
                
    def _simulate_thermal_dynamics(self):
        """Simulate temperature changes based on conditions"""
        
        # External factors
        if self.door_open:
            self.current_temp += random.uniform(0.5, self.door_warming_rate)
            self.humidity += random.uniform(2, 5)
        elif not self.compressor_running or not self.engine_running:
            # Slower cooling without compressor
            self.current_temp += random.uniform(0.05, self.warming_rate)
        else:
            # Active cooling
            if self.current_temp > self.target_temp:
                self.current_temp -= random.uniform(0.1, self.cooling_rate)
                
        # Compressor logic
        if self.engine_running:
            if self.current_temp > self.target_temp + 2:
                self.compressor_running = True
            elif self.current_temp < self.target_temp - 1:
                self.compressor_running = random.random() > 0.3
                
        # Clamp humidity
        self.humidity = max(30, min(95, self.humidity))
    
    @property
    def mqtt_topic(self) -> str:
        return f"fleet/{self.truck_id}/telemetry"


class SensorFleetSimulator:
    """Manages a fleet of simulated sensors"""
    
    def __init__(self, num_cold_rooms: int = 10, num_trucks: int = 12):
        self.sensors = []
        self.client: Optional[mqtt.Client] = None
        self.running = False
        
        # Create cold room sensors across multiple sites
        sites = ["site1", "site2", "site3"]
        for i in range(num_cold_rooms):
            site = sites[i % len(sites)]
            room_id = f"room{i + 1}"
            # Vary target temps: freezer (-20), refrigerator (2-8), etc.
            target_temp = random.choice([-20, -18, -15, 2, 4, 8])
            self.sensors.append(ColdRoomSensor(site, room_id, target_temp))
            
        # Create truck sensors
        for i in range(num_trucks):
            truck_id = f"truck{i + 1:02d}"
            target_temp = random.choice([-18, -15, 2, 4])
            self.sensors.append(TruckSensor(truck_id, target_temp=target_temp))
            
        print(f"Initialized {len(self.sensors)} sensors:")
        print(f"  - {num_cold_rooms} cold rooms across {len(sites)} sites")
        print(f"  - {num_trucks} refrigerated trucks")
        
    def connect_mqtt(self):
        """Establish MQTT connection"""
        self.client = mqtt.Client(
            client_id=f"cold-chain-simulator-{random.randint(1000, 9999)}",
            protocol=mqtt.MQTTv311
        )
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            else:
                print(f"Failed to connect, return code: {rc}")
                
        def on_publish(client, userdata, mid):
            pass  # Successful publish
            
        self.client.on_connect = on_connect
        self.client.on_publish = on_publish
        
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"MQTT connection error: {e}")
            return False
            
    def publish_telemetry(self, sensor, telemetry):
        """Publish sensor telemetry to MQTT"""
        if not self.client:
            return False
            
        topic = sensor.mqtt_topic
        payload = json.dumps(asdict(telemetry))
        
        result = self.client.publish(topic, payload, qos=MQTT_QOS)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return True
        else:
            print(f"Publish failed for {topic}: {result.rc}")
            return False
            
    def run(self):
        """Main simulation loop"""
        if not self.connect_mqtt():
            print("Failed to connect to MQTT broker. Exiting.")
            return
            
        self.running = True
        iteration = 0
        
        print(f"\nStarting telemetry simulation (interval: {PUBLISH_INTERVAL}s)")
        print("-" * 60)
        
        try:
            while self.running:
                iteration += 1
                published = 0
                
                for sensor in self.sensors:
                    telemetry = sensor.simulate_step()
                    if self.publish_telemetry(sensor, telemetry):
                        published += 1
                        
                # Status update every 10 iterations
                if iteration % 10 == 0:
                    # Sample a truck and room for status display
                    truck = next((s for s in self.sensors if isinstance(s, TruckSensor)), None)
                    room = next((s for s in self.sensors if isinstance(s, ColdRoomSensor)), None)
                    
                    print(f"\n[Iteration {iteration}] Published {published}/{len(self.sensors)} messages")
                    if truck:
                        print(f"  Truck {truck.truck_id}: {truck.current_temp:.1f}°C, "
                              f"GPS: ({truck.latitude:.4f}, {truck.longitude:.4f}), "
                              f"Speed: {truck.speed:.0f} km/h")
                    if room:
                        print(f"  Room {room.room_id}: {room.current_temp:.1f}°C, "
                              f"Door: {'OPEN' if room.door_open else 'closed'}, "
                              f"Compressor: {'ON' if room.compressor_running else 'OFF'}")
                
                time.sleep(PUBLISH_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\nShutting down simulator...")
        finally:
            self.running = False
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            print("Simulator stopped.")
            
    def stop(self):
        """Stop the simulation"""
        self.running = False


def main():
    """Entry point"""
    num_rooms = int(os.getenv("NUM_COLD_ROOMS", 10))
    num_trucks = int(os.getenv("NUM_TRUCKS", 12))
    
    print("=" * 60)
    print("Cold Chain Digital Twin - Edge Layer Simulator")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  QoS Level: {MQTT_QOS}")
    print(f"  Publish Interval: {PUBLISH_INTERVAL}s")
    print(f"  Cold Rooms: {num_rooms}")
    print(f"  Trucks: {num_trucks}")
    print()
    
    simulator = SensorFleetSimulator(num_rooms, num_trucks)
    simulator.run()


if __name__ == "__main__":
    main()