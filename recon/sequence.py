''' Sequence parameters '''
from __future__ import annotations

import numpy as np
import yaml

from dataclasses import dataclass
from enum import IntEnum

class Dim(IntEnum):
    X = 0 # in-plane, susceptible to distortion 
    Y = 1 # in-plane, not susceptible to distortion
    Z = 2 # slice, selectively excited
    C = 3 # coil
    M = 4 # maps (required by bart for espirit with -m option >1)
    B = 5 # bin/slab

@dataclass
class Seq:
    sampling: str
    x_gradient_hz_mm: float
    z_gradient_hz_mm: float
    z_centers_mm: list[float]
    xyz_resolution_mm: list[float]
    corners: list[dict]
    path_to_src: str | None = None
    partial_fourier_fraction: float = 1.0

    @classmethod
    def from_yaml(cls, path: str) -> Seq:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_yaml(self, path: str):
        with open(path, "w") as f:
            yaml.dump(self.__dict__, f)
    
    @property
    def shear_factor(self) -> float:
        return self.z_gradient_hz_mm / self.x_gradient_hz_mm
    
    @property
    def shear_angle(self) -> float:
        return np.arctan(self.shear_factor)
    
    def field_of_view_mm(self, shape) -> np.ndarray:
        return np.array([shape[i] * self.xyz_resolution_mm[i] for i in range(3)], dtype=float)
    
    def trajectory(self, shape: tuple) -> np.ndarray:
        ''' Get trajectory for k-space samples with 1/FOV units. '''
        traj = np.mgrid[
            -shape[Dim.X]//2:shape[Dim.X]//2,
            -shape[Dim.Y]//2:shape[Dim.Y]//2,
            -shape[Dim.Z]//2:shape[Dim.Z]//2
            ].astype(float)
        if self.sampling == 'gz_on':
            fov = self.field_of_view_mm(shape)
            traj[Dim.Z] += traj[Dim.X] * self.shear_factor * fov[Dim.Z] / fov[Dim.X]
        return traj[..., None, None, None] # (3, nx, ny, nz, 1, 1, 1)
