from dataclasses import dataclass, field
import numpy as np
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

@dataclass
class Device:
    device_id: str = "rising_moon"
    server_ip: str = "10.85.61.2"
    stream_port: int = 8000

@dataclass
class Camera:
    id: int = 1
    sensor: str = "IMX296"  
    res_w: int = 1280      
    res_h: int = 720      
    gain: int = 25
    fps: int = 60
    auto_exposure: int = 1
    exposure: int = 1

@dataclass
class Environment:
    tag_size_m: float = 0.1651
    tag_map: dict = field(default_factory=lambda: Environment.load_tag_map())

    @staticmethod
    def load_tag_map():
        map_file = os.path.join(script_dir, "2025-official.json")
        try:
            with open(map_file, "r") as file:
                return json.load(file) 
        except Exception as e:
            print(f"Error loading tag map: {e}")
            return {}

@dataclass
class Intrinsics:
    camera_matrix: np.ndarray = field(default_factory=lambda: np.array([]))
    distortion_coefficients: np.ndarray = field(default_factory=lambda: np.array([]))

@dataclass
class RisingMoonConfiguration:
    camera: Camera = field(default_factory=Camera)
    intrinsics: Intrinsics = field(default_factory=Intrinsics)
    device: Device = field(default_factory=Device)
    environment: Environment = field(default_factory=Environment)