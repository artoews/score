''' Embed flattened k-space samples into a full-size Cartesian grid. '''
import argparse
import cfl
from os import path

from utils import embed_kspace

p = argparse.ArgumentParser(description="Embed flattened k-space samples into a full-size Cartesian grid.")
p.add_argument("root", type=str, help="Directory containing ksp_flat.{cfl,hdr} and pat.{cfl,hdr}. Output ksp.{cfl,hdr} is saved here too.")

if __name__ == "__main__":

    args = p.parse_args()

    ksp_flat = cfl.readcfl(path.join(args.root, 'ksp_flat'))
    pat = cfl.readcfl(path.join(args.root, 'pat')).astype(bool)

    ksp = embed_kspace(ksp_flat, pat)

    cfl.writecfl(path.join(args.root, 'ksp'), ksp)
