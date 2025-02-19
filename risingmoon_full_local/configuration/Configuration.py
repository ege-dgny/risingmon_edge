from dataclasses import dataclass, field
import numpy

@dataclass
class Device:
    device_id: str = "polaris"
    server_ip: str = "10.16.78.2"
    stream_port: int = 8000

@dataclass
class Camera:
    id: int = 0
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
    tag_map: any = "frc2025r2_ANDYMARK.fmap"

@dataclass
class Intrinsics:
    camera_matrix: numpy._typing.NDArray[numpy.float64] = field(default_factory=lambda: numpy.array([]))
    distortion_coefficients: numpy._typing.NDArray[numpy.float64] = field(default_factory=lambda: numpy.array([]))

# Main config class
@dataclass
class PolarisConfiguration:
    camera: Camera = field(default_factory=Camera)
    intrinsics: Intrinsics = field(default_factory=Intrinsics)
    device: Device = field(default_factory=Device)
    environment: Environment = field(default_factory=Environment)
